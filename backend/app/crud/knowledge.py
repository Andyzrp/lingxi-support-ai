# backend/app/crud/knowledge.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func, and_
from sqlalchemy.orm import selectinload
from typing import Optional, List, Tuple
from app.models.knowledge import KnowledgeBase, KnowledgeItem, KnowledgeSimilarQuestion
from app.schemas.knowledge import (
    KnowledgeBaseCreate,
    KnowledgeBaseUpdate,
    KnowledgeItemCreate,
    KnowledgeItemUpdate,
    KnowledgeItemQuery,
)


class CRUDKnowledgeBase:
    async def create(
        self,
        db: AsyncSession,
        obj_in: KnowledgeBaseCreate,
    ) -> KnowledgeBase:
        db_obj = KnowledgeBase(
            name=obj_in.name,
            description=obj_in.description,
            # ✅ 不传status（模型没有），不传item_count（默认0）
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def get(
        self,
        db: AsyncSession,
        kb_id: int,
    ) -> Optional[KnowledgeBase]:
        result = await db.execute(
            select(KnowledgeBase).where(KnowledgeBase.id == kb_id)
        )
        return result.scalar_one_or_none()

    async def get_list(
        self,
        db: AsyncSession,
    ) -> List[KnowledgeBase]:
        result = await db.execute(
            select(KnowledgeBase).order_by(KnowledgeBase.created_at.desc())
        )
        return list(result.scalars().all())

    async def update(
        self,
        db: AsyncSession,
        kb_id: int,
        obj_in: KnowledgeBaseUpdate,
    ) -> Optional[KnowledgeBase]:
        update_data = obj_in.model_dump(exclude_unset=True)
        # ✅ 过滤掉模型不存在的字段
        valid_fields = {"name", "description", "status"}
        update_data = {k: v for k, v in update_data.items() if k in valid_fields}

        if not update_data:
            return await self.get(db, kb_id)

        await db.execute(
            update(KnowledgeBase).where(KnowledgeBase.id == kb_id).values(**update_data)
        )
        await db.commit()
        return await self.get(db, kb_id)

        await db.execute(
            update(KnowledgeBase).where(KnowledgeBase.id == kb_id).values(**update_data)
        )
        await db.commit()
        return await self.get(db, kb_id)

    async def get_item_count(
        self,
        db: AsyncSession,
        kb_id: int,
    ) -> int:
        result = await db.execute(
            select(func.count(KnowledgeItem.id)).where(
                and_(
                    KnowledgeItem.knowledge_base_id == kb_id,
                    KnowledgeItem.status == 1,
                )
            )
        )
        return result.scalar() or 0


class CRUDKnowledgeItem:
    async def create(
        self,
        db: AsyncSession,
        kb_id: int,
        obj_in: KnowledgeItemCreate,
        embedding_vector: Optional[List[float]] = None,
        qdrant_ids: Optional[List[str]] = None,
    ) -> KnowledgeItem:
        db_obj = KnowledgeItem(
            knowledge_base_id=kb_id,
            title=obj_in.title,
            answer_content=obj_in.answer,  # ✅ answer → answer_content
            answer_type=int(obj_in.answer_type),
            category=obj_in.category,
            tags={
                "tags": obj_in.tags.split(",") if obj_in.tags else []
            },  # ✅ JSONB格式
            status=1,
        )
        db.add(db_obj)
        await db.flush()

        if obj_in.similar_questions:
            for q in obj_in.similar_questions:
                similar = KnowledgeSimilarQuestion(
                    knowledge_item_id=db_obj.id,
                    question=q,
                )
                db.add(similar)

        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def create_batch(
        self,
        db: AsyncSession,
        kb_id: int,
        items: List[KnowledgeItemCreate],
    ) -> List[KnowledgeItem]:
        created = []
        for item_in in items:
            try:
                db_obj = KnowledgeItem(
                    knowledge_base_id=kb_id,
                    title=item_in.title,
                    answer_content=item_in.answer,
                    answer_type=int(item_in.answer_type),
                    category=item_in.category,
                    tags={"tags": item_in.tags.split(",") if item_in.tags else []},
                    status=1,
                )
                db.add(db_obj)
                await db.flush()

                if item_in.similar_questions:
                    for q in item_in.similar_questions:
                        similar = KnowledgeSimilarQuestion(
                            knowledge_item_id=db_obj.id,
                            question=q,
                        )
                        db.add(similar)

                created.append(db_obj)
            except Exception as e:
                import logging

                logging.error(
                    f"创建知识条目失败 title={item_in.title[:30] if item_in.title else 'None'}: {e}"
                )
                raise

        await db.commit()
        return created

    async def get(
        self,
        db: AsyncSession,
        item_id: int,
    ) -> Optional[KnowledgeItem]:
        result = await db.execute(
            select(KnowledgeItem).where(KnowledgeItem.id == item_id)
        )
        return result.scalar_one_or_none()

    async def get_with_similars(
        self,
        db: AsyncSession,
        item_id: int,
    ) -> Optional[KnowledgeItem]:
        from sqlalchemy.orm import selectinload

        result = await db.execute(
            select(KnowledgeItem)
            .options(selectinload(KnowledgeItem.similar_questions))
            .where(KnowledgeItem.id == item_id)
        )
        return result.scalar_one_or_none()

    async def get_list(
        self,
        db: AsyncSession,
        kb_id: int,
        query: KnowledgeItemQuery,
    ) -> Tuple[List[KnowledgeItem], int]:
        conditions = [KnowledgeItem.knowledge_base_id == kb_id]

        if query.keyword:
            conditions.append(KnowledgeItem.title.ilike(f"%{query.keyword}%"))
        if query.category:
            conditions.append(KnowledgeItem.category == query.category)
        if query.status is not None:
            conditions.append(KnowledgeItem.status == int(query.status))

        count_result = await db.execute(
            select(func.count(KnowledgeItem.id)).where(and_(*conditions))
        )
        total = count_result.scalar() or 0

        offset = (query.page - 1) * query.page_size
        result = await db.execute(
            select(KnowledgeItem)
            .options(selectinload(KnowledgeItem.similar_questions))
            .where(and_(*conditions))
            .order_by(KnowledgeItem.created_at.desc())
            .offset(offset)
            .limit(query.page_size)
        )
        items = list(result.scalars().all())
        return items, total

    async def update(
        self,
        db: AsyncSession,
        item_id: int,
        obj_in: KnowledgeItemUpdate,
    ) -> Optional[KnowledgeItem]:
        update_data = obj_in.model_dump(
            exclude_unset=True,
            exclude={"similar_questions"},
        )

        # ✅ answer → answer_content
        if "answer" in update_data:
            update_data["answer_content"] = update_data.pop("answer")

        # ✅ tags → JSONB格式
        if "tags" in update_data and update_data["tags"]:
            update_data["tags"] = {"tags": update_data["tags"].split(",")}

        # ✅ 过滤掉模型不存在的字段
        valid_fields = {
            "title",
            "answer_content",
            "answer_type",
            "category",
            "tags",
            "status",
        }
        update_data = {k: v for k, v in update_data.items() if k in valid_fields}

        if update_data:
            await db.execute(
                update(KnowledgeItem)
                .where(KnowledgeItem.id == item_id)
                .values(**update_data)
            )

        if obj_in.similar_questions is not None:
            await db.execute(
                delete(KnowledgeSimilarQuestion).where(
                    KnowledgeSimilarQuestion.knowledge_item_id == item_id
                )
            )
            for q in obj_in.similar_questions:
                similar = KnowledgeSimilarQuestion(
                    knowledge_item_id=item_id,
                    question=q,
                )
                db.add(similar)

        await db.commit()
        return await self.get_with_similars(db, item_id)

    async def delete(
        self,
        db: AsyncSession,
        item_id: int,
    ) -> bool:
        await db.execute(
            delete(KnowledgeSimilarQuestion).where(
                KnowledgeSimilarQuestion.knowledge_item_id == item_id
            )
        )
        result = await db.execute(
            delete(KnowledgeItem).where(KnowledgeItem.id == item_id)
        )
        await db.commit()
        return result.rowcount > 0

    async def delete_batch(
        self,
        db: AsyncSession,
        item_ids: List[int],
    ) -> int:
        if not item_ids:
            return 0

        await db.execute(
            delete(KnowledgeSimilarQuestion).where(
                KnowledgeSimilarQuestion.knowledge_item_id.in_(item_ids)
            )
        )
        result = await db.execute(
            delete(KnowledgeItem).where(KnowledgeItem.id.in_(item_ids))
        )
        await db.commit()
        return result.rowcount

    async def get_all_by_kb(
        self,
        db: AsyncSession,
        kb_id: int,
    ) -> List[KnowledgeItem]:
        from sqlalchemy.orm import selectinload

        result = await db.execute(
            select(KnowledgeItem)
            .options(selectinload(KnowledgeItem.similar_questions))
            .where(
                and_(
                    KnowledgeItem.knowledge_base_id == kb_id,
                    KnowledgeItem.status == 1,
                )
            )
        )
        return list(result.scalars().all())

    async def get_similar_count(
        self,
        db: AsyncSession,
        item_id: int,
    ) -> int:
        result = await db.execute(
            select(func.count(KnowledgeSimilarQuestion.id)).where(
                KnowledgeSimilarQuestion.knowledge_item_id == item_id
            )
        )
        return result.scalar() or 0


crud_knowledge_base = CRUDKnowledgeBase()
crud_knowledge_item = CRUDKnowledgeItem()
