# backend/app/models/knowledge.py
from sqlalchemy import (
    BigInteger,
    String,
    SmallInteger,
    DateTime,
    Text,
    Integer,
    ForeignKey,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from app.core.database import Base


class KnowledgeBase(Base):
    __tablename__ = "knowledge_bases"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, comment="知识库名称")
    description: Mapped[str | None] = mapped_column(
        String(500), nullable=True, comment="描述"
    )
    item_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, comment="知识条目数量"
    )
    vector_status: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, default=0, comment="0未建立/1建立中/2已完成/3失败"
    )
    status: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, default=1, comment="0禁用/1启用"
    )
    last_import_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # ✅ relationship 需要子表有ForeignKey才能自动推断
    items: Mapped[list["KnowledgeItem"]] = relationship(
        "KnowledgeItem",
        back_populates="knowledge_base",
        lazy="select",
    )

    def __repr__(self):
        return f"<KnowledgeBase {self.name}>"


class KnowledgeItem(Base):
    __tablename__ = "knowledge_items"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    # ✅ 必须加 ForeignKey！
    knowledge_base_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("knowledge_bases.id", ondelete="RESTRICT"),
        nullable=False,
        comment="所属知识库ID",
    )
    external_id: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="原系统知识ID"
    )
    category: Mapped[str | None] = mapped_column(
        String(200), nullable=True, comment="类目"
    )
    title: Mapped[str] = mapped_column(
        String(120), nullable=False, comment="知识标题/标准问题"
    )
    answer_type: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, default=0, comment="0纯文本/1富文本"
    )
    answer_content: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="答案内容"
    )
    vector_id: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Qdrant向量ID"
    )
    tags: Mapped[dict | None] = mapped_column(JSONB, nullable=True, comment="标签")
    status: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, default=1, comment="0禁用/1启用"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # ✅ 关联关系（ForeignKey已定义，可自动推断）
    knowledge_base: Mapped["KnowledgeBase"] = relationship(
        "KnowledgeBase",
        back_populates="items",
        lazy="select",
    )

    similar_questions: Mapped[list["KnowledgeSimilarQuestion"]] = relationship(
        "KnowledgeSimilarQuestion",
        back_populates="knowledge_item",
        lazy="select",
    )

    def __repr__(self):
        return f"<KnowledgeItem {self.title}>"


class KnowledgeSimilarQuestion(Base):
    __tablename__ = "knowledge_similar_questions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    # ✅ 必须加 ForeignKey！
    knowledge_item_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("knowledge_items.id", ondelete="RESTRICT"),
        nullable=False,
        comment="所属知识条目ID",
    )
    question: Mapped[str] = mapped_column(
        String(200), nullable=False, comment="相似问法"
    )
    vector_id: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Qdrant向量ID"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # ✅ 关联关系
    knowledge_item: Mapped["KnowledgeItem"] = relationship(
        "KnowledgeItem",
        back_populates="similar_questions",
        lazy="select",
    )

    def __repr__(self):
        return f"<KnowledgeSimilarQuestion {self.question}>"
