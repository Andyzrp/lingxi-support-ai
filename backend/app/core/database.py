from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config import settings

DATABASE_URL = settings.DATABASE_URL
if "+asyncpg" in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
elif "+aiopostgresql" in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.replace("postgresql+aiopostgresql://", "postgresql://")

sync_engine = create_engine(
    DATABASE_URL,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,
)

SyncSessionLocal = sessionmaker(
    bind=sync_engine,
    autocommit=False,
    autoflush=False,
)


# 创建异步引擎
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,  # 关闭SQL日志打印
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
)

# 创建异步Session工厂
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# 基础模型类
class Base(DeclarativeBase):
    pass


# 获取数据库Session（依赖注入用）
async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# 测试数据库连接
async def check_db_connection():
    try:
        async with engine.connect() as conn:
            await conn.execute(__import__("sqlalchemy").text("SELECT 1"))
        print("✅ PostgreSQL连接成功")
        return True
    except Exception as e:
        print(f"❌ PostgreSQL连接失败: {e}")
        return False
