# backend/app/services/bot/faq.py
import logging
import time
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.bot import crud_bot
from app.crud.knowledge import crud_knowledge_item
from app.services.knowledge.vectorizer import search_similar
from app.schemas.bot import FaqHit, FaqSearchResponse

logger = logging.getLogger(__name__)


# ==================== FAQ检索主入口 ====================


async def faq_search(
    query: str,
    bot_id: int,
    db: AsyncSession,
) -> FaqSearchResponse:
    """
    FAQ检索主入口

    流程：
    1. 查询Bot配置（知识库ID、权重、阈值）
    2. 混合检索召回候选
    3. 取最高分判断是否超过阈值
    4. 超过 → 返回答案；未超过 → hit=False
    """
    start_time = time.time()

    # ── Step1：查询Bot配置 ──
    bot = await crud_bot.get(db, bot_id)
    if not bot:
        logger.error(f"Bot不存在 bot_id={bot_id}")
        return FaqSearchResponse(
            query=query,
            bot_id=bot_id,
            hit=False,
            result=None,
            elapsed_ms=0.0,
        )

    kb_id = bot.knowledge_base_id
    # ✅ 使用实际表字段名
    similarity_threshold = bot.match_threshold or 0.85
    print(f"[FAQ_SEARCH] kb_id={kb_id}, similarity_threshold={similarity_threshold}")
    # ✅ 表里没有bm25_weight/vector_weight，使用固定值
    bm25_weight = 0.3
    vector_weight = 0.7

    if not kb_id:
        logger.warning(f"Bot未绑定知识库 bot_id={bot_id}")
        return FaqSearchResponse(
            query=query,
            bot_id=bot_id,
            hit=False,
            result=None,
            elapsed_ms=0.0,
        )

    # ── Step2：纯向量检索（与知识库检索测试保持一致）──
    from app.services.knowledge.vectorizer import search_similar

    vector_hits = await search_similar(
        query=query,
        kb_id=kb_id,
        top_k=3,
        score_threshold=0.0,  # 不过滤，后面再判断
    )

    elapsed_ms = round((time.time() - start_time) * 1000, 2)

    # ── Step3：无候选 ──
    if not vector_hits:
        return FaqSearchResponse(
            query=query,
            bot_id=bot_id,
            hit=False,
            result=None,
            elapsed_ms=elapsed_ms,
        )

    # ── Step4：取最高分 ──
    best = vector_hits[0]
    best_score = best.get("vector_score", best.get("score", 0))
    print(f"[FAQ_SEARCH] 检索返回 {len(vector_hits)} 条, best_score={best_score}")

    logger.info(
        f"FAQ检索结果 bot_id={bot_id} "
        f"query='{query}' "
        f"best_score={best_score} "
        f"threshold={similarity_threshold}"
    )

    # ── Step5：未达阈值 ──
    print(
        f"[FAQ_SEARCH] 判断: best_score={best_score} < similarity_threshold={similarity_threshold} ? {float(best_score) < float(similarity_threshold)}"
    )
    if float(best_score) < float(similarity_threshold):
        print(f"[FAQ_SEARCH] ❌ 未达阈值，返回hit=False")
        return FaqSearchResponse(
            query=query,
            bot_id=bot_id,
            hit=False,
            result=None,
            elapsed_ms=elapsed_ms,
        )

    # ── Step6：查询知识条目详情 ──
    item = await crud_knowledge_item.get(db, best["item_id"])
    if not item:
        logger.warning(f"FAQ命中条目不存在 item_id={best['item_id']}")
        return FaqSearchResponse(
            query=query,
            bot_id=bot_id,
            hit=False,
            result=None,
            elapsed_ms=elapsed_ms,
        )

    # ── Step7：构建命中结果 ──
    faq_hit = FaqHit(
        item_id=item.id,
        title=item.title,
        answer=item.answer_content or "",
        answer_type=item.answer_type,
        score=best_score,
        bm25_score=0.0,  # 纯向量模式，BM25不参与评分
        vector_score=best_score,
        matched_question=best.get("question", ""),
        hit_by_keyword=False,
        keyword_action=None,
    )

    return FaqSearchResponse(
        query=query,
        bot_id=bot_id,
        hit=True,
        result=faq_hit,
        elapsed_ms=elapsed_ms,
    )


# ==================== 对外统一入口 ====================


async def process_faq(
    query: str,
    bot_id: int,
    db: AsyncSession,
) -> tuple[Optional[FaqHit], bool]:
    """
    FAQ检索对外统一入口

    执行顺序：
    1. 关键词干预（最高优先级）
    2. FAQ混合检索

    Returns:
        (faq_hit, need_transfer)
        faq_hit:       命中的FAQ结果，未命中时为None
        need_transfer: 是否需要转人工（关键词触发）
    """
    from app.services.bot.keyword import process_keyword_intervention

    # ── Step1：关键词干预 ──
    keyword_hit, need_transfer = await process_keyword_intervention(
        query=query,
        bot_id=bot_id,
        db=db,
    )

    # 关键词触发转人工
    if need_transfer:
        return None, True

    # 关键词命中固定话术或FAQ
    if keyword_hit:
        return keyword_hit, False

    # ── Step2：混合检索FAQ ──
    response = await faq_search(
        query=query,
        bot_id=bot_id,
        db=db,
    )

    if response.hit and response.result:
        return response.result, False

    return None, False
