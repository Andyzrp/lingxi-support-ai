# backend/app/schemas/bot.py
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime
from enum import IntEnum


class BotStatus(IntEnum):
    DISABLED = 0
    ENABLED = 1


class KeywordMatchType(IntEnum):
    EXACT = 0
    CONTAINS = 1


class KeywordActionType(IntEnum):
    FIXED_REPLY = 0
    RECOMMEND_FAQ = 1
    TRANSFER = 2


class BotCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    knowledge_base_id: int
    similarity_threshold: float = Field(0.85, ge=0.0, le=1.0)
    bm25_weight: float = Field(0.3, ge=0.0, le=1.0)
    vector_weight: float = Field(0.7, ge=0.0, le=1.0)
    no_answer_reply: str = Field("您好，我暂时无法回答这个问题，是否需要转接人工客服？")
    max_no_answer_count: int = Field(3, ge=1, le=10)


class BotUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    knowledge_base_id: Optional[int] = None
    similarity_threshold: Optional[float] = Field(None, ge=0.0, le=1.0)
    bm25_weight: Optional[float] = Field(None, ge=0.0, le=1.0)
    vector_weight: Optional[float] = Field(None, ge=0.0, le=1.0)
    no_answer_reply: Optional[str] = None
    max_no_answer_count: Optional[int] = Field(None, ge=1, le=10)
    status: Optional[BotStatus] = None


class BotOut(BaseModel):
    id: int
    name: str
    knowledge_base_id: Optional[int]
    knowledge_base_name: Optional[str] = None
    knowledge_base_status: Optional[int] = None
    similarity_threshold: float
    no_answer_reply: str
    max_no_answer_count: int
    status: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": False}


class KeywordCreate(BaseModel):
    keyword: str = Field(..., min_length=1, max_length=100)
    match_type: KeywordMatchType = Field(KeywordMatchType.CONTAINS)
    action_type: KeywordActionType = Field(KeywordActionType.FIXED_REPLY)
    reply_content: Optional[str] = Field(None, max_length=1000)
    faq_item_id: Optional[int] = None
    priority: int = Field(0, ge=0, le=100)


class KeywordUpdate(BaseModel):
    keyword: Optional[str] = Field(None, min_length=1, max_length=100)
    match_type: Optional[KeywordMatchType] = None
    action_type: Optional[KeywordActionType] = None
    reply_content: Optional[str] = Field(None, max_length=1000)
    faq_item_id: Optional[int] = None
    priority: Optional[int] = Field(None, ge=0, le=100)
    status: Optional[int] = Field(None, ge=0, le=1)


class KeywordOut(BaseModel):
    id: int
    bot_id: int
    keyword: str
    match_type: int
    action_type: int  # 从actions JSONB中取
    reply_content: Optional[str]
    faq_item_id: Optional[int]
    priority: int
    status: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": False}


class FaqSearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=200)
    bot_id: int
    top_k: int = Field(1, ge=1, le=5)


class FaqHit(BaseModel):
    item_id: int
    title: str
    answer: str
    answer_type: int
    score: float
    bm25_score: float
    vector_score: float
    matched_question: str
    hit_by_keyword: bool = False
    keyword_action: Optional[str] = None


class FaqSearchResponse(BaseModel):
    query: str
    bot_id: int
    hit: bool
    result: Optional[FaqHit] = None
    elapsed_ms: float
