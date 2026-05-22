# backend/app/crud/conversation.py
import logging
import uuid
from datetime import datetime
from typing import Optional, List, Tuple, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func, and_

from app.models.conversation import Conversation, Message, AiConversationDetail
from app.models.bot import Bot
from app.models.agent import Agent

logger = logging.getLogger(__name__)


def _gen_conv_no() -> str:
    """生成唯一会话编号"""
    return f"C{datetime.now().strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:6].upper()}"


# ==================== 会话 CRUD ====================


class CRUDConversation:
    async def create(
        self,
        db: AsyncSession,
        channel_id: int,
        user_id: Optional[int] = None,
        username: Optional[str] = None,
        bot_id: Optional[int] = None,
        agent_id: Optional[int] = None,
    ) -> Conversation:
        """
        创建新会话

        字段映射（对应实际建表SQL）：
        current_mode=0  → Bot模式
        is_transferred=0 → 未转人工
        is_resolved=0   → 未解决
        evaluated=0     → 未评价
        """
        db_obj = Conversation(
            conversation_no=_gen_conv_no(),
            channel_id=channel_id,
            user_id=user_id,
            username=username,
            bot_id=bot_id,
            agent_id=agent_id,
            current_mode=0,
            is_transferred=0,
            is_resolved=0,
            evaluated=0,
            started_at=datetime.utcnow(),
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        logger.info(
            f"会话创建成功 "
            f"conversation_id={db_obj.id} "
            f"conversation_no={db_obj.conversation_no} "
            f"channel_id={channel_id}"
        )
        return db_obj

    async def get(
        self,
        db: AsyncSession,
        conversation_id: int,
    ) -> Optional[Conversation]:
        """按ID查询会话"""
        result = await db.execute(
            select(Conversation).where(Conversation.id == conversation_id)
        )
        return result.scalar_one_or_none()

    async def get_by_no(
        self,
        db: AsyncSession,
        conversation_no: str,
    ) -> Optional[Conversation]:
        """按会话编号查询"""
        result = await db.execute(
            select(Conversation).where(Conversation.conversation_no == conversation_no)
        )
        return result.scalar_one_or_none()

    async def get_list(
        self,
        db: AsyncSession,
        page: int = 1,
        page_size: int = 20,
        channel_id: Optional[int] = None,
        status: Optional[int] = None,
        is_transferred: Optional[int] = None,
        user_id: Optional[int] = None,
        username: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        conversation_id: Optional[int] = None,
    ) -> Tuple[List[Conversation], int]:
        """分页获取会话列表"""
        conditions = []

        if conversation_id is not None:
            conditions.append(Conversation.id == conversation_id)
        if channel_id is not None:
            conditions.append(Conversation.channel_id == channel_id)
        if status is not None:
            conditions.append(Conversation.current_mode == status)
        if is_transferred is not None:
            conditions.append(Conversation.is_transferred == is_transferred)
        if user_id is not None:
            conditions.append(Conversation.user_id == user_id)
        if username:
            conditions.append(Conversation.username.ilike(f"%{username}%"))
        if start_date:
            conditions.append(Conversation.created_at >= start_date)
        if end_date:
            conditions.append(Conversation.created_at <= end_date)

        where_clause = and_(*conditions) if conditions else True

        count_result = await db.execute(
            select(func.count(Conversation.id)).where(where_clause)
        )
        total = count_result.scalar() or 0

        offset = (page - 1) * page_size
        result = await db.execute(
            select(Conversation)
            .where(where_clause)
            .order_by(Conversation.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        items = list(result.scalars().all())

        # 批量查询 Bot / Agent 名称
        bot_ids = list({c.bot_id for c in items if c.bot_id})
        agent_ids = list({c.agent_id for c in items if c.agent_id})

        bot_map = {}
        agent_map = {}
        if bot_ids:
            bot_rows = await db.execute(
                select(Bot.id, Bot.name).where(Bot.id.in_(bot_ids))
            )
            bot_map = {r.id: r.name for r in bot_rows.all()}
        if agent_ids:
            agent_rows = await db.execute(
                select(Agent.id, Agent.name).where(Agent.id.in_(agent_ids))
            )
            agent_map = {r.id: r.name for r in agent_rows.all()}

        for c in items:
            c.bot_name = bot_map.get(c.bot_id)
            c.agent_name = agent_map.get(c.agent_id)

        return items, total

    async def close(
        self,
        db: AsyncSession,
        conversation_id: int,
    ) -> Optional[Conversation]:
        """关闭会话，记录结束时间和时长"""
        now = datetime.utcnow()
        conv = await self.get(db, conversation_id)

        duration = None
        if conv and conv.started_at:
            duration = int((now - conv.started_at).total_seconds())

        await db.execute(
            update(Conversation)
            .where(Conversation.id == conversation_id)
            .values(
                ended_at=now,
                duration=duration,
                status="closed",
            )
        )
        await db.commit()
        return await self.get(db, conversation_id)

    async def set_transfer(
        self,
        db: AsyncSession,
        conversation_id: int,
        agent_name: str,
        transfer_reason: Optional[int] = None,
    ) -> Optional[Conversation]:
        """
        标记会话已转人工

        字段映射：
        is_transferred=1  → 已转人工
        staff_name        → 分配的客服名称
        current_mode=1    → 切换为人工模式
        transfer_at       → 转人工时间
        transfer_reason   → 转人工原因(SMALLINT)
        """
        await db.execute(
            update(Conversation)
            .where(Conversation.id == conversation_id)
            .values(
                is_transferred=1,
                staff_name=agent_name,
                current_mode=1,
                transfer_at=datetime.utcnow(),
                transfer_reason=transfer_reason,
                status="transferred",
            )
        )
        await db.commit()
        logger.info(
            f"会话转人工成功 conversation_id={conversation_id} staff_name={agent_name}"
        )
        return await self.get(db, conversation_id)

    async def set_resolved(
        self,
        db: AsyncSession,
        conversation_id: int,
    ) -> Optional[Conversation]:
        """标记会话已解决"""
        await db.execute(
            update(Conversation)
            .where(Conversation.id == conversation_id)
            .values(is_resolved=1)
        )
        await db.commit()
        return await self.get(db, conversation_id)

    async def set_evaluate(
        self,
        db: AsyncSession,
        conversation_id: int,
        rating: int,
        comment: Optional[str] = None,
    ) -> Optional[Conversation]:
        """
        提交评价

        字段映射：
        evaluated=1    → 已评价
        eval_score     → 评分(1-5)
        eval_comment   → 评价内容
        eval_at        → 评价时间
        eval_resolved  → 评价中是否标记解决
        """
        await db.execute(
            update(Conversation)
            .where(Conversation.id == conversation_id)
            .values(
                evaluated=1,
                eval_score=rating,
                eval_comment=comment,
                eval_at=datetime.utcnow(),
                eval_resolved=1 if rating >= 4 else 0,
            )
        )
        await db.commit()
        logger.info(f"会话评价提交 conversation_id={conversation_id} rating={rating}")
        return await self.get(db, conversation_id)

    async def increment_message_count(
        self,
        db: AsyncSession,
        conversation_id: int,
    ):
        """消息数+1"""
        await db.execute(
            update(Conversation)
            .where(Conversation.id == conversation_id)
            .values(message_count=Conversation.message_count + 1)
        )
        await db.commit()

    async def increment_no_answer_count(
        self,
        db: AsyncSession,
        conversation_id: int,
    ) -> int:
        """未回答次数+1，返回新计数"""
        conv = await self.get(db, conversation_id)
        new_count = (conv.no_answer_count or 0) + 1 if conv else 1

        await db.execute(
            update(Conversation)
            .where(Conversation.id == conversation_id)
            .values(no_answer_count=new_count)
        )
        await db.commit()
        return new_count

    async def get_message_count(
        self,
        db: AsyncSession,
        conversation_id: int,
    ) -> int:
        """查询会话消息数量"""
        result = await db.execute(
            select(func.count(Message.id)).where(
                Message.conversation_id == conversation_id
            )
        )
        return result.scalar() or 0


# ==================== 消息 CRUD ====================


class CRUDMessage:
    async def create(
        self,
        db: AsyncSession,
        conversation_id: int,
        role: int,
        content: str,
        message_type: int = 0,
        answer_source: Optional[str] = None,
        intent: Optional[str] = None,
        emotion: Optional[str] = None,
        confidence_score: Optional[float] = None,
        sender_name: Optional[str] = None,
        card_type: Optional[str] = None,
        card_data: Optional[Any] = None,
    ) -> Message:
        """
        创建消息记录

        字段映射（对应实际建表SQL）：
        role         → sender_type   (0用户/1Bot/2人工)
        message_type → content_type  (0文本/1富文本)
        额外信息      → extra(JSONB)  存储answer_source/intent/emotion等
        """
        extra = {}
        if answer_source:
            extra["answer_source"] = answer_source
        if intent:
            extra["intent"] = intent
        if emotion:
            extra["emotion"] = emotion
        if confidence_score is not None:
            extra["confidence_score"] = confidence_score
        if card_type:
            extra["card_type"] = card_type
        if card_data:
            extra["card_data"] = card_data

        db_obj = Message(
            conversation_id=conversation_id,
            sender_type=role,
            sender_name=sender_name,
            content_type=message_type,
            content=content,
            extra=extra if extra else None,
            is_read=0,
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def get(
        self,
        db: AsyncSession,
        message_id: int,
    ) -> Optional[Message]:
        result = await db.execute(select(Message).where(Message.id == message_id))
        return result.scalar_one_or_none()

    async def get_list(
        self,
        db: AsyncSession,
        conversation_id: int,
        limit: int = 200,
    ) -> List[Message]:
        """获取会话消息列表（正序）"""
        result = await db.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.asc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_recent(
        self,
        db: AsyncSession,
        conversation_id: int,
        rounds: int = 3,
    ) -> List[Message]:
        """
        获取最近N轮对话历史（用于构建LLM上下文）

        取最近 rounds*2 条消息，倒序查询后正序返回
        """
        limit = rounds * 2
        result = await db.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.desc())
            .limit(limit)
        )
        messages = list(result.scalars().all())
        messages.reverse()  # 转为正序
        return messages

    async def mark_read(
        self,
        db: AsyncSession,
        conversation_id: int,
    ):
        """标记会话所有消息为已读"""
        await db.execute(
            update(Message)
            .where(Message.conversation_id == conversation_id)
            .values(is_read=1)
        )
        await db.commit()


# ==================== 全局实例 ====================

crud_conversation = CRUDConversation()
crud_message = CRUDMessage()


# ==================== AI 会话明细 CRUD ====================


class CRUDConversationDetail:
    async def create(
        self,
        db: AsyncSession,
        conversation_id: int,
        channel_id: int | None,
        user_id: int | None,
        round_index: int,
        user_message: str,
        bot_answer: str | None,
        agent_answer: str | None,
        answer_source: int,
        is_resolved: int = 0,
        is_transferred: int = 0,
        is_no_answer: int = 0,
        emotion_detected: int = 0,
        response_ms: int | None = None,
        tools_called: dict | None = None,
    ) -> AiConversationDetail:
        """
        创建 AI 会话明细记录

        字段映射（对应 ai_conversation_details 表）：
        - answer_source: 0=Bot FAQ / 1=关键词干预 / 2=Agent / 3=人工客服 / 99=未知
        - is_resolved: 置信度≥0.7 → 1，否则 0（由调用方计算后传入）
        - is_transferred: 是否转人工（由调用方判断后传入）
        - is_no_answer: answer_source 为 default/error/unknown → 1
        """
        db_obj = AiConversationDetail(
            conversation_id=conversation_id,
            channel_id=channel_id,
            user_id=user_id,
            round_index=round_index,
            user_message=user_message,
            bot_answer=bot_answer,
            agent_answer=agent_answer,
            answer_source=answer_source,
            is_resolved=is_resolved,
            is_transferred=is_transferred,
            is_no_answer=is_no_answer,
            emotion_detected=emotion_detected,
            response_ms=response_ms,
            tools_called=tools_called,
        )
        db.add(db_obj)
        await db.flush()
        return db_obj


crud_conversation_detail = CRUDConversationDetail()
