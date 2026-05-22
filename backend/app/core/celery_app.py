from celery import Celery
from celery.schedules import crontab
from app.config import settings

# ==================== 创建 Celery 实例 ====================
celery_app = Celery(
    "lingxi_tasks",
    broker=f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/1",
    backend=f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/2",
    include=[
        "app.tasks.statistics",
        "app.tasks.conversation",
    ],
)

# ==================== Celery 基础配置 ====================
celery_app.conf.update(
    # 时区配置
    timezone="Asia/Shanghai",
    enable_utc=True,
    # 序列化配置
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    # 任务结果过期时间（1天）
    result_expires=86400,
    # 任务超时配置
    task_soft_time_limit=300,  # 软超时 5 分钟
    task_time_limit=600,  # 硬超时 10 分钟
    # Worker 并发数
    worker_concurrency=4,
    # 任务重试配置
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    # 失败任务最大重试次数
    task_max_retries=3,
    task_default_retry_delay=60,  # 重试间隔 60 秒
)

# ==================== 定时任务配置（Beat 调度）====================
celery_app.conf.beat_schedule = {
    # ── 每日统计：每天 00:05 生成昨日统计数据 ──
    "daily-statistics-task": {
        "task": "app.tasks.statistics.generate_daily_statistics",
        "schedule": crontab(hour=0, minute=5),
        "args": (),
    },
    # ── 会话超时检查：每 1 分钟执行一次 ──
    "session-timeout-check": {
        "task": "app.tasks.conversation.close_timeout_sessions",
        "schedule": 60.0,  # 每 60 秒
        "args": (),
    },
    # ── 评价卡片推送：每 30 秒检查一次 ──
    "evaluate-card-push": {
        "task": "app.tasks.conversation.push_evaluate_cards",
        "schedule": 30.0,  # 每 30 秒
        "args": (),
    },
    # ── 人工状态超时重置：每 30 秒检查一次 ──
    "reset-transfer-timeout": {
        "task": "app.tasks.conversation.reset_transfer_timeout",
        "schedule": 30.0,  # 每 30 秒
        "args": (),
    },
}
