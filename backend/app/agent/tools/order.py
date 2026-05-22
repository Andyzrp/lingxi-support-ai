# backend/app/agent/tools/order.py
import logging
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, text

from app.models.order import Order
from app.models.product import Product
from app.agent.state import ToolResult

logger = logging.getLogger(__name__)


# ==================== 订单查询工具 ====================


async def query_order(
    db: AsyncSession,
    user_id: Optional[int] = None,
    order_no: Optional[str] = None,
) -> ToolResult:
    """
    查询订单信息

    优先用 order_no 精确查询，
    没有 order_no 则查询该用户最近一条订单

    Args:
        db: 数据库Session
        user_id: 用户ID
        order_no: 订单号（从用户问题中提取）

    Returns:
        ToolResult
    """
    try:
        order = None

        # ── 按订单号查询 ──
        if order_no:
            result = await db.execute(select(Order).where(Order.order_no == order_no))
            order = result.scalar_one_or_none()

            if not order:
                return ToolResult(
                    tool_name="query_order",
                    success=False,
                    data=None,
                    error_msg=f"未找到订单号为 {order_no} 的订单",
                )

            # 验证订单归属（防止越权查询）
            if user_id and order.user_id != user_id:
                return ToolResult(
                    tool_name="query_order",
                    success=False,
                    data=None,
                    error_msg="该订单不属于当前用户",
                )

        # ── 查询最近一条订单 ──
        elif user_id:
            result = await db.execute(
                select(Order)
                .where(Order.user_id == user_id)
                .order_by(Order.created_at.desc())
                .limit(1)
            )
            order = result.scalar_one_or_none()

            if not order:
                return ToolResult(
                    tool_name="query_order",
                    success=False,
                    data=None,
                    error_msg="您还没有任何订单记录",
                )

        else:
            return ToolResult(
                tool_name="query_order",
                success=False,
                data=None,
                error_msg="请提供订单号或用户信息",
            )

        # ── 格式化订单状态 ──
        status_map = {
            0: "待付款",
            1: "已付款",
            2: "已发货",
            3: "已完成",
            4: "已取消",
            5: "退款中",
            6: "已退款",
        }
        status_text = status_map.get(order.status, "未知状态")

        # ── 格式化返回数据 ──
        order_data = {
            "order_no": order.order_no,
            "status": order.status,
            "status_text": status_text,
            "total_amount": float(order.total_amount),
            "product_info": {
                "id": order.product_id,
                "name": order.product_name,
                "price": float(order.product_price),
            },
            "created_at": order.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            "paid_at": (
                order.paid_at.strftime("%Y-%m-%d %H:%M:%S") if order.paid_at else None
            ),
            "remark": getattr(order, "remark", None),
            "logistics_no": getattr(order, "logistics_no", None),
            "logistics_company": getattr(order, "logistics_company", None),
            "logistics_status": getattr(order, "logistics_status", None),
            "card_type": "order",
            "card_data": {
                "order_no": order.order_no,
                "product_name": order.product_name,
                "product_price": float(order.product_price),
                "quantity": order.quantity,
                "total_amount": float(order.total_amount),
                "status": order.status,
                "logistics_no": getattr(order, "logistics_no", None),
                "logistics_status": getattr(order, "logistics_status", None),
                "created_at": order.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            },
        }

        logger.info(
            f"查询订单成功 order_no={order.order_no} "
            f"status={status_text} user_id={user_id}"
        )

        return ToolResult(
            tool_name="query_order",
            success=True,
            data=order_data,
            error_msg=None,
        )

    except Exception as e:
        logger.error(f"查询订单异常: {e}")
        return ToolResult(
            tool_name="query_order",
            success=False,
            data=None,
            error_msg=f"查询订单失败，请稍后重试",
        )


# ==================== 查询订单列表（7天内） ====================


