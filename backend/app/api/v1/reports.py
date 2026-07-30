from datetime import date, timedelta
from typing import Optional, List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.core.database import get_db
from app.core.response import success_response
from app.api.deps import get_current_admin
from app.schemas.reports import (
    DashboardSchema,
    SessionsTrendSchema,
    ResolveRateTrendSchema,
    IntentItemSchema,
    UnansweredItemSchema,
    SatisfactionSchema,
    TagCountSchema,
)

router = APIRouter(tags=["数据报表"])


@router.get("/debug-subquery")
async def debug_subquery(
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_admin),
):
    sql = text("""
        SELECT
            DATE(c.created_at) AS day,
            COUNT(*) AS cnt
        FROM conversations c
        WHERE DATE(c.created_at) BETWEEN '2026-05-01' AND '2026-05-15'
        GROUP BY DATE(c.created_at)
        ORDER BY day
    """)
    res = await db.execute(sql)
    rows = res.fetchall()
    return success_response(data=[dict(r._mapping) for r in rows])


# ==================== 工具函数 ====================


def parse_dates(start_date: Optional[str], end_date: Optional[str]):
    """解析日期范围，默认近14天，返回 (date, date)"""
    if end_date:
        end = date.fromisoformat(end_date)
    else:
        end = date.today()

    if start_date:
        start = date.fromisoformat(start_date)
    else:
        start = end - timedelta(days=13)

    return start, end


def parse_date_range(start_date: Optional[str], end_date: Optional[str]):
    """解析日期范围，返回 (start_str, end_str)，用于 SQL 插桩"""
    start, end = parse_dates(start_date, end_date)
    return start.isoformat(), end.isoformat()


def date_range_list(start: date, end: date) -> List[str]:
    """生成连续日期列表"""
    days = (end - start).days + 1
    return [(start + timedelta(days=i)).isoformat() for i in range(days)]


# ==================== 10.1 核心指标概览 ====================


@router.get("/dashboard")
async def get_dashboard(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_admin),
):
    start, end = parse_dates(start_date, end_date)
    start_str, end_str = start.isoformat(), end.isoformat()
    today = date.today()
    yesterday = today - timedelta(days=1)
    today_str = today.isoformat()
    yesterday_str = yesterday.isoformat()

    # ── 日期范围内总会话数 ──
    total_sql = text(f"""
        SELECT COUNT(*) AS cnt
        FROM conversations
        WHERE DATE(created_at) BETWEEN '{start_str}' AND '{end_str}'
    """)
    total_res = await db.execute(total_sql)
    total_sessions = total_res.scalar() or 0

    # ── 今日会话数 ──
    today_sql = text(f"""
        SELECT COUNT(*) AS cnt
        FROM conversations
        WHERE DATE(created_at) = '{today_str}'
    """)
    today_res = await db.execute(today_sql)
    today_sessions = today_res.scalar() or 0

    # ── 昨日会话数（用于对比）──
    yest_sql = text(f"""
        SELECT COUNT(*) AS cnt
        FROM conversations
        WHERE DATE(created_at) = '{yesterday_str}'
    """)
    yest_res = await db.execute(yest_sql)
    yesterday_sessions = yest_res.scalar() or 0
    compared_yesterday = today_sessions - yesterday_sessions

    # ── AI 解决率 / 转人工率 ──
    resolve_sql = text(f"""
        SELECT
            COUNT(*) FILTER (WHERE status = 'closed')      AS closed_cnt,
            COUNT(*) FILTER (WHERE status = 'transferred') AS transfer_cnt,
            COUNT(*)                                        AS total_cnt
        FROM conversations
        WHERE DATE(created_at) BETWEEN '{start_str}' AND '{end_str}'
    """)
    resolve_res = await db.execute(resolve_sql)
    row = resolve_res.fetchone()

    closed_cnt = row.closed_cnt or 0
    transfer_cnt = row.transfer_cnt or 0
    total_cnt = row.total_cnt or 1  # 防除零

    ai_resolve_rate = round(closed_cnt / total_cnt, 4)
    transfer_rate = round(transfer_cnt / total_cnt, 4)

    # ── 平均响应时长（毫秒）──
    avg_ms_sql = text(f"""
        SELECT ROUND(AVG(response_ms)) AS avg_ms
        FROM ai_conversation_details
        WHERE DATE(created_at) BETWEEN '{start_str}' AND '{end_str}'
          AND response_ms IS NOT NULL
    """)
    try:
        avg_ms_res = await db.execute(avg_ms_sql)
        avg_response_ms = avg_ms_res.scalar()
    except Exception:
        avg_response_ms = None

    # ── 满意度均分（字段：eval_score）──
    sat_sql = text(f"""
        SELECT ROUND(AVG(eval_score)::numeric, 1) AS avg_score
        FROM conversations
        WHERE DATE(created_at) BETWEEN '{start_str}' AND '{end_str}'
          AND eval_score IS NOT NULL
    """)
    sat_res = await db.execute(sat_sql)
    satisfaction_score = sat_res.scalar()

    data = DashboardSchema(
        total_sessions=total_sessions,
        today_sessions=today_sessions,
        compared_yesterday=compared_yesterday,
        ai_resolve_rate=ai_resolve_rate,
        transfer_rate=transfer_rate,
        avg_response_ms=float(avg_response_ms) if avg_response_ms else None,
        satisfaction_score=float(satisfaction_score) if satisfaction_score else None,
    )
    return success_response(data=data.model_dump())


