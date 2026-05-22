import logging
import json
from datetime import datetime, timedelta

from sqlalchemy import text

from app.core.celery_app import celery_app
from app.core.database import SyncSessionLocal

logger = logging.getLogger(__name__)


# ==================== 会话超时自动关闭 ====================


@celery_app.task(
    name="app.tasks.conversation.close_timeout_sessions",
    bind=True,
)
def close_timeout_sessions(self):
    """
    检查并关闭超时会话
    超时规则：status='active' 且 updated_at 距今超过 5 分钟
    每 60 秒由 Celery Beat 触发一次
    """
    timeout_minutes = 5
    cutoff_time = datetime.utcnow() - timedelta(minutes=timeout_minutes)

    try:
        with SyncSessionLocal() as db:
            # 查找超时的 active 会话
            find_sql = text("""
                SELECT id
                FROM conversations
                WHERE status     = 'active'
                  AND updated_at < :cutoff
                LIMIT 100
            """)
            rows = db.execute(find_sql, {"cutoff": cutoff_time}).fetchall()
            timeout_ids = [r.id for r in rows]

            if not timeout_ids:
                return {"closed": 0}

            # 批量更新为 closed
            close_sql = text("""
                UPDATE conversations
                SET
                    status     = 'closed',
                    updated_at = NOW()
                WHERE id = ANY(:ids)
            """)
            db.execute(close_sql, {"ids": timeout_ids})
            db.commit()

            logger.info(
                f"[SessionTimeout] 关闭超时会话 {len(timeout_ids)} 个："
                f"{timeout_ids[:10]}{'...' if len(timeout_ids) > 10 else ''}"
            )
            return {"closed": len(timeout_ids)}

    except Exception as exc:
        logger.error(f"[SessionTimeout] 关闭超时会话失败：{exc}", exc_info=True)
        raise self.retry(exc=exc, countdown=30)


# ==================== 评价卡片定时推送 ====================


@celery_app.task(
    name="app.tasks.conversation.push_evaluate_cards",
    bind=True,
)
def push_evaluate_cards(self):
    """
    检查已结束会话，定时推送评价卡片
    推送规则：
      - status = 'closed'
      - eval_score IS NULL（未评价）
      - closed_at 距今超过 30 秒（evaluate_delay）
      - eval_pushed_at IS NULL（未推送过）
    每 30 秒由 Celery Beat 触发一次
    """
    evaluate_delay_seconds = 30
    cutoff_time = datetime.utcnow() - timedelta(seconds=evaluate_delay_seconds)

    try:
        with SyncSessionLocal() as db:
            # 查找需要推送评价卡片的会话
            find_sql = text("""
                SELECT
                    c.id,
                    c.user_id,
                    ch.channel_token
                FROM conversations c
                JOIN channels ch ON ch.id = c.channel_id
                WHERE c.status          = 'closed'
                  AND c.eval_score      IS NULL
                  AND c.eval_pushed_at  IS NULL
                  AND c.updated_at   < :cutoff
                LIMIT 50
            """)
            rows = db.execute(find_sql, {"cutoff": cutoff_time}).fetchall()

            if not rows:
                return {"pushed": 0}

            pushed_count = 0
            for row in rows:
                try:
                    # 通过 Redis 发布评价卡片消息
                    # WebSocket handler 订阅此频道后推送给用户
                    _publish_evaluate_card(
                        conversation_id=row.id,
                        user_id=row.user_id,
                        channel_token=row.channel_token,
                    )

                    # 标记已推送
                    mark_sql = text("""
                        UPDATE conversations
                        SET eval_pushed_at = NOW(),
                            updated_at     = NOW()
                        WHERE id = :conv_id
                    """)
                    db.execute(mark_sql, {"conv_id": row.id})
                    pushed_count += 1

                except Exception as e:
                    logger.warning(f"[EvaluateCard] 推送会话 {row.id} 失败：{e}")
                    continue

            db.commit()

            if pushed_count:
                logger.info(f"[EvaluateCard] 推送评价卡片 {pushed_count} 条")

            return {"pushed": pushed_count}

    except Exception as exc:
        logger.error(f"[EvaluateCard] 定时推送失败：{exc}", exc_info=True)
        raise self.retry(exc=exc, countdown=15)


def _publish_evaluate_card(conversation_id: int, user_id: int, channel_token: str):
    """
    通过 Redis Pub/Sub 发布评价卡片消息
    WebSocket 连接层订阅此频道后，将消息推送给指定用户
    """
    import redis
    from app.config import settings

    r = redis.Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        db=0,
        password=settings.REDIS_PASSWORD or None,
        decode_responses=True,
    )

    # 评价卡片消息格式（与 WebSocket 推送格式保持一致）[2]
    message = {
        "type": "message",
        "role": "bot",
        "content": "本次服务已结束，请对本次服务进行评价",
        "conversation_id": conversation_id,
        "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
        "extra": {
            "card_type": "evaluate",
            "card_data": {
                "conversation_id": conversation_id,
            },
        },
    }

    # 发布到 Redis 频道：ws:{channel_token}:{user_id}
    channel = f"ws:{channel_token}:{user_id}"
    r.publish(channel, json.dumps(message, ensure_ascii=False))

    logger.debug(
        f"[EvaluateCard] 发布到频道 {channel}，conversation_id={conversation_id}"
    )


# ==================== 人工状态超时重置 ====================


@celery_app.task(
    name="app.tasks.conversation.reset_transfer_timeout",
    bind=True,
)
def reset_transfer_timeout(self):
    """
    检查人工状态超时的会话
    规则：status='transferred' 且超过 1 分钟没有新消息
    超时后：重置为 active（智能客服模式），清除 staff_name
    每 30 秒由 Celery Beat 触发一次
    """
    timeout_seconds = 60
    cutoff_time = datetime.utcnow() - timedelta(seconds=timeout_seconds)

    try:
        with SyncSessionLocal() as db:
            find_sql = text("""
                SELECT c.id
                FROM conversations c
                WHERE c.status = 'transferred'
                  AND (
                      (
                          SELECT MAX(created_at)
                          FROM messages
                          WHERE conversation_id = c.id
                      ) < :cutoff
                      OR
                      (
                          SELECT COUNT(*) FROM messages
                          WHERE conversation_id = c.id
                      ) = 0
                  )
                LIMIT 100
            """)
            rows = db.execute(find_sql, {"cutoff": cutoff_time}).fetchall()
            timeout_ids = [r.id for r in rows]

            if not timeout_ids:
                return {"reset": 0}

            reset_sql = text("""
                UPDATE conversations
                SET
                    status         = 'active',
                    is_transferred = FALSE,
                    staff_name     = NULL,
                    updated_at     = NOW()
                WHERE id = ANY(:ids)
            """)
            db.execute(reset_sql, {"ids": timeout_ids})
            db.commit()

            logger.info(
                f"[TransferTimeout] 重置人工超时会话 "
                f"{len(timeout_ids)} 个：{timeout_ids[:10]}"
            )
            return {"reset": len(timeout_ids)}

    except Exception as exc:
        logger.error(f"[TransferTimeout] 重置失败：{exc}", exc_info=True)
        raise self.retry(exc=exc, countdown=15)
