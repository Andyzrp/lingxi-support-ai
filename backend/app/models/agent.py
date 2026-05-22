from sqlalchemy import BigInteger, String, SmallInteger, DateTime, Text, Integer, Float
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from app.core.database import Base


class Agent(Base):
    __tablename__ = "agents"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, comment="Agent名称")
    description: Mapped[str | None] = mapped_column(String(500), nullable=True, comment="描述")
    current_version_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True, comment="当前生效版本ID")
    draft_version_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True, comment="当前草稿版本ID")
    status: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=1, comment="0禁用/1启用")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<Agent {self.name}>"


class AgentVersion(Base):
    __tablename__ = "agent_versions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    agent_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment="所属Agent ID")
    version_no: Mapped[str] = mapped_column(String(20), nullable=False, comment="版本号如v1.0")
    status: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=False,
        default=0,
        comment="0草稿/1已发布/2已归档"
    )
    published_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, comment="发布时间")
    remark: Mapped[str | None] = mapped_column(String(500), nullable=True, comment="版本备注")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<AgentVersion {self.version_no}>"


class AgentConfig(Base):
    __tablename__ = "agent_configs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    agent_version_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False, comment="关联版本ID")
    knowledge_base_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True, comment="关联知识库ID")
    system_prompt: Mapped[str | None] = mapped_column(Text, nullable=True, comment="机器人模式系统Prompt")
    human_prompt: Mapped[str | None] = mapped_column(Text, nullable=True, comment="人工客服模式Prompt")
    model_type: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0, comment="0DeepSeek/1Qwen")
    model_params: Mapped[dict | None] = mapped_column(JSONB, nullable=True, comment="模型参数")
    rag_threshold: Mapped[float] = mapped_column(Float, nullable=False, default=0.75, comment="RAG检索阈值")
    context_rounds: Mapped[int] = mapped_column(Integer, nullable=False, default=3, comment="上下文保留轮数")
    emotion_detection: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=1, comment="0关/1开")
    emotion_keywords: Mapped[dict | None] = mapped_column(JSONB, nullable=True, comment="情绪关键词列表")
    complaint_keywords: Mapped[dict | None] = mapped_column(JSONB, nullable=True, comment="投诉关键词列表")
    auto_transfer: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=1, comment="0关/1开")
    auto_transfer_count: Mapped[int] = mapped_column(Integer, nullable=False, default=3, comment="连续答不上N次触发")
    staff_names: Mapped[dict | None] = mapped_column(JSONB, nullable=True, comment="客服名字库列表")
    tools_config: Mapped[dict | None] = mapped_column(JSONB, nullable=True, comment="工具调用配置")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<AgentConfig version_id={self.agent_version_id}>"