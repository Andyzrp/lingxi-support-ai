from pydantic import BaseModel, field_validator
from datetime import datetime
from decimal import Decimal


# ==================== 请求模型 ====================

class ProductCreate(BaseModel):
    """创建商品"""
    name: str
    description: str | None = None
    price: Decimal
    stock: int = 0
    category: str | None = None
    images: list[str] | None = None
    status: int = 1

    @field_validator("name")
    @classmethod
    def name_validator(cls, v: str) -> str:
        if len(v) < 1:
            raise ValueError("商品名称不能为空")
        if len(v) > 200:
            raise ValueError("商品名称不能超过200个字符")
        return v

    @field_validator("price")
    @classmethod
    def price_validator(cls, v: Decimal) -> Decimal:
        if v < 0:
            raise ValueError("价格不能为负数")
        return v

    @field_validator("stock")
    @classmethod
    def stock_validator(cls, v: int) -> int:
        if v < 0:
            raise ValueError("库存不能为负数")
        return v

    @field_validator("status")
    @classmethod
    def status_validator(cls, v: int) -> int:
        if v not in [0, 1]:
            raise ValueError("状态值无效，0下架/1上架")
        return v


class ProductUpdate(BaseModel):
    """更新商品"""
    name: str | None = None
    description: str | None = None
    price: Decimal | None = None
    stock: int | None = None
    category: str | None = None
    images: list[str] | None = None
    status: int | None = None

    @field_validator("price")
    @classmethod
    def price_validator(cls, v: Decimal | None) -> Decimal | None:
        if v is not None and v < 0:
            raise ValueError("价格不能为负数")
        return v

    @field_validator("stock")
    @classmethod
    def stock_validator(cls, v: int | None) -> int | None:
        if v is not None and v < 0:
            raise ValueError("库存不能为负数")
        return v

    @field_validator("status")
    @classmethod
    def status_validator(cls, v: int | None) -> int | None:
        if v is not None and v not in [0, 1]:
            raise ValueError("状态值无效，0下架/1上架")
        return v


class ProductQuery(BaseModel):
    """商品查询参数"""
    keyword: str | None = None
    category: str | None = None
    status: int | None = None


# ==================== 响应模型 ====================

class ProductInfo(BaseModel):
    """商品信息响应"""
    id: int
    name: str
    description: str | None = None
    price: Decimal
    stock: int
    category: str | None = None
    images: list[str] | None = None
    status: int
    created_by: int | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ProductSimple(BaseModel):
    """商品简单信息（列表用）"""
    id: int
    name: str
    price: Decimal
    stock: int
    category: str | None = None
    images: list[str] | None = None
    status: int

    class Config:
        from_attributes = True