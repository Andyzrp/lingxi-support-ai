from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.security import get_current_user_id, get_current_admin_id
from app.crud.user import crud_user
from app.crud.admin import crud_admin
from app.models.user import User
from app.models.admin import Admin


async def get_current_user(
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
) -> User:
    """获取当前登录用户"""
    user = await crud_user.get_active_user(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在或已被禁用",
        )
    return user


async def get_current_admin(
    db: AsyncSession = Depends(get_db),
    admin_id: int = Depends(get_current_admin_id),
) -> Admin:
    """获取当前登录管理员"""
    admin = await crud_admin.get_active_admin(db, admin_id)
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="管理员不存在或已被禁用",
        )
    return admin


async def get_current_super_admin(
    db: AsyncSession = Depends(get_db),
    admin_id: int = Depends(get_current_admin_id),
) -> Admin:
    """获取当前超级管理员"""
    admin = await crud_admin.get_active_admin(db, admin_id)
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="管理员不存在或已被禁用",
        )
    if admin.role != 0:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要超级管理员权限",
        )
    return admin


async def get_current_operator(
    db: AsyncSession = Depends(get_db),
    admin_id: int = Depends(get_current_admin_id),
) -> Admin:
    """获取当前运营人员或以上权限管理员"""
    admin = await crud_admin.get_active_admin(db, admin_id)
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="管理员不存在或已被禁用",
        )
    if admin.role not in [0, 1, 2]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权限访问",
        )
    return admin