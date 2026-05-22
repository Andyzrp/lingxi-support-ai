# backend/app/agent/tools/product.py
import logging
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.models.product import Product
from app.agent.state import ToolResult

logger = logging.getLogger(__name__)


# ==================== 商品查询工具 ====================


async def query_product(
    db: AsyncSession,
    product_name: Optional[str] = None,
    product_id: Optional[int] = None,
    category: Optional[str] = None,
) -> ToolResult:
    """
    查询商品信息

    优先级：
    1. product_id 精确查询
    2. product_name 模糊查询
    3. category 分类查询

    Args:
        db: 数据库Session
        product_name: 商品名称（模糊匹配）
        product_id: 商品ID（精确匹配）
        category: 商品分类

    Returns:
        ToolResult
    """
    try:
        # ── 按ID精确查询 ──
        if product_id:
            result = await db.execute(
                select(Product).where(
                    and_(
                        Product.id == product_id,
                        Product.status == 1,
                    )
                )
            )
            product = result.scalar_one_or_none()

            if not product:
                return ToolResult(
                    tool_name="query_product",
                    success=False,
                    data=None,
                    error_msg=f"未找到ID为 {product_id} 的商品",
                )

            return ToolResult(
                tool_name="query_product",
                success=True,
                data={"products": [_format_product(product)], "total": 1},
                error_msg=None,
            )

        # ── 按名称模糊查询 ──
        if product_name:
            result = await db.execute(
                select(Product)
                .where(
                    and_(
                        Product.name.ilike(f"%{product_name}%"),
                        Product.status == 1,
                    )
                )
                .order_by(Product.created_at.desc())
                .limit(5)
            )
            products = result.scalars().all()

            if not products:
                return ToolResult(
                    tool_name="query_product",
                    success=False,
                    data=None,
                    error_msg=f"未找到名称包含'{product_name}'的商品",
                )

            return ToolResult(
                tool_name="query_product",
                success=True,
                data={
                    "products": [_format_product(p) for p in products],
                    "total": len(products),
                },
                error_msg=None,
            )

        # ── 按分类查询 ──
        if category:
            result = await db.execute(
                select(Product)
                .where(
                    and_(
                        Product.category == category,
                        Product.status == 1,
                    )
                )
                .order_by(Product.created_at.desc())
                .limit(5)
            )
            products = result.scalars().all()

            if not products:
                return ToolResult(
                    tool_name="query_product",
                    success=False,
                    data=None,
                    error_msg=f"分类'{category}'下暂无商品",
                )

            return ToolResult(
                tool_name="query_product",
                success=True,
                data={
                    "products": [_format_product(p) for p in products],
                    "total": len(products),
                },
                error_msg=None,
            )

        # ── 无查询条件 ──
        return ToolResult(
            tool_name="query_product",
            success=False,
            data=None,
            error_msg="请提供商品名称或分类以查询商品",
        )

    except Exception as e:
        logger.error(f"查询商品异常: {e}")
        return ToolResult(
            tool_name="query_product",
            success=False,
            data=None,
            error_msg="查询商品失败，请稍后重试",
        )


# ==================== 查询热销商品 ====================


async def query_hot_products(
    db: AsyncSession,
    limit: int = 5,
) -> ToolResult:
    """
    查询热销商品列表

    Args:
        db: 数据库Session
        limit: 返回条数，默认5条

    Returns:
        ToolResult
    """
    try:
        result = await db.execute(
            select(Product)
            .where(Product.status == 1)
            .order_by(Product.created_at.desc())
            .limit(limit)
        )
        products = result.scalars().all()

        if not products:
            return ToolResult(
                tool_name="query_hot_products",
                success=True,
                data={
                    "products": [],
                    "total": 0,
                    "card_type": "product_list",
                    "card_data": [],
                    "message": "暂无热销商品数据",
                },
                error_msg=None,
            )

        card_data = [_format_product_for_card(p) for p in products]

        return ToolResult(
            tool_name="query_hot_products",
            success=True,
            data={
                "products": [_format_product(p) for p in products],
                "total": len(products),
                "card_type": "product_list",
                "card_data": card_data,
            },
            error_msg=None,
        )

    except Exception as e:
        logger.error(f"查询热销商品异常: {e}")
        return ToolResult(
            tool_name="query_hot_products",
            success=False,
            data=None,
            error_msg="查询热销商品失败，请稍后重试",
        )


