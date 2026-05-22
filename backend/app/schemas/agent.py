# backend/app/schemas/agent.py
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import IntEnum


class AgentStatus(IntEnum):
    DISABLED = 0
    ENABLED = 1


class VersionStatus(IntEnum):
    DRAFT = 0
    PUBLISHED = 1
    ARCHIVED = 2


# ==================== Agent ====================


class AgentCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    # ✅ agents表没有bot_id，bot关联在agent_configs表
    knowledge_base_id: Optional[int] = Field(None, description="绑定的知识库ID")


class AgentUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    status: Optional[AgentStatus] = None


class AgentOut(BaseModel):
    id: int
    name: str
    description: Optional[str]
    status: int
    current_version_id: Optional[int] = None
    draft_version_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    current_version: Optional[str] = None
    model: Optional[str] = None
    tools_enabled: Optional[List[str]] = None
    version_count: int = 0
    today_sessions: int = 0
    resolve_rate: Optional[float] = None

    model_config = {"from_attributes": False}


# ==================== Agent版本 ====================


class AgentVersionCreate(BaseModel):
    description: Optional[str] = Field(None, max_length=200)


class AgentVersionOut(BaseModel):
    id: int
    agent_id: int
    version_no: str
    status: int
    status_text: Optional[str] = None
    remark: Optional[str]
    published_at: Optional[datetime]
    created_at: datetime
    model: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    tools_enabled: Optional[List[str]] = None
    no_answer_threshold: Optional[int] = None
    system_prompt: Optional[str] = None

    model_config = {"from_attributes": False}


# ==================== Agent配置 ====================


class AgentConfigUpdate(BaseModel):
    model: Optional[str] = Field(None, description="模型标识")
    system_prompt: Optional[str] = Field(None, max_length=4000)
    temperature: Optional[float] = Field(None, ge=0.0, le=1.0)
    max_tokens: Optional[int] = Field(None, ge=256, le=8192)
    tools_enabled: Optional[List[str]] = Field(None)
    no_answer_threshold: Optional[int] = Field(None, ge=1, le=10)
    transfer_keywords: Optional[List[str]] = Field(None)
    knowledge_base_id: Optional[int] = None


class AgentConfigOut(BaseModel):
    id: int
    agent_version_id: int
    knowledge_base_id: Optional[int]
    system_prompt: Optional[str]
    model: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    tools_enabled: Optional[List[str]] = None
    no_answer_threshold: Optional[int] = None
    transfer_keywords: Optional[List[str]] = None
    model_type: int
    rag_threshold: float
    context_rounds: int
    emotion_detection: int
    auto_transfer: int
    auto_transfer_count: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": False}


# ==================== 工作流展示 ====================


class WorkflowNode(BaseModel):
    id: str
    name: str
    type: str
    description: str
    inputs: List[str] = Field(default_factory=list)
    outputs: List[str] = Field(default_factory=list)


class WorkflowEdge(BaseModel):
    from_node: str
    to_node: str
    condition: Optional[str] = None


class WorkflowGraph(BaseModel):
    nodes: List[WorkflowNode]
    edges: List[WorkflowEdge]
