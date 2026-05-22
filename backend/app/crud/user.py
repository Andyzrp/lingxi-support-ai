from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.crud.base import CRUDBase
from app.models.user import User
from app.core.security import get_password_hash, verify_password


class CRUDUser(CRUDBase[User]):

    async def get_by_username(
        self,
        db: AsyncSession,
        username: str,
    ) -> User | None:
        """根据用户名获取用户"""
        result = await db.execute(
            select(User).where(User.username == username)
        )
        return result.scalar_one_or_none()

    async def create_user(
        self,
        db: AsyncSession,
        username: str,
        password: str,
        nickname: str | None = None,
    ) -> User:
        """创建用户"""
        user = User(
            username=username,
            password_hash=get_password_hash(password),
            nickname=nickname or username,
        )
        db.add(user)
        await db.flush()
        await db.refresh(user)
        return user

    async def authenticate(
        self,
        db: AsyncSession,
        username: str,
        password: str,
    ) -> User | None:
        """验证用户名密码"""
        user = await self.get_by_username(db, username)
        if not user:
            return None
        if not verify_password(password, user.password_hash):
            return None
        return user

    async def update_user(
        self,
        db: AsyncSession,
        user: User,
        nickname: str | None = None,
        avatar: str | None = None,
        phone: str | None = None,
    ) -> User:
        """更新用户信息"""
        if nickname is not None:
            user.nickname = nickname
        if avatar is not None:
            user.avatar = avatar
        if phone is not None:
            user.phone = phone
        db.add(user)
        await db.flush()
        await db.refresh(user)
        return user

    async def update_password(
        self,
        db: AsyncSession,
        user: User,
        new_password: str,
    ) -> User:
        """更新密码"""
        user.password_hash = get_password_hash(new_password)
        db.add(user)
        await db.flush()
        await db.refresh(user)
        return user

    async def username_exists(
        self,
        db: AsyncSession,
        username: str,
    ) -> bool:
        """判断用户名是否已存在"""
        result = await db.execute(
            select(func.count()).select_from(User).where(
                User.username == username
            )
        )
        return result.scalar_one() > 0

    async def get_active_user(
        self,
        db: AsyncSession,
        user_id: int,
    ) -> User | None:
        """获取正常状态的用户"""
        result = await db.execute(
            select(User).where(
                User.id == user_id,
                User.status == 1,
            )
        )
        return result.scalar_one_or_none()


crud_user = CRUDUser(User)