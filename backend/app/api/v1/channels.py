# backend/app/api/v1/channels.py
import json
import logging
from datetime import date
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_admin_id
from app.crud.channel import crud_channel
from app.crud.agent import crud_agent
from app.schemas.channel import (
    ChannelCreate,
    ChannelUpdate,
    ChannelOut,
    ChannelTokenOut,
)
from app.utils.response import Response
from app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()

CHANNEL_TYPE_TEXT = {0: "测试渠道", 1: "正式渠道"}


# ==================== 辅助函数 ====================


def _build_ws_url(channel_token: str) -> str:
    """构建WebSocket地址"""
    host = getattr(settings, "SERVER_HOST", "localhost")
    port = getattr(settings, "SERVER_PORT", 8000)
    return f"ws://{host}:{port}/api/v1/chat/ws/{channel_token}"


def _channel_to_out(channel, agent_name: str = None) -> ChannelOut:
    """Channel模型 → ChannelOut Schema"""
    return ChannelOut(
        id=channel.id,
        name=channel.name,
        channel_type=channel.type,  # ✅ type → channel_type
        channel_type_text=CHANNEL_TYPE_TEXT.get(channel.type),
        channel_token=channel.channel_token,
        agent_id=channel.agent_id,
        agent_name=agent_name,
        bot_id=getattr(channel, "bot_id", None),
        bot_name=None,
        description=channel.description,
        status=channel.status,
        created_at=channel.created_at,
        updated_at=channel.updated_at,
    )


# ==================== 渠道管理接口 ====================


@router.get("", summary="获取渠道列表")
async def list_channels(
    db: AsyncSession = Depends(get_db),
    admin_id: int = Depends(get_current_admin_id),
):
    today = date.today().isoformat()

    # 用单条 SQL 一次性查出渠道 + 今日会话数 + 累计会话数
    sql = text("""
        SELECT
            c.id,
            COUNT(*) FILTER (WHERE DATE(cv.created_at) = CURRENT_DATE) AS today_sessions,
            COUNT(*) AS total_sessions
        FROM channels c
        LEFT JOIN conversations cv ON cv.channel_id = c.id
        GROUP BY c.id
    """)
    stats_res = await db.execute(sql)
    stats_map = {
        row.id: {"today": row.today_sessions, "total": row.total_sessions}
        for row in stats_res
    }

    channels = await crud_channel.get_list(db)
    result = []
    for channel in channels:
        agent = await crud_agent.get(db, channel.agent_id) if channel.agent_id else None
        s = stats_map.get(channel.id, {"today": 0, "total": 0})
        out = _channel_to_out(
            channel,
            agent_name=agent.name if agent else None,
        )
        out.today_sessions = s["today"]
        out.total_sessions = s["total"]
        result.append(out)

    return Response.success(data=result)


