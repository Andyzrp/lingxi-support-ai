# backend/app/api/v1/__init__.py
from fastapi import APIRouter

api_router = APIRouter(prefix="/api/v1")

from app.api.v1.auth import router as auth_router

api_router.include_router(auth_router, prefix="/auth", tags=["用户认证"])

from app.api.v1.admin_auth import router as admin_auth_router

api_router.include_router(admin_auth_router, prefix="/admin/auth", tags=["管理员认证"])

from app.api.v1.products import router as products_router

api_router.include_router(products_router, prefix="/products", tags=["商品管理"])

from app.api.v1.orders import router as orders_router

api_router.include_router(orders_router, prefix="/orders", tags=["订单管理"])

from app.api.v1.knowledge import router as knowledge_router

api_router.include_router(knowledge_router, prefix="/knowledge", tags=["知识库管理"])

from app.api.v1.bots import router as bots_router

api_router.include_router(bots_router, prefix="/bots", tags=["Bot管理"])

from app.api.v1.agents import router as agents_router

api_router.include_router(agents_router, prefix="/agents", tags=["Agent管理"])

from app.api.v1.channels import router as channels_router

api_router.include_router(channels_router, prefix="/channels", tags=["渠道管理"])

from app.api.v1.reports import router as reports_router

api_router.include_router(reports_router, prefix="/reports", tags=["数据报表"])

from app.api.v1.chat import router as chat_router

api_router.include_router(chat_router, prefix="/chat", tags=["对话接口"])

from app.api.v1.annotations import router as annotations_router

api_router.include_router(annotations_router, prefix="/annotations", tags=["数据标注"])
