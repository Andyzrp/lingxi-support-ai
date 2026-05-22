# backend/app/crud/bot.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func, and_
from typing import Optional, List
from app.models.bot import Bot, BotKeyword
from app.schemas.bot import BotCreate, BotUpdate, KeywordCreate, KeywordUpdate


class CRUDBot:

    async def create(self, db: AsyncSession, obj_in: BotCreate) -> Bot:
        db_obj = Bot(
            name=obj_in.name,
            knowledge_base_id=obj_in.knowledge_base_id,
            match_threshold=obj_in.similarity_threshold,  # ✅ 字段名映射
            no_answer_count=obj_in.max_no_answer_count,   # ✅ 字段名映射
            auto_transfer=1,
            status=1,
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def get(self, db: AsyncSession, bot_id: int) -> Optional[Bot]:
        result = await db.execute(
            select(Bot).where(Bot.id == bot_id)
        )
        return result.scalar_one_or_none()

    async def get_list(self, db: AsyncSession) -> List[Bot]:
        result = await db.execute(
            select(Bot).order_by(Bot.created_at.desc())
        )
        return list(result.scalars().all())

    async def update(
        self,
        db: AsyncSession,
        bot_id: int,
        obj_in: BotUpdate,
    ) -> Optional[Bot]:
        update_data = {}

        if obj_in.name is not None:
            update_data["name"] = obj_in.name
        if obj_in.knowledge_base_id is not None:
            update_data["knowledge_base_id"] = obj_in.knowledge_base_id
        if obj_in.similarity_threshold is not None:
            update_data["match_threshold"] = obj_in.similarity_threshold
        if obj_in.max_no_answer_count is not None:
            update_data["no_answer_count"] = obj_in.max_no_answer_count
        if obj_in.status is not None:
            update_data["status"] = int(obj_in.status)

        if not update_data:
            return await self.get(db, bot_id)

        await db.execute(
            update(Bot).where(Bot.id == bot_id).values(**update_data)
        )
        await db.commit()
        return await self.get(db, bot_id)

    async def delete(self, db: AsyncSession, bot_id: int) -> bool:
        result = await db.execute(
            delete(Bot).where(Bot.id == bot_id)
        )
        await db.commit()
        return result.rowcount > 0

    async def get_by_knowledge_base(
        self, db: AsyncSession, kb_id: int
    ) -> List[Bot]:
        result = await db.execute(
            select(Bot).where(
                and_(Bot.knowledge_base_id == kb_id, Bot.status == 1)
            )
        )
        return list(result.scalars().all())


class CRUDBotKeyword:

    async def create(
        self,
        db: AsyncSession,
        bot_id: int,
        obj_in: KeywordCreate,
    ) -> BotKeyword:
        # ✅ actions字段是JSONB，把action信息打包进去
        actions = {
            "action_type": int(obj_in.action_type),
            "reply_content": obj_in.reply_content,
            "faq_item_id": obj_in.faq_item_id,
        }
        db_obj = BotKeyword(
            bot_id=bot_id,
            keyword=obj_in.keyword,
            match_type=int(obj_in.match_type),
            actions=actions,
            priority=obj_in.priority,
            status=1,
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def get(
        self, db: AsyncSession, keyword_id: int
    ) -> Optional[BotKeyword]:
        result = await db.execute(
            select(BotKeyword).where(BotKeyword.id == keyword_id)
        )
        return result.scalar_one_or_none()

    async def get_list_by_bot(
        self, db: AsyncSession, bot_id: int
    ) -> List[BotKeyword]:
        result = await db.execute(
            select(BotKeyword)
            .where(BotKeyword.bot_id == bot_id)
            .order_by(BotKeyword.priority.desc(), BotKeyword.created_at.asc())
        )
        return list(result.scalars().all())

    async def get_enabled_by_bot(
        self, db: AsyncSession, bot_id: int
    ) -> List[BotKeyword]:
        result = await db.execute(
            select(BotKeyword)
            .where(
                and_(BotKeyword.bot_id == bot_id, BotKeyword.status == 1)
            )
            .order_by(BotKeyword.priority.desc(), BotKeyword.created_at.asc())
        )
        return list(result.scalars().all())

    async def update(
        self,
        db: AsyncSession,
        keyword_id: int,
        obj_in: KeywordUpdate,
    ) -> Optional[BotKeyword]:
        update_data = {}

        if obj_in.keyword is not None:
            update_data["keyword"] = obj_in.keyword
        if obj_in.match_type is not None:
            update_data["match_type"] = int(obj_in.match_type)
        if obj_in.priority is not None:
            update_data["priority"] = obj_in.priority
        if obj_in.status is not None:
            update_data["status"] = obj_in.status

        # 更新actions JSONB
        if any([
            obj_in.action_type is not None,
            obj_in.reply_content is not None,
            obj_in.faq_item_id is not None,
        ]):
            kw = await self.get(db, keyword_id)
            if kw:
                actions = dict(kw.actions or {})
                if obj_in.action_type is not None:
                    actions["action_type"] = int(obj_in.action_type)
                if obj_in.reply_content is not None:
                    actions["reply_content"] = obj_in.reply_content
                if obj_in.faq_item_id is not None:
                    actions["faq_item_id"] = obj_in.faq_item_id
                update_data["actions"] = actions

        if not update_data:
            return await self.get(db, keyword_id)

        await db.execute(
            update(BotKeyword)
            .where(BotKeyword.id == keyword_id)
            .values(**update_data)
        )
        await db.commit()
        return await self.get(db, keyword_id)

    async def delete(self, db: AsyncSession, keyword_id: int) -> bool:
        result = await db.execute(
            delete(BotKeyword).where(BotKeyword.id == keyword_id)
        )
        await db.commit()
        return result.rowcount > 0

    async def count_by_bot(self, db: AsyncSession, bot_id: int) -> int:
        result = await db.execute(
            select(func.count(BotKeyword.id))
            .where(BotKeyword.bot_id == bot_id)
        )
        return result.scalar() or 0


crud_bot = CRUDBot()
crud_bot_keyword = CRUDBotKeyword()