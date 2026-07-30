# backend/app/agent/tools/logistics.py
import logging
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.order import Order
from app.agent.state import ToolResult

logger = logging.getLogger(__name__)


# ==================== 物流状态定义 ====================

LOGISTICS_STATUS_MAP = {
    0: "待揽收",
    1: "已揽收",
    2: "运输中",
    3: "派送中",
    4: "已签收",
    5: "派送失败",
    6: "已退回",
}

# Mock物流公司列表
LOGISTICS_COMPANIES = {
    "SF": "顺丰速运",
    "ZTO": "中通快递",
    "YTO": "圆通速递",
    "STO": "申通快递",
    "YUNDA": "韵达快递",
    "JD": "京东物流",
}


# ==================== Mock物流轨迹生成 ====================


def _generate_mock_tracks(
    order_no: str,
    order_status: int,
) -> list:
    """
    根据订单状态生成Mock物流轨迹

    实际项目中这里对接真实物流API
    现在用Mock数据模拟，保证链路跑通

    Args:
        order_no: 订单号
        order_status: 订单状态

    Returns:
        物流轨迹列表，按时间倒序
    """
    import hashlib
    from datetime import datetime, timedelta

    # 用订单号生成伪随机但稳定的数据
    seed = int(hashlib.md5(order_no.encode()).hexdigest()[:8], 16)
    base_time = datetime(2024, 1, 1) + timedelta(days=seed % 365)

    tracks = []

    # 根据订单状态决定显示哪些轨迹
    if order_status >= 1:  # 已付款
        tracks.append(
            {
                "time": (base_time + timedelta(hours=2)).strftime("%Y-%m-%d %H:%M:%S"),
                "status": "待揽收",
                "location": "商家仓库",
                "description": "商家已备货，等待快递揽收",
            }
        )

    if order_status >= 2:  # 已发货
        tracks.append(
            {
                "time": (base_time + timedelta(hours=6)).strftime("%Y-%m-%d %H:%M:%S"),
                "status": "已揽收",
                "location": "上海市浦东新区",
                "description": "快件已被顺丰速运揽收",
            }
        )
        tracks.append(
            {
                "time": (base_time + timedelta(hours=14)).strftime("%Y-%m-%d %H:%M:%S"),
                "status": "运输中",
                "location": "上海转运中心",
                "description": "快件已到达上海转运中心，正在分拣",
            }
        )
        tracks.append(
            {
                "time": (base_time + timedelta(hours=30)).strftime("%Y-%m-%d %H:%M:%S"),
                "status": "运输中",
                "location": "北京转运中心",
                "description": "快件已到达北京转运中心",
            }
        )
        tracks.append(
            {
                "time": (base_time + timedelta(hours=46)).strftime("%Y-%m-%d %H:%M:%S"),
                "status": "派送中",
                "location": "北京市朝阳区",
                "description": "快件正在派送中，请保持电话畅通",
            }
        )

    if order_status >= 3:  # 已完成
        tracks.append(
            {
                "time": (base_time + timedelta(hours=50)).strftime("%Y-%m-%d %H:%M:%S"),
                "status": "已签收",
                "location": "北京市朝阳区",
                "description": "快件已由本人签收，感谢使用顺丰速运",
            }
        )

    # 按时间倒序（最新的在前）
    tracks.reverse()
    return tracks


def _get_mock_logistics_no(order_no: str) -> str:
    """根据订单号生成稳定的Mock快递单号"""
    import hashlib

    hash_val = hashlib.md5(order_no.encode()).hexdigest()[:12].upper()
    return f"SF{hash_val}"


def _get_mock_company(order_no: str) -> tuple:
    """根据订单号稳定分配快递公司"""
    import hashlib

    seed = int(hashlib.md5(order_no.encode()).hexdigest()[:4], 16)
    companies = list(LOGISTICS_COMPANIES.items())
    code, name = companies[seed % len(companies)]
    return code, name


# ==================== 物流查询工具 ====================


