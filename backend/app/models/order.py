from sqlalchemy import BigInteger, String, SmallInteger, DateTime, Numeric, Integer
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from decimal import Decimal
from app.core.database import Base


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    order_no: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, comment="订单号")
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment="用户ID")
    product_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True, comment="商品ID")
    product_name: Mapped[str] = mapped_column(String(200), nullable=False, comment="商品名称快照")
    product_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, comment="下单时价格快照")
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1, comment="购买数量")
    total_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, comment="订单总金额")
    status: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=False,
        default=0,
        comment="0待付款/1已付款/2已发货/3已收货/4退款中/5已退款/6已取消"
    )
    logistics_no: Mapped[str | None] = mapped_column(String(100), nullable=True, comment="物流单号")
    logistics_company: Mapped[str | None] = mapped_column(String(100), nullable=True, comment="物流公司")
    logistics_status: Mapped[str | None] = mapped_column(String(50), nullable=True, comment="待发货/已发货/运输中/已签收")
    address: Mapped[dict | None] = mapped_column(JSONB, nullable=True, comment="收货地址快照")
    paid_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, comment="付款时间")
    shipped_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, comment="发货时间")
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, comment="完成时间")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<Order {self.order_no}>"