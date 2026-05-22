from typing import Any
from app.utils.response import Response


def success_response(data: Any = None, message: str = "success"):
    """统一成功响应"""
    return Response.success(data=data, message=message)


def fail_response(code: int = 400, message: str = "fail", data: Any = None):
    """统一失败响应"""
    return Response.fail(code=code, message=message, data=data)