# ==================== 查询商品分类列表 ====================


async def query_categories(
    db: AsyncSession,
) -> ToolResult:
    """
    查询所有商品分类

    Args:
        db: 数据库Session

    Returns:
        ToolResult
    """
    try:
        from sqlalchemy import distinct, func

        result = await db.execute(
            select(
                Product.category,
                func.count(Product.id).label("count"),
            )
            .where(
                and_(
                    Product.status == 1,
                    Product.category.isnot(None),
                )
            )
            .group_by(Product.category)
            .order_by(func.count(Product.id).desc())
        )
        rows = result.all()

        if not rows:
            return ToolResult(
                tool_name="query_categories",
                success=False,
                data=None,
                error_msg="暂无商品分类数据",
            )

        categories = [{"name": row.category, "count": row.count} for row in rows]

        return ToolResult(
            tool_name="query_categories",
            success=True,
            data={"categories": categories, "total": len(categories)},
            error_msg=None,
        )

    except Exception as e:
        logger.error(f"查询商品分类异常: {e}")
        return ToolResult(
            tool_name="query_categories",
            success=False,
            data=None,
            error_msg="查询分类失败，请稍后重试",
        )


# ==================== 内部辅助函数 ====================


def _format_product(product: Product) -> dict:
    """
    格式化商品数据

    Args:
        product: Product ORM对象

    Returns:
        格式化后的dict
    """
    if product.stock == 0:
        stock_status = "已售罄"
    elif product.stock <= 10:
        stock_status = f"仅剩{product.stock}件"
    else:
        stock_status = "有货"

    return {
        "id": product.id,
        "name": product.name,
        "category": product.category,
        "price": float(product.price),
        "stock": product.stock,
        "stock_status": stock_status,
        "description": product.description,
        "images": product.images,
    }


def _format_product_for_card(product: Product) -> dict:
    """
    格式化商品数据（用于卡片展示）

    Args:
        product: Product ORM对象

    Returns:
        格式化后的dict，符合前端ProductListCard组件期望格式
    """
    images = product.images if isinstance(product.images, list) else []
    image_url = images[0] if images else None

    return {
        "id": product.id,
        "name": product.name,
        "image": image_url,
        "price": float(product.price),
        "stock": product.stock,
    }


# ==================== 格式化商品信息为自然语言 ====================


def format_product_for_prompt(tool_result: ToolResult) -> str:
    """
    将商品查询结果格式化为自然语言
    注入到 Prompt 中供大模型生成回答使用

    Args:
        tool_result: query_product 返回的 ToolResult

    Returns:
        格式化后的字符串
    """
    if not tool_result["success"]:
        return f"商品查询失败：{tool_result['error_msg']}"

    data = tool_result["data"]
    if not data or not data.get("products"):
        return "未查询到商品信息"

    products = data["products"]
    total = data["total"]

    # 单个商品详细展示
    if total == 1:
        p = products[0]
        lines = [f"商品名称：{p['name']}"]

        if p.get("category"):
            lines.append(f"商品分类：{p['category']}")

        lines.append(f"销售价格：¥{p['price']:.2f}")

        lines.append(f"库存状态：{p['stock_status']}")

        if p.get("description"):
            lines.append(f"商品描述：{p['description'][:100]}")

        return "\n".join(lines)

    # 多个商品列表展示
    lines = [f"为您找到以下 {total} 款相关商品："]
    for i, p in enumerate(products, 1):
        price_str = f"¥{p['price']:.2f}"
        lines.append(f"{i}. {p['name']} - {price_str} ({p['stock_status']})")

    return "\n".join(lines)


def format_hot_products_for_prompt(tool_result: ToolResult) -> str:
    """
    将热销商品格式化为自然语言

    Args:
        tool_result: query_hot_products 返回的 ToolResult

    Returns:
        格式化后的字符串
    """
    if not tool_result["success"]:
        return f"热销商品查询失败：{tool_result['error_msg']}"

    data = tool_result["data"]
    if not data or not data.get("products"):
        return "暂无热销商品信息"

    products = data["products"]
    lines = ["以下是我们的热销商品："]

    for i, p in enumerate(products, 1):
        lines.append(f"{i}. {p['name']} ¥{p['price']:.2f} ({p['stock_status']})")

    return "\n".join(lines)
