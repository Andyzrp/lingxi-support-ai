from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from app.crud.base import CRUDBase
from app.models.admin import Admin
from app.core.security import get_password_hash, verify_password


class CRUDAdmin(CRUDBase[Admin]):

    async def get_by_username(
        self,
        db: AsyncSession,
        username: str,
    ) -> Admin | None:
        """根据用户名获取管理员"""
        result = await db.execute(
            select(Admin).where(Admin.username == username)
        )
        return result.scalar_one_or_none()

    async def create_admin(
        self,
        db: AsyncSession,
        username: str,
        password: str,
        nickname: str | None = None,
        role: int = 1,
    ) -> Admin:
        """创建管理员"""
        admin = Admin(
            username=username,
            password_hash=get_password_hash(password),
            nickname=nickname or username,
            role=role,
        )
        db.add(admin)
        await db.flush()
        await db.refresh(admin)
        return admin

    async def authenticate(
        self,
        db: AsyncSession,
        username: str,
        password: str,
    ) -> Admin | None:
        """验证管理员用户名密码"""
        admin = await self.get_by_username(db, username)
        if not admin:
            return None
        if not verify_password(password, admin.password_hash):
            return None
        return admin

    async def update_last_login(
        self,
        db: AsyncSession,
        admin: Admin,
    ) -> Admin:
        """更新最后登录时间"""
        admin.last_login_at = datetime.utcnow()
        db.add(admin)
        await db.flush()
        await db.refresh(admin)
        return admin

    async def update_admin(
        self,
        db: AsyncSession,
        admin: Admin,
        nickname: str | None = None,
        role: int | None = None,
        status: int | None = None,
    ) -> Admin:
        """更新管理员信息"""
        if nickname is not None:
            admin.nickname = nickname
        if role is not None:
            admin.role = role
        if status is not None:
            admin.status = status
        db.add(admin)
        await db.flush()
        await db.refresh(admin)
        return admin

    async def update_password(
        self,
        db: AsyncSession,
        admin: Admin,
        new_password: str,
    ) -> Admin:
        """更新密码"""
        admin.password_hash = get_password_hash(new_password)
        db.add(admin)
        await db.flush()
        await db.refresh(admin)
        return admin

    async def username_exists(
        self,
        db: AsyncSession,
        username: str,
    ) -> bool:
        """判断用户名是否已存在"""
        result = await db.execute(
            select(func.count()).select_from(Admin).where(
                Admin.username == username
            )
        )
        return result.scalar_one() > 0

    async def get_active_admin(
        self,
        db: AsyncSession,
        admin_id: int,
    ) -> Admin | None:
        """获取正常状态的管理员"""
        result = await db.execute(
            select(Admin).where(
                Admin.id == admin_id,
                Admin.status == 1,
            )
        )
        return result.scalar_one_or_none()

    async def get_multi_by_role(
        self,
        db: AsyncSession,
        role: int,
        offset: int = 0,
        limit: int = 20,
    ) -> list[Admin]:
        """根据角色获取管理员列表"""
        result = await db.execute(
            select(Admin).where(
                Admin.role == role,
            ).offset(offset).limit(limit)
        )
        return list(result.scalars().all())

    async def count_by_role(
        self,
        db: AsyncSession,
        role: int,
    ) -> int:
        """根据角色统计管理员数量"""
        result = await db.execute(
            select(func.count()).select_from(Admin).where(
                Admin.role == role,
            )
        )
        return result.scalar_one()


crud_admin = CRUDAdmin(Admin)