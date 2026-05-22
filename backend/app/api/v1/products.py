from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.exceptions import NotFoundException
from app.crud.product import crud_product
from app.schemas.product import (
    ProductCreate,
    ProductUpdate,
    ProductInfo,
    ProductSimple,
)
from app.utils.response import Response, PageResponse
from app.utils.pagination import get_page_params, PageParams
from app.api.deps import get_current_user, get_current_admin
from app.models.user import User
from app.models.admin import Admin

router = APIRouter()


# ==================== 前台接口（用户使用）====================

@router.get("", response_model=PageResponse[ProductSimple], summary="获取商品列表")
async def get_products(
    keyword: str | None = None,
    category: str | None = None,
    db: AsyncSession = Depends(get_db),
    page_params: PageParams = Depends(get_page_params),
):
    """获取上架商品列表（前台）"""
    products = await crud_product.get_multi_with_filter(
        db=db,
        offset=page_params.offset,
        limit=page_params.limit,
        keyword=keyword,
        category=category,
        status=1,
    )
    total = await crud_product.count_with_filter(
        db=db,
        keyword=keyword,
        category=category,
        status=1,
    )
    return PageResponse.success(
        data=[ProductSimple.model_validate(p) for p in products],
        total=total,
        page=page_params.page,
        page_size=page_params.page_size,
    )


@router.get("/categories", response_model=Response[list[str]], summary="获取商品分类")
async def get_categories(
    db: AsyncSession = Depends(get_db),
):
    """获取所有商品分类"""
    categories = await crud_product.get_categories(db)
    return Response.success(data=categories)


@router.get("/{product_id}", response_model=Response[ProductInfo], summary="获取商品详情")
async def get_product(
    product_id: int,
    db: AsyncSession = Depends(get_db),
):
    """获取商品详情（前台）"""
    product = await crud_product.get_active_product(db, product_id)
    if not product:
        raise NotFoundException("商品不存在或已下架")
    return Response.success(data=ProductInfo.model_validate(product))


# ==================== 后台接口（管理员使用）====================

@router.get("/admin/list", response_model=PageResponse[ProductInfo], summary="管理员获取商品列表")
async def admin_get_products(
    keyword: str | None = None,
    category: str | None = None,
    status: int | None = None,
    db: AsyncSession = Depends(get_db),
    page_params: PageParams = Depends(get_page_params),
    current_admin: Admin = Depends(get_current_admin),
):
    """管理员获取商品列表（包含下架商品）"""
    products = await crud_product.get_multi_with_filter(
        db=db,
        offset=page_params.offset,
        limit=page_params.limit,
        keyword=keyword,
        category=category,
        status=status,
    )
    total = await crud_product.count_with_filter(
        db=db,
        keyword=keyword,
        category=category,
        status=status,
    )
    return PageResponse.success(
        data=[ProductInfo.model_validate(p) for p in products],
        total=total,
        page=page_params.page,
        page_size=page_params.page_size,
    )


@router.post("/admin", response_model=Response[ProductInfo], summary="创建商品")
async def create_product(
    data: ProductCreate,
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin),
):
    """创建商品（管理员）"""
    product = await crud_product.create_product(
        db=db,
        name=data.name,
        price=data.price,
        stock=data.stock,
        description=data.description,
        category=data.category,
        images=data.images,
        status=data.status,
        created_by=current_admin.id,
    )
    return Response.success(
        data=ProductInfo.model_validate(product),
        message="创建成功",
    )


@router.put("/admin/{product_id}", response_model=Response[ProductInfo], summary="更新商品")
async def update_product(
    product_id: int,
    data: ProductUpdate,
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin),
):
    """更新商品信息（管理员）"""
    product = await crud_product.get(db, product_id)
    if not product:
        raise NotFoundException("商品不存在")
    product = await crud_product.update_product(
        db=db,
        product=product,
        name=data.name,
        description=data.description,
        price=data.price,
        stock=data.stock,
        category=data.category,
        images=data.images,
        status=data.status,
    )
    return Response.success(
        data=ProductInfo.model_validate(product),
        message="更新成功",
    )


@router.delete("/admin/{product_id}", response_model=Response, summary="删除商品")
async def delete_product(
    product_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin),
):
    """删除商品（管理员）"""
    success = await crud_product.delete(db, product_id)
    if not success:
        raise NotFoundException("商品不存在")
    return Response.success(message="删除成功")


@router.patch("/admin/{product_id}/status", response_model=Response[ProductInfo], summary="更新商品状态")
async def update_product_status(
    product_id: int,
    status: int,
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin),
):
    """上架/下架商品（管理员）"""
    if status not in [0, 1]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="状态值无效，0下架/1上架",
        )
    product = await crud_product.get(db, product_id)
    if not product:
        raise NotFoundException("商品不存在")
    product = await crud_product.update_product(
        db=db,
        product=product,
        status=status,
    )
    return Response.success(
        data=ProductInfo.model_validate(product),
        message="更新成功",
    )