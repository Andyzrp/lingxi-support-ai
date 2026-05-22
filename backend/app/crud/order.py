from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
import uuid
from app.crud.base import CRUDBase
from app.models.order import Order


class CRUDOrder(CRUDBase[Order]):

    def _generate_order_no(self) -> str:
        """生成订单号"""
        now = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        unique = str(uuid.uuid4()).replace("-", "")[:8].upper()
        return f"ORD{now}{unique}"

    async def create_order(
        self,
        db: AsyncSession,
        user_id: int,
        product_id: int,
        product_name: str,
        product_price: float,
        quantity: int,
        address: dict,
    ) -> Order:
        """创建订单"""
        order = Order(
            order_no=self._generate_order_no(),
            user_id=user_id,
            product_id=product_id,
            product_name=product_name,
            product_price=product_price,
            quantity=quantity,
            total_amount=product_price * quantity,
            address=address,
            status=1,
            paid_at=datetime.utcnow(),
            logistics_status="待发货",
        )
        db.add(order)
        await db.flush()
        await db.refresh(order)
        return order

    async def get_by_order_no(
        self,
        db: AsyncSession,
        order_no: str,
    ) -> Order | None:
        """根据订单号获取订单"""
        result = await db.execute(
            select(Order).where(Order.order_no == order_no)
        )
        return result.scalar_one_or_none()

    async def get_user_orders(
        self,
        db: AsyncSession,
        user_id: int,
        offset: int = 0,
        limit: int = 20,
        status: int | None = None,
    ) -> list[Order]:
        """获取用户订单列表"""
        query = select(Order).where(Order.user_id == user_id)
        if status is not None:
            query = query.where(Order.status == status)
        query = query.order_by(Order.created_at.desc()).offset(offset).limit(limit)
        result = await db.execute(query)
        return list(result.scalars().all())

    async def count_user_orders(
        self,
        db: AsyncSession,
        user_id: int,
        status: int | None = None,
    ) -> int:
        """统计用户订单数量"""
        query = select(func.count()).select_from(Order).where(
            Order.user_id == user_id
        )
        if status is not None:
            query = query.where(Order.status == status)
        result = await db.execute(query)
        return result.scalar_one()

    async def get_multi_with_filter(
        self,
        db: AsyncSession,
        offset: int = 0,
        limit: int = 20,
        user_id: int | None = None,
        status: int | None = None,
        keyword: str | None = None,
    ) -> list[Order]:
        """带过滤条件获取订单列表"""
        query = select(Order)
        if user_id is not None:
            query = query.where(Order.user_id == user_id)
        if status is not None:
            query = query.where(Order.status == status)
        if keyword:
            query = query.where(
                or_(
                    Order.order_no.ilike(f"%{keyword}%"),
                    Order.product_name.ilike(f"%{keyword}%"),
                )
            )
        query = query.order_by(Order.created_at.desc()).offset(offset).limit(limit)
        result = await db.execute(query)
        return list(result.scalars().all())

    async def count_with_filter(
        self,
        db: AsyncSession,
        user_id: int | None = None,
        status: int | None = None,
        keyword: str | None = None,
    ) -> int:
        """带过滤条件统计订单数量"""
        query = select(func.count()).select_from(Order)
        if user_id is not None:
            query = query.where(Order.user_id == user_id)
        if status is not None:
            query = query.where(Order.status == status)
        if keyword:
            query = query.where(
                or_(
                    Order.order_no.ilike(f"%{keyword}%"),
                    Order.product_name.ilike(f"%{keyword}%"),
                )
            )
        result = await db.execute(query)
        return result.scalar_one()

    async def update_status(
        self,
        db: AsyncSession,
        order: Order,
        status: int,
    ) -> Order:
        """更新订单状态"""
        order.status = status
        if status == 1:
            order.paid_at = datetime.utcnow()
        elif status == 2:
            order.shipped_at = datetime.utcnow()
            order.logistics_status = "已发货"
        elif status == 3:
            order.completed_at = datetime.utcnow()
            order.logistics_status = "已签收"
        elif status == 4:
            order.logistics_status = "退款中"
        elif status == 5:
            order.logistics_status = "已退款"
        db.add(order)
        await db.flush()
        await db.refresh(order)
        return order

    async def apply_refund(
        self,
        db: AsyncSession,
        order: Order,
    ) -> Order:
        """申请退款"""
        order.status = 4
        order.logistics_status = "退款中"
        db.add(order)
        await db.flush()
        await db.refresh(order)
        return order

    async def get_latest_user_order(
        self,
        db: AsyncSession,
        user_id: int,
    ) -> Order | None:
        """获取用户最新订单"""
        result = await db.execute(
            select(Order).where(
                Order.user_id == user_id,
            ).order_by(Order.created_at.desc()).limit(1)
        )
        return result.scalar_one_or_none()


crud_order = CRUDOrder(Order)