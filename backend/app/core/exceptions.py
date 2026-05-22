from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError


# ==================== 自定义异常 ====================


class AppException(Exception):
    """基础业务异常"""

    def __init__(self, code: int = 400, message: str = "业务异常"):
        self.code = code
        self.message = message
        super().__init__(message)


class NotFoundException(AppException):
    """资源不存在"""

    def __init__(self, message: str = "资源不存在"):
        super().__init__(code=404, message=message)


class UnauthorizedException(AppException):
    """未授权"""

    def __init__(self, message: str = "未授权访问"):
        super().__init__(code=401, message=message)


class ForbiddenException(AppException):
    """禁止访问"""

    def __init__(self, message: str = "禁止访问"):
        super().__init__(code=403, message=message)


class BadRequestException(AppException):
    """请求参数错误"""

    def __init__(self, message: str = "请求参数错误"):
        super().__init__(code=400, message=message)


class ConflictException(AppException):
    """资源冲突"""

    def __init__(self, message: str = "资源已存在"):
        super().__init__(code=409, message=message)


# ==================== 异常处理器 ====================


def register_exception_handlers(app: FastAPI):
    """注册全局异常处理器"""

    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException):
        """处理业务异常"""
        return JSONResponse(
            status_code=exc.code,
            content={
                "code": exc.code,
                "message": exc.message,
                "data": None,
            },
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ):
        """处理请求参数验证异常"""
        errors = exc.errors()
        message = errors[0].get("msg") if errors else "参数验证失败"
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "code": 422,
                "message": f"参数验证失败: {message}",
                "data": None,
            },
        )

    @app.exception_handler(SQLAlchemyError)
    async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
        """处理数据库异常"""
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "code": 500,
                "message": f"数据库操作失败: {str(exc)[:100]}",
                "data": None,
            },
        )

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        """处理未知异常"""
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "code": 500,
                "message": f"服务器内部错误: {str(exc)}",
                "data": None,
            },
        )
