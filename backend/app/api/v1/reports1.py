from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc
from datetime import datetime, timedelta
from typing import Optional
from app.core.database import get_db
from app.api.deps import get_current_admin
from app.models.conversation import Conversation, AiConversationDetail
from app.models.agent import Agent
from app.models.channel import Channel
from app.utils.response import Response, PageResponse
from app.utils.pagination import get_page_params, PageParams

router = APIRouter()


def get_date_range(start_date: Optional[str], end_date: Optional[str]):
    if start_date:
        start = datetime.strptime(start_date, "%Y-%m-%d").replace(
            hour=0, minute=0, second=0
        )
    else:
        start = datetime.utcnow() - timedelta(days=7)
    if end_date:
        end = datetime.strptime(end_date, "%Y-%m-%d").replace(
            hour=23, minute=59, second=59
        )
    else:
        end = datetime.utcnow()
    return start, end


@router.get("/dashboard", summary="核心指标概览")
async def get_dashboard(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    channel_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_admin=Depends(get_current_admin),
):
    start, end = get_date_range(start_date, end_date)

    base_filter = and_(
        Conversation.started_at >= start,
        Conversation.started_at <= end,
    )
    if channel_id:
        base_filter = and_(base_filter, Conversation.channel_id == channel_id)

    total_sessions = await db.execute(
        select(func.count(Conversation.id)).where(base_filter)
    )
    total = total_sessions.scalar() or 0

    bot_sessions = await db.execute(
        select(func.count(Conversation.id)).where(
            and_(base_filter, Conversation.session_type == 0)
        )
    )
    bot_total = bot_sessions.scalar() or 0

    agent_sessions = await db.execute(
        select(func.count(Conversation.id)).where(
            and_(base_filter, Conversation.session_type.in_([1, 2]))
        )
    )
    agent_total = agent_sessions.scalar() or 0

    transferred = await db.execute(
        select(func.count(Conversation.id)).where(
            and_(base_filter, Conversation.is_transferred == 1)
        )
    )
    transferred_total = transferred.scalar() or 0

    resolved = await db.execute(
        select(func.count(Conversation.id)).where(
            and_(base_filter, Conversation.is_resolved == 1)
        )
    )
    resolved_total = resolved.scalar() or 0

    eval_count_result = await db.execute(
        select(func.count(Conversation.id)).where(
            and_(base_filter, Conversation.evaluated == 1)
        )
    )
    eval_count = eval_count_result.scalar() or 0

    avg_score_result = await db.execute(
        select(func.avg(Conversation.eval_score)).where(
            and_(
                base_filter,
                Conversation.evaluated == 1,
                Conversation.eval_score.isnot(None),
            )
        )
    )
    avg_score = avg_score_result.scalar() or 0.0

    transfer_rate = round(transferred_total / total * 100, 2) if total > 0 else 0.0
    resolve_rate = round(resolved_total / total * 100, 2) if total > 0 else 0.0

    return Response.success(
        data={
            "total_sessions": total,
            "bot_sessions": bot_total,
            "agent_sessions": agent_total,
            "transferred_sessions": transferred_total,
            "resolved_sessions": resolved_total,
            "resolve_rate": resolve_rate,
            "transfer_rate": transfer_rate,
            "eval_count": eval_count,
            "avg_eval_score": round(avg_score, 2),
        }
    )


@router.get("/sessions", summary="会话量趋势")
async def get_sessions(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    channel_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_admin=Depends(get_current_admin),
):
    start, end = get_date_range(start_date, end_date)

    base_filter = and_(
        Conversation.started_at >= start,
        Conversation.started_at <= end,
    )
    if channel_id:
        base_filter = and_(base_filter, Conversation.channel_id == channel_id)

    result = await db.execute(
        select(
            func.date(Conversation.started_at).label("date"),
            func.count(Conversation.id).label("count"),
        )
        .where(base_filter)
        .group_by(func.date(Conversation.started_at))
        .order_by(func.date(Conversation.started_at))
    )
    rows = result.all()

    return Response.success(
        data=[{"date": str(r.date), "count": r.count} for r in rows]
    )


