from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from contextlib import asynccontextmanager

from app.config import settings
from app.core.database import check_db_connection
from app.core.redis import init_redis, close_redis, check_redis_connection
from app.core.qdrant import (
    init_qdrant,
    close_qdrant,
    check_qdrant_connection,
    init_knowledge_collection,
)
from app.core.exceptions import register_exception_handlers
from app.api.v1 import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """启动和关闭事件"""
    print("[Lingxi] 灵犀智能客服系统启动中...")

    # 检查数据库连接
    await check_db_connection()

    # 初始化Redis
    await init_redis()
    await check_redis_connection()

    # 初始化Qdrant
    await init_qdrant()
    await check_qdrant_connection()
    await init_knowledge_collection()

    print("[Lingxi] 所有服务初始化完成！")

    yield

    # 关闭连接
    print("[Lingxi] 系统关闭中...")
    await close_redis()
    await close_qdrant()
    print("[Lingxi] 所有连接已关闭")


# 创建FastAPI实例
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    debug=settings.DEBUG,
    lifespan=lifespan,
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition", "Content-Type"],
)

# 注册全局异常处理器
register_exception_handlers(app)

# 注册路由
app.include_router(api_router)

# 静态托管上传文件（商品图片等）
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")


# 根路由
@app.get("/")
async def root():
    return {
        "name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "running",
    }


# 健康检查
@app.get("/health")
async def health():
    return {
        "status": "ok",
        "version": settings.VERSION,
    }
