# backend/app/services/chat.py
import logging
import random
import time
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.conversation import (
    crud_conversation,
    crud_message,
    crud_conversation_detail,
)
from app.crud.channel import crud_channel
from app.crud.agent import crud_agent
from app.crud.bot import crud_bot
from app.agent.graph import run_agent
from app.agent.state import MessageItem
from app.config import settings

logger = logging.getLogger(__name__)

AGENT_NAMES = [
    "小美",
    "小丽",
    "小芳",
    "小燕",
    "小云",
    "小慧",
    "小雪",
    "小月",
]


def _error_reply(msg: str) -> dict:
    """快速构建错误回复"""
    return {
        "answer": msg,
        "role": "bot",
        "need_transfer": False,
        "agent_name": None,
        "message_id": None,
        "intent": None,
        "emotion": None,
        "answer_source": "error",
    }


# ==================== 用户信息摘要 ====================


async def build_user_summary(
    db: AsyncSession,
    user_id: Optional[int],
) -> Optional[str]:
    """构建用户信息摘要，注入Agent Prompt"""
    if not user_id:
        return None

    # 防御性类型转换，确保一定是 int
    try:
        user_id = int(user_id)
    except (TypeError, ValueError):
        return None

    try:
        from app.crud.user import crud_user
        from app.agent.tools.order import query_recent_orders

        user = await crud_user.get(db, user_id)
        if not user:
            return None

        lines = [f"用户昵称：{user.nickname or user.username}"]

        orders_result = await query_recent_orders(
            db=db,
            user_id=user_id,
            limit=3,
        )

        if orders_result["success"] and orders_result["data"]["total"] > 0:
            orders = orders_result["data"]["orders"]
            lines.append(f"最近订单（共{len(orders)}条）：")
            for order in orders:
                lines.append(
                    f"  - 订单{order['order_no']} "
                    f"[{order['status_text']}] "
                    f"¥{order['total_amount']:.2f}"
                )

        return "\n".join(lines)

    except Exception as e:
        logger.error(f"构建用户摘要失败 user_id={user_id}: {e}")
        return None


# ==================== 对话历史构建 ====================


async def build_history(
    db: AsyncSession,
    conversation_id: int,
    rounds: int = 3,
) -> List[MessageItem]:
    """
    从数据库读取最近N轮对话历史

    ✅ 使用 sender_type 而不是 role
    sender_type: 0=用户 1=Bot 2=人工客服
    """
    messages = await crud_message.get_recent(
        db=db,
        conversation_id=conversation_id,
        rounds=rounds,
    )

    # ✅ 正确字段名：sender_type
    role_map = {0: "user", 1: "assistant", 2: "assistant"}
    history = []
    for msg in messages:
        history.append(
            MessageItem(
                role=role_map.get(msg.sender_type, "user"),  # ✅ sender_type
                content=msg.content or "",
            )
        )

    return history


# ==================== 获取Bot ID ====================


async def _get_bot_id(
    db: AsyncSession,
    channel,
    agent,
) -> Optional[int]:
    """
    获取Bot ID

    优先级：
    1. channel.bot_id（渠道直接绑定的Bot）
    2. 取第一个可用Bot（兜底）
    """
    # ✅ 从channel直接取bot_id
    if channel.bot_id:
        return channel.bot_id

    # 兜底：取第一个Bot
    logger.warning(f"渠道未绑定Bot channel_id={channel.id}，使用第一个可用Bot")
    bots = await crud_bot.get_list(db)
    if bots:
        return bots[0].id

    return None


# ==================== 核心对话处理 ====================


