# backend/app/agent/nodes/generate.py
import logging
from typing import Optional
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

from app.agent.state import (
    AgentState,
    AgentAction,
    IntentType,
    EmotionType,
    state_set_answer,
)
from app.config import settings

logger = logging.getLogger(__name__)

BASE_SYSTEM_PROMPT = """你是灵犀智能客服，一个专业、友善的电商客服助手。

## 你的职责
- 解答用户关于订单、物流、退款、商品的问题
- 提供准确、简洁、有温度的回答

## 回答原则
1. 简洁明了：回答控制在200字以内
2. 有温度：使用礼貌、亲切的语气
3. 准确优先：基于提供的资料回答，不要编造信息

## 输出格式
- **必须使用 HTML 格式输出**，不要使用 Markdown
- 可用标签：<p>、<strong>、<em>、<ul>、<li>、<a>、<br>
- 例：<p>您的订单号是 <strong>123456</strong>，<a href="链接">点击查看</a></p>
- <ul><li>每条信息一项</li></ul>

## 限制
- 不讨论与电商客服无关的话题
- 遇到无法解决的问题，引导转人工

## 知识库问答模式（当有参考资料时）
当提供了知识库参考资料时，你的工作是：
1. 仔细阅读每条参考资料
2. 判断哪条（或哪几条）最能回答用户问题
3. 如果只有一条最相关：直接返回该知识的答案原文，只做轻微润色（如有必要）
4. 如果多条都相关：合并答案原文，保持原有格式和链接
5. 重要：保留原文中的所有格式、超链接等信息，不要丢失
6. 只在必要时做微小调整让语句更通顺，不要改变原文核心内容"""

RAG_MODE_PROMPT = """
## 知识库问答模式
你将从知识库中获取多条可能的答案，你的任务是选择最合适的一条或合并多条。
- 如果只有一条完全匹配的问题，直接返回其答案原文
- 如果多条都相关，请合并后返回，保持原文格式和超链接
- 保留答案中的所有格式、链接、列表等元素
- 只做最小程度的润色，不要改变原文的核心信息"""

EMOTION_PROMPTS = {
    EmotionType.ANGRY: """
## 当前用户情绪：愤怒
- 首先表达理解和歉意
- 语气要更加温和和耐心
- 积极提供解决方案""",
    EmotionType.NEGATIVE: """
## 当前用户情绪：负面
- 表达关心和理解
- 提供具体可操作的解决方案""",
    EmotionType.POSITIVE: """
## 当前用户情绪：正面
用户心情不错，可以适当轻松友好地回答。""",
}

INTENT_PROMPTS = {
    IntentType.REFUND_REQUEST: """
## 当前意图：退款申请
退款成功告知预计3-5个工作日到账。""",
    IntentType.COMPLAINT: """
## 当前意图：投诉
首先真诚道歉，然后提供解决方案。""",
}


def _build_system_prompt(state: AgentState) -> str:
    parts = [BASE_SYSTEM_PROMPT]

    user_summary = state.get("user_summary")
    if user_summary:
        parts.append(f"\n## 用户信息\n{user_summary}")

    rag_context = state.get("rag_context")
    if rag_context:
        parts.append(f"\n## 知识库参考资料\n{rag_context}")

    tool_results = state.get("tool_results", [])
    if tool_results:
        tool_context = _build_tool_context(tool_results)
        if tool_context:
            parts.append(f"\n## 查询结果\n{tool_context}")

    emotion = state.get("emotion")
    if emotion and emotion in EMOTION_PROMPTS:
        parts.append(EMOTION_PROMPTS[emotion])

    intent = state.get("intent")
    if intent and intent in INTENT_PROMPTS:
        parts.append(INTENT_PROMPTS[intent])

    return "\n".join(parts)


