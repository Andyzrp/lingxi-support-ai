# backend/app/services/bot/keyword.py
import logging
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.bot import crud_bot_keyword
from app.models.bot import BotKeyword
from app.schemas.bot import FaqHit

logger = logging.getLogger(__name__)


# ==================== 关键词匹配核心 ====================

def _is_match(query: str, keyword: str, match_type: int) -> bool:
    """
    判断用户问题是否命中关键词

    match_type:
        0 = 精确匹配
        1 = 包含匹配
    """
    query = query.strip()
    keyword = keyword.strip()

    if match_type == 0:
        return query == keyword
    elif match_type == 1:
        return keyword in query
    return False


async def match_keyword(
    query: str,
    bot_id: int,
    db: AsyncSession,
) -> Optional[dict]:
    """
    关键词干预匹配

    ✅ actions字段是JSONB，从中取action_type/reply_content/faq_item_id
    """
    keywords: List[BotKeyword] = await crud_bot_keyword.get_enabled_by_bot(
        db=db,
        bot_id=bot_id,
    )

    if not keywords:
        return None

    for kw in keywords:
        if _is_match(query, kw.keyword, kw.match_type):
            # ✅ 从JSONB actions字段取action信息
            actions = kw.actions or {}
            action_type = actions.get("action_type", 0)

            logger.info(
                f"关键词命中 bot_id={bot_id} "
                f"keyword='{kw.keyword}' "
                f"action_type={action_type}"
            )

            return {
                "hit": True,
                "keyword": kw.keyword,
                "action_type": action_type,
                "reply_content": actions.get("reply_content"),
                "faq_item_id": actions.get("faq_item_id"),
                "transfer": action_type == 2,
            }

    return None


# ==================== 关键词命中转FAQ结果 ====================

async def keyword_hit_to_faq(
    query: str,
    keyword_result: dict,
    db: AsyncSession,
) -> Optional[FaqHit]:
    """将关键词命中结果转换为FaqHit格式"""
    action_type = keyword_result.get("action_type")

    # 转人工
    if action_type == 2:
        return None

    # 固定话术
    if action_type == 0:
        reply_content = keyword_result.get("reply_content", "")
        if not reply_content:
            logger.warning(
                f"关键词固定话术为空 keyword={keyword_result.get('keyword')}"
            )
            return None

        return FaqHit(
            item_id=0,
            title=keyword_result.get("keyword", ""),
            answer=reply_content,
            answer_type=0,
            score=1.0,
            bm25_score=0.0,
            vector_score=0.0,
            matched_question=query,
            hit_by_keyword=True,
            keyword_action="fixed_reply",
        )

    # 推荐FAQ
    if action_type == 1:
        faq_item_id = keyword_result.get("faq_item_id")
        if not faq_item_id:
            return None

        from app.crud.knowledge import crud_knowledge_item
        item = await crud_knowledge_item.get(db, faq_item_id)
        if not item:
            logger.warning(
                f"关键词推荐FAQ条目不存在 item_id={faq_item_id}"
            )
            return None

        return FaqHit(
            item_id=item.id,
            title=item.title,
            answer=item.answer_content or "",   # ✅ answer_content
            answer_type=item.answer_type,
            score=1.0,
            bm25_score=0.0,
            vector_score=0.0,
            matched_question=query,
            hit_by_keyword=True,
            keyword_action="recommend_faq",
        )

    return None


# ==================== 对外统一入口 ====================

async def process_keyword_intervention(
    query: str,
    bot_id: int,
    db: AsyncSession,
) -> tuple[Optional[FaqHit], bool]:
    """
    关键词干预统一处理入口

    Returns:
        (faq_hit, need_transfer)
    """
    keyword_result = await match_keyword(query, bot_id, db)

    if not keyword_result:
        return None, False

    if keyword_result.get("transfer"):
        logger.info(
            f"关键词触发转人工 bot_id={bot_id} query='{query}'"
        )
        return None, True

    faq_hit = await keyword_hit_to_faq(query, keyword_result, db)
    return faq_hit, False