import json
import logging
from datetime import date, timedelta, datetime

from sqlalchemy import text

from app.core.celery_app import celery_app
from app.core.database import SyncSessionLocal

logger = logging.getLogger(__name__)


# ==================== 每日统计任务 ====================

@celery_app.task(
    name="app.tasks.statistics.generate_daily_statistics",
    bind=True,
    max_retries=3,
    default_retry_delay=300,
)
def generate_daily_statistics(self, target_date: str = None):
    """
    生成每日统计数据，写入 daily_statistics 表
    策略：
      - 先按各渠道分别写入（channel_id > 0）
      - 再写入全渠道汇总行（channel_id = 0）
    UPSERT 唯一键：(stat_date, channel_id)
    每天 00:05 由 Celery Beat 自动触发
    """
    stat_date = (
        date.fromisoformat(target_date)
        if target_date
        else date.today() - timedelta(days=1)
    )
    logger.info(f"[Statistics] 开始生成 {stat_date} 的统计数据")

    try:
        with SyncSessionLocal() as db:

            # ── Step 1：获取当天有会话的所有渠道 ID ──
            channel_ids_sql = text("""
                SELECT DISTINCT channel_id
                FROM conversations
                WHERE DATE(created_at) = :stat_date
                ORDER BY channel_id
            """)
            channel_rows = db.execute(
                channel_ids_sql, {"stat_date": stat_date}
            ).fetchall()
            channel_ids = [r.channel_id for r in channel_rows]

            logger.info(f"[Statistics] {stat_date} 涉及渠道：{channel_ids}")

            # ── Step 2：按渠道逐条写入 ──
            for cid in channel_ids:
                _upsert_stat_row(db, stat_date, channel_id=cid)

            # ── Step 3：写入 channel_id=0 全渠道汇总行 ──
            _upsert_stat_row(db, stat_date, channel_id=0)

            db.commit()

            logger.info(
                f"[Statistics] {stat_date} 统计完成，"
                f"共处理渠道 {len(channel_ids)} 个 + 全渠道汇总"
            )
            return {
                "stat_date":   str(stat_date),
                "channel_ids": channel_ids,
                "total":       len(channel_ids) + 1,
            }

    except Exception as exc:
        logger.error(
            f"[Statistics] {stat_date} 统计失败：{exc}",
            exc_info=True
        )
        raise self.retry(exc=exc)