# ==================== 10.2 会话量趋势 ====================


@router.get("/sessions")
async def get_sessions_trend(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_admin),
):
    start, end = parse_dates(start_date, end_date)
    start_str, end_str = start.isoformat(), end.isoformat()
    dates = date_range_list(start, end)

    conv_sql = text(f"""
        SELECT
            DATE(created_at) AS day,
            COUNT(*) FILTER (WHERE current_mode = 0 AND is_transferred = 0) AS bot_cnt,
            COUNT(*) FILTER (WHERE current_mode = 1 AND is_transferred = 0) AS agent_cnt,
            COUNT(*) FILTER (WHERE is_transferred = 1) AS human_cnt
        FROM conversations
        WHERE DATE(created_at) BETWEEN '{start_str}' AND '{end_str}'
        GROUP BY DATE(created_at)
        ORDER BY day
    """)
    conv_res = await db.execute(conv_sql)
    conv_rows = conv_res.fetchall()

    day_data = {}
    for _r in conv_rows:
        row_dict = dict(_r._mapping)
        day_data[str(row_dict["day"])] = row_dict

    bot_sessions = []
    agent_sessions = []
    human_sessions = []

    for d in dates:
        r = day_data.get(d)
        bot_sessions.append(r["bot_cnt"] if r else 0)
        agent_sessions.append(r["agent_cnt"] if r else 0)
        human_sessions.append(r["human_cnt"] if r else 0)

    data = {
        "dates": dates,
        "bot_sessions": bot_sessions,
        "agent_sessions": agent_sessions,
        "human_sessions": human_sessions,
    }
    return success_response(data=data)


# ==================== 10.3 解决率趋势 ====================


@router.get("/resolve-rate")
async def get_resolve_rate(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_admin),
):
    start, end = parse_dates(start_date, end_date)
    start_str, end_str = start.isoformat(), end.isoformat()
    dates = date_range_list(start, end)

    # 基础统计：每日会话总量 + closed 数量，并按 Bot/Agent 分层统计
    stat_sql = text(f"""
        SELECT
            DATE(created_at) AS day,
            COUNT(*)         AS total,
            COUNT(*) FILTER (WHERE status = 'closed') AS resolved,
            COUNT(*) FILTER (WHERE current_mode = 0 AND is_transferred = 0) AS bot_total,
            COUNT(*) FILTER (WHERE current_mode = 0 AND is_transferred = 0 AND status = 'closed') AS bot_resolved,
            COUNT(*) FILTER (WHERE current_mode = 1 AND is_transferred = 0) AS agent_total,
            COUNT(*) FILTER (WHERE current_mode = 1 AND is_transferred = 0 AND status = 'closed') AS agent_resolved
        FROM conversations
        WHERE DATE(created_at) BETWEEN '{start_str}' AND '{end_str}'
        GROUP BY DATE(created_at)
        ORDER BY day
    """)
    stat_res = await db.execute(stat_sql)
    stat_rows = stat_res.fetchall()

    day_data = {}
    for _r in stat_rows:
        rd = dict(_r._mapping)
        day_data[str(rd["day"])] = rd

    bot_resolve_rate = []
    agent_resolve_rate = []
    overall_resolve_rate = []

    for d in dates:
        r = day_data.get(d)
        if r:
            total = r["total"] or 1
            overall = round(r["resolved"] / total, 4)
            bot_rate = round(r["bot_resolved"] / r["bot_total"], 4) if r["bot_total"] else 0.0
            agent_rate = round(r["agent_resolved"] / r["agent_total"], 4) if r["agent_total"] else 0.0
        else:
            overall = 0.0
            bot_rate = 0.0
            agent_rate = 0.0
        bot_resolve_rate.append(bot_rate)
        agent_resolve_rate.append(agent_rate)
        overall_resolve_rate.append(overall)

    data = ResolveRateTrendSchema(
        dates=dates,
        bot_resolve_rate=bot_resolve_rate,
        agent_resolve_rate=agent_resolve_rate,
        overall_resolve_rate=overall_resolve_rate,
    )
    return success_response(data=data.model_dump())


# ==================== 10.5 意图分布统计 ====================


