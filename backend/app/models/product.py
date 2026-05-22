from sqlalchemy import (
    BigInteger,
    String,
    SmallInteger,
    DateTime,
    Text,
    Numeric,
    Integer,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from decimal import Decimal
from app.core.database import Base


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False, comment="商品名称")
    description: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="商品描述"
    )
    price: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False, comment="价格"
    )
    stock: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, comment="库存"
    )
    category: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="分类"
    )
    images: Mapped[dict | None] = mapped_column(
        JSONB, nullable=True, comment="商品图片列表"
    )
    status: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, default=1, comment="0下架/1上架"
    )
    created_by: Mapped[int | None] = mapped_column(
        BigInteger, nullable=True, comment="创建管理员ID"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    def __repr__(self):
        return f"<Product {self.name}>"
