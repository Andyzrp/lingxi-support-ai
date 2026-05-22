# backend/reindex.py
import asyncio
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def reindex_all():
    # ✅ 第一步：初始化Qdrant客户端
    from app.core.qdrant import init_qdrant
    await init_qdrant()
    logger.info("Qdrant客户端初始化完成")

    from app.core.database import AsyncSessionLocal
    from app.services.knowledge.vectorizer import upsert_item_vectors
    from app.models.knowledge import KnowledgeItem
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(KnowledgeItem)
            .options(selectinload(KnowledgeItem.similar_questions))
            .where(KnowledgeItem.status == 1)
        )
        items = result.scalars().all()
        print(f"共 {len(items)} 条需要向量化")

        success = 0
        failed = 0

        for item in items:
            similars = [sq.question for sq in item.similar_questions]
            print(f"处理 item_id={item.id} title={item.title}")
            print(f"  similars={similars}")

            try:
                await upsert_item_vectors(
                    item_id=item.id,
                    kb_id=item.knowledge_base_id,
                    title=item.title,
                    similar_questions=similars,
                )
                print(f"  ✅ 成功")
                success += 1
            except Exception as e:
                import traceback
                print(f"  ❌ 失败: {e}")
                traceback.print_exc()
                failed += 1

        print(f"\n完成！成功={success} 失败={failed}")

    # ✅ 关闭Qdrant客户端
    from app.core.qdrant import close_qdrant
    await close_qdrant()


if __name__ == "__main__":
    asyncio.run(reindex_all())