async def process_chat(
    query: str,
    conversation_id: int,
    channel_token: str,
    db: AsyncSession,
    user_id: Optional[int] = None,
) -> dict:
    """
    核心对话处理逻辑

    流程：
    1. 查询渠道和Agent配置
    2. 保存用户消息
    3. 查询是否已转人工
    4. 构建历史和用户摘要
    5. 运行Agent工作流
    6. 保存回复消息
    7. 处理转人工
    """
    # ── Step1：查询渠道配置 ──
    channel = await crud_channel.get_by_token(db, channel_token)
    if not channel:
        return _error_reply("服务配置错误，请联系管理员")

    agent = await crud_agent.get(db, channel.agent_id)
    if not agent:
        return _error_reply("服务配置错误，请联系管理员")

    # ✅ bot_id从channel取，不从agent取
    bot_id = await _get_bot_id(db, channel, agent)
    if not bot_id:
        logger.error(f"无可用Bot channel_id={channel.id}")
        return _error_reply("服务配置错误，暂无可用Bot")

    # ── Step2：保存用户消息 ──
    await crud_message.create(
        db=db,
        conversation_id=conversation_id,
        role=0,  # 0=用户
        content=query,
        message_type=0,
    )

    # ── Step3：查询会话状态 ──
    conversation = await crud_conversation.get(db, conversation_id)
    is_transferred = (
        conversation and conversation.is_transferred == 1
    )  # ✅ is_transferred
    current_agent_name = (
        conversation.staff_name if conversation else None
    )  # ✅ staff_name

    # ── Step4：已转人工，走人工模拟逻辑 ──
    if is_transferred:
        answer, msg = await _handle_human_agent_reply(
            query=query,
            conversation_id=conversation_id,
            agent_name=current_agent_name,
            db=db,
        )
        return {
            "answer": answer,
            "role": "agent",
            "need_transfer": False,
            "agent_name": current_agent_name,
            "message_id": msg.id,
            "intent": None,
            "emotion": None,
            "answer_source": "human_agent",
        }

    # ── Step5：Bot层拦截（关键词 + FAQ）→ 命中直接返回，不走Agent ──
    logger.info(
        f"process_chat开始 conversation_id={conversation_id} query={query[:50]}"
    )

    from app.services.bot.faq import process_faq

    print(f"[BOT] process_chat开始 conversation_id={conversation_id} bot_id={bot_id}")

    try:
        faq_hit, need_transfer = await process_faq(
            query=query,
            bot_id=bot_id,
            db=db,
        )
        print(
            f"[BOT] process_faq完成 faq_hit={'是' if faq_hit else '否'} need_transfer={need_transfer}"
        )
    except Exception as e:
        import traceback

        print(f"[ERROR] process_faq异常: {e}\n{traceback.format_exc()}")
        faq_hit = None
        need_transfer = False
        print("[BOT] process_faq异常，降级到Agent工作流")

    # 关键词触发转人工
    if need_transfer:
        agent_name = random.choice(AGENT_NAMES)
        await crud_conversation.set_transfer(
            db=db,
            conversation_id=conversation_id,
            agent_name=agent_name,
        )
        reply_role = 2
        msg = await crud_message.create(
            db=db,
            conversation_id=conversation_id,
            role=reply_role,
            content="已为您转接人工客服，请稍候...",
            message_type=0,
            answer_source="keyword_transfer",
            sender_name=agent_name,
        )
        return {
            "answer": "已为您转接人工客服，请稍候...",
            "role": "agent",
            "need_transfer": True,
            "agent_name": agent_name,
            "message_id": msg.id,
            "intent": None,
            "emotion": None,
            "answer_source": "keyword_transfer",
        }

    # Bot FAQ命中 → 直接返回知识库原文，不走LLM
    if faq_hit:
        print(
            f"[BOT] ✅ Bot层直接返回（不走Agent） item_id={faq_hit.item_id} score={faq_hit.score}"
        )
        answer_html = faq_hit.answer

        msg = await crud_message.create(
            db=db,
            conversation_id=conversation_id,
            role=1,  # Bot
            content=answer_html,
            message_type=0,
            answer_source="faq_direct",
            intent=None,
            emotion=None,
            confidence_score=faq_hit.score,
        )
        return {
            "answer": answer_html,
            "role": "bot",
            "need_transfer": False,
            "message_id": msg.id,
            "intent": None,
            "emotion": None,
            "answer_source": "faq_direct",
            "extra": {
                "faq_title": faq_hit.title,
                "faq_score": round(faq_hit.score, 4),
            },
        }

    print(f"[AGENT] Bot层未命中，继续Agent工作流")

    # ── Step6：构建上下文 ──
    try:
        history = await build_history(db, conversation_id, rounds=3)
    except Exception as e:
        import traceback

        logger.error(f"build_history异常: {e}\n{traceback.format_exc()}")
        history = []

    try:
        user_summary = await build_user_summary(db, user_id)
    except Exception as e:
        import traceback

        logger.error(f"build_user_summary异常: {e}\n{traceback.format_exc()}")
        user_summary = None

    # ── Step7：运行Agent工作流 ──
    print(f"╔══════════════════════════════════════════════════════╗")
    print(f"║          🤖 AGENT 工作流启动                            ║")
    print(f"╚══════════════════════════════════════════════════════╝")
    try:
        result = await run_agent(
            query=query,
            conversation_id=conversation_id,
            bot_id=bot_id,  # ✅ 正确的bot_id
            agent_id=agent.id,
            channel_token=channel_token,
            db=db,
            history=history,
            user_id=user_id,
            user_summary=user_summary,
        )
    except Exception as e:
        import traceback

        logger.error(f"Agent工作流异常: {e}\n{traceback.format_exc()}")
        await db.rollback()
        result = {
            "final_answer": "非常抱歉，系统处理异常，请稍后重试。",
            "need_transfer": False,
            "answer_source": "error",
            "intent": None,
            "emotion": None,
            "confidence_score": 0.0,
            "elapsed_ms": 0,
        }

    final_answer = result.get("final_answer", "")
    need_transfer = result.get("need_transfer", False)
    answer_source = result.get("answer_source", "unknown")
    intent = result.get("intent")
    emotion = result.get("emotion")
    confidence_score = result.get("confidence_score", 0.0)

    # Agent层返回时，把Markdown转成HTML
    from markdownify import markdownify

    final_answer = markdownify(final_answer)

    print(
        f"[AGENT] Agent层返回 answer_source={answer_source} need_transfer={need_transfer}"
    )
    card_type = result.get("card_type")
    card_data = result.get("card_data")

    # ── Step8：处理转人工 ──
    agent_name = None
    reply_role = 1  # 1=Bot

    if need_transfer:
        agent_name = random.choice(AGENT_NAMES)
        await crud_conversation.set_transfer(
            db=db,
            conversation_id=conversation_id,
            agent_name=agent_name,
        )
        reply_role = 2  # 2=人工客服

    # ── Step8：保存回复消息 ──
    msg = await crud_message.create(
        db=db,
        conversation_id=conversation_id,
        role=reply_role,
        content=final_answer,
        message_type=0,
        answer_source=answer_source,
        intent=intent,
        emotion=emotion,
        confidence_score=confidence_score,
        sender_name=agent_name,
        card_type=card_type,
        card_data=card_data,
    )

    print(
        f"[FINAL] ✅ 对话处理完成 | conv_id={conversation_id} | "
        f"answer_source={answer_source} | need_transfer={need_transfer} | "
        f"elapsed_ms={result.get('elapsed_ms', 0)}ms"
    )
    print(f"╚══════════════════════════════════════════════════════╝")

    # ── Step 9：写入 AI 会话明细 ──────────────────────────
    _source_map = {
        "rag": 0,
        "faq_direct": 0,  # Bot直接返回，不走LLM
        "keyword": 1,
        "keyword_transfer": 1,
        "default": 2,
        "tool": 2,
        "llm": 2,
        "unknown": 99,
        "error": 99,
    }
    src_code = _source_map.get(answer_source, 99)

    msg_count = await crud_conversation.get_message_count(db, conversation_id)
    round_idx = (msg_count + 1) // 2

    is_resolved_flag = 1 if confidence_score >= 0.7 else 0
    is_noanswer_flag = 1 if answer_source in ("default", "error", "unknown") else 0
    resp_ms = int(result.get("elapsed_ms", 0) or 0)

    tool_results = result.get("tool_results", [])
    tools_list = (
        [tr.get("tool_name", "unknown") for tr in tool_results] if tool_results else None
    )

    _emotion_map = {"neutral": 0, "negative": 2, "angry": 3}
    emotion_det = _emotion_map.get(emotion, 0) if emotion else 0

    try:
        detail = await crud_conversation_detail.create(
            db=db,
            conversation_id=conversation_id,
            channel_id=channel.id,
            user_id=user_id,
            round_index=round_idx,
            user_message=query,
            bot_answer=final_answer if reply_role == 1 else None,
            agent_answer=final_answer if reply_role == 2 else None,
            answer_source=src_code,
            is_resolved=is_resolved_flag,
            is_transferred=1 if need_transfer else 0,
            is_no_answer=is_noanswer_flag,
            emotion_detected=emotion_det,
            response_ms=resp_ms if resp_ms > 0 else None,
            tools_called={"tools": tools_list} if tools_list else None,
        )
        logger.info(f"[ConvDetail] 写入成功 id={detail.id} conv={conversation_id}")
    except Exception as e:
        import traceback

        logger.error(
            f"[ConvDetail] 写入失败 conversation_id={conversation_id} "
            f"src_code={src_code} round={round_idx}: {e}\n"
            f"{traceback.format_exc()}"
        )

    response = {
        "answer": final_answer,
        "role": "agent" if need_transfer else "bot",
        "need_transfer": need_transfer,
        "agent_name": agent_name,
        "message_id": msg.id,
        "intent": intent,
        "emotion": emotion,
        "answer_source": answer_source,
    }

    if card_type and card_data:
        response["card_type"] = card_type
        response["card_data"] = card_data

    return response


