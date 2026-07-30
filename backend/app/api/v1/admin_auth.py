from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.security import (
    create_access_token,
    create_refresh_token,
    verify_refresh_token,
    store_refresh_token,
    get_stored_refresh_token,
    delete_refresh_token,
)
from app.core.exceptions import (
    ConflictException,
    UnauthorizedException,
    ForbiddenException,
)
from app.crud.admin import crud_admin
from app.schemas.admin import (
    AdminLogin,
    AdminCreate,
    AdminUpdate,
    AdminPasswordUpdate,
    AdminInfo,
    AdminLoginResponse,
)
from app.utils.response import Response, PageResponse
from app.utils.pagination import get_page_params, PageParams
from app.api.deps import get_current_admin, get_current_super_admin
from app.models.admin import Admin

router = APIRouter()


@router.post(
    "/login", response_model=Response[AdminLoginResponse], summary="管理员登录"
)
async def admin_login(
    data: AdminLogin,
    db: AsyncSession = Depends(get_db),
):
    """管理员登录"""
    admin = await crud_admin.authenticate(
        db=db,
        username=data.username,
        password=data.password,
    )
    if not admin:
        raise UnauthorizedException("用户名或密码错误")

    if admin.status == 0:
        raise UnauthorizedException("账号已被禁用")

    await crud_admin.update_last_login(db=db, admin=admin)

    role_map = {0: "super_admin", 1: "admin", 2: "operator"}
    role = role_map.get(admin.role, "admin")

    access_token = create_access_token(subject=admin.id, role=role)
    refresh_token = create_refresh_token(subject=admin.id, role=role)
    await store_refresh_token(user_id=admin.id, role=role, token=refresh_token)

    return Response.success(
        data=AdminLoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            admin_info=AdminInfo.model_validate(admin),
        ),
        message="登录成功",
    )


@router.get("/me", response_model=Response[AdminInfo], summary="获取当前管理员信息")
async def get_me(
    current_admin: Admin = Depends(get_current_admin),
):
    """获取当前登录管理员信息"""
    return Response.success(
        data=AdminInfo.model_validate(current_admin),
    )


@router.put("/me", response_model=Response[AdminInfo], summary="更新管理员信息")
async def update_me(
    data: AdminUpdate,
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin),
):
    """更新当前管理员信息"""
    admin = await crud_admin.update_admin(
        db=db,
        admin=current_admin,
        nickname=data.nickname,
    )
    return Response.success(
        data=AdminInfo.model_validate(admin),
        message="更新成功",
    )


@router.put("/me/password", response_model=Response, summary="修改密码")
async def update_password(
    data: AdminPasswordUpdate,
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin),
):
    """修改当前管理员密码"""
    from app.core.security import verify_password

    if not verify_password(data.old_password, current_admin.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="原密码错误",
        )
    await crud_admin.update_password(
        db=db,
        admin=current_admin,
        new_password=data.new_password,
    )
    return Response.success(message="密码修改成功")


@router.post("/admins", response_model=Response[AdminInfo], summary="创建管理员")
async def create_admin(
    data: AdminCreate,
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(get_current_super_admin),
):
    """创建管理员（仅超级管理员）"""
    if await crud_admin.username_exists(db, data.username):
        raise ConflictException("用户名已存在")

    admin = await crud_admin.create_admin(
        db=db,
        username=data.username,
        password=data.password,
        nickname=data.nickname,
        role=data.role,
    )
    return Response.success(
        data=AdminInfo.model_validate(admin),
        message="创建成功",
    )


@router.get("/admins", response_model=PageResponse[AdminInfo], summary="获取管理员列表")
async def get_admins(
    db: AsyncSession = Depends(get_db),
    page_params: PageParams = Depends(get_page_params),
    current_admin: Admin = Depends(get_current_super_admin),
):
    """获取管理员列表（仅超级管理员）"""
    admins = await crud_admin.get_multi(
        db=db,
        offset=page_params.offset,
        limit=page_params.limit,
    )
    total = await crud_admin.count(db=db)
    return PageResponse.success(
        data=[AdminInfo.model_validate(a) for a in admins],
        total=total,
        page=page_params.page,
        page_size=page_params.page_size,
    )


@router.put(
    "/admins/{admin_id}", response_model=Response[AdminInfo], summary="更新管理员"
)
async def update_admin(
    admin_id: int,
    data: AdminUpdate,
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(get_current_super_admin),
):
    """更新管理员信息（仅超级管理员）"""
    admin = await crud_admin.get(db, admin_id)
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="管理员不存在",
        )
    admin = await crud_admin.update_admin(
        db=db,
        admin=admin,
        nickname=data.nickname,
        role=data.role,
        status=data.status,
    )
    return Response.success(
        data=AdminInfo.model_validate(admin),
        message="更新成功",
    )


@router.delete("/admins/{admin_id}", response_model=Response, summary="删除管理员")
async def delete_admin(
    admin_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(get_current_super_admin),
):
    """删除管理员（仅超级管理员）"""
    if admin_id == current_admin.id:
        raise ForbiddenException("不能删除自己的账号")
    success = await crud_admin.delete(db, admin_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="管理员不存在",
        )
    return Response.success(message="删除成功")


# ==================== Token 刷新 ====================


class RefreshTokenRequest(BaseModel):
    refresh_token: str


@router.post("/refresh", summary="管理员刷新 Access Token")
async def admin_refresh_token(
    body: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    管理员用 Refresh Token 换新的 Access Token
    不需要携带 Authorization Header
    """
    try:
        payload = verify_refresh_token(body.refresh_token)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))

    if payload.get("role") not in ("admin", "super_admin", "operator"):
        raise HTTPException(status_code=401, detail="Token 类型错误")

    admin_id = int(payload["sub"])

    stored = await get_stored_refresh_token(user_id=admin_id, role=payload["role"])
    if stored != body.refresh_token:
        raise HTTPException(
            status_code=401,
            detail="Token 已失效，请重新登录",
        )

    admin = await crud_admin.get(db, admin_id)
    if not admin or admin.status != 1:
        raise HTTPException(
            status_code=401,
            detail="账号已停用，请联系超级管理员",
        )

    role_map = {0: "super_admin", 1: "admin", 2: "operator"}
    role = role_map.get(admin.role, "admin")
    new_access_token = create_access_token(subject=admin.id, role=role)

    return Response.success(
        data={
            "access_token": new_access_token,
            "token_type": "bearer",
            "expires_in": 7200,
        },
    )


@router.post("/logout", summary="管理员退出登录")
async def admin_logout(
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin),
):
    """退出登录，删除 Redis 中的 Refresh Token"""
    role_map = {0: "super_admin", 1: "admin", 2: "operator"}
    role = role_map.get(current_admin.role, "admin")
    await delete_refresh_token(user_id=current_admin.id, role=role)
    return Response.success(message="已退出登录")
