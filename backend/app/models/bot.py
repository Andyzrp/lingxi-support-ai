from sqlalchemy import BigInteger, String, SmallInteger, DateTime, Integer, Float
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from app.core.database import Base


class Bot(Base):
    __tablename__ = "bots"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, comment="Bot名称")
    description: Mapped[str | None] = mapped_column(String(500), nullable=True, comment="描述")
    knowledge_base_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True, comment="关联知识库ID")
    match_threshold: Mapped[float] = mapped_column(Float, nullable=False, default=0.85, comment="匹配相似度阈值")
    no_answer_count: Mapped[int] = mapped_column(Integer, nullable=False, default=3, comment="连续答不上N次触发转人工")
    auto_transfer: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=1, comment="0否/1是")
    status: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=1, comment="0禁用/1启用")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<Bot {self.name}>"


class BotKeyword(Base):
    __tablename__ = "bot_keywords"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    bot_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment="所属Bot ID")
    keyword: Mapped[str] = mapped_column(String(100), nullable=False, comment="关键词")
    match_type: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=1, comment="0精确/1包含")
    actions: Mapped[dict] = mapped_column(JSONB, nullable=False, comment="触发动作组合")
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=0, comment="优先级数字越小越高")
    status: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=1, comment="0禁用/1启用")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<BotKeyword {self.keyword}>"