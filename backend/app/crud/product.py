from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from app.crud.base import CRUDBase
from app.models.product import Product


class CRUDProduct(CRUDBase[Product]):

    async def get_multi_with_filter(
        self,
        db: AsyncSession,
        offset: int = 0,
        limit: int = 20,
        keyword: str | None = None,
        category: str | None = None,
        status: int | None = None,
    ) -> list[Product]:
        """带过滤条件获取商品列表"""
        query = select(Product)
        if keyword:
            query = query.where(
                or_(
                    Product.name.ilike(f"%{keyword}%"),
                    Product.description.ilike(f"%{keyword}%"),
                )
            )
        if category:
            query = query.where(Product.category == category)
        if status is not None:
            query = query.where(Product.status == status)
        query = query.offset(offset).limit(limit)
        result = await db.execute(query)
        return list(result.scalars().all())

    async def count_with_filter(
        self,
        db: AsyncSession,
        keyword: str | None = None,
        category: str | None = None,
        status: int | None = None,
    ) -> int:
        """带过滤条件统计商品数量"""
        query = select(func.count()).select_from(Product)
        if keyword:
            query = query.where(
                or_(
                    Product.name.ilike(f"%{keyword}%"),
                    Product.description.ilike(f"%{keyword}%"),
                )
            )
        if category:
            query = query.where(Product.category == category)
        if status is not None:
            query = query.where(Product.status == status)
        result = await db.execute(query)
        return result.scalar_one()

    async def create_product(
        self,
        db: AsyncSession,
        name: str,
        price: float,
        stock: int = 0,
        description: str | None = None,
        category: str | None = None,
        images: list[str] | None = None,
        status: int = 1,
        created_by: int | None = None,
    ) -> Product:
        """创建商品"""
        product = Product(
            name=name,
            price=price,
            stock=stock,
            description=description,
            category=category,
            images=images,
            status=status,
            created_by=created_by,
        )
        db.add(product)
        await db.flush()
        await db.refresh(product)
        return product

    async def update_product(
        self,
        db: AsyncSession,
        product: Product,
        name: str | None = None,
        description: str | None = None,
        price: float | None = None,
        stock: int | None = None,
        category: str | None = None,
        images: list[str] | None = None,
        status: int | None = None,
    ) -> Product:
        """更新商品信息"""
        if name is not None:
            product.name = name
        if description is not None:
            product.description = description
        if price is not None:
            product.price = price
        if stock is not None:
            product.stock = stock
        if category is not None:
            product.category = category
        if images is not None:
            product.images = images
        if status is not None:
            product.status = status
        db.add(product)
        await db.flush()
        await db.refresh(product)
        return product

    async def update_stock(
        self,
        db: AsyncSession,
        product_id: int,
        quantity: int,
    ) -> Product | None:
        """更新库存（下单时减库存）"""
        product = await self.get(db, product_id)
        if not product:
            return None
        if product.stock < quantity:
            raise ValueError("库存不足")
        product.stock -= quantity
        db.add(product)
        await db.flush()
        await db.refresh(product)
        return product

    async def get_active_product(
        self,
        db: AsyncSession,
        product_id: int,
    ) -> Product | None:
        """获取上架状态的商品"""
        result = await db.execute(
            select(Product).where(
                Product.id == product_id,
                Product.status == 1,
            )
        )
        return result.scalar_one_or_none()

    async def get_categories(
        self,
        db: AsyncSession,
    ) -> list[str]:
        """获取所有分类"""
        result = await db.execute(
            select(Product.category).where(
                Product.category.isnot(None),
                Product.status == 1,
            ).distinct()
        )
        return [row[0] for row in result.all()]


crud_product = CRUDProduct(Product)