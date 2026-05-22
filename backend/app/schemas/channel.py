# backend/app/schemas/channel.py
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import IntEnum


# ==================== 枚举定义 ====================


class ChannelType(IntEnum):
    TEST = 0  # 测试渠道
    PRODUCTION = 1  # 正式渠道


class ChannelStatus(IntEnum):
    DISABLED = 0
    ENABLED = 1


# ==================== 渠道 ====================


class ChannelCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="渠道名称")
    channel_type: ChannelType = Field(
        ChannelType.TEST, description="渠道类型 0测试 1正式"
    )
    agent_id: int = Field(..., description="绑定的Agent ID")
    description: Optional[str] = Field(None, max_length=500, description="渠道描述")


class ChannelUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    agent_id: Optional[int] = None
    description: Optional[str] = Field(None, max_length=500)
    status: Optional[ChannelStatus] = None


class ChannelOut(BaseModel):
    id: int
    name: str
    channel_type: int
    channel_type_text: Optional[str] = None
    channel_token: str
    agent_id: int
    agent_name: Optional[str] = None
    bot_id: Optional[int] = None
    bot_name: Optional[str] = None
    description: Optional[str]
    status: int
    today_sessions: int = 0
    total_sessions: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ChannelTokenOut(BaseModel):
    channel_token: str = Field(..., description="渠道Token（对话接口使用）")
    ws_url: str = Field(..., description="WebSocket对话地址")