def _build_tool_context(tool_results: list) -> str:
    from app.agent.tools.order import format_order_for_prompt
    from app.agent.tools.logistics import format_logistics_for_prompt
    from app.agent.tools.refund import format_refund_for_prompt
    from app.agent.tools.product import (
        format_product_for_prompt,
        format_hot_products_for_prompt,
    )

    lines = []
    for result in tool_results:
        try:
            if not isinstance(result, dict):
                continue
            tool_name = result.get("tool_name", "")
            if tool_name == "query_order":
                lines.append(format_order_for_prompt(result))
            elif tool_name == "query_logistics":
                lines.append(format_logistics_for_prompt(result))
            elif tool_name in ("apply_refund", "check_refund_eligibility"):
                lines.append(format_refund_for_prompt(result))
            elif tool_name == "query_product":
                lines.append(format_product_for_prompt(result))
            elif tool_name == "query_hot_products":
                lines.append(format_hot_products_for_prompt(result))
        except Exception as e:
            logger.warning(
                f"格式化工具结果失败 tool_name={result.get('tool_name')}: {e}"
            )
            continue

    return "\n\n".join(lines)


def _build_messages(state: AgentState) -> list:
    messages = []
    system_prompt = _build_system_prompt(state)
    messages.append(SystemMessage(content=system_prompt))

    history = state.get("history", [])
    recent_history = history[-6:] if len(history) > 6 else history
    for msg in recent_history:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        if role == "user":
            messages.append(HumanMessage(content=content))
        elif role == "assistant":
            messages.append(AIMessage(content=content))

    messages.append(HumanMessage(content=state["query"]))
    return messages


def _build_no_answer_reply(state: AgentState) -> str:
    no_answer_count = state.get("no_answer_count", 0)
    if no_answer_count >= 2:
        return (
            "非常抱歉，我理解您的问题但暂时无法给出满意的答复。"
            "建议转接人工客服处理，请问是否需要转接人工？"
        )
    return (
        "非常抱歉，我暂时无法回答您的这个问题。"
        "您可以尝试换个方式描述，或者联系人工客服获取帮助。"
    )


async def _call_llm(messages: list) -> tuple[str, int]:
    llm = ChatOpenAI(
        base_url=settings.LLM_BASE_URL,
        api_key=settings.LLM_API_KEY,
        model=settings.LLM_MODEL,
        temperature=0.7,
        max_tokens=512,
    )
    response = await llm.ainvoke(messages)
    content = response.content.strip()
    tokens_used = 0
    if hasattr(response, "usage_metadata") and response.usage_metadata:
        tokens_used = response.usage_metadata.get("total_tokens", 0)
    return content, tokens_used


