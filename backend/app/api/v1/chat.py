# backend/app/api/v1/chat.py
import logging
import json
from datetime import datetime
from typing import Optional
from fastapi import (
    APIRouter,
    WebSocket,
    WebSocketDisconnect,
    Depends,
    Query,
    HTTPException,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db, AsyncSessionLocal
from app.crud.channel import crud_channel
from app.crud.conversation import crud_conversation, crud_message
from app.services.chat import process_chat, process_human_chat, AGENT_NAMES
from app.schemas.conversation import (
    EvaluateRequest,
    EvaluateOut,
    ConversationOut,
    MessageOut,
)
from app.utils.response import Response, PageResponse
from app.core.security import get_current_admin_id, oauth2_scheme, decode_token

logger = logging.getLogger(__name__)
router = APIRouter()

ROLE_TEXT_MAP = {0: "user", 1: "bot", 2: "agent"}


# ==================== 辅助函数 ====================


def _build_ws_message(
    msg_type: str,
    role: Optional[str] = None,
    content: Optional[str] = None,
    conversation_id: Optional[int] = None,
    message_id: Optional[int] = None,
    need_transfer: Optional[bool] = None,
    agent_name: Optional[str] = None,
    extra: Optional[dict] = None,
) -> dict:
    """构建WebSocket推送消息"""
    return {
        "type": msg_type,
        "role": role,
        "content": content,
        "message_id": message_id,
        "conversation_id": conversation_id,
        "need_transfer": need_transfer,
        "agent_name": agent_name,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "extra": extra,
    }


async def _handle_transfer_request(
    websocket: WebSocket,
    conversation_id: int,
    user_message: str,
    db: AsyncSession,
):
    """处理用户主动转人工请求"""
    import random

    conversation = await crud_conversation.get(db, conversation_id)

    # 已经转人工
    if conversation and conversation.is_transferred == 1:
        await websocket.send_text(
            json.dumps(
                {
                    "type": "transfer",
                    "role": "system",
                    "content": f"您已在与{conversation.staff_name}沟通中",
                    "agent_name": conversation.staff_name,
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                },
                ensure_ascii=False,
            )
        )
        return

    # 分配客服
    agent_name = random.choice(AGENT_NAMES)
    await crud_conversation.set_transfer(
        db=db,
        conversation_id=conversation_id,
        agent_name=agent_name,
    )

    # ── Step 2：推送系统消息（转接通知）─────────────────
    await websocket.send_text(
        json.dumps(
            {
                "type": "transfer",
                "role": "system",
                "content": f"已为您转接人工客服 {agent_name}，请稍候...",
                "agent_name": agent_name,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            },
            ensure_ascii=False,
        )
    )

    # ── Step 3：推送 thinking 状态 ───────────────────────
    await websocket.send_text(
        json.dumps(
            {
                "type": "thinking",
                "content": "正在思考中...",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            },
            ensure_ascii=False,
        )
    )

    # ── Step 4：调用 Agent 工作流生成人工客服回复 ────────
    if conversation and conversation.agent_id:
        agent_id = conversation.agent_id
    else:
        agent_id = 1

    try:
        result = await process_human_chat(
            db=db,
            conversation_id=conversation_id,
            agent_id=agent_id,
            staff_name=agent_name,
            user_message=user_message,
        )

        await websocket.send_text(
            json.dumps(
                {
                    "type": "message",
                    "role": "agent",
                    "content": result["content"],
                    "message_id": result["message_id"],
                    "conversation_id": conversation_id,
                    "agent_name": agent_name,
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "extra": result.get("extra", {}),
                },
                ensure_ascii=False,
            )
        )
    except Exception as e:
        logger.error(f"process_human_chat异常: {e}")
        await websocket.send_text(
            json.dumps(
                {
                    "type": "message",
                    "role": "agent",
                    "content": f"您好！我是人工客服{agent_name}，请问有什么可以帮助您？",
                    "conversation_id": conversation_id,
                    "agent_name": agent_name,
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "extra": {},
                },
                ensure_ascii=False,
            )
        )

    logger.info(
        f"用户主动转人工 conversation_id={conversation_id} agent_name={agent_name}"
    )


# ==================== WebSocket 对话核心 ====================


@router.websocket("/ws/{channel_token}")
async def websocket_chat(
    websocket: WebSocket,
    channel_token: str,
    user_id: Optional[str] = Query(None, description="用户ID（已登录时传入）"),
    conversation_id: Optional[int] = Query(None, description="复用已有会话ID"),
):
    """
    WebSocket 对话接口

    连接地址：
        ws://host:port/api/v1/chat/ws/{channel_token}?user_id=123

    客户端发送格式：
    {
        "type": "chat",       # chat / transfer / ping
        "content": "用户消息"
    }

    服务端推送格式：
    {
        "type": "message",    # message / transfer / thinking / evaluate / error / pong
        "role": "bot",        # bot / agent / system
        "content": "回复内容",
        "message_id": 1,
        "conversation_id": 1,
        "need_transfer": false,
        "agent_name": null,
        "timestamp": "2024-01-01 12:00:00",
        "extra": {}
    }
    """
    await websocket.accept()

    logger.info(
        f"WebSocket连接建立 channel_token={channel_token[:8]}... user_id={user_id}"
    )

    async with AsyncSessionLocal() as db:
        # ── Step1：验证渠道 ──
        channel = await crud_channel.get_by_token(db, channel_token)
        if not channel or channel.status == 0:
            await websocket.send_text(
                json.dumps(
                    {
                        "type": "error",
                        "content": "渠道不存在或已禁用",
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    },
                    ensure_ascii=False,
                )
            )
            await websocket.close()
            return

        # ── Step2：创建或复用会话 ──
        # guest 用户（字符串 id）: user_id 存 None，username 存 guest_id
        # 登录用户（数字 id）: user_id 存数字，username 存 None
        numeric_user_id: Optional[int] = None
        snapshot_username: Optional[str] = None
        if user_id and user_id.isdigit():
            numeric_user_id = int(user_id)

            from app.crud.user import crud_user

            user = await crud_user.get(db, numeric_user_id)
            if user:
                snapshot_username = user.username
        else:
            snapshot_username = user_id

        # 尝试复用已有会话（刷新/重进聊天窗口时恢复上下文）
        is_new_conversation = True
        if conversation_id:
            try:
                existing = await crud_conversation.get(db, conversation_id)
                if existing and existing.channel_id == channel.id:
                    # 会话归属校验：登录用户匹配 user_id，游客匹配 username
                    user_match = (
                        (existing.user_id == numeric_user_id)
                        or (existing.username == snapshot_username)
                    )
                    if user_match:
                        conversation = existing
                        conversation_id = conversation.id
                        is_new_conversation = False
                        logger.info(
                            f"复用已有会话 conversation_id={conversation_id}"
                        )
            except Exception as e:
                logger.warning(f"复用会话失败，将新建: {e}")

        # 创建新会话
        if is_new_conversation:
            conversation = await crud_conversation.create(
                db=db,
                channel_id=channel.id,
                user_id=numeric_user_id,
                username=snapshot_username,
            )
            conversation_id = conversation.id
            logger.info(
                f"会话创建成功 conversation_id={conversation_id} channel_id={channel.id}"
            )

        # ── Step3：仅新会话推送欢迎消息（复用时不发，避免重复） ──
        if is_new_conversation:
            welcome = _build_ws_message(
                msg_type="message",
                role="bot",
                content="您好！我是灵犀智能客服，请问有什么可以帮助您？",
                conversation_id=conversation_id,
            )
            await websocket.send_text(json.dumps(welcome, ensure_ascii=False))

        # ── Step4：主循环 ──
        try:
            while True:
                raw = await websocket.receive_text()

                # 解析消息
                try:
                    data = json.loads(raw)
                except json.JSONDecodeError:
                    await websocket.send_text(
                        json.dumps(
                            {
                                "type": "error",
                                "content": "消息格式错误，请发送JSON",
                                "timestamp": datetime.now().strftime(
                                    "%Y-%m-%d %H:%M:%S"
                                ),
                            },
                            ensure_ascii=False,
                        )
                    )
                    continue

                msg_type = data.get("type", "chat")

                # ── 心跳 ──
                if msg_type == "ping":
                    await websocket.send_text(
                        json.dumps(
                            {
                                "type": "pong",
                                "timestamp": datetime.now().strftime(
                                    "%Y-%m-%d %H:%M:%S"
                                ),
                            }
                        )
                    )
                    continue

                # ── 主动转人工 ──
                if msg_type == "transfer":
                    user_message = data.get("content", "我需要人工客服")
                    await _handle_transfer_request(
                        websocket=websocket,
                        conversation_id=conversation_id,
                        user_message=user_message,
                        db=db,
                    )
                    continue

                # ── 申请退款 ──
                if msg_type == "refund":
                    order_no = data.get("order_no", "")
                    reason = data.get("reason", "用户申请退款")
                    if not order_no:
                        await websocket.send_text(
                            json.dumps(
                                {
                                    "type": "message",
                                    "role": "bot",
                                    "content": "退款申请失败：缺少订单号",
                                    "timestamp": datetime.now().strftime(
                                        "%Y-%m-%d %H:%M:%S"
                                    ),
                                },
                                ensure_ascii=False,
                            )
                        )
                        continue

                    from app.agent.tools.refund import apply_refund as apply_refund_tool

                    result = await apply_refund_tool(
                        db=db,
                        user_id=int(user_id) if user_id and user_id.isdigit() else None,
                        order_no=order_no,
                        reason=reason,
                    )

                    if result["success"]:
                        content = result["data"].get(
                            "message",
                            "退款申请已提交，我们将在1-3个工作日内处理",
                        )
                    else:
                        content = f"退款申请失败：{result.get('error_msg', '未知错误')}"

                    await websocket.send_text(
                        json.dumps(
                            {
                                "type": "message",
                                "role": "bot",
                                "content": content,
                                "timestamp": datetime.now().strftime(
                                    "%Y-%m-%d %H:%M:%S"
                                ),
                            },
                            ensure_ascii=False,
                        )
                    )
                    continue

                # ── 普通对话 ──
                if msg_type == "chat":
                    content = data.get("content", "").strip()
                    if not content:
                        continue

                    # 推送思考状态
                    await websocket.send_text(
                        json.dumps(
                            {
                                "type": "thinking",
                                "content": "正在思考中...",
                                "timestamp": datetime.now().strftime(
                                    "%Y-%m-%d %H:%M:%S"
                                ),
                            },
                            ensure_ascii=False,
                        )
                    )

                    # 处理对话（核心）
                    try:
                        result = await process_chat(
                            query=content,
                            conversation_id=conversation_id,
                            channel_token=channel_token,
                            db=db,
                            user_id=numeric_user_id,
                        )
                    except Exception as e:
                        logger.error(f"process_chat异常: {e}")
                        await websocket.send_text(
                            json.dumps(
                                {
                                    "type": "error",
                                    "content": "处理消息失败，请稍后重试",
                                    "timestamp": datetime.now().strftime(
                                        "%Y-%m-%d %H:%M:%S"
                                    ),
                                },
                                ensure_ascii=False,
                            )
                        )
                        continue

                    # 推送回复
                    extra = {
                        "intent": result.get("intent"),
                        "emotion": result.get("emotion"),
                        "answer_source": result.get("answer_source"),
                    }
                    if result.get("card_type") and result.get("card_data"):
                        extra["card_type"] = result["card_type"]
                        extra["card_data"] = result["card_data"]

                    reply = _build_ws_message(
                        msg_type="message",
                        role=result["role"],
                        content=result["answer"],
                        conversation_id=conversation_id,
                        message_id=result.get("message_id"),
                        need_transfer=result.get("need_transfer", False),
                        agent_name=result.get("agent_name"),
                        extra=extra,
                    )
                    await websocket.send_text(json.dumps(reply, ensure_ascii=False))

                    # 触发转人工时额外推送转人工事件
                    if result.get("need_transfer"):
                        transfer_notify = _build_ws_message(
                            msg_type="transfer",
                            role="system",
                            content=f"已为您转接人工客服 {result.get('agent_name', '')}，请继续描述您的问题。",
                            conversation_id=conversation_id,
                            agent_name=result.get("agent_name"),
                        )
                        await websocket.send_text(
                            json.dumps(transfer_notify, ensure_ascii=False)
                        )

        except WebSocketDisconnect:
            logger.info(f"WebSocket正常断开 conversation_id={conversation_id}")
            await crud_conversation.close(db, conversation_id)

        except Exception as e:
            logger.error(f"WebSocket异常 conversation_id={conversation_id}: {e}")
            try:
                await websocket.send_text(
                    json.dumps(
                        {
                            "type": "error",
                            "content": "服务异常，连接即将断开",
                            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        },
                        ensure_ascii=False,
                    )
                )
            except Exception:
                pass
            await crud_conversation.close(db, conversation_id)


# ==================== 转人工（HTTP接口备用）====================


@router.post("/transfer", summary="主动转人工")
async def transfer_to_human(
    conversation_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    主动转人工（HTTP备用接口）
    WebSocket已内置transfer消息类型，此接口作为备用
    """
    import random

    conversation = await crud_conversation.get(db, conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="会话不存在")

    if conversation.is_transferred == 1:
        return Response.success(
            data={"agent_name": conversation.staff_name}, message="已在人工客服处理中"
        )

    agent_name = random.choice(AGENT_NAMES)
    await crud_conversation.set_transfer(
        db=db,
        conversation_id=conversation_id,
        agent_name=agent_name,
    )

    return Response.success(
        data={"agent_name": agent_name}, message=f"已转接人工客服 {agent_name}"
    )


# ==================== 提交评价 ====================


@router.post("/evaluate", summary="提交对话评价")
async def evaluate_conversation(
    conversation_id: int,
    req: EvaluateRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    提交对话评价

    在对话结束后调用，记录用户满意度评分
    """
    conversation = await crud_conversation.get(db, conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="会话不存在")

    if conversation.evaluated == 1:
        raise HTTPException(status_code=400, detail="该会话已评价")

    conversation = await crud_conversation.set_evaluate(
        db=db,
        conversation_id=conversation_id,
        rating=req.rating,
        comment=req.comment,
    )

    logger.info(f"会话评价提交 conversation_id={conversation_id} rating={req.rating}")

    return Response.success(
        data=EvaluateOut(
            conversation_id=conversation_id,
            rating=req.rating,
            comment=req.comment,
            evaluated_at=datetime.utcnow(),
        ),
        message="感谢您的评价！",
    )


# ==================== 会话历史（公开，聊天窗口使用） ====================


@router.get(
    "/conversations/{conversation_id}/messages/public",
    summary="获取会话消息记录（聊天窗口公开接口，按 user_id 校验归属）",
)
async def get_conversation_messages_public(
    conversation_id: int,
    user_id: Optional[str] = Query(None, description="用户ID（登录用户或游客ID）"),
    db: AsyncSession = Depends(get_db),
):
    """
    聊天窗口加载历史消息使用，无需登录Token。
    通过 user_id（数字登录用户 或 游客字符串）校验会话归属，
    与 WebSocket 建连时的归属校验逻辑一致。
    """
    conversation = await crud_conversation.get(db, conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="会话不存在")

    # 归属校验：登录用户匹配 user_id，游客匹配 username
    numeric_user_id: Optional[int] = None
    snapshot_username: Optional[str] = None
    if user_id and user_id.isdigit():
        numeric_user_id = int(user_id)
    else:
        snapshot_username = user_id

    user_match = (
        (conversation.user_id == numeric_user_id and numeric_user_id is not None)
        or (conversation.username == snapshot_username and snapshot_username is not None)
    )
    if not user_match:
        raise HTTPException(status_code=403, detail="无权访问该会话")

    messages = await crud_message.get_list(
        db=db,
        conversation_id=conversation_id,
        limit=200,
    )

    result = []
    for msg in messages:
        extra = msg.extra or {}
        result.append(
            {
                "id": msg.id,
                "conversation_id": msg.conversation_id,
                "role": ROLE_TEXT_MAP.get(msg.sender_type, "unknown"),
                "content": msg.content or "",
                "card_type": extra.get("card_type"),
                "card_data": extra.get("card_data"),
                "created_at": msg.created_at,
            }
        )

    return Response.success(data=result)


# ==================== 会话管理（管理员） ====================


@router.get("/conversations", summary="获取会话列表（管理员）")
async def list_conversations(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    channel_id: Optional[int] = Query(None),
    status: Optional[int] = Query(None),
    user_id: Optional[int] = Query(None),
    username: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    conversation_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
    admin_id: int = Depends(get_current_admin_id),
):
    from datetime import datetime

    start_dt = datetime.fromisoformat(start_date) if start_date else None
    end_dt = datetime.fromisoformat(end_date) if end_date else None

    conversations, total = await crud_conversation.get_list(
        db=db,
        page=page,
        page_size=page_size,
        channel_id=channel_id,
        status=status,
        user_id=user_id,
        username=username,
        start_date=start_dt,
        end_date=end_dt,
        conversation_id=int(conversation_id) if conversation_id else None,
    )

    channel_ids = list({conv.channel_id for conv in conversations if conv.channel_id})
    channel_map = {}
    if channel_ids:
        from app.crud.channel import crud_channel

        channels = await crud_channel.get_list(db)
        channel_map = {c.id: c.name for c in channels if c.id in channel_ids}

    result = []
    for conv in conversations:
        msg_count = await crud_conversation.get_message_count(db, conv.id)
        result.append(
            ConversationOut(
                id=conv.id,
                channel_id=conv.channel_id,
                channel_name=channel_map.get(conv.channel_id),
                user_id=conv.user_id,
                username=getattr(conv, "username", None),
                status=conv.current_mode,
                transfer_status=conv.is_transferred,
                agent_name=conv.staff_name,
                bot_name=getattr(conv, "bot_name", None),
                started_at=conv.started_at,
                ended_at=conv.ended_at if hasattr(conv, "ended_at") else None,
                message_count=msg_count,
                created_at=conv.created_at,
            )
        )

    return PageResponse.success(
        data=result,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/conversations/{conversation_id}/messages", summary="获取会话消息记录"
)
async def get_conversation_messages(
    conversation_id: int,
    db: AsyncSession = Depends(get_db),
    token: str = Depends(oauth2_scheme),
):
    """
    获取会话消息记录

    管理员Token：可查看任意会话
    用户Token：仅可查看自己拥有的会话
    """
    payload = decode_token(token)
    role = payload.get("role")
    subject_id = payload.get("sub")
    is_admin = role in ("admin", "super_admin", "operator")

    conversation = await crud_conversation.get(db, conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="会话不存在")

    if not is_admin:
        if role != "user" or not subject_id or int(subject_id) != conversation.user_id:
            raise HTTPException(status_code=403, detail="无权访问该会话")

    messages = await crud_message.get_list(
        db=db,
        conversation_id=conversation_id,
        limit=200,
    )

    result = []
    for msg in messages:
        result.append(
            MessageOut(
                id=msg.id,
                conversation_id=msg.conversation_id,
                role=msg.sender_type,
                role_text=ROLE_TEXT_MAP.get(msg.sender_type, "unknown"),
                message_type=msg.content_type,
                content=msg.content or "",
                answer_source=(msg.extra or {}).get("answer_source"),
                intent=(msg.extra or {}).get("intent"),
                emotion=(msg.extra or {}).get("emotion"),
                confidence_score=(msg.extra or {}).get("confidence_score"),
                card_type=(msg.extra or {}).get("card_type"),
                card_data=(msg.extra or {}).get("card_data"),
                created_at=msg.created_at,
            )
        )

    return Response.success(data=result)