@router.get("/intent-distribution")
async def get_intent_distribution(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_admin),
):
    start_str, end_str = parse_date_range(start_date, end_date)

    sql = text(f"""
        SELECT
            extra->>'intent' AS intent,
            COUNT(*)          AS cnt
        FROM messages
        WHERE sender_type = 1
          AND extra->>'intent' IS NOT NULL
          AND DATE(created_at) BETWEEN '{start_str}' AND '{end_str}'
        GROUP BY extra->>'intent'
        ORDER BY cnt DESC
    """)
    res = await db.execute(sql)
    rows = res.fetchall()
    total = sum(r.cnt for r in rows) or 1

    data = [
        IntentItemSchema(
            intent=r.intent,
            count=r.cnt,
            rate=round(r.cnt / total, 4),
        ).model_dump()
        for r in rows
    ]
    return success_response(data=data)


# ==================== 10.4 Top 未解决问题 ====================


@router.get("/top-unanswered")
async def get_top_unanswered(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_admin),
):
    start_str, end_str = parse_date_range(start_date, end_date)

    # 先找出所有 answer_source='default' 的 bot 消息，取其上一条用户消息
    sql = text(f"""
        WITH bot_default_msgs AS (
            SELECT
                conversation_id,
                content,
                created_at,
                LAG(content)  OVER w AS prev_user_msg,
                LAG(sender_type) OVER w AS prev_sender_type,
                LAG(created_at) OVER w AS prev_created_at
            FROM messages
            WHERE sender_type = 1
              AND extra->>'answer_source' = 'default'
              AND DATE(created_at) BETWEEN '{start_str}' AND '{end_str}'
            WINDOW w AS (PARTITION BY conversation_id ORDER BY created_at)
        )
        SELECT prev_user_msg AS question, COUNT(*) AS cnt
        FROM bot_default_msgs
        WHERE prev_user_msg IS NOT NULL
          AND prev_sender_type = 0
        GROUP BY prev_user_msg
        ORDER BY cnt DESC
        LIMIT {limit}
    """)
    res = await db.execute(sql)
    rows = res.fetchall()

    data = [
        UnansweredItemSchema(
            question=dict(r._mapping)["question"],
            count=dict(r._mapping)["cnt"],
        ).model_dump()
        for r in rows
    ]
    return success_response(data=data)


# ==================== 10.6 满意度统计 ====================


@router.get("/satisfaction")
async def get_satisfaction(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_admin),
):
    start_str, end_str = parse_date_range(start_date, end_date)

    # ── 均分 + 总评价数（字段：eval_score）──
    base_sql = text(f"""
        SELECT
            ROUND(AVG(eval_score)::numeric, 1) AS avg_score,
            COUNT(*)                            AS total_evaluations
        FROM conversations
        WHERE DATE(created_at) BETWEEN '{start_str}' AND '{end_str}'
          AND eval_score IS NOT NULL
    """)
    base_res = await db.execute(base_sql)
    base_row = base_res.fetchone()

    avg_score = float(base_row.avg_score) if base_row.avg_score else 0.0
    total_evaluations = (
        int(base_row.total_evaluations) if base_row.total_evaluations else 0
    )

    # ── 评分分布（字段：eval_score）──
    dist_sql = text(f"""
        SELECT
            eval_score::int AS star,
            COUNT(*)        AS cnt
        FROM conversations
        WHERE DATE(created_at) BETWEEN '{start_str}' AND '{end_str}'
          AND eval_score IS NOT NULL
        GROUP BY eval_score::int
        ORDER BY star DESC
    """)
    dist_res = await db.execute(dist_sql)
    dist_rows = dist_res.fetchall()
    score_distribution = {str(r.star): r.cnt for r in dist_rows}

    # 补全 1-5 缺失星级
    for star in range(1, 6):
        score_distribution.setdefault(str(star), 0)

    # ── Top 标签（字段：eval_tags，JSONB 数组）──
    tag_sql = text(f"""
        SELECT
            tag_elem AS tag,
            COUNT(*) AS cnt
        FROM conversations,
             jsonb_array_elements_text(eval_tags) AS tag_elem
        WHERE DATE(created_at) BETWEEN '{start_str}' AND '{end_str}'
          AND eval_tags IS NOT NULL
          AND jsonb_array_length(eval_tags) > 0
        GROUP BY tag_elem
        ORDER BY cnt DESC
        LIMIT 10
    """)
    try:
        tag_res = await db.execute(tag_sql)
        tag_rows = tag_res.fetchall()
        top_tags = [
            TagCountSchema(tag=r.tag, count=r.cnt).model_dump() for r in tag_rows
        ]
    except Exception:
        top_tags = []

    data = SatisfactionSchema(
        avg_score=avg_score,
        total_evaluations=total_evaluations,
        score_distribution=score_distribution,
        top_tags=top_tags,
    )
    return success_response(data=data.model_dump())