@router.get("/resolve-rate", summary="解决率趋势")
async def get_resolve_rate(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    channel_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_admin=Depends(get_current_admin),
):
    start, end = get_date_range(start_date, end_date)

    base_filter = and_(
        Conversation.started_at >= start,
        Conversation.started_at <= end,
    )
    if channel_id:
        base_filter = and_(base_filter, Conversation.channel_id == channel_id)

    result = await db.execute(
        select(
            func.date(Conversation.started_at).label("date"),
            func.count(Conversation.id).label("total"),
            func.sum(Conversation.is_resolved).label("resolved"),
        )
        .where(base_filter)
        .group_by(func.date(Conversation.started_at))
        .order_by(func.date(Conversation.started_at))
    )
    rows = result.all()

    return Response.success(
        data=[
            {
                "date": str(r.date),
                "total": r.total,
                "resolved": r.resolved or 0,
                "rate": round((r.resolved or 0) / r.total * 100, 2)
                if r.total > 0
                else 0,
            }
            for r in rows
        ]
    )


@router.get("/top-unanswered", summary="Top未解决问题")
async def get_top_unanswered(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = 8,
    db: AsyncSession = Depends(get_db),
    current_admin=Depends(get_current_admin),
):
    start, end = get_date_range(start_date, end_date)

    result = await db.execute(
        select(
            AiConversationDetail.user_message,
            func.count(AiConversationDetail.id).label("count"),
        )
        .join(Conversation, AiConversationDetail.conversation_id == Conversation.id)
        .where(
            and_(
                Conversation.started_at >= start,
                Conversation.started_at <= end,
                AiConversationDetail.is_no_answer == 1,
                AiConversationDetail.user_message.isnot(None),
            )
        )
        .group_by(AiConversationDetail.user_message)
        .order_by(func.count(AiConversationDetail.id).desc())
        .limit(limit)
    )
    rows = result.all()

    return Response.success(
        data=[{"question": r.user_message, "count": r.count} for r in rows]
    )


@router.get("/intent-distribution", summary="意图分布")
async def get_intent_distribution(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    channel_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_admin=Depends(get_current_admin),
):
    return Response.success(
        data=[
            {"intent": "查询订单", "count": 120, "rate": 30.0},
            {"intent": "退款申请", "count": 80, "rate": 20.0},
            {"intent": "商品咨询", "count": 60, "rate": 15.0},
            {"intent": "物流查询", "count": 50, "rate": 12.5},
            {"intent": "其他", "count": 90, "rate": 22.5},
        ]
    )


@router.get("/satisfaction", summary="满意度统计")
async def get_satisfaction(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    channel_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_admin=Depends(get_current_admin),
):
    start, end = get_date_range(start_date, end_date)

    base_filter = and_(
        Conversation.started_at >= start,
        Conversation.started_at <= end,
        Conversation.evaluated == 1,
    )
    if channel_id:
        base_filter = and_(base_filter, Conversation.channel_id == channel_id)

    result = await db.execute(
        select(
            Conversation.eval_score,
            func.count(Conversation.id).label("count"),
        )
        .where(base_filter)
        .group_by(Conversation.eval_score)
        .order_by(Conversation.eval_score)
    )
    rows = result.all()

    total = sum(r.count for r in rows)
    distribution = []
    for r in rows:
        distribution.append(
            {
                "score": r.eval_score,
                "count": r.count,
                "rate": round(r.count / total * 100, 2) if total > 0 else 0,
            }
        )

    avg_result = await db.execute(
        select(func.avg(Conversation.eval_score)).where(base_filter)
    )
    avg_score = avg_result.scalar() or 0.0

    return Response.success(
        data={
            "avg_score": round(avg_score, 2),
            "total_eval": total,
            "distribution": distribution,
        }
    )
