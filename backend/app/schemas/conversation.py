# backend/app/schemas/conversation.py
from pydantic import BaseModel, Field
from typing import Optional, List, Any
from datetime import datetime
from enum import IntEnum


# ==================== 枚举定义 ====================


class ConversationStatus(IntEnum):
    ACTIVE = 0  # 进行中
    CLOSED = 1  # 已结束
    EVALUATED = 2  # 已评价


class MessageRole(IntEnum):
    USER = 0  # 用户
    BOT = 1  # 机器人
    AGENT = 2  # AI人工客服


class MessageType(IntEnum):
    TEXT = 0  # 纯文本
    HTML = 1  # 富文本
    SYSTEM = 2  # 系统消息


class TransferStatus(IntEnum):
    NOT_TRANSFERRED = 0  # 未转人工
    TRANSFERRED = 1  # 已转人工


# ==================== WebSocket消息格式 ====================


class WsMessageIn(BaseModel):
    """客户端发送的WebSocket消息"""

    type: str = Field(..., description="消息类型: chat/transfer/ping")
    content: Optional[str] = Field(None, description="消息内容")
    user_id: Optional[int] = Field(None, description="用户ID（已登录时传入）")


class WsMessageOut(BaseModel):
    """服务端推送的WebSocket消息"""

    type: str = Field(..., description="消息类型: message/transfer/evaluate/error/pong")
    role: Optional[str] = Field(None, description="消息角色: bot/agent/system")
    content: Optional[str] = Field(None, description="消息内容")
    message_id: Optional[int] = Field(None, description="消息ID")
    conversation_id: Optional[int] = Field(None, description="会话ID")
    need_transfer: Optional[bool] = Field(None, description="是否需要转人工")
    agent_name: Optional[str] = Field(None, description="人工客服名称")
    timestamp: Optional[str] = Field(None, description="消息时间")
    extra: Optional[dict] = Field(None, description="额外信息")


# ==================== 会话 ====================


class ConversationOut(BaseModel):
    """会话返回"""

    id: int
    channel_id: int
    channel_name: Optional[str] = None
    user_id: Optional[int]
    username: Optional[str] = None
    status: int
    transfer_status: int
    agent_name: Optional[str]
    bot_name: Optional[str]
    started_at: datetime
    ended_at: Optional[datetime]
    message_count: int = 0
    created_at: datetime

    model_config = {"from_attributes": True}


# ==================== 消息 ====================


class MessageOut(BaseModel):
    """消息返回"""

    id: int
    conversation_id: int
    role: int
    role_text: Optional[str] = None
    message_type: int
    content: str
    answer_source: Optional[str] = None
    intent: Optional[str] = None
    emotion: Optional[str] = None
    confidence_score: Optional[float] = None
    card_type: Optional[str] = None
    card_data: Optional[Any] = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ==================== 评价 ====================


class EvaluateRequest(BaseModel):
    """提交评价请求"""

    rating: int = Field(..., ge=1, le=5, description="评分 1-5星")
    comment: Optional[str] = Field(None, max_length=500, description="评价内容")


class EvaluateOut(BaseModel):
    """评价返回"""

    conversation_id: int
    rating: int
    comment: Optional[str]
    evaluated_at: datetime
