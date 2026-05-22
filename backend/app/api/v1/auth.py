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
from app.core.exceptions import ConflictException, UnauthorizedException
from app.crud.user import crud_user
from app.schemas.user import (
    UserRegister,
    UserLogin,
    UserUpdate,
    UserPasswordUpdate,
    UserInfo,
    UserLoginResponse,
)
from app.utils.response import Response
from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter()


@router.post("/register", response_model=Response[UserInfo], summary="用户注册")
async def register(
    data: UserRegister,
    db: AsyncSession = Depends(get_db),
):
    """用户注册"""
    # 检查用户名是否已存在
    if await crud_user.username_exists(db, data.username):
        raise ConflictException("用户名已存在")

    # 创建用户
    user = await crud_user.create_user(
        db=db,
        username=data.username,
        password=data.password,
        nickname=data.nickname,
    )
    return Response.success(
        data=UserInfo.model_validate(user),
        message="注册成功",
    )


@router.post("/login", response_model=Response[UserLoginResponse], summary="用户登录")
async def login(
    data: UserLogin,
    db: AsyncSession = Depends(get_db),
):
    """用户登录"""
    user = await crud_user.authenticate(
        db=db,
        username=data.username,
        password=data.password,
    )
    if not user:
        raise UnauthorizedException("用户名或密码错误")

    if user.status == 0:
        raise UnauthorizedException("账号已被禁用")

    access_token = create_access_token(subject=user.id, role="user")
    refresh_token = create_refresh_token(subject=user.id, role="user")
    store_refresh_token(user_id=user.id, role="user", token=refresh_token)

    return Response.success(
        data=UserLoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            user_info=UserInfo.model_validate(user),
        ),
        message="登录成功",
    )


@router.get("/me", response_model=Response[UserInfo], summary="获取当前用户信息")
async def get_me(
    current_user: User = Depends(get_current_user),
):
    """获取当前登录用户信息"""
    return Response.success(
        data=UserInfo.model_validate(current_user),
    )


@router.put("/me", response_model=Response[UserInfo], summary="更新用户信息")
async def update_me(
    data: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """更新当前用户信息"""
    user = await crud_user.update_user(
        db=db,
        user=current_user,
        nickname=data.nickname,
        avatar=data.avatar,
        phone=data.phone,
    )
    return Response.success(
        data=UserInfo.model_validate(user),
        message="更新成功",
    )


@router.put("/me/password", response_model=Response, summary="修改密码")
async def update_password(
    data: UserPasswordUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """修改当前用户密码"""
    from app.core.security import verify_password

    if not verify_password(data.old_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="原密码错误",
        )
    await crud_user.update_password(
        db=db,
        user=current_user,
        new_password=data.new_password,
    )
    return Response.success(message="密码修改成功")


# ==================== Token 刷新 ====================


class RefreshTokenRequest(BaseModel):
    refresh_token: str


@router.post("/refresh", summary="刷新 Access Token")
async def refresh_token(
    body: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    用 Refresh Token 换新的 Access Token
    不需要携带 Authorization Header
    """
    try:
        payload = verify_refresh_token(body.refresh_token)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))

    user_id = int(payload["sub"])

    stored = get_stored_refresh_token(user_id=user_id, role="user")
    if stored != body.refresh_token:
        raise HTTPException(
            status_code=401,
            detail="Token 已失效，请重新登录",
        )

    user = await crud_user.get(db, user_id)
    if not user or user.status != 1:
        raise HTTPException(
            status_code=401,
            detail="账号已停用，请联系管理员",
        )

    new_access_token = create_access_token(subject=user.id)

    return Response.success(
        data={
            "access_token": new_access_token,
            "token_type": "bearer",
            "expires_in": 7200,
        },
    )


@router.post("/logout", summary="退出登录")
async def logout(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """退出登录，删除 Redis 中的 Refresh Token"""
    delete_refresh_token(user_id=current_user.id, role="user")
    return Response.success(message="已退出登录")
