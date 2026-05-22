from pydantic import BaseModel, field_validator
from datetime import datetime


# ==================== 请求模型 ====================


class AdminLogin(BaseModel):
    """管理员登录"""

    username: str
    password: str


class AdminCreate(BaseModel):
    """创建管理员"""

    username: str
    password: str
    nickname: str | None = None
    role: int = 1

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

    @field_validator("role")
    @classmethod
    def role_validator(cls, v: int) -> int:
        if v not in [0, 1, 2]:
            raise ValueError("角色值无效，0超级管理员/1普通管理员/2运营人员")
        return v


class AdminUpdate(BaseModel):
    """更新管理员信息"""

    nickname: str | None = None
    role: int | None = None
    status: int | None = None

    @field_validator("role")
    @classmethod
    def role_validator(cls, v: int | None) -> int | None:
        if v is not None and v not in [0, 1, 2]:
            raise ValueError("角色值无效，0超级管理员/1普通管理员/2运营人员")
        return v

    @field_validator("status")
    @classmethod
    def status_validator(cls, v: int | None) -> int | None:
        if v is not None and v not in [0, 1]:
            raise ValueError("状态值无效，0禁用/1正常")
        return v


class AdminPasswordUpdate(BaseModel):
    """管理员密码更新"""

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


class AdminInfo(BaseModel):
    """管理员信息响应"""

    id: int
    username: str
    nickname: str | None = None
    role: int
    status: int
    last_login_at: datetime | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class AdminLoginResponse(BaseModel):
    """管理员登录响应"""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = 7200
    admin_info: AdminInfo