def _upsert_stat_row(db, stat_date: date, channel_id: int):
    """
    计算并 UPSERT 一条统计记录
    channel_id=0 → 全渠道汇总（不加 channel_id 过滤）
    channel_id>0 → 指定渠道统计
    """
    # 构建渠道过滤条件（conversations 表用）
    channel_filter_c = (
        "AND c.channel_id = :channel_id"
        if channel_id > 0
        else ""
    )
    # conversations 表直接过滤（无别名）
    channel_filter_plain = (
        "AND channel_id = :channel_id"
        if channel_id > 0
        else ""
    )

    params_base = {"stat_date": stat_date, "channel_id": channel_id}

    # ── 1. 会话量统计 ──────────────────────────────────
    session_sql = text(f"""
        SELECT
            COUNT(*)
                FILTER (WHERE status = 'closed')      AS resolved_sessions,
            COUNT(*)
                FILTER (WHERE status = 'transferred') AS transferred_sessions,
            COUNT(*)                                   AS total_sessions
        FROM conversations
        WHERE DATE(created_at) = :stat_date
        {channel_filter_plain}
    """)
    s = db.execute(session_sql, params_base).fetchone()

    total_sessions       = s.total_sessions       or 0
    resolved_sessions    = s.resolved_sessions    or 0
    transferred_sessions = s.transferred_sessions or 0

    resolve_rate  = round(resolved_sessions    / total_sessions, 4) \
                    if total_sessions > 0 else 0.0
    transfer_rate = round(transferred_sessions / total_sessions, 4) \
                    if total_sessions > 0 else 0.0

    # ── 2. Bot / Agent 会话量细分 ──────────────────────
    # ✅ 修复问题1：messages.sender_type 替代 role
    # sender_type = 1 → Bot，sender_type = 0 → User
    split_sql = text(f"""
        SELECT
            COUNT(*) FILTER (
                WHERE m.extra->>'answer_source' IN ('rag', 'keyword')
            )                AS bot_sessions,
            COUNT(*) FILTER (
                WHERE m.extra->>'answer_source' IN ('tool', 'llm', 'default')
                  AND c.status != 'transferred'
            )                AS agent_sessions
        FROM conversations c
        LEFT JOIN LATERAL (
            SELECT extra
            FROM messages
            WHERE conversation_id = c.id
              AND sender_type = 1
            ORDER BY created_at DESC
            LIMIT 1
        ) m ON TRUE
        WHERE DATE(c.created_at) = :stat_date
        {channel_filter_c}
    """)
    sp = db.execute(split_sql, params_base).fetchone()
    bot_sessions   = sp.bot_sessions   or 0
    agent_sessions = sp.agent_sessions or 0

    # ── 3. 平均响应时长（毫秒）──────────────────────────
    avg_ms_sql = text(f"""
        SELECT ROUND(AVG(d.response_ms)) AS avg_ms
        FROM ai_conversation_details d
        JOIN conversations c ON c.id = d.conversation_id
        WHERE DATE(c.created_at) = :stat_date
          AND d.response_ms IS NOT NULL
        {channel_filter_c}
    """)
    avg_ms_row      = db.execute(avg_ms_sql, params_base).fetchone()
    avg_response_ms = float(avg_ms_row.avg_ms) if avg_ms_row.avg_ms else None

    # ── 4. 平均对话轮次 ────────────────────────────────
    # ✅ 修复问题1：sender_type = 0 替代 role = 'user'
    round_sql = text(f"""
        SELECT ROUND(AVG(msg_count)::numeric, 1) AS avg_round
        FROM (
            SELECT
                c.id,
                COUNT(m.id) FILTER (
                    WHERE m.sender_type = 0
                ) AS msg_count
            FROM conversations c
            JOIN messages m ON m.conversation_id = c.id
            WHERE DATE(c.created_at) = :stat_date
            {channel_filter_c}
            GROUP BY c.id
        ) t
    """)
    round_row       = db.execute(round_sql, params_base).fetchone()
    avg_round_count = float(round_row.avg_round) if round_row.avg_round else None

    # ── 5. 平均会话时长 ────────────────────────────────
    # ✅ 修复问题3：conversations 无 closed_at，改用 updated_at 估算
    # 只统计 status=closed 的会话，updated_at 近似为结束时间
    duration_sql = text(f"""
        SELECT ROUND(AVG(
            EXTRACT(EPOCH FROM (updated_at - created_at))
        ))::int AS avg_dur
        FROM conversations
        WHERE DATE(created_at) = :stat_date
          AND status = 'closed'
          AND updated_at > created_at
        {channel_filter_plain}
    """)
    dur_row      = db.execute(duration_sql, params_base).fetchone()
    avg_duration = int(dur_row.avg_dur) if dur_row.avg_dur else None

    # ── 6. 高峰小时 ────────────────────────────────────
    peak_sql = text(f"""
        SELECT
            EXTRACT(HOUR FROM created_at)::int AS hour,
            COUNT(*)                            AS cnt
        FROM conversations
        WHERE DATE(created_at) = :stat_date
        {channel_filter_plain}
        GROUP BY EXTRACT(HOUR FROM created_at)
        ORDER BY cnt DESC
        LIMIT 1
    """)
    peak_row           = db.execute(peak_sql, params_base).fetchone()
    peak_hour          = int(peak_row.hour) if peak_row else None
    peak_session_count = int(peak_row.cnt)  if peak_row else None

    # ── 7. 未解决数量（兜底回复数）────────────────────
    # ✅ 修复问题2：sender_type = 1 替代 role = 'bot'
    no_answer_sql = text(f"""
        SELECT COUNT(*) AS no_answer_cnt
        FROM messages m
        JOIN conversations c ON c.id = m.conversation_id
        WHERE m.sender_type = 1
          AND m.extra->>'answer_source' = 'default'
          AND DATE(c.created_at) = :stat_date
        {channel_filter_c}
    """)
    no_answer_row   = db.execute(no_answer_sql, params_base).fetchone()
    no_answer_count = int(no_answer_row.no_answer_cnt) if no_answer_row else 0

    # ── 8. Top 未解决问题（JSONB）─────────────────────
    # ✅ 修复问题2：
    #   bot_msg.sender_type = 1 替代 bot_msg.role = 'bot'
    #   user msg: sender_type = 0 替代 role = 'user'
    top_no_answer_sql = text(f"""
        SELECT
            user_msg.content AS question,
            COUNT(*)         AS cnt
        FROM messages bot_msg
        JOIN conversations c ON c.id = bot_msg.conversation_id
        JOIN LATERAL (
            SELECT content
            FROM messages
            WHERE conversation_id = bot_msg.conversation_id
              AND sender_type = 0
              AND created_at < bot_msg.created_at
            ORDER BY created_at DESC
            LIMIT 1
        ) user_msg ON TRUE
        WHERE bot_msg.sender_type = 1
          AND bot_msg.extra->>'answer_source' = 'default'
          AND DATE(c.created_at) = :stat_date
        {channel_filter_c}
        GROUP BY user_msg.content
        ORDER BY cnt DESC
        LIMIT 10
    """)
    top_rows      = db.execute(top_no_answer_sql, params_base).fetchall()
    top_no_answer = [
        {"question": r.question, "count": r.cnt}
        for r in top_rows
    ]

    # ── 9. 满意度统计 ──────────────────────────────────
    eval_sql = text(f"""
        SELECT
            ROUND(AVG(eval_score)::numeric, 2)         AS avg_score,
            COUNT(*) FILTER (WHERE eval_score IS NOT NULL) AS eval_count
        FROM conversations
        WHERE DATE(created_at) = :stat_date
        {channel_filter_plain}
    """)
    eval_row       = db.execute(eval_sql, params_base).fetchone()
    avg_eval_score = float(eval_row.avg_score) if eval_row.avg_score else None
    eval_count     = int(eval_row.eval_count)  if eval_row.eval_count else 0

    # ── 10. 意图分布（额外字段）───────────────────────
    # ✅ sender_type = 1 替代 role = 'bot'
    intent_sql = text(f"""
        SELECT
            m.extra->>'intent' AS intent,
            COUNT(*)            AS cnt
        FROM messages m
        JOIN conversations c ON c.id = m.conversation_id
        WHERE m.sender_type = 1
          AND m.extra->>'intent' IS NOT NULL
          AND DATE(c.created_at) = :stat_date
        {channel_filter_c}
        GROUP BY m.extra->>'intent'
        ORDER BY cnt DESC
    """)
    intent_rows         = db.execute(intent_sql, params_base).fetchall()
    intent_distribution = {r.intent: r.cnt for r in intent_rows}

    # ── 11. 回答来源分布（额外字段）──────────────────
    # ✅ sender_type = 1 替代 role = 'bot'
    source_sql = text(f"""
        SELECT
            m.extra->>'answer_source' AS source,
            COUNT(*)                   AS cnt
        FROM messages m
        JOIN conversations c ON c.id = m.conversation_id
        WHERE m.sender_type = 1
          AND m.extra->>'answer_source' IS NOT NULL
          AND DATE(c.created_at) = :stat_date
        {channel_filter_c}
        GROUP BY m.extra->>'answer_source'
    """)
    source_rows         = db.execute(source_sql, params_base).fetchall()
    source_distribution = {r.source: r.cnt for r in source_rows}

    # ── 12. UPSERT 写入（字段名与实际表对齐）─────────
    upsert_sql = text("""
        INSERT INTO daily_statistics (
            stat_date,
            channel_id,
            total_sessions,
            bot_sessions,
            agent_sessions,
            transferred_sessions,
            resolved_sessions,
            resolve_rate,
            transfer_rate,
            avg_round_count,
            avg_duration,
            avg_response_ms,
            peak_hour,
            peak_session_count,
            no_answer_count,
            top_no_answer,
            eval_count,
            avg_eval_score,
            intent_distribution,
            source_distribution,
            created_at,
            updated_at
        ) VALUES (
            :stat_date,
            :channel_id,
            :total_sessions,
            :bot_sessions,
            :agent_sessions,
            :transferred_sessions,
            :resolved_sessions,
            :resolve_rate,
            :transfer_rate,
            :avg_round_count,
            :avg_duration,
            :avg_response_ms,
            :peak_hour,
            :peak_session_count,
            :no_answer_count,
            :top_no_answer,
            :eval_count,
            :avg_eval_score,
            :intent_distribution,
            :source_distribution,
            NOW(),
            NOW()
        )
        ON CONFLICT (stat_date, channel_id)
        DO UPDATE SET
            total_sessions       = EXCLUDED.total_sessions,
            bot_sessions         = EXCLUDED.bot_sessions,
            agent_sessions       = EXCLUDED.agent_sessions,
            transferred_sessions = EXCLUDED.transferred_sessions,
            resolved_sessions    = EXCLUDED.resolved_sessions,
            resolve_rate         = EXCLUDED.resolve_rate,
            transfer_rate        = EXCLUDED.transfer_rate,
            avg_round_count      = EXCLUDED.avg_round_count,
            avg_duration         = EXCLUDED.avg_duration,
            avg_response_ms      = EXCLUDED.avg_response_ms,
            peak_hour            = EXCLUDED.peak_hour,
            peak_session_count   = EXCLUDED.peak_session_count,
            no_answer_count      = EXCLUDED.no_answer_count,
            top_no_answer        = EXCLUDED.top_no_answer,
            eval_count           = EXCLUDED.eval_count,
            avg_eval_score       = EXCLUDED.avg_eval_score,
            intent_distribution  = EXCLUDED.intent_distribution,
            source_distribution  = EXCLUDED.source_distribution,
            updated_at           = NOW()
    """)

    db.execute(upsert_sql, {
        "stat_date":            str(stat_date),
        "channel_id":           channel_id,
        "total_sessions":       total_sessions,
        "bot_sessions":         bot_sessions,
        "agent_sessions":       agent_sessions,
        "transferred_sessions": transferred_sessions,
        "resolved_sessions":    resolved_sessions,
        "resolve_rate":         resolve_rate,
        "transfer_rate":        transfer_rate,
        "avg_round_count":      avg_round_count,
        "avg_duration":         avg_duration,
        "avg_response_ms":      avg_response_ms,
        "peak_hour":            peak_hour,
        "peak_session_count":   peak_session_count,
        "no_answer_count":      no_answer_count,
        "top_no_answer":        json.dumps(top_no_answer, ensure_ascii=False),
        "eval_count":           eval_count,
        "avg_eval_score":       avg_eval_score,
        "intent_distribution":  json.dumps(intent_distribution, ensure_ascii=False),
        "source_distribution":  json.dumps(source_distribution, ensure_ascii=False),
    })

    tag = "全渠道" if channel_id == 0 else f"渠道{channel_id}"
    logger.info(
        f"[Statistics] {stat_date} [{tag}] "
        f"总会话={total_sessions} "
        f"解决率={resolve_rate:.1%} "
        f"转人工率={transfer_rate:.1%}"
    )