from sqlalchemy import BigInteger, String, SmallInteger, DateTime, Text, Integer, Float
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from app.core.database import Base


class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    conversation_no: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False, comment="会话编号"
    )
    channel_id: Mapped[int | None] = mapped_column(
        BigInteger, nullable=True, comment="渠道ID"
    )
    user_id: Mapped[int | None] = mapped_column(
        BigInteger, nullable=True, comment="用户ID，访客可为空"
    )
    username: Mapped[str | None] = mapped_column(
        String(50), nullable=True, comment="用户名快照"
    )
    agent_id: Mapped[int | None] = mapped_column(
        BigInteger, nullable=True, comment="使用的Agent ID"
    )
    bot_id: Mapped[int | None] = mapped_column(
        BigInteger, nullable=True, comment="使用的Bot ID"
    )
    session_type: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=False,
        default=0,
        comment="0机器人会话/1人工会话/2机器人转人工",
    )
    current_mode: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, default=0, comment="0Bot/1Agent/2人工"
    )
    staff_name: Mapped[str | None] = mapped_column(
        String(50), nullable=True, comment="分配的客服名称"
    )
    is_transferred: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, default=0, comment="0否/1是"
    )
    transfer_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True, comment="转人工时间"
    )
    transfer_reason: Mapped[int | None] = mapped_column(
        SmallInteger,
        nullable=True,
        comment="0用户主动/1连续答不上/2情绪激动/3关键词触发",
    )
    is_resolved: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, default=0, comment="0否/1是"
    )
    no_answer_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, comment="连续未答上次数"
    )
    message_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, comment="消息总数"
    )
    round_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, comment="对话轮次"
    )
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True, comment="会话开始时间"
    )
    ended_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True, comment="会话结束时间"
    )
    duration: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="会话时长秒"
    )
    first_response_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True, comment="首次响应时间"
    )
    close_reason: Mapped[int | None] = mapped_column(
        SmallInteger, nullable=True, comment="0超时自动关闭/1用户主动关闭/2系统关闭"
    )
    evaluated: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, default=0, comment="0否/1是"
    )
    eval_score: Mapped[int | None] = mapped_column(
        SmallInteger, nullable=True, comment="评价分数1-5星"
    )
    eval_tags: Mapped[dict | None] = mapped_column(
        JSONB, nullable=True, comment="评价标签列表"
    )
    eval_comment: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="评价留言"
    )
    eval_resolved: Mapped[int | None] = mapped_column(
        SmallInteger, nullable=True, comment="评价是否解决0否/1是"
    )
    eval_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True, comment="评价时间"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="active",
        index=True,
        comment="会话状态: active/closed/transferred",
    )
    eval_pushed_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True, comment="评价卡片推送时间"
    )

    def __repr__(self):
        return f"<Conversation {self.conversation_no}>"


class AiConversationDetail(Base):
    __tablename__ = "ai_conversation_details"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    conversation_id: Mapped[int] = mapped_column(
        BigInteger, nullable=False, comment="会话ID"
    )
    channel_id: Mapped[int | None] = mapped_column(
        BigInteger, nullable=True, comment="渠道ID"
    )
    channel_type: Mapped[str | None] = mapped_column(
        String(50), nullable=True, comment="渠道类型快照"
    )
    channel_name: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="渠道名称快照"
    )
    user_id: Mapped[int | None] = mapped_column(
        BigInteger, nullable=True, comment="用户ID"
    )
    round_index: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1, comment="第几轮对话"
    )
    user_message: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="用户原声"
    )
    bot_answer: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="Bot回答内容"
    )
    agent_answer: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="Agent回答内容"
    )
    answer_source: Mapped[int | None] = mapped_column(
        SmallInteger, nullable=True, comment="0Bot FAQ/1关键词干预/2Agent/3人工模式"
    )
    is_resolved: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, default=0, comment="0否/1是"
    )
    is_transferred: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, default=0, comment="0否/1是"
    )
    is_no_answer: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, default=0, comment="0否/1是"
    )
    is_clicked: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, default=0, comment="0否/1是"
    )
    is_liked: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, default=0, comment="0否/1是"
    )
    is_disliked: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, default=0, comment="0否/1是"
    )
    dislike_reason: Mapped[int | None] = mapped_column(
        SmallInteger, nullable=True, comment="0答非所问/1太简单/2太复杂/3格式问题"
    )
    knowledge_item_id: Mapped[int | None] = mapped_column(
        BigInteger, nullable=True, comment="命中的知识条目ID"
    )
    match_score: Mapped[float | None] = mapped_column(
        Float, nullable=True, comment="匹配相似度分数"
    )
    emotion_detected: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, default=0, comment="0否/1是"
    )
    tools_called: Mapped[dict | None] = mapped_column(
        JSONB, nullable=True, comment="本轮调用的工具列表"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
    response_ms: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="Bot/Agent 响应耗时（毫秒），每轮对话记录一次"
    )

    def __repr__(self):
        return f"<AiConversationDetail conv={self.conversation_id} round={self.round_index}>"


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    conversation_id: Mapped[int] = mapped_column(
        BigInteger, nullable=False, comment="会话ID"
    )
    sender_type: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, comment="0用户/1Bot/2Agent/3人工客服/4系统"
    )
    sender_name: Mapped[str | None] = mapped_column(
        String(50), nullable=True, comment="发送方名称快照"
    )
    content_type: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=False,
        default=0,
        comment="0纯文本/1HTML富文本/2系统通知/3评价卡片",
    )
    content: Mapped[str | None] = mapped_column(Text, nullable=True, comment="消息内容")
    extra: Mapped[dict | None] = mapped_column(JSONB, nullable=True, comment="附加信息")
    is_read: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, default=0, comment="0否/1是"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    def __repr__(self):
        return f"<Message conv={self.conversation_id} type={self.sender_type}>"


class AnnotationRecord(Base):
    __tablename__ = "annotation_records"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    conversation_id: Mapped[int] = mapped_column(
        BigInteger, nullable=False, comment="会话ID"
    )
    message_id: Mapped[int | None] = mapped_column(
        BigInteger, nullable=True, comment="标注的具体消息ID"
    )
    ai_detail_id: Mapped[int | None] = mapped_column(
        BigInteger, nullable=True, comment="AI会话明细ID"
    )
    annotation_type: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, comment="0好回答/1差回答"
    )
    annotation_tags: Mapped[dict | None] = mapped_column(
        JSONB, nullable=True, comment="标注标签列表"
    )
    annotation_note: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="标注备注"
    )
    knowledge_item_id: Mapped[int | None] = mapped_column(
        BigInteger, nullable=True, comment="关联知识条目ID"
    )
    annotated_by: Mapped[int] = mapped_column(
        BigInteger, nullable=False, comment="标注人ID"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    def __repr__(self):
        return f"<AnnotationRecord conv={self.conversation_id} type={self.annotation_type}>"