@router.post("", summary="创建渠道")
async def create_channel(
    obj_in: ChannelCreate,
    db: AsyncSession = Depends(get_db),
    admin_id: int = Depends(get_current_admin_id),
):
    # 验证Agent存在
    agent = await crud_agent.get(db, obj_in.agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent不存在")

    if agent.status == 0:
        raise HTTPException(status_code=400, detail="Agent已禁用，无法创建渠道")

    channel = await crud_channel.create(db, obj_in)

    logger.info(
        f"渠道创建成功 "
        f"channel_id={channel.id} "
        f"channel_type={channel.type} "  # ✅ 用 channel.type
        f"agent_id={channel.agent_id}"
    )

    return Response.success(data=_channel_to_out(channel, agent_name=agent.name))


@router.get("/{channel_id}", summary="获取渠道详情")
async def get_channel(
    channel_id: int,
    db: AsyncSession = Depends(get_db),
    admin_id: int = Depends(get_current_admin_id),
):
    channel = await crud_channel.get(db, channel_id)
    if not channel:
        raise HTTPException(status_code=404, detail="渠道不存在")

    agent = await crud_agent.get(db, channel.agent_id) if channel.agent_id else None
    return Response.success(
        data=_channel_to_out(channel, agent_name=agent.name if agent else None)
    )


@router.put("/{channel_id}", summary="更新渠道")
async def update_channel(
    channel_id: int,
    obj_in: ChannelUpdate,
    db: AsyncSession = Depends(get_db),
    admin_id: int = Depends(get_current_admin_id),
):
    channel = await crud_channel.get(db, channel_id)
    if not channel:
        raise HTTPException(status_code=404, detail="渠道不存在")

    if obj_in.agent_id:
        agent = await crud_agent.get(db, obj_in.agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent不存在")

    channel = await crud_channel.update(db, channel_id, obj_in)
    agent = await crud_agent.get(db, channel.agent_id) if channel.agent_id else None
    return Response.success(
        data=_channel_to_out(channel, agent_name=agent.name if agent else None)
    )


@router.delete("/{channel_id}", summary="删除渠道")
async def delete_channel(
    channel_id: int,
    db: AsyncSession = Depends(get_db),
    admin_id: int = Depends(get_current_admin_id),
):
    channel = await crud_channel.get(db, channel_id)
    if not channel:
        raise HTTPException(status_code=404, detail="渠道不存在")

    await crud_channel.delete(db, channel_id)
    return Response.success(message="删除成功")


@router.post("/{channel_id}/regenerate-token", summary="重新生成渠道Token")
async def regenerate_token(
    channel_id: int,
    db: AsyncSession = Depends(get_db),
    admin_id: int = Depends(get_current_admin_id),
):
    channel = await crud_channel.get(db, channel_id)
    if not channel:
        raise HTTPException(status_code=404, detail="渠道不存在")

    channel = await crud_channel.regenerate_token(db, channel_id)

    logger.info(f"渠道Token重新生成 channel_id={channel_id}")

    ws_url = _build_ws_url(channel.channel_token)
    return Response.success(
        data=ChannelTokenOut(
            channel_token=channel.channel_token,
            ws_url=ws_url,
        ),
        message="Token已重新生成，请更新前端配置",
    )


@router.get("/{channel_id}/token", summary="获取渠道Token和WS地址")
async def get_channel_token(
    channel_id: int,
    db: AsyncSession = Depends(get_db),
    admin_id: int = Depends(get_current_admin_id),
):
    channel = await crud_channel.get(db, channel_id)
    if not channel:
        raise HTTPException(status_code=404, detail="渠道不存在")

    ws_url = _build_ws_url(channel.channel_token)
    return Response.success(
        data=ChannelTokenOut(
            channel_token=channel.channel_token,
            ws_url=ws_url,
        )
    )


# ==================== 渠道内容配置 ====================


@router.get("/{channel_id}/config", summary="获取渠道内容配置（管理端）")
async def get_channel_config(
    channel_id: int,
    db: AsyncSession = Depends(get_db),
    admin_id: int = Depends(get_current_admin_id),
):
    """获取渠道内容配置"""
    sql = text("""
        SELECT
            config_type,
            title,
            content,
            image_url,
            link_url,
            sort_order,
            status,
            extra
        FROM channel_configs
        WHERE channel_id = :channel_id
          AND status = 1
        ORDER BY config_type, sort_order ASC
    """)
    res = await db.execute(sql, {"channel_id": channel_id})
    rows = res.fetchall()

    channel_sql = text("SELECT name FROM channels WHERE id = :channel_id")
    channel_res = await db.execute(channel_sql, {"channel_id": channel_id})
    channel_row = channel_res.fetchone()
    channel_name = channel_row.name if channel_row else f"渠道{channel_id}"

    hot_questions = []
    banners = []
    quick_tags = []

    for row in rows:
        if row.config_type == "hot_question":
            hot_questions.append(
                {
                    "id": row.sort_order,
                    "text": row.title or "",
                }
            )
        elif row.config_type == "banner":
            extra = (
                row.extra
                if isinstance(row.extra, dict)
                else (json.loads(row.extra) if row.extra else {})
            )
            banners.append(
                {
                    "id": row.sort_order,
                    "image_url": row.image_url or "",
                    "title": row.title or "",
                    "subtitle": extra.get("subtitle") or row.content or "",
                    "link_url": row.link_url or "",
                }
            )
        elif row.config_type == "quick_tag":
            extra = (
                row.extra
                if isinstance(row.extra, dict)
                else (json.loads(row.extra) if row.extra else {})
            )
            quick_tags.append(
                {
                    "id": row.sort_order,
                    "icon": extra.get("icon", ""),
                    "label": row.title or "",
                    "send_text": row.content or "",
                }
            )

    return Response.success(
        data={
            "channel_name": channel_name,
            "hot_questions_enabled": len(hot_questions) > 0,
            "hot_questions": hot_questions,
            "banners_enabled": len(banners) > 0,
            "banners": banners,
            "quick_tags_enabled": len(quick_tags) > 0,
            "quick_tags": quick_tags,
        }
    )


@router.put("/{channel_id}/config", summary="保存渠道内容配置")
async def save_channel_config(
    channel_id: int,
    body: dict,
    db: AsyncSession = Depends(get_db),
    admin_id: int = Depends(get_current_admin_id),
):
    """保存渠道内容配置（全量覆盖写入）"""
    delete_sql = text("DELETE FROM channel_configs WHERE channel_id = :channel_id")
    await db.execute(delete_sql, {"channel_id": channel_id})

    insert_sql = text("""
        INSERT INTO channel_configs (
            channel_id, config_type, title,
            content, image_url, link_url,
            sort_order, status, extra,
            created_at, updated_at
        ) VALUES (
            :channel_id, :config_type, :title,
            :content, :image_url, :link_url,
            :sort_order, 1, :extra,
            NOW(), NOW()
        )
    """)

    if body.get("hot_questions_enabled"):
        for idx, q in enumerate(body.get("hot_questions", [])):
            if not q.get("text", "").strip():
                continue
            await db.execute(
                insert_sql,
                {
                    "channel_id": channel_id,
                    "config_type": "hot_question",
                    "title": q["text"].strip(),
                    "content": None,
                    "image_url": None,
                    "link_url": None,
                    "sort_order": idx,
                    "extra": None,
                },
            )

    if body.get("banners_enabled"):
        for idx, b in enumerate(body.get("banners", [])):
            if not b.get("title", "").strip() and not b.get("image_url", "").strip():
                continue
            await db.execute(
                insert_sql,
                {
                    "channel_id": channel_id,
                    "config_type": "banner",
                    "title": b.get("title", "").strip(),
                    "content": b.get("content", "").strip() or None,
                    "image_url": b.get("image_url", "").strip(),
                    "link_url": b.get("link_url", "").strip() or None,
                    "sort_order": idx,
                    "extra": json.dumps({"subtitle": b.get("content", "").strip()}),
                },
            )

    if body.get("quick_tags_enabled"):
        for idx, t in enumerate(body.get("quick_tags", [])):
            if not t.get("label", "").strip():
                continue
            await db.execute(
                insert_sql,
                {
                    "channel_id": channel_id,
                    "config_type": "quick_tag",
                    "title": t.get("label", "").strip(),
                    "content": t.get("send_text", "").strip() or None,
                    "image_url": None,
                    "link_url": None,
                    "sort_order": idx,
                    "extra": json.dumps({"icon": t.get("icon", "").strip()}),
                },
            )

    await db.commit()
    return Response.success(message="配置已保存")


@router.get("/{channel_id}/config/public", summary="获取渠道内容配置（公开）")
async def get_channel_config_public(
    channel_id: int,
    db: AsyncSession = Depends(get_db),
):
    """前端公开访问渠道配置（供商城前台聊天窗口调用）"""
    sql = text("""
        SELECT config_type, title, content,
               image_url, link_url, sort_order, extra
        FROM channel_configs
        WHERE channel_id = :channel_id
          AND status = 1
        ORDER BY config_type, sort_order ASC
    """)
    res = await db.execute(sql, {"channel_id": channel_id})
    rows = res.fetchall()

    hot_questions = []
    banners = []
    quick_tags = []

    for row in rows:
        if row.config_type == "hot_question":
            hot_questions.append(row.title or "")

        elif row.config_type == "banner":
            extra = (
                row.extra
                if isinstance(row.extra, dict)
                else (json.loads(row.extra) if row.extra else {})
            )
            banners.append(
                {
                    "image_url": row.image_url or "",
                    "title": row.title or "",
                    "subtitle": extra.get("subtitle", ""),
                    "link_url": row.link_url or "",
                }
            )

        elif row.config_type == "quick_tag":
            extra = (
                row.extra
                if isinstance(row.extra, dict)
                else (json.loads(row.extra) if row.extra else {})
            )
            quick_tags.append(
                {
                    "icon": extra.get("icon", ""),
                    "label": row.title or "",
                    "send_text": row.content or "",
                }
            )

    return Response.success(
        data={
            "hot_questions": hot_questions,
            "banners": banners,
            "quick_tags": quick_tags,
        }
    )


@router.get("/config/public", summary="通过 Token 获取渠道配置（公开）")
async def get_channel_config_by_token(
    token: str,
    db: AsyncSession = Depends(get_db),
):
    """供 ChatPage 等前端页面直接通过 channel_token 加载配置"""
    channel = await crud_channel.get_by_token(db, token)
    if not channel or channel.status == 0:
        raise HTTPException(status_code=404, detail="渠道不存在")

    sql = text("""
        SELECT config_type, title, content,
               image_url, link_url, sort_order, extra
        FROM channel_configs
        WHERE channel_id = :channel_id
          AND status = 1
        ORDER BY config_type, sort_order ASC
    """)
    res = await db.execute(sql, {"channel_id": channel.id})
    rows = res.fetchall()

    hot_questions = []
    banners = []
    quick_tags = []

    for row in rows:
        if row.config_type == "hot_question":
            hot_questions.append(row.title or "")

        elif row.config_type == "banner":
            extra = (
                row.extra
                if isinstance(row.extra, dict)
                else (json.loads(row.extra) if row.extra else {})
            )
            banners.append(
                {
                    "image_url": row.image_url or "",
                    "title": row.title or "",
                    "subtitle": extra.get("subtitle") or row.content or "",
                    "link_url": row.link_url or "",
                }
            )

        elif row.config_type == "quick_tag":
            extra = (
                row.extra
                if isinstance(row.extra, dict)
                else (json.loads(row.extra) if row.extra else {})
            )
            quick_tags.append(
                {
                    "icon": extra.get("icon", ""),
                    "label": row.title or "",
                    "send_text": row.content or "",
                }
            )

    return Response.success(
        data={
            "channel_id": channel.id,
            "channel_name": channel.name,
            "hot_questions": hot_questions,
            "banners": banners,
            "quick_tags": quick_tags,
        }
    )
