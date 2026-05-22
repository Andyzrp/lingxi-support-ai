from pydantic import BaseModel, field_validator, computed_field
from datetime import datetime
from decimal import Decimal


# ==================== 请求模型 ====================


class AddressInfo(BaseModel):
    """收货地址"""

    name: str
    phone: str
    province: str
    city: str
    district: str
    detail: str


class OrderCreate(BaseModel):
    """创建订单"""

    product_id: int
    quantity: int = 1
    address: AddressInfo

    @field_validator("quantity")
    @classmethod
    def quantity_validator(cls, v: int) -> int:
        if v < 1:
            raise ValueError("购买数量不能少于1")
        if v > 999:
            raise ValueError("购买数量不能超过999")
        return v


class OrderQuery(BaseModel):
    """订单查询参数"""

    status: int | None = None
    keyword: str | None = None


class OrderStatusUpdate(BaseModel):
    """更新订单状态"""

    status: int

    @field_validator("status")
    @classmethod
    def status_validator(cls, v: int) -> int:
        if v not in [0, 1, 2, 3, 4, 5, 6]:
            raise ValueError(
                "状态值无效，0待付款/1已付款/2已发货/3已收货/4退款中/5已退款/6已取消"
            )
        return v


class RefundRequest(BaseModel):
    """申请退款"""

    order_no: str
    reason: str | None = None


# ==================== 响应模型 ====================


class OrderInfo(BaseModel):
    """订单信息响应"""

    id: int
    order_no: str
    user_id: int
    product_id: int | None = None
    product_name: str
    product_price: Decimal
    quantity: int
    total_amount: Decimal
    status: int
    logistics_no: str | None = None
    logistics_company: str | None = None
    logistics_status: str | None = None
    address: dict | None = None
    paid_at: datetime | None = None
    shipped_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

    @computed_field
    @property
    def status_text(self) -> str:
        status_map = {
            0: "待付款",
            1: "已付款",
            2: "已发货",
            3: "已收货",
            4: "退款中",
            5: "已退款",
            6: "已取消",
        }
        return status_map.get(self.status, "未知")


class OrderSimple(BaseModel):
    """订单简单信息（列表用）"""

    id: int
    order_no: str
    product_name: str
    total_amount: Decimal
    status: int
    logistics_status: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class LogisticsInfo(BaseModel):
    """物流信息响应"""

    order_no: str
    logistics_no: str | None = None
    logistics_company: str | None = None
    logistics_status: str | None = None
    shipped_at: datetime | None = None
