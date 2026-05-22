import redis.asyncio as aioredis
from app.config import settings

# 创建Redis连接池（字符串模式）
redis_client: aioredis.Redis = None

# 二进制模式连接池（用于存储bytes如Excel文件）
redis_binary_client: aioredis.Redis = None


async def init_redis() -> aioredis.Redis:
    global redis_client, redis_binary_client

    # 字符串模式（decode_responses=True）
    redis_client = aioredis.from_url(
        settings.REDIS_URL,
        encoding="utf-8",
        decode_responses=True,
        max_connections=20,
    )

    # 二进制模式（不decode，用于Excel等bytes存储）
    redis_binary_client = aioredis.from_url(
        settings.REDIS_URL,
        decode_responses=False,
        max_connections=10,
    )

    return redis_client


async def get_redis() -> aioredis.Redis:
    return redis_client


async def get_redis_binary() -> aioredis.Redis:
    """获取二进制模式的Redis客户端（用于bytes存储）"""
    global redis_binary_client
    if redis_binary_client is None:
        redis_binary_client = aioredis.from_url(
            settings.REDIS_URL,
            decode_responses=False,
            max_connections=10,
        )
    return redis_binary_client


async def close_redis():
    global redis_client, redis_binary_client
    if redis_client:
        await redis_client.close()
    if redis_binary_client:
        await redis_binary_client.close()


# 测试Redis连接
async def check_redis_connection():
    try:
        client = aioredis.from_url(settings.REDIS_URL)
        await client.ping()
        await client.close()
        print("✅ Redis连接成功")
        return True
    except Exception as e:
        print(f"❌ Redis连接失败: {e}")
        return False


# 会话相关操作
class SessionCache:
    """会话上下文缓存"""

    PREFIX = "session:"

    @staticmethod
    async def get(conversation_id: str) -> str:
        key = f"{SessionCache.PREFIX}{conversation_id}"
        return await redis_client.get(key)

    @staticmethod
    async def set(conversation_id: str, data: str, expire: int = 3600):
        key = f"{SessionCache.PREFIX}{conversation_id}"
        await redis_client.setex(key, expire, data)

    @staticmethod
    async def delete(conversation_id: str):
        key = f"{SessionCache.PREFIX}{conversation_id}"
        await redis_client.delete(key)

    @staticmethod
    async def exists(conversation_id: str) -> bool:
        key = f"{SessionCache.PREFIX}{conversation_id}"
        return await redis_client.exists(key) > 0

    @staticmethod
    async def expire(conversation_id: str, seconds: int):
        key = f"{SessionCache.PREFIX}{conversation_id}"
        await redis_client.expire(key, seconds)