async def generate_node(state: AgentState) -> dict:
    query = state["query"]
    intent = state.get("intent")
    rag_results = state.get("rag_results", [])
    tool_results = state.get("tool_results", [])

    print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    intent_repr = repr(intent)
    print(
        f"[GENERATE] 🔵 进入生成节点 | intent={intent_repr} | "
        f"rag_hits={len(rag_results)} | tool_results={len(tool_results)}"
    )

    print(f"[GENERATE] │  有上下文: rag={len(rag_results)} tool={len(tool_results)}")

    has_context = bool(rag_results or tool_results)

    if not has_context:
        print(f"[GENERATE] │  → 无上下文，LLM自由生成兜底")
        try:
            messages = _build_messages(state)
            answer, tokens = await _call_llm(messages)
            if answer:
                answer = _fix_markdown_links(answer)
                return {
                    **state_set_answer(answer=answer, source="llm", confidence=0.6),
                    "llm_tokens_used": tokens,
                    "next_action": AgentAction.CHECK_CONFIDENCE,
                }
        except Exception as e:
            logger.error(f"LLM通用回答失败: {e}")

        default_reply = _build_no_answer_reply(state)
        return {
            "generated_answer": default_reply,
            "final_answer": default_reply,
            "answer_source": "default",
            "confidence_score": 0.0,
            "confidence_passed": False,
            "next_action": AgentAction.CHECK_CONFIDENCE,
        }

    # 优先级 1：有工具结果 → 直接返回结构化数据，不走LLM
    if tool_results:
        tool_name = tool_results[0].get("tool_name", "unknown")
        print(f"[GENERATE] │  → 命中工具分支[{tool_name}]，跳过LLM直接返回")

        tool_data = tool_results[0].get("data") or {}
        if not isinstance(tool_data, dict):
            tool_data = {}
        card_type = tool_data.get("card_type")
        card_data = tool_data.get("card_data")

        if card_type:
            tool_label_map = {
                "order": "订单",
                "order_list": "订单",
                "orders_list": "订单",
                "logistics": "物流",
                "product": "商品",
                "product_list": "商品",
            }
            label = tool_label_map.get(card_type, "信息")
            answer = f"已为您查到{label}信息，卡片展示中"
        else:
            try:
                tool_context = _build_tool_context(tool_results)
                answer = (
                    f"【{tool_name}】{tool_context}"
                    if tool_context
                    else f"已为您查询完成"
                )
            except Exception as e:
                logger.error(f"构建工具上下文失败: {e}")
                answer = f"已为您查询完成"
                card_type = None
                card_data = None

        print(f"[GENERATE] │  ✅ 工具直接返回，跳过LLM耗时")
        result = {
            **state_set_answer(answer=answer, source="tool", confidence=0.9),
            "llm_tokens_used": 0,
            "next_action": AgentAction.CHECK_CONFIDENCE,
        }
        if card_type:
            result["card_type"] = card_type
            result["card_data"] = card_data
        return result

    # 优先级 2：有 RAG 结果 → 直接返回原文或 LLM 选择
    if rag_results:
        top_score = float(rag_results[0].get("score", 0))
        print(f"[GENERATE] │  → 命中RAG分支 top_score={top_score:.4f}")

        if top_score > 0.85:
            print(f"[GENERATE] │  → 高置信度，直接返回原文")
            answer = rag_results[0]["answer"]
            answer = _fix_markdown_links(answer)
            print(f"[GENERATE] │  → 高置信度RAG(score={top_score:.4f})，直接返回原文")
            return {
                **state_set_answer(
                    answer=answer,
                    source="faq_direct",
                    confidence=top_score,
                ),
                "llm_tokens_used": 0,
                "next_action": AgentAction.CHECK_CONFIDENCE,
            }

        print(f"[GENERATE] │  → RAG候选分数较低，让LLM选择最佳答案")
        try:
            select_prompt = f"""用户问题：{query}

以下是知识库中的候选答案：

"""
            for i, r in enumerate(rag_results, 1):
                select_prompt += f"【候选{i}】(分数={r.get('score', 0):.4f})\n标题：{r['title']}\n答案：{r['answer']}\n\n"

            select_prompt += """请选择最合适回答用户问题的答案。
规则：
1. 如果只有一个答案完全匹配，直接返回该答案的完整原文
2. 如果多个答案都相关，请合并后返回，保持原文格式和超链接
3. 只做最小润色（如有必要），保持原文所有信息完整
4. 返回格式：直接输出答案原文，不要解释你选择了哪个

请输出答案原文："""

            from langchain_openai import ChatOpenAI
            from langchain_core.messages import HumanMessage, SystemMessage

            llm = ChatOpenAI(
                base_url=settings.LLM_BASE_URL,
                api_key=settings.LLM_API_KEY,
                model=settings.LLM_MODEL,
                temperature=0.3,
                max_tokens=2048,
            )
            messages = [
                SystemMessage(
                    content="你是一个答案选择器，只返回最匹配的答案原文，不做解释。"
                ),
                HumanMessage(content=select_prompt),
            ]
            answer = await llm.ainvoke(messages)
            answer = (
                answer.content.strip() if hasattr(answer, "content") else str(answer)
            )
            if answer:
                answer = _fix_markdown_links(answer)
                print(f"[GENERATE] │  → LLM选择完成，答案长度={len(answer)}")
                return {
                    **state_set_answer(
                        answer=answer, source="faq_selected", confidence=top_score
                    ),
                    "llm_tokens_used": 0,
                    "next_action": AgentAction.CHECK_CONFIDENCE,
                }
        except Exception as e:
            logger.error(f"LLM选择答案失败: {e}")
            answer = rag_results[0]["answer"]
            answer = _fix_markdown_links(answer)
            return {
                **state_set_answer(
                    answer=answer, source="faq_fallback", confidence=top_score
                ),
                "llm_tokens_used": 0,
                "next_action": AgentAction.CHECK_CONFIDENCE,
            }

    # 优先级 3：无任何上下文 → LLM 自由生成兜底
    print(f"[GENERATE] │  → 无上下文，LLM自由生成兜底")
    try:
        messages = _build_messages(state)
        answer, tokens = await _call_llm(messages)
        if answer:
            answer = _fix_markdown_links(answer)
            return {
                **state_set_answer(answer=answer, source="llm", confidence=0.6),
                "llm_tokens_used": tokens,
                "next_action": AgentAction.CHECK_CONFIDENCE,
            }
    except Exception as e:
        logger.error(f"LLM自由生成失败: {e}")

    default_reply = _build_no_answer_reply(state)
    print(f"[GENERATE] │  ⚠️  无任何结果，返回兜底回复")
    return {
        "generated_answer": default_reply,
        "final_answer": default_reply,
        "answer_source": "default",
        "confidence_score": 0.0,
        "confidence_passed": False,
        "next_action": AgentAction.CHECK_CONFIDENCE,
    }


