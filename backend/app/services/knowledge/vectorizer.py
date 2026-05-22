# backend/app/services/knowledge/vectorizer.py
import httpx
import logging
import uuid
from typing import List, Optional
from app.config import settings
from qdrant_client.models import PointStruct, VectorParams, Distance

logger = logging.getLogger(__name__)

COLLECTION_NAME = "knowledge_items"
VECTOR_SIZE = 512


def _get_qdrant():
    """获取qdrant客户端"""
    from app.core.qdrant import qdrant_client
    if qdrant_client is None:
        raise RuntimeError("Qdrant客户端未初始化")
    return qdrant_client


# ==================== Encoder调用 ====================

async def get_embeddings(texts: List[str]) -> List[List[float]]:
    """调用Encoder服务批量向量化"""
    if not texts:
        return []

    encoder_url = (
        f"http://{settings.EMBEDDING_HOST}"
        f":{settings.EMBEDDING_PORT}/encode"
    )

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            encoder_url,
            json={"texts": texts, "batch_size": 32},
        )
        response.raise_for_status()
        data = response.json()
        return data["embeddings"]


async def get_single_embedding(text: str) -> List[float]:
    """单条文本向量化"""
    embeddings = await get_embeddings([text])
    return embeddings[0]


# ==================== Qdrant集合管理 ====================

async def ensure_collection_exists():
    """确保Qdrant集合存在"""
    client = _get_qdrant()
    collections = await client.get_collections()
    collection_names = [c.name for c in collections.collections]

    if COLLECTION_NAME not in collection_names:
        logger.info(f"创建Qdrant集合: {COLLECTION_NAME}")
        await client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(
                size=VECTOR_SIZE,
                distance=Distance.COSINE,
            ),
        )
        logger.info(f"Qdrant集合创建成功: {COLLECTION_NAME}")


# ==================== 向量存储 ====================

async def upsert_item_vectors(
    item_id: int,
    kb_id: int,
    title: str,
    similar_questions: Optional[List[str]] = None,
) -> List[str]:
    """将知识条目向量化并存入Qdrant"""
    await ensure_collection_exists()

    texts = [title]
    question_types = ["title"]

    if similar_questions:
        for q in similar_questions:
            if q.strip():
                texts.append(q.strip())
                question_types.append("similar")

    embeddings = await get_embeddings(texts)

    points = []
    point_ids = []
    for text, embedding, q_type in zip(texts, embeddings, question_types):
        point_id = str(uuid.uuid4())
        point_ids.append(point_id)
        points.append(PointStruct(
            id=point_id,
            vector=embedding,
            payload={
                "item_id": item_id,
                "kb_id": kb_id,
                "question": text,
                "is_title": q_type == "title",
            },
        ))

    client = _get_qdrant()
    await client.upsert(
        collection_name=COLLECTION_NAME,
        points=points,
    )

    logger.info(f"向量存储成功 item_id={item_id}，存入{len(points)}个向量")
    return point_ids


async def delete_item_vectors(item_id: int):
    """删除知识条目的所有向量"""
    from qdrant_client.models import Filter, FieldCondition, MatchValue

    client = _get_qdrant()
    await client.delete(
        collection_name=COLLECTION_NAME,
        points_selector=Filter(
            must=[
                FieldCondition(
                    key="item_id",
                    match=MatchValue(value=item_id),
                )
            ]
        ),
    )
    logger.info(f"删除向量成功 item_id={item_id}")


# ==================== 向量检索 ====================

async def search_similar(
    query: str,
    kb_id: int,
    top_k: int = 5,
    score_threshold: float = 0.0,
) -> List[dict]:
    """向量相似度检索"""
    from qdrant_client.models import Filter, FieldCondition, MatchValue

    query_vector = await get_single_embedding(query)
    client = _get_qdrant()

    # ✅ 兼容新旧版本qdrant-client
    hits_raw = []
    try:
        # 新版本 >= 1.7.0 用 query_points
        results = await client.query_points(
            collection_name=COLLECTION_NAME,
            query=query_vector,
            query_filter=Filter(
                must=[
                    FieldCondition(
                        key="kb_id",
                        match=MatchValue(value=kb_id),
                    )
                ]
            ),
            limit=top_k,
            score_threshold=score_threshold,
            with_payload=True,
        )
        hits_raw = results.points

    except AttributeError:
        # 旧版本用 search
        hits_raw = await client.search(
            collection_name=COLLECTION_NAME,
            query_vector=query_vector,
            query_filter=Filter(
                must=[
                    FieldCondition(
                        key="kb_id",
                        match=MatchValue(value=kb_id),
                    )
                ]
            ),
            limit=top_k,
            score_threshold=score_threshold,
            with_payload=True,
        )

    hits = []
    for hit in hits_raw:
        hits.append({
            "item_id": hit.payload["item_id"],
            "question": hit.payload["question"],
            "is_title": hit.payload.get("is_title", True),
            "vector_score": hit.score,
        })

    logger.info(
        f"向量检索完成 query='{query}' "
        f"kb_id={kb_id} hits={len(hits)}"
    )
    return hits


# ==================== 批量向量化 ====================

async def batch_upsert_vectors(
    items: List[dict],
    batch_size: int = 50,
) -> int:
    """批量向量化（Excel导入时使用）"""
    await ensure_collection_exists()
    total_vectors = 0

    for batch_start in range(0, len(items), batch_size):
        batch = items[batch_start: batch_start + batch_size]
        all_texts = []
        meta_list = []

        for item in batch:
            item_id = item["item_id"]
            kb_id = item["kb_id"]
            title = item["title"]
            similars = item.get("similar_questions", [])

            all_texts.append(title)
            meta_list.append({
                "item_id": item_id, "kb_id": kb_id,
                "question": title, "is_title": True,
            })

            for q in similars:
                if q.strip():
                    all_texts.append(q.strip())
                    meta_list.append({
                        "item_id": item_id, "kb_id": kb_id,
                        "question": q.strip(), "is_title": False,
                    })

        if not all_texts:
            continue

        embeddings = await get_embeddings(all_texts)
        points = []
        for meta, embedding in zip(meta_list, embeddings):
            points.append(PointStruct(
                id=str(uuid.uuid4()),
                vector=embedding,
                payload=meta,
            ))

        client = _get_qdrant()
        await client.upsert(
            collection_name=COLLECTION_NAME,
            points=points,
        )
        total_vectors += len(points)
        logger.info(
            f"批量向量化进度: {batch_start + len(batch)}/{len(items)}，"
            f"已存入{total_vectors}个向量"
        )

    return total_vectors