from typing import Any, Generic, TypeVar
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import Base

ModelType = TypeVar("ModelType", bound=Base)


class CRUDBase(Generic[ModelType]):
    """基础CRUD操作"""

    def __init__(self, model: type[ModelType]):
        self.model = model

    async def get(self, db: AsyncSession, id: int) -> ModelType | None:
        """根据ID获取单条记录"""
        result = await db.execute(
            select(self.model).where(self.model.id == id)
        )
        return result.scalar_one_or_none()

    async def get_multi(
        self,
        db: AsyncSession,
        offset: int = 0,
        limit: int = 20,
    ) -> list[ModelType]:
        """获取多条记录"""
        result = await db.execute(
            select(self.model).offset(offset).limit(limit)
        )
        return list(result.scalars().all())

    async def count(self, db: AsyncSession) -> int:
        """获取总数"""
        result = await db.execute(
            select(func.count()).select_from(self.model)
        )
        return result.scalar_one()

    async def create(self, db: AsyncSession, obj_in: dict) -> ModelType:
        """创建记录"""
        db_obj = self.model(**obj_in)
        db.add(db_obj)
        await db.flush()
        await db.refresh(db_obj)
        return db_obj

    async def update(
        self,
        db: AsyncSession,
        db_obj: ModelType,
        obj_in: dict,
    ) -> ModelType:
        """更新记录"""
        for field, value in obj_in.items():
            if value is not None and hasattr(db_obj, field):
                setattr(db_obj, field, value)
        db.add(db_obj)
        await db.flush()
        await db.refresh(db_obj)
        return db_obj

    async def delete(self, db: AsyncSession, id: int) -> bool:
        """删除记录"""
        db_obj = await self.get(db, id)
        if not db_obj:
            return False
        await db.delete(db_obj)
        await db.flush()
        return True

    async def exists(self, db: AsyncSession, id: int) -> bool:
        """判断记录是否存在"""
        result = await db.execute(
            select(func.count()).select_from(self.model).where(
                self.model.id == id
            )
        )
        return result.scalar_one() > 0