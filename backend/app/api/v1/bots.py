# backend/app/api/v1/bots.py
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_admin_id
from app.crud.bot import crud_bot, crud_bot_keyword
from app.crud.knowledge import crud_knowledge_base
from app.schemas.bot import (
    BotCreate,
    BotUpdate,
    BotOut,
    KeywordCreate,
    KeywordUpdate,
    KeywordOut,
    FaqSearchRequest,
)
from app.utils.response import Response

logger = logging.getLogger(__name__)
router = APIRouter()

DEFAULT_NO_ANSWER_REPLY = "您好，我暂时无法回答这个问题，是否需要转接人工客服？"


def _bot_to_out(bot, kb_name: str = None, kb_status: int = None) -> BotOut:
    """Bot模型 → BotOut Schema"""
    return BotOut(
        id=bot.id,
        name=bot.name,
        knowledge_base_id=bot.knowledge_base_id,
        knowledge_base_name=kb_name,
        knowledge_base_status=kb_status,
        similarity_threshold=bot.match_threshold or 0.85,
        no_answer_reply=DEFAULT_NO_ANSWER_REPLY,
        max_no_answer_count=bot.no_answer_count or 3,
        status=bot.status,
        created_at=bot.created_at,
        updated_at=bot.updated_at,
    )


def _keyword_to_out(kw) -> KeywordOut:
    """BotKeyword模型 → KeywordOut Schema"""
    actions = kw.actions or {}
    return KeywordOut(
        id=kw.id,
        bot_id=kw.bot_id,
        keyword=kw.keyword,
        match_type=kw.match_type,
        action_type=actions.get("action_type", 0),
        reply_content=actions.get("reply_content"),
        faq_item_id=actions.get("faq_item_id"),
        priority=kw.priority,
        status=kw.status,
        created_at=kw.created_at,
        updated_at=kw.updated_at,
    )


# ==================== Bot管理 ====================


@router.get("", summary="获取Bot列表")
async def list_bots(
    db: AsyncSession = Depends(get_db),
    admin_id: int = Depends(get_current_admin_id),
):
    bots = await crud_bot.get_list(db)
    result = []
    for bot in bots:
        kb = (
            await crud_knowledge_base.get(db, bot.knowledge_base_id)
            if bot.knowledge_base_id
            else None
        )
        result.append(
            _bot_to_out(bot, kb.name if kb else None, kb.status if kb else None)
        )
    return Response.success(data=result)


@router.post("", summary="创建Bot")
async def create_bot(
    obj_in: BotCreate,
    db: AsyncSession = Depends(get_db),
    admin_id: int = Depends(get_current_admin_id),
):
    kb = await crud_knowledge_base.get(db, obj_in.knowledge_base_id)
    if not kb:
        raise HTTPException(status_code=404, detail="知识库不存在")

    bot = await crud_bot.create(db, obj_in)
    return Response.success(data=_bot_to_out(bot, kb.name, kb.status))


@router.put("/{bot_id}", summary="更新Bot")
async def update_bot(
    bot_id: int,
    obj_in: BotUpdate,
    db: AsyncSession = Depends(get_db),
    admin_id: int = Depends(get_current_admin_id),
):
    bot = await crud_bot.get(db, bot_id)
    if not bot:
        raise HTTPException(status_code=404, detail="Bot不存在")

    if obj_in.knowledge_base_id:
        kb = await crud_knowledge_base.get(db, obj_in.knowledge_base_id)
        if not kb:
            raise HTTPException(status_code=404, detail="知识库不存在")

    bot = await crud_bot.update(db, bot_id, obj_in)
    kb = (
        await crud_knowledge_base.get(db, bot.knowledge_base_id)
        if bot.knowledge_base_id
        else None
    )
    return Response.success(
        data=_bot_to_out(bot, kb.name if kb else None, kb.status if kb else None)
    )