# ==================== 人工客服模拟回复 ====================


async def _handle_human_agent_reply(
    query: str,
    conversation_id: int,
    agent_name: Optional[str],
    db: AsyncSession,
) -> tuple:
    """模拟人工客服回复"""
    from langchain_openai import ChatOpenAI
    from langchain_core.messages import HumanMessage, SystemMessage
    from app.config import settings

    name = agent_name or "客服"

    system_prompt = f"""你是{name}，一名真实的电商人工客服。

请用口语化、有温度的方式回答用户问题。
要求：
1. 用第一人称"我"而不是"客服"
2. 语气亲切自然，像真人对话
3. 遇到复杂问题说"我帮您查一下"
4. 回答简洁，不超过150字
5. 不要暴露自己是AI"""

    try:
        llm = ChatOpenAI(
            base_url=settings.LLM_BASE_URL,
            api_key=settings.LLM_API_KEY,
            model=settings.LLM_MODEL,
            temperature=0.9,
            max_tokens=256,
        )

        response = await llm.ainvoke(
            [
                SystemMessage(content=system_prompt),
                HumanMessage(content=query),
            ]
        )
        answer = response.content.strip()

    except Exception as e:
        logger.error(f"人工客服模拟回复失败: {e}")
        answer = f"您好，我是{name}，您的问题我已记录，稍后为您处理。"

    msg = await crud_message.create(
        db=db,
        conversation_id=conversation_id,
        role=2,
        content=answer,
        message_type=0,
        answer_source="human_agent",
        sender_name=name,
    )

    # 写入人工客服明细（answer_source=3）
    msg_count = await crud_conversation.get_message_count(db, conversation_id)
    round_idx = (msg_count + 1) // 2

    try:
        detail = await crud_conversation_detail.create(
            db=db,
            conversation_id=conversation_id,
            channel_id=None,
            user_id=None,
            round_index=round_idx,
            user_message=query,
            bot_answer=None,
            agent_answer=answer,
            answer_source=3,
            is_resolved=1,
            is_transferred=1,
            is_no_answer=0,
            emotion_detected=0,
            response_ms=None,
            tools_called=None,
        )
        logger.info(
            f"[ConvDetail] 人工明细写入成功 id={detail.id} conv={conversation_id}"
        )
    except Exception as e:
        import traceback

        logger.error(
            f"[ConvDetail] 人工客服明细写入失败 conv={conversation_id}: {e}\n"
            f"{traceback.format_exc()}"
        )

    return answer, msg