async def query_orders(
    db: AsyncSession,
    user_id: int,
    limit: int = 5,
) -> ToolResult:
    """
    查询用户7天内的订单列表

    Args:
        db: 数据库Session
        user_id: 用户ID
        limit: 返回条数，默认5条

    Returns:
        ToolResult
    """
    try:
        seven_days_ago = func.now() - text("INTERVAL '7 days'")
        result = await db.execute(
            select(Order, Product)
            .outerjoin(Product, Order.product_id == Product.id)
            .where(
                and_(
                    Order.user_id == user_id,
                    Order.created_at >= seven_days_ago,
                )
            )
            .order_by(Order.created_at.desc())
            .limit(limit)
        )
        rows = result.all()

        status_map = {
            0: "待付款",
            1: "已付款",
            2: "已发货",
            3: "已完成",
            4: "已取消",
            5: "退款中",
            6: "已退款",
        }

        card_data_list = []
        for order, product in rows:
            images = product.images if (product and product.images) else []
            image_url = images[0] if isinstance(images, list) and images else None

            card_data_list.append(
                {
                    "order_no": order.order_no,
                    "product_name": order.product_name,
                    "total_amount": float(order.total_amount),
                    "status": order.status,
                    "status_text": status_map.get(order.status, "未知"),
                    "created_at": order.created_at.strftime("%Y-%m-%d %H:%M"),
                    "image": image_url,
                }
            )

        return ToolResult(
            tool_name="query_orders",
            success=True,
            data={
                "total": len(card_data_list),
                "card_type": "orders_list",
                "card_data": card_data_list,
            },
            error_msg=None,
        )

    except Exception as e:
        logger.error(f"查询订单列表异常: {e}")
        return ToolResult(
            tool_name="query_orders",
            success=False,
            data=None,
            error_msg="查询订单列表失败，请稍后重试",
        )


# ==================== 格式化订单信息为自然语言 ====================


def format_order_for_prompt(tool_result: ToolResult) -> str:
    """
    将订单查询结果格式化为自然语言
    注入到 Prompt 中供大模型生成回答使用

    Args:
        tool_result: query_order 返回的 ToolResult

    Returns:
        格式化后的字符串
    """
    if not tool_result["success"]:
        return f"订单查询失败：{tool_result['error_msg']}"

    data = tool_result["data"]
    if not data:
        return "未查询到订单信息"

    lines = [
        f"订单号：{data['order_no']}",
        f"订单状态：{data['status_text']}",
        f"订单金额：¥{data['total_amount']:.2f}",
        f"下单时间：{data['created_at']}",
    ]

    if data.get("paid_at"):
        lines.append(f"付款时间：{data['paid_at']}")

    if data.get("product_info"):
        p = data["product_info"]
        lines.append(f"商品信息：{p['name']}（¥{p['price']:.2f}）")

    if data.get("remark"):
        lines.append(f"备注：{data['remark']}")

    return "\n".join(lines)


# ==================== 查询用户最近N条订单 ====================


async def query_recent_orders(
    db: AsyncSession,
    user_id: int,
    limit: int = 3,
) -> ToolResult:
    """
    查询用户最近N条订单（用于生成用户摘要）

    Args:
        db: 数据库Session
        user_id: 用户ID
        limit: 返回条数，默认3条

    Returns:
        ToolResult
    """
    try:
        result = await db.execute(
            select(Order)
            .where(Order.user_id == user_id)
            .order_by(Order.created_at.desc())
            .limit(limit)
        )
        orders = result.scalars().all()

        if not orders:
            return ToolResult(
                tool_name="query_recent_orders",
                success=True,
                data={"orders": [], "total": 0},
                error_msg=None,
            )

        status_map = {
            0: "待付款",
            1: "已付款",
            2: "已发货",
            3: "已完成",
            4: "已取消",
            5: "退款中",
            6: "已退款",
        }

        orders_data = []
        card_data_list = []
        for order in orders:
            order_info = {
                "order_no": order.order_no,
                "status": order.status,
                "status_text": status_map.get(order.status, "未知"),
                "total_amount": float(order.total_amount),
                "product_info": {
                    "id": order.product_id,
                    "name": order.product_name,
                    "price": float(order.product_price),
                },
                "created_at": order.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            }
            orders_data.append(order_info)
            card_data_list.append(
                {
                    "order_no": order.order_no,
                    "product_name": order.product_name,
                    "total_amount": float(order.total_amount),
                    "status": order.status,
                    "created_at": order.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                }
            )

        result_data = {
            "orders": orders_data,
            "total": len(orders_data),
            "card_type": "order_list",
            "card_data": card_data_list,
        }

        return ToolResult(
            tool_name="query_recent_orders",
            success=True,
            data=result_data,
            error_msg=None,
        )

    except Exception as e:
        logger.error(f"查询最近订单异常: {e}")
        return ToolResult(
            tool_name="query_recent_orders",
            success=False,
            data=None,
            error_msg="查询订单失败",
        )