@router.delete("/{bot_id}", summary="删除Bot")
async def delete_bot(
    bot_id: int,
    db: AsyncSession = Depends(get_db),
    admin_id: int = Depends(get_current_admin_id),
):
    from sqlalchemy import select
    from app.models.channel import Channel

    bot = await crud_bot.get(db, bot_id)
    if not bot:
        raise HTTPException(status_code=404, detail="Bot不存在")

    result = await db.execute(select(Channel).where(Channel.bot_id == bot_id))
    channels = result.scalars().all()
    if channels:
        raise HTTPException(
            status_code=400,
            detail=f"该 Bot 被 {len(channels)} 个渠道引用，请先在渠道管理中解绑或删除相关渠道",
        )

    await crud_bot.delete(db, bot_id)
    return Response.success(message="删除成功")


# ==================== 关键词管理 ====================


@router.get("/{bot_id}/keywords", summary="获取关键词列表")
async def list_keywords(
    bot_id: int,
    db: AsyncSession = Depends(get_db),
    admin_id: int = Depends(get_current_admin_id),
):
    bot = await crud_bot.get(db, bot_id)
    if not bot:
        raise HTTPException(status_code=404, detail="Bot不存在")

    keywords = await crud_bot_keyword.get_list_by_bot(db, bot_id)
    return Response.success(data=[_keyword_to_out(kw) for kw in keywords])


@router.post("/{bot_id}/keywords", summary="创建关键词")
async def create_keyword(
    bot_id: int,
    obj_in: KeywordCreate,
    db: AsyncSession = Depends(get_db),
    admin_id: int = Depends(get_current_admin_id),
):
    bot = await crud_bot.get(db, bot_id)
    if not bot:
        raise HTTPException(status_code=404, detail="Bot不存在")

    keyword = await crud_bot_keyword.create(db, bot_id, obj_in)
    return Response.success(data=_keyword_to_out(keyword))


@router.put("/{bot_id}/keywords/{keyword_id}", summary="更新关键词")
async def update_keyword(
    bot_id: int,
    keyword_id: int,
    obj_in: KeywordUpdate,
    db: AsyncSession = Depends(get_db),
    admin_id: int = Depends(get_current_admin_id),
):
    bot = await crud_bot.get(db, bot_id)
    if not bot:
        raise HTTPException(status_code=404, detail="Bot不存在")

    keyword = await crud_bot_keyword.get(db, keyword_id)
    if not keyword:
        raise HTTPException(status_code=404, detail="关键词不存在")
    if keyword.bot_id != bot_id:
        raise HTTPException(status_code=403, detail="该关键词不属于此Bot")

    keyword = await crud_bot_keyword.update(db, keyword_id, obj_in)
    return Response.success(data=_keyword_to_out(keyword))


@router.delete("/{bot_id}/keywords/{keyword_id}", summary="删除关键词")
async def delete_keyword(
    bot_id: int,
    keyword_id: int,
    db: AsyncSession = Depends(get_db),
    admin_id: int = Depends(get_current_admin_id),
):
    bot = await crud_bot.get(db, bot_id)
    if not bot:
        raise HTTPException(status_code=404, detail="Bot不存在")

    keyword = await crud_bot_keyword.get(db, keyword_id)
    if not keyword:
        raise HTTPException(status_code=404, detail="关键词不存在")
    if keyword.bot_id != bot_id:
        raise HTTPException(status_code=403, detail="该关键词不属于此Bot")

    await crud_bot_keyword.delete(db, keyword_id)
    return Response.success(message="删除成功")


# ==================== FAQ检索测试 ====================


@router.post("/{bot_id}/faq/test", summary="FAQ检索效果测试")
async def test_faq_search(
    bot_id: int,
    req: FaqSearchRequest,
    db: AsyncSession = Depends(get_db),
    admin_id: int = Depends(get_current_admin_id),
):
    bot = await crud_bot.get(db, bot_id)
    if not bot:
        raise HTTPException(status_code=404, detail="Bot不存在")

    from app.services.bot.faq import faq_search

    response = await faq_search(query=req.query, bot_id=bot_id, db=db)
    return Response.success(data=response)
