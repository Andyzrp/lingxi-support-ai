from datetime import datetime, timedelta
from typing import Any
from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from app.config import settings
import hashlib

# 密码加密上下文（使用sha256_crypt避免bcrypt的72字节限制）
pwd_context = CryptContext(schemes=["sha256_crypt"], deprecated="auto")

# OAuth2 Token获取
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")
oauth2_scheme_admin = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/admin/auth/login"
)

# JWT配置
ALGORITHM = "HS256"


# ==================== 密码相关 ====================


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """生成密码哈希"""
    return pwd_context.hash(password)


# ==================== Token相关 ====================


def create_access_token(
    subject: Any,
    role: str = "user",
    expires_delta: timedelta | None = None,
) -> str:
    """生成JWT Token"""
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    payload = {
        "sub": str(subject),
        "role": role,
        "exp": expire,
        "iat": datetime.utcnow(),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    """解析JWT Token"""
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[ALGORITHM],
        )
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token无效或已过期",
            headers={"WWW-Authenticate": "Bearer"},
        )


# ==================== 依赖注入 ====================


async def get_current_user_id(token: str = Depends(oauth2_scheme)) -> int:
    """获取当前登录用户ID"""
    payload = decode_token(token)
    user_id = payload.get("sub")
    role = payload.get("role")
    if not user_id or role != "user":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token无效",
        )
    return int(user_id)


async def get_current_admin_id(token: str = Depends(oauth2_scheme_admin)) -> int:
    """获取当前登录管理员ID"""
    payload = decode_token(token)
    admin_id = payload.get("sub")
    role = payload.get("role")
    if not admin_id or role not in ["admin", "super_admin", "operator"]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无权限访问",
        )
    return int(admin_id)


async def get_current_super_admin_id(token: str = Depends(oauth2_scheme_admin)) -> int:
    """获取当前超级管理员ID"""
    payload = decode_token(token)
    admin_id = payload.get("sub")
    role = payload.get("role")
    if not admin_id or role != "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要超级管理员权限",
        )
    return int(admin_id)


# ==================== Refresh Token ====================


def create_refresh_token(subject: int, role: str = "user") -> str:
    """
    生成 Refresh Token
    有效期：7天
    payload 中 type='refresh' 用于区分 access/refresh
    """
    expire = datetime.utcnow() + timedelta(days=7)
    payload = {
        "sub": str(subject),
        "role": role,
        "type": "refresh",
        "exp": expire,
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)


def verify_refresh_token(token: str) -> dict:
    """
    验证 Refresh Token
    失败时抛出 ValueError
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[ALGORITHM],
        )
    except jwt.ExpiredSignatureError:
        raise ValueError("Refresh Token 已过期，请重新登录")
    except jwt.JWTError:
        raise ValueError("Refresh Token 无效")

    if payload.get("type") != "refresh":
        raise ValueError("不是有效的 Refresh Token")

    return payload


# ==================== Redis Token 存储 ====================


def _get_redis():
    import redis

    return redis.Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        db=3,
        password=settings.REDIS_PASSWORD or None,
        decode_responses=True,
    )


def store_refresh_token(user_id: int, role: str, token: str) -> None:
    """
    登录成功后将 Refresh Token 存入 Redis
    key 格式：refresh_token:{role}:{user_id}
    有效期：7天
    """
    r = _get_redis()
    key = f"refresh_token:{role}:{user_id}"
    r.setex(key, 604800, token)


def get_stored_refresh_token(user_id: int, role: str) -> str | None:
    """从 Redis 读取已存储的 Refresh Token"""
    r = _get_redis()
    key = f"refresh_token:{role}:{user_id}"
    return r.get(key)


def delete_refresh_token(user_id: int, role: str) -> None:
    """退出登录时删除 Refresh Token（主动失效）"""
    r = _get_redis()
    key = f"refresh_token:{role}:{user_id}"
    r.delete(key)
