from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


# ==================== 请求 Schema ====================


class AnnotationCreateSchema(BaseModel):
    """创建标注请求体"""

    conversation_id: int = Field(..., description="会话 ID")
    message_id: int = Field(..., description="被标注的消息 ID")
    label: str = Field(
        ...,
        description="标注标签：good / bad / neutral",
        pattern="^(good|bad|neutral)$",
    )
    correct_answer: Optional[str] = Field(
        None, description="人工修正的正确答案（label=bad 时填写）", max_length=2000
    )
    remark: Optional[str] = Field(None, description="标注备注", max_length=500)


class AnnotationUpdateSchema(BaseModel):
    """更新标注请求体"""

    label: Optional[str] = Field(None, pattern="^(good|bad|neutral)$")
    correct_answer: Optional[str] = Field(None, max_length=2000)
    remark: Optional[str] = Field(None, max_length=500)


# ==================== 响应 Schema ====================


class AnnotationSchema(BaseModel):
    """标注记录响应"""

    id: int
    conversation_id: int
    message_id: int
    annotator_id: Optional[int]
    label: str
    correct_answer: Optional[str]
    remark: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==================== 统计 Schema ====================


class AnnotationStatsSchema(BaseModel):
    """标注统计响应"""

    total: int
    good: int
    bad: int
    neutral: int
    good_rate: float
    bad_rate: float
