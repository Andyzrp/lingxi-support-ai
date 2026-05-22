from fastapi import APIRouter, Body, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.exceptions import NotFoundException, BadRequestException
from app.crud.order import crud_order
from app.crud.product import crud_product
from app.schemas.order import (
    OrderCreate,
    OrderInfo,
    OrderSimple,
    LogisticsInfo,
    RefundRequest,
)
from app.utils.response import Response, PageResponse
from app.utils.pagination import get_page_params, PageParams
from app.api.deps import get_current_user, get_current_admin
from app.models.user import User
from app.models.admin import Admin

router = APIRouter()


# ==================== 前台接口（用户使用）====================


@router.post("", response_model=Response[OrderInfo], summary="创建订单")
async def create_order(
    data: OrderCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """用户下单"""
    # 获取商品信息
    product = await crud_product.get_active_product(db, data.product_id)
    if not product:
        raise NotFoundException("商品不存在或已下架")

    # 检查库存
    if product.stock < data.quantity:
        raise BadRequestException(f"库存不足，当前库存{product.stock}")

    # 扣减库存
    await crud_product.update_stock(db, data.product_id, data.quantity)

    # 创建订单
    order = await crud_order.create_order(
        db=db,
        user_id=current_user.id,
        product_id=data.product_id,
        product_name=product.name,
        product_price=float(product.price),
        quantity=data.quantity,
        address=data.address.model_dump(),
    )
    return Response.success(
        data=OrderInfo.model_validate(order),
        message="下单成功",
    )


@router.get("", response_model=PageResponse[OrderSimple], summary="获取我的订单列表")
async def get_my_orders(
    status: int | None = None,
    db: AsyncSession = Depends(get_db),
    page_params: PageParams = Depends(get_page_params),
    current_user: User = Depends(get_current_user),
):
    """获取当前用户订单列表"""
    orders = await crud_order.get_user_orders(
        db=db,
        user_id=current_user.id,
        offset=page_params.offset,
        limit=page_params.limit,
        status=status,
    )
    total = await crud_order.count_user_orders(
        db=db,
        user_id=current_user.id,
        status=status,
    )
    return PageResponse.success(
        data=[OrderSimple.model_validate(o) for o in orders],
        total=total,
        page=page_params.page,
        page_size=page_params.page_size,
    )


@router.get("/{order_no}", response_model=Response[OrderInfo], summary="获取订单详情")
async def get_order_detail(
    order_no: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取订单详情"""
    order = await crud_order.get_by_order_no(db, order_no)
    if not order:
        raise NotFoundException("订单不存在")
    if order.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权限查看此订单",
        )
    return Response.success(data=OrderInfo.model_validate(order))


@router.get(
    "/{order_no}/logistics",
    response_model=Response[LogisticsInfo],
    summary="查询物流信息",
)
async def get_logistics(
    order_no: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """查询订单物流信息"""
    order = await crud_order.get_by_order_no(db, order_no)
    if not order:
        raise NotFoundException("订单不存在")
    if order.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权限查看此订单",
        )
    return Response.success(
        data=LogisticsInfo(
            order_no=order.order_no,
            logistics_no=order.logistics_no,
            logistics_company=order.logistics_company,
            logistics_status=order.logistics_status,
            shipped_at=order.shipped_at,
        )
    )


@router.post("/refund", response_model=Response, summary="申请退款")
async def apply_refund(
    data: RefundRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """申请退款"""
    order = await crud_order.get_by_order_no(db, data.order_no)
    if not order:
        raise NotFoundException("订单不存在")
    if order.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权限操作此订单",
        )
    if order.status not in [1, 2, 3]:
        raise BadRequestException("当前订单状态不支持退款")
    await crud_order.apply_refund(db=db, order=order)
    return Response.success(message="退款申请已提交")


# ==================== 后台接口（管理员使用）====================


@router.get(
    "/admin/list", response_model=PageResponse[OrderInfo], summary="管理员获取订单列表"
)
async def admin_get_orders(
    user_id: int | None = None,
    status: int | None = None,
    keyword: str | None = None,
    db: AsyncSession = Depends(get_db),
    page_params: PageParams = Depends(get_page_params),
    current_admin: Admin = Depends(get_current_admin),
):
    """管理员获取订单列表"""
    orders = await crud_order.get_multi_with_filter(
        db=db,
        offset=page_params.offset,
        limit=page_params.limit,
        user_id=user_id,
        status=status,
        keyword=keyword,
    )
    total = await crud_order.count_with_filter(
        db=db,
        user_id=user_id,
        status=status,
        keyword=keyword,
    )
    return PageResponse.success(
        data=[OrderInfo.model_validate(o) for o in orders],
        total=total,
        page=page_params.page,
        page_size=page_params.page_size,
    )


class UpdateOrderStatusBody(BaseModel):
    status: int


@router.patch(
    "/admin/{order_no}/status",
    response_model=Response[OrderInfo],
    summary="更新订单状态",
)
async def admin_update_order_status(
    order_no: str,
    body: UpdateOrderStatusBody,
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin),
):
    """管理员更新订单状态"""
    order = await crud_order.get_by_order_no(db, order_no)
    if not order:
        raise NotFoundException("订单不存在")
    order = await crud_order.update_status(
        db=db,
        order=order,
        status=body.status,
    )
    return Response.success(
        data=OrderInfo.model_validate(order),
        message="更新成功",
    )


@router.get(
    "/admin/{order_no}",
    response_model=Response[OrderInfo],
    summary="管理员获取订单详情",
)
async def admin_get_order_detail(
    order_no: str,
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin),
):
    """管理员获取订单详情"""
    order = await crud_order.get_by_order_no(db, order_no)
    if not order:
        raise NotFoundException("订单不存在")
    return Response.success(data=OrderInfo.model_validate(order))
