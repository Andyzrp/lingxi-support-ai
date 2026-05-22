# backend/app/agent/tools/refund.py
import logging
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.models.order import Order
from app.agent.state import ToolResult

logger = logging.getLogger(__name__)


# ==================== 退款条件定义 ====================

# 可申请退款的订单状态
REFUNDABLE_STATUS = [1, 2, 3]  # 已付款、已发货、已完成

# 退款状态说明
REFUND_STATUS_MAP = {
    0: "待付款",
    1: "已付款",
    2: "已发货",
    3: "已完成",
    4: "已取消",
    5: "退款中",
    6: "已退款",
}


# ==================== 退款资格检查 ====================


async def check_refund_eligibility(
    db: AsyncSession,
    user_id: Optional[int] = None,
    order_no: Optional[str] = None,
) -> ToolResult:
    """
    检查订单是否具备退款资格

    Args:
        db: 数据库Session
        user_id: 用户ID
        order_no: 订单号

    Returns:
        ToolResult，data字段包含资格检查结果
    """
    try:
        # ── Step1：查询订单 ──
        if not order_no and not user_id:
            return ToolResult(
                tool_name="check_refund_eligibility",
                success=False,
                data=None,
                error_msg="请提供订单号以查询退款资格",
            )

        order = None

        if order_no:
            result = await db.execute(select(Order).where(Order.order_no == order_no))
            order = result.scalar_one_or_none()

            if not order:
                return ToolResult(
                    tool_name="check_refund_eligibility",
                    success=False,
                    data=None,
                    error_msg=f"未找到订单号 {order_no}",
                )

            # 验证订单归属
            if user_id and order.user_id != user_id:
                return ToolResult(
                    tool_name="check_refund_eligibility",
                    success=False,
                    data=None,
                    error_msg="该订单不属于当前用户",
                )

        elif user_id:
            # 查最近一条订单
            result = await db.execute(
                select(Order)
                .where(Order.user_id == user_id)
                .order_by(Order.created_at.desc())
                .limit(1)
            )
            order = result.scalar_one_or_none()

            if not order:
                return ToolResult(
                    tool_name="check_refund_eligibility",
                    success=False,
                    data=None,
                    error_msg="您暂无订单记录",
                )

        # ── Step2：检查退款资格 ──
        status_text = REFUND_STATUS_MAP.get(order.status, "未知状态")

        # 构建公共数据（包含卡片信息）
        base_data = {
            "order_no": order.order_no,
            "eligible": False,
            "reason": "",
            "status": order.status,
            "status_text": status_text,
            "amount": float(order.total_amount),
            "product_name": getattr(order, "product_name", None),
            "product_price": float(getattr(order, "product_price", 0)),
            "quantity": getattr(order, "quantity", 1),
            "logistics_no": getattr(order, "logistics_no", None),
            "logistics_status": getattr(order, "logistics_status", None),
            "created_at": order.created_at.strftime("%Y-%m-%d %H:%M:%S")
            if order.created_at
            else None,
            "card_type": "order",
            "card_data": {
                "order_no": order.order_no,
                "product_name": getattr(order, "product_name", None),
                "product_price": float(getattr(order, "product_price", 0)),
                "quantity": getattr(order, "quantity", 1),
                "total_amount": float(order.total_amount),
                "status": order.status,
                "logistics_no": getattr(order, "logistics_no", None),
                "logistics_status": getattr(order, "logistics_status", None),
                "created_at": order.created_at.strftime("%Y-%m-%d %H:%M:%S")
                if order.created_at
                else None,
                "refund_eligible": False,
                "refund_tip": "",
            },
        }

        # 设置卡片上的退款提示
        def _set_card_refund(eligible: bool, tip: str):
            base_data["card_data"]["refund_eligible"] = eligible
            base_data["card_data"]["refund_tip"] = tip

        # 已经在退款中
        if order.status == 5:
            base_data["eligible"] = False
            base_data["reason"] = "该订单已在退款处理中，请耐心等待"
            _set_card_refund(False, "该订单已在退款处理中，请耐心等待")
            return ToolResult(
                tool_name="check_refund_eligibility",
                success=True,
                data=base_data,
                error_msg=None,
            )

        # 已经退款完成
        if order.status == 6:
            base_data["eligible"] = False
            base_data["reason"] = "该订单已完成退款"
            _set_card_refund(False, "该订单已完成退款")
            return ToolResult(
                tool_name="check_refund_eligibility",
                success=True,
                data=base_data,
                error_msg=None,
            )

        # 已取消
        if order.status == 4:
            base_data["eligible"] = False
            base_data["reason"] = "该订单已取消，无需退款"
            _set_card_refund(False, "该订单已取消，无需退款")
            return ToolResult(
                tool_name="check_refund_eligibility",
                success=True,
                data=base_data,
                error_msg=None,
            )

        # 待付款无需退款
        if order.status == 0:
            base_data["eligible"] = False
            base_data["reason"] = "该订单尚未付款，可直接取消订单"
            _set_card_refund(False, "该订单尚未付款，可直接取消订单")
            return ToolResult(
                tool_name="check_refund_eligibility",
                success=True,
                data=base_data,
                error_msg=None,
            )

        # 符合退款条件
        if order.status in REFUNDABLE_STATUS:
            base_data["eligible"] = True
            base_data["reason"] = "订单符合退款条件，确认后将退款至原支付渠道"
            _set_card_refund(True, "")
            return ToolResult(
                tool_name="check_refund_eligibility",
                success=True,
                data=base_data,
                error_msg=None,
            )

        # 其他状态不支持退款
        base_data["eligible"] = False
        base_data["reason"] = f"当前订单状态（{status_text}）不支持退款"
        _set_card_refund(False, f"当前订单状态（{status_text}）不支持退款")
        return ToolResult(
            tool_name="check_refund_eligibility",
            success=True,
            data=base_data,
            error_msg=None,
        )

    except Exception as e:
        logger.error(f"检查退款资格异常: {e}")
        return ToolResult(
            tool_name="check_refund_eligibility",
            success=False,
            data=None,
            error_msg="查询退款资格失败，请稍后重试",
        )


