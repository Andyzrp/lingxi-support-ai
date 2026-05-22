from pydantic import BaseModel, field_validator
from datetime import datetime


# ==================== 请求模型 ====================


class UserRegister(BaseModel):
    """用户注册"""

    username: str
    password: str
    nickname: str | None = None

    @field_validator("username")
    @classmethod
    def username_validator(cls, v: str) -> str:
        if len(v) < 3:
            raise ValueError("用户名不能少于3个字符")
        if len(v) > 50:
            raise ValueError("用户名不能超过50个字符")
        return v

    @field_validator("password")
    @classmethod
    def password_validator(cls, v: str) -> str:
        if len(v) < 6:
            raise ValueError("密码不能少于6个字符")
        if len(v) > 50:
            raise ValueError("密码不能超过50个字符")
        return v


class UserLogin(BaseModel):
    """用户登录"""

    username: str
    password: str


class UserUpdate(BaseModel):
    """用户信息更新"""

    nickname: str | None = None
    avatar: str | None = None
    phone: str | None = None


class UserPasswordUpdate(BaseModel):
    """用户密码更新"""

    old_password: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def new_password_validator(cls, v: str) -> str:
        if len(v) < 6:
            raise ValueError("新密码不能少于6个字符")
        if len(v) > 50:
            raise ValueError("新密码不能超过50个字符")
        return v


# ==================== 响应模型 ====================


class UserInfo(BaseModel):
    """用户信息响应"""

    id: int
    username: str
    nickname: str | None = None
    avatar: str | None = None
    phone: str | None = None
    status: int
    created_at: datetime

    class Config:
        from_attributes = True


class UserLoginResponse(BaseModel):
    """登录响应"""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = 7200
    user_info: UserInfo
