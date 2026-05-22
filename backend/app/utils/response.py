from typing import Any, Generic, TypeVar
from pydantic import BaseModel

T = TypeVar("T")


class Response(BaseModel, Generic[T]):
    """统一响应格式"""
    code: int = 200
    message: str = "success"
    data: T | None = None

    @classmethod
    def success(cls, data: Any = None, message: str = "success"):
        return cls(code=200, message=message, data=data)

    @classmethod
    def fail(cls, code: int = 400, message: str = "fail", data: Any = None):
        return cls(code=code, message=message, data=data)


class PageInfo(BaseModel):
    """分页信息"""
    total: int
    page: int
    page_size: int
    total_pages: int


class PageResponse(BaseModel, Generic[T]):
    """分页响应格式"""
    code: int = 200
    message: str = "success"
    data: list[T] | None = None
    page_info: PageInfo | None = None

    @classmethod
    def success(
        cls,
        data: list[Any],
        total: int,
        page: int,
        page_size: int,
    ):
        import math
        total_pages = math.ceil(total / page_size) if page_size > 0 else 0
        return cls(
            code=200,
            message="success",
            data=data,
            page_info=PageInfo(
                total=total,
                page=page,
                page_size=page_size,
                total_pages=total_pages,
            ),
        )