async def apply_refund(
    db: AsyncSession,
    user_id: Optional[int] = None,
    order_no: Optional[str] = None,
    reason: Optional[str] = None,
) -> ToolResult:
    """
    申请退款

    流程：
    1. 检查退款资格
    2. 更新订单状态为退款中(5)
    3. 记录退款原因

    Args:
        db: 数据库Session
        user_id: 用户ID
        order_no: 订单号
        reason: 退款原因

    Returns:
        ToolResult
    """
    try:
        # ── Step1：检查退款资格 ──
        eligibility = await check_refund_eligibility(
            db=db,
            user_id=user_id,
            order_no=order_no,
        )

        if not eligibility["success"]:
            return ToolResult(
                tool_name="apply_refund",
                success=False,
                data=None,
                error_msg=eligibility["error_msg"],
            )

        data = eligibility["data"]

        if not data.get("eligible"):
            return ToolResult(
                tool_name="apply_refund",
                success=False,
                data=data,
                error_msg=data.get("reason", "不符合退款条件"),
            )

        actual_order_no = data["order_no"]
        refund_amount = data["amount"]

        # ── Step2：更新订单状态为退款中 ──
        remark = f"退款申请：{reason}" if reason else "用户申请退款"

        await db.execute(
            update(Order)
            .where(Order.order_no == actual_order_no)
            .values(status=5)  # 退款中
        )
        await db.commit()

        logger.info(
            f"退款申请成功 order_no={actual_order_no} "
            f"amount={refund_amount} user_id={user_id}"
        )

        return ToolResult(
            tool_name="apply_refund",
            success=True,
            data={
                "order_no": actual_order_no,
                "refund_amount": refund_amount,
                "reason": reason or "用户申请退款",
                "status": "退款中",
                "message": f"退款申请已提交成功！退款金额 ¥{refund_amount:.2f} 将在3-5个工作日内原路退回",
                "card_type": "order",
                "card_data": {
                    "order_no": actual_order_no,
                    "status": 5,
                    "status_text": "退款中",
                    "total_amount": refund_amount,
                },
            },
            error_msg=None,
        )

    except Exception as e:
        logger.error(f"申请退款异常: {e}")
        return ToolResult(
            tool_name="apply_refund",
            success=False,
            data=None,
            error_msg="退款申请失败，请稍后重试或联系人工客服",
        )


# ==================== 格式化退款信息为自然语言 ====================


def format_refund_for_prompt(tool_result: ToolResult) -> str:
    """
    将退款结果格式化为自然语言
    注入到 Prompt 中供大模型生成回答使用

    Args:
        tool_result: apply_refund 或 check_refund_eligibility 返回的 ToolResult

    Returns:
        格式化后的字符串
    """
    tool_name = tool_result.get("tool_name", "")

    if not tool_result["success"]:
        return f"退款操作失败：{tool_result['error_msg']}"

    data = tool_result.get("data")
    if not data or not isinstance(data, dict):
        return f"退款操作失败：{tool_result.get('error_msg', '未知错误')}"

    # 资格检查结果
    if tool_name == "check_refund_eligibility":
        lines = [
            f"订单号：{data.get('order_no')}",
            f"订单状态：{data.get('status_text')}",
            f"订单金额：¥{data.get('amount', 0):.2f}",
            f"是否可退款：{'是' if data.get('eligible') else '否'}",
            f"原因：{data.get('reason')}",
        ]
        return "\n".join(lines)

    # 退款申请结果
    if tool_name == "apply_refund":
        lines = [
            f"订单号：{data.get('order_no')}",
            f"退款金额：¥{data.get('refund_amount', 0):.2f}",
            f"退款状态：{data.get('status')}",
            f"退款说明：{data.get('message')}",
        ]
        return "\n".join(lines)