# ==================== Markdown超链格式修复 ====================


def _fix_markdown_links(text: str) -> str:
    """
    检测并修复Markdown中格式不规范的超链接

    处理模式：
    1. "文字：URL" 或 "文字 URL" → "[文字](URL)"
    2. "👉 点击这里：https://..." → "👉 [点击这里](https://...)"
    3. 裸URL检测（可选）：如果一行只有一个URL，直接转成链接
    """
    import re

    if not text:
        return text

    # 模式1：修复 "文字：URL" 或 "文字 URL" → "[文字](URL)"
    # 匹配2-50个非换行非括号字符，后面跟冒号或空格，再跟URL
    pattern1 = r"([^\n\[\]]{1,50}?)[:：]\s*(https?://\S+)"

    def replace1(m):
        text_part = m.group(1).strip()
        # 去掉末尾的标点符号
        text_part = text_part.rstrip(".,，。!！?？、")
        url = m.group(2).strip()
        return f"[{text_part}]({url})"

    text = re.sub(pattern1, replace1, text)

    # 模式2：修复 "👉[文字](URL)" 或 "👉 [文字](URL)" 或 "👉 **加粗文字**(URL)"
    # emoji紧贴[或中间有空格都可以匹配，[]内可能是纯文字或加粗格式
    pattern2 = r"([👉👍❓❗🔥💡⭐✨➡️🎯📌🔔]+)\s*\**([^\**]+)\**\s*\]\((https?://\S+)\)"

    def replace2(m):
        emoji = m.group(1).strip()
        # 移除可能的**加粗**标记
        link_text = m.group(2).strip().lstrip("*").rstrip("*")
        url = m.group(3).strip()
        return f"{emoji} [{link_text}]({url})"

    text = re.sub(pattern2, replace2, text)

    # 也处理emoji后面直接跟[文字]的情况（没有加粗）
    pattern2b = r"([👉👍❓❗🔥💡⭐✨➡️🎯📌🔔]+)\s*\[([^\]]+)\]\((https?://\S+)\)"

    def replace2b(m):
        emoji = m.group(1).strip()
        link_text = m.group(2).strip()
        url = m.group(3).strip()
        return f"{emoji} [{link_text}]({url})"

    text = re.sub(pattern2b, replace2b, text)

    # 模式3：如果有"点击这里"或类似文字后面直接跟URL，但没有中括号
    pattern3 = r"([点击这里请您]+)[:：\s]+(https?://\S+)"

    def replace3(m):
        link_text = m.group(1).strip()
        url = m.group(2).strip()
        return f"[{link_text}]({url})"

    text = re.sub(pattern3, replace3, text)

    return text
