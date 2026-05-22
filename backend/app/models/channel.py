from sqlalchemy import BigInteger, String, SmallInteger, DateTime, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from app.core.database import Base


class Channel(Base):
    __tablename__ = "channels"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, comment="渠道名称")
    description: Mapped[str | None] = mapped_column(
        String(500), nullable=True, comment="描述"
    )
    type: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, default=0, comment="0测试/1正式"
    )
    language: Mapped[str] = mapped_column(
        String(20), nullable=False, default="zh-CN", comment="语种"
    )
    access_mode: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, default=0, comment="0需登录/1允许访客"
    )
    bot_id: Mapped[int | None] = mapped_column(
        BigInteger, nullable=True, comment="关联Bot ID"
    )
    agent_id: Mapped[int | None] = mapped_column(
        BigInteger, nullable=True, comment="关联Agent ID"
    )
    channel_token: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False, comment="渠道唯一标识Token"
    )
    status: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, default=1, comment="0禁用/1启用"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    configs: Mapped[list["ChannelConfig"]] = relationship(
        back_populates="channel", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Channel {self.name}>"


class ChannelConfig(Base):
    __tablename__ = "channel_configs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    channel_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("channels.id", ondelete="CASCADE"),
        nullable=False,
        comment="渠道ID",
    )
    config_type: Mapped[str] = mapped_column(
        String(20), nullable=False, comment="hot_questions / banners / quick_tags"
    )
    title: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="标题/问题/标签文字"
    )
    content: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="热点问答案/标签发送内容/Banner副标题"
    )
    image_url: Mapped[str | None] = mapped_column(
        String(500), nullable=True, comment="Banner图片地址"
    )
    link_url: Mapped[str | None] = mapped_column(
        String(500), nullable=True, comment="Banner跳转链接"
    )
    icon: Mapped[str | None] = mapped_column(
        String(10), nullable=True, comment="标签图标emoji"
    )
    sort_order: Mapped[int] = mapped_column(default=0, comment="排序")
    status: Mapped[int] = mapped_column(SmallInteger, default=1, comment="0禁用/1启用")
    extra: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="扩展字段JSON"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    channel: Mapped["Channel"] = relationship(back_populates="configs")

    def __repr__(self):
        return f"<ChannelConfig {self.channel_id}/{self.config_type}>"
