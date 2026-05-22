# backend/app/schemas/knowledge.py
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime
from enum import IntEnum


class AnswerType(IntEnum):
    TEXT = 0
    HTML = 1


class KnowledgeItemStatus(IntEnum):
    DISABLED = 0
    ENABLED = 1


# ==================== 知识库 ====================


class KnowledgeBaseCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)


class KnowledgeBaseUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    status: Optional[int] = Field(None, ge=0, le=1)


class KnowledgeBaseOut(BaseModel):
    id: int
    name: str
    description: Optional[str]
    status: int = 1
    item_count: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": False}


# ==================== 相似问法 ====================


class SimilarQuestionOut(BaseModel):
    id: int
    question: str
    created_at: datetime

    model_config = {"from_attributes": False}


# ==================== 知识条目 ====================


class KnowledgeItemCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    answer: str = Field(..., min_length=1)
    answer_type: AnswerType = Field(AnswerType.TEXT)
    category: Optional[str] = Field(None, max_length=50)
    tags: Optional[str] = Field(None, max_length=200)
    similar_questions: Optional[List[str]] = Field(default_factory=list)

    @field_validator("similar_questions")
    @classmethod
    def validate_similar_questions(cls, v):
        if v is None:
            return []
        return [q.strip() for q in v if q.strip()]


class KnowledgeItemUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    answer: Optional[str] = Field(None, min_length=1)
    answer_type: Optional[AnswerType] = None
    category: Optional[str] = Field(None, max_length=50)
    tags: Optional[str] = Field(None, max_length=200)
    status: Optional[KnowledgeItemStatus] = None
    similar_questions: Optional[List[str]] = None

    @field_validator("similar_questions")
    @classmethod
    def validate_similar_questions(cls, v):
        if v is None:
            return None
        return [q.strip() for q in v if q.strip()]


class KnowledgeItemOut(BaseModel):
    id: int
    knowledge_base_id: int
    title: str
    answer: str
    answer_type: int
    category: Optional[str]
    tags: Optional[List[str]] = Field(default_factory=list)
    status: int
    similar_count: int = 0
    similar_questions: List[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": False}


class KnowledgeItemDetail(KnowledgeItemOut):
    similar_questions: List[SimilarQuestionOut] = Field(default_factory=list)

    model_config = {"from_attributes": False}


# ==================== Excel导入 ====================


class ImportRowData(BaseModel):
    title: str
    answer: str
    answer_type: AnswerType = AnswerType.TEXT
    category: Optional[str] = None
    tags: Optional[str] = None
    similar_questions: List[str] = Field(default_factory=list)


class ImportProgress(BaseModel):
    task_id: str
    status: str
    total: int = 0
    processed: int = 0
    succeeded: int = 0
    failed: int = 0
    progress: float = 0.0
    error_msg: Optional[str] = None
    has_errors: bool = False


class ImportResult(BaseModel):
    task_id: str
    total: int
    succeeded: int
    failed: int
    failed_rows: List[dict] = Field(default_factory=list)


# ==================== 检索测试 ====================


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=200)
    top_k: int = Field(5, ge=1, le=20)
    score_threshold: float = Field(0.0, ge=0.0, le=1.0)


class SearchResultItem(BaseModel):
    item_id: int
    title: str
    answer: str
    answer_type: int
    category: Optional[str]
    score: float
    bm25_score: float = 0.0
    vector_score: float = 0.0
    matched_question: str

    model_config = {"from_attributes": False}


class SearchResponse(BaseModel):
    query: str
    results: List[SearchResultItem]
    total: int
    elapsed_ms: float


# ==================== 列表查询参数 ====================


class KnowledgeItemQuery(BaseModel):
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)
    keyword: Optional[str] = None
    category: Optional[str] = None
    status: Optional[KnowledgeItemStatus] = None