# ==================== 转人工首条接待语 ====================


async def process_human_chat(
    db: AsyncSession,
    conversation_id: int,
    agent_id: int,
    staff_name: str,
    user_message: str,
) -> dict:
    """
    转人工后的首条 Agent 回复
    使用 Agent 的 human_prompt 构造人工客服风格回复
    """
    from sqlalchemy import select
    from openai import AsyncOpenAI
    from app.models.agent import Agent, AgentConfig, AgentVersion
    from app.models.conversation import Message as DbMessage

    start_ms = int(time.time() * 1000)

    # ── Step 1：加载 Agent 配置 ──────────────────────────
    result = await db.execute(
        select(AgentConfig)
        .join(AgentVersion, AgentVersion.id == AgentConfig.agent_version_id)
        .where(AgentVersion.agent_id == agent_id, AgentVersion.status == 1)
        .limit(1)
    )
    config = result.scalar_one_or_none()

    if config:
        human_prompt = config.human_prompt or ""
        model_type = config.model_type or 0
        model_params = config.model_params or {}
        temperature = model_params.get("temperature", 0.7)
        max_tokens = model_params.get("max_tokens", 512)
    else:
        human_prompt = ""
        model_type = 0
        temperature = 0.7
        max_tokens = 512

    model_name = "deepseek-v3.2-chat-private" if model_type == 0 else "qwen-plus"

    # ── Step 2：构造人工客服风格 Prompt ──────────────────
    if human_prompt:
        final_system = human_prompt.replace("{staff_name}", staff_name)
    else:
        final_system = (
            f"你现在扮演人工客服「{staff_name}」，"
            f"请用亲切、专业的语气回复用户。\n"
            f"你擅长处理电商售后问题，包括退款、物流、换货等。\n"
            f"每次回复都要体现出人工服务的温度感，避免机械化措辞。"
        )

    # ── Step 3：拉取最近5条历史消息 ─────────────────────
    result = await db.execute(
        select(DbMessage)
        .where(DbMessage.conversation_id == conversation_id)
        .order_by(DbMessage.created_at.desc())
        .limit(5)
    )
    history_rows = list(reversed(result.scalars().all()))

    openai_messages = [{"role": "system", "content": final_system}]
    for msg in history_rows:
        if msg.sender_type == 0:
            openai_messages.append({"role": "user", "content": msg.content or ""})
        elif msg.sender_type in (1, 2):
            openai_messages.append({"role": "assistant", "content": msg.content or ""})

    if not history_rows or history_rows[-1].sender_type != 0:
        openai_messages.append({"role": "user", "content": user_message})

    openai_messages.append(
        {
            "role": "user",
            "content": (
                f"我是人工客服{staff_name}，刚接手了这个会话，"
                f"请以{staff_name}的身份生成一句简短的接待语（不超过50字），"
                f"表示已接手并询问用户需要什么帮助。"
            ),
        }
    )

    # ── Step 4：调用 LLM 生成回复 ────────────────────────
    client = AsyncOpenAI(
        api_key=settings.LLM_API_KEY,
        base_url=settings.LLM_BASE_URL,
    )

    try:
        response = await client.chat.completions.create(
            model=model_name,
            messages=openai_messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        reply_content = response.choices[0].message.content.strip()
        prompt_tokens = response.usage.prompt_tokens
        completion_tokens = response.usage.completion_tokens
        total_tokens = response.usage.total_tokens
    except Exception as e:
        logger.error(f"process_human_chat LLM调用失败: {e}")
        reply_content = f"您好！我是人工客服{staff_name}，已为您接手本次服务，请问有什么可以帮助您的？"
        prompt_tokens = None
        completion_tokens = None
        total_tokens = None

    response_ms = int(time.time() * 1000) - start_ms

    # ── Step 5：写入 messages 表 ─────────────────────────
    extra_data = {
        "answer_source": "llm",
        "intent": None,
        "emotion": None,
    }

    msg_obj = DbMessage(
        conversation_id=conversation_id,
        sender_type=2,
        sender_name=staff_name,
        content_type=0,
        content=reply_content,
        extra=extra_data,
        is_read=0,
    )
    db.add(msg_obj)
    await db.flush()
    message_id = msg_obj.id

    # ── Step 6：写入 ai_conversation_details 表 ──────────
    msg_count = await crud_conversation.get_message_count(db, conversation_id)
    round_idx = (msg_count + 1) // 2

    try:
        await crud_conversation_detail.create(
            db=db,
            conversation_id=conversation_id,
            channel_id=None,
            user_id=None,
            round_index=round_idx,
            user_message=user_message,
            bot_answer=None,
            agent_answer=reply_content,
            answer_source=3,
            is_resolved=1,
            is_transferred=1,
            is_no_answer=0,
            emotion_detected=0,
            response_ms=response_ms if response_ms > 0 else None,
            tools_called=None,
        )
    except Exception as e:
        logger.error(f"[ConvDetail] 人工接待语明细写入失败 conv={conversation_id}: {e}")

    await db.commit()

    return {
        "role": "agent",
        "content": reply_content,
        "message_id": message_id,
        "staff_name": staff_name,
        "extra": extra_data,
    }