async def query_logistics(
    db: AsyncSession,
    user_id: Optional[int] = None,
    order_no: Optional[str] = None,
) -> ToolResult:
    """
    查询物流信息

    Args:
        db: 数据库Session
        user_id: 用户ID（用于验证订单归属）
        order_no: 订单号

    Returns:
        ToolResult，data字段包含物流详情
    """
    try:
        # ── Step1：查询订单 ──
        if not order_no and not user_id:
            return ToolResult(
                tool_name="query_logistics",
                success=False,
                data=None,
                error_msg="请提供订单号以查询物流",
            )

        order = None

        if order_no:
            result = await db.execute(select(Order).where(Order.order_no == order_no))
            order = result.scalar_one_or_none()

            if not order:
                return ToolResult(
                    tool_name="query_logistics",
                    success=False,
                    data=None,
                    error_msg=f"未找到订单号 {order_no}",
                )

            # 验证归属
            if user_id and order.user_id != user_id:
                return ToolResult(
                    tool_name="query_logistics",
                    success=False,
                    data=None,
                    error_msg="该订单不属于当前用户",
                )

        elif user_id:
            # 查最近一条已发货订单
            result = await db.execute(
                select(Order)
                .where(
                    Order.user_id == user_id,
                    Order.status.in_([2, 3]),  # 已发货或已完成
                )
                .order_by(Order.created_at.desc())
                .limit(1)
            )
            order = result.scalar_one_or_none()

            if not order:
                return ToolResult(
                    tool_name="query_logistics",
                    success=False,
                    data=None,
                    error_msg="您暂无可查询物流的订单（订单需处于已发货状态）",
                )

        # ── Step2：判断订单状态 ──
        order_status = order.status

        if order_status == 0:
            return ToolResult(
                tool_name="query_logistics",
                success=True,
                data={
                    "order_no": order.order_no,
                    "logistics_status": "待付款",
                    "message": "订单尚未付款，暂无物流信息",
                    "tracks": [],
                },
                error_msg=None,
            )

        if order_status == 1:
            return ToolResult(
                tool_name="query_logistics",
                success=True,
                data={
                    "order_no": order.order_no,
                    "logistics_status": "待发货",
                    "message": "商家正在备货，预计1-2个工作日内发货",
                    "tracks": [],
                },
                error_msg=None,
            )

        if order_status == 6:
            return ToolResult(
                tool_name="query_logistics",
                success=True,
                data={
                    "order_no": order.order_no,
                    "logistics_status": "已取消",
                    "message": "订单已取消，无物流信息",
                    "tracks": [],
                },
                error_msg=None,
            )

        # ── Step3：生成Mock物流数据 ──
        logistics_no = _get_mock_logistics_no(order.order_no)
        company_code, company_name = _get_mock_company(order.order_no)
        tracks = _generate_mock_tracks(order.order_no, order_status)

        # 当前物流状态
        current_status = "运输中"
        if order_status == 2:
            current_status = "运输中"
        elif order_status == 3:
            current_status = "已签收"
        elif order_status == 4:
            current_status = "退款中"
        elif order_status == 5:
            current_status = "已退款"

        logistics_data = {
            "order_no": order.order_no,
            "logistics_no": logistics_no,
            "company_code": company_code,
            "company_name": company_name,
            "logistics_status": current_status,
            "latest_track": tracks[0] if tracks else None,
            "tracks": tracks,
            "estimated_delivery": ("预计明天送达" if order_status == 2 else None),
        }

        logger.info(f"查询物流成功 order_no={order.order_no} status={current_status}")

        return ToolResult(
            tool_name="query_logistics",
            success=True,
            data={
                "card_type": "logistics",
                "card_data": logistics_data,
            },
            error_msg=None,
        )

    except Exception as e:
        logger.error(f"查询物流异常: {e}")
        return ToolResult(
            tool_name="query_logistics",
            success=False,
            data=None,
            error_msg="查询物流失败，请稍后重试",
        )


# ==================== 格式化物流信息为自然语言 ====================


def format_logistics_for_prompt(tool_result: ToolResult) -> str:
    """
    将物流查询结果格式化为自然语言
    注入到 Prompt 中供大模型生成回答使用

    Args:
        tool_result: query_logistics 返回的 ToolResult

    Returns:
        格式化后的字符串
    """
    if not tool_result["success"]:
        return f"物流查询失败：{tool_result['error_msg']}"

    data = tool_result["data"]
    if not data:
        return "未查询到物流信息"

    # 无轨迹的情况
    if not data.get("tracks"):
        return (
            f"订单号：{data['order_no']}\n"
            f"物流状态：{data['logistics_status']}\n"
            f"{data.get('message', '')}"
        )

    lines = [
        f"订单号：{data['order_no']}",
        f"快递公司：{data['company_name']}",
        f"快递单号：{data['logistics_no']}",
        f"当前状态：{data['logistics_status']}",
    ]

    if data.get("estimated_delivery"):
        lines.append(f"预计送达：{data['estimated_delivery']}")

    # 最新轨迹
    latest = data.get("latest_track")
    if latest:
        lines.append(
            f"最新动态：{latest['time']} "
            f"【{latest['location']}】{latest['description']}"
        )

    return "\n".join(lines)
