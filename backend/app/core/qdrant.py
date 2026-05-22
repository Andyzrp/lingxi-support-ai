from qdrant_client import AsyncQdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
)
from app.config import settings

# 全局Qdrant客户端
qdrant_client: AsyncQdrantClient = None

# 知识库集合名称
KNOWLEDGE_COLLECTION = "knowledge_items"

# 向量维度（bge-small-zh输出512维）
VECTOR_SIZE = 512


async def init_qdrant() -> AsyncQdrantClient:
    global qdrant_client
    qdrant_client = AsyncQdrantClient(
        host=settings.QDRANT_HOST,
        port=settings.QDRANT_PORT,
    )
    return qdrant_client


async def get_qdrant() -> AsyncQdrantClient:
    return qdrant_client


async def close_qdrant():
    global qdrant_client
    if qdrant_client:
        await qdrant_client.close()


# 测试Qdrant连接
async def check_qdrant_connection():
    try:
        client = AsyncQdrantClient(
            host=settings.QDRANT_HOST,
            port=settings.QDRANT_PORT,
        )
        await client.get_collections()
        await client.close()
        print("✅ Qdrant连接成功")
        return True
    except Exception as e:
        print(f"❌ Qdrant连接失败: {e}")
        return False


# 初始化知识库集合
async def init_knowledge_collection():
    try:
        collections = await qdrant_client.get_collections()
        collection_names = [c.name for c in collections.collections]

        if KNOWLEDGE_COLLECTION not in collection_names:
            await qdrant_client.create_collection(
                collection_name=KNOWLEDGE_COLLECTION,
                vectors_config=VectorParams(
                    size=VECTOR_SIZE,
                    distance=Distance.COSINE,
                ),
            )
            print(f"✅ Qdrant集合 {KNOWLEDGE_COLLECTION} 创建成功")
        else:
            print(f"✅ Qdrant集合 {KNOWLEDGE_COLLECTION} 已存在")
    except Exception as e:
        print(f"❌ Qdrant集合初始化失败: {e}")
        raise


# 向量搜索
async def search_vectors(
    query_vector: list[float],
    knowledge_base_id: int,
    limit: int = 5,
    score_threshold: float = 0.85,
) -> list[dict]:
    try:
        results = await qdrant_client.search(
            collection_name=KNOWLEDGE_COLLECTION,
            query_vector=query_vector,
            query_filter=Filter(
                must=[
                    FieldCondition(
                        key="knowledge_base_id",
                        match=MatchValue(value=knowledge_base_id),
                    )
                ]
            ),
            limit=limit,
            score_threshold=score_threshold,
        )
        return [
            {
                "id": hit.id,
                "score": hit.score,
                "payload": hit.payload,
            }
            for hit in results
        ]
    except Exception as e:
        print(f"❌ 向量搜索失败: {e}")
        return []


# 插入向量
async def upsert_vectors(points: list[dict]):
    try:
        await qdrant_client.upsert(
            collection_name=KNOWLEDGE_COLLECTION,
            points=[
                PointStruct(
                    id=p["id"],
                    vector=p["vector"],
                    payload=p["payload"],
                )
                for p in points
            ],
        )
        return True
    except Exception as e:
        print(f"❌ 向量插入失败: {e}")
        return False


# 删除向量
async def delete_vectors(vector_ids: list[str]):
    try:
        await qdrant_client.delete(
            collection_name=KNOWLEDGE_COLLECTION,
            points_selector=vector_ids,
        )
        return True
    except Exception as e:
        print(f"❌ 向量删除失败: {e}")
        return False