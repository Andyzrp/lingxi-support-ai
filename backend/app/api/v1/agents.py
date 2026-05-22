# backend/app/api/v1/agents.py
import logging
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_admin_id
from app.crud.agent import crud_agent, crud_agent_version, crud_agent_config
from app.schemas.agent import (
    AgentCreate,
    AgentUpdate,
    AgentOut,
    AgentVersionCreate,
    AgentVersionOut,
    AgentConfigUpdate,
    AgentConfigOut,
    WorkflowGraph,
    WorkflowNode,
    WorkflowEdge,
)
from app.utils.response import Response

logger = logging.getLogger(__name__)
router = APIRouter()


def _version_to_out(version) -> AgentVersionOut:
    """AgentVersion模型 → AgentVersionOut Schema（不含配置）"""
    status_text_map = {0: "草稿", 1: "已发布", 2: "已归档"}
    return AgentVersionOut(
        id=version.id,
        agent_id=version.agent_id,
        version_no=version.version_no,
        status=version.status,
        status_text=status_text_map.get(version.status, "未知"),
        remark=version.remark,
        published_at=getattr(version, "published_at", None),
        created_at=version.created_at,
    )


async def _enrich_version(version, db: AsyncSession) -> dict:
    """AgentVersion模型 → enriched dict（含配置数据）"""
    from app.crud.agent import crud_agent_config

    result = {
        "id": version.id,
        "agent_id": version.agent_id,
        "version_no": version.version_no,
        "status": version.status,
        "status_text": {0: "草稿", 1: "已发布", 2: "已归档"}.get(
            version.status, "未知"
        ),
        "remark": version.remark,
        "published_at": getattr(version, "published_at", None),
        "created_at": version.created_at,
        "model": None,
        "temperature": None,
        "max_tokens": None,
        "tools_enabled": None,
        "no_answer_threshold": None,
        "system_prompt": None,
    }

    try:
        config = await crud_agent_config.get_or_create(db, version.id)
        model_params = config.model_params or {}
        tools_config = config.tools_config or {}
        result["model"] = model_params.get("model")
        result["temperature"] = model_params.get("temperature")
        result["max_tokens"] = model_params.get("max_tokens")
        result["tools_enabled"] = tools_config.get("enabled_tools")
        result["no_answer_threshold"] = config.auto_transfer_count
        result["system_prompt"] = config.system_prompt
    except Exception:
        pass

    return result


# ==================== 辅助函数 ====================


async def _enrich_agent(agent, db: AsyncSession) -> dict:
    """Agent模型 →  enriched dict with related data"""
    from app.crud.agent import crud_agent_version, crud_agent_config

    result = {
        "id": agent.id,
        "name": agent.name,
        "description": agent.description,
        "status": agent.status,
        "current_version_id": agent.current_version_id,
        "draft_version_id": agent.draft_version_id,
        "created_at": agent.created_at,
        "updated_at": agent.updated_at,
        "current_version": None,
        "model": None,
        "tools_enabled": None,
        "version_count": 0,
        "today_sessions": 0,
        "resolve_rate": None,
    }

    try:
        from app.models.conversation import Conversation

        versions = await crud_agent_version.get_list(db, agent.id)
        result["version_count"] = len(versions)

        published = next((v for v in versions if v.status == 1), None)
        if published:
            result["current_version"] = published.version_no

            config = await crud_agent_config.get_or_create(db, published.id)
            model_params = config.model_params or {}
            tools_config = config.tools_config or {}
            result["model"] = model_params.get("model")
            result["tools_enabled"] = tools_config.get("enabled_tools")

        today_start = datetime.utcnow().replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        total_result = await db.execute(
            select(func.count(Conversation.id)).where(Conversation.agent_id == agent.id)
        )
        total = total_result.scalar() or 0

        today_result = await db.execute(
            select(func.count(Conversation.id)).where(
                and_(
                    Conversation.agent_id == agent.id,
                    Conversation.started_at >= today_start,
                )
            )
        )
        today_count = today_result.scalar() or 0

        resolved_result = await db.execute(
            select(func.count(Conversation.id)).where(
                and_(
                    Conversation.agent_id == agent.id,
                    Conversation.is_resolved == 1,
                )
            )
        )
        resolved = resolved_result.scalar() or 0

        result["today_sessions"] = today_count
        result["resolve_rate"] = round(resolved / total, 4) if total > 0 else None
    except Exception:
        pass

    return result


def _config_to_out(config) -> AgentConfigOut:
    """AgentConfig模型 → AgentConfigOut Schema"""
    model_params = config.model_params or {}
    tools_config = config.tools_config or {}
    complaint_keywords = config.complaint_keywords or {}

    return AgentConfigOut(
        id=config.id,
        agent_version_id=config.agent_version_id,
        knowledge_base_id=config.knowledge_base_id,
        system_prompt=config.system_prompt,
        model=model_params.get("model"),
        temperature=model_params.get("temperature"),
        max_tokens=model_params.get("max_tokens"),
        tools_enabled=tools_config.get("enabled_tools"),
        no_answer_threshold=config.auto_transfer_count,
        transfer_keywords=complaint_keywords.get("transfer_keywords"),
        model_type=config.model_type or 0,
        rag_threshold=config.rag_threshold or 0.75,
        context_rounds=config.context_rounds or 3,
        emotion_detection=config.emotion_detection or 1,
        auto_transfer=config.auto_transfer or 1,
        auto_transfer_count=config.auto_transfer_count or 3,
        created_at=config.created_at,
        updated_at=config.updated_at,
    )


@router.get("", summary="获取Agent列表")
async def list_agents(
    db: AsyncSession = Depends(get_db),
    admin_id: int = Depends(get_current_admin_id),
):
    agents = await crud_agent.get_list(db)
    result = [await _enrich_agent(agent, db) for agent in agents]
    return Response.success(data=result)


@router.post("", summary="创建Agent")
async def create_agent(
    obj_in: AgentCreate,
    db: AsyncSession = Depends(get_db),
    admin_id: int = Depends(get_current_admin_id),
):
    # ✅ agents表没有bot_id字段，直接创建
    agent = await crud_agent.create(db, obj_in)

    # 自动创建第一个草稿版本
    version = await crud_agent_version.create(
        db=db,
        agent_id=agent.id,
        obj_in=AgentVersionCreate(description="初始版本"),
    )

    # 自动创建默认配置（挂在版本下）
    await crud_agent_config.get_or_create(
        db=db,
        agent_version_id=version.id,
        knowledge_base_id=obj_in.knowledge_base_id,
    )

    logger.info(f"Agent创建成功 agent_id={agent.id} version_id={version.id}")

    return Response.success(data=await _enrich_agent(agent, db))


@router.get("/{agent_id}", summary="获取Agent详情")
async def get_agent(
    agent_id: int,
    db: AsyncSession = Depends(get_db),
    admin_id: int = Depends(get_current_admin_id),
):
    agent = await crud_agent.get(db, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent不存在")

    return Response.success(data=await _enrich_agent(agent, db))


@router.put("/{agent_id}", summary="更新Agent")
async def update_agent(
    agent_id: int,
    obj_in: AgentUpdate,
    db: AsyncSession = Depends(get_db),
    admin_id: int = Depends(get_current_admin_id),
):
    agent = await crud_agent.get(db, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent不存在")

    agent = await crud_agent.update(db, agent_id, obj_in)
    return Response.success(data=await _enrich_agent(agent, db))


@router.delete("/{agent_id}", summary="删除Agent")
async def delete_agent(
    agent_id: int,
    db: AsyncSession = Depends(get_db),
    admin_id: int = Depends(get_current_admin_id),
):
    agent = await crud_agent.get(db, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent不存在")

    from app.models.channel import Channel

    result = await db.execute(select(Channel).where(Channel.agent_id == agent_id))
    channels = result.scalars().all()
    if channels:
        raise HTTPException(
            status_code=400,
            detail=f"该 Agent 被 {len(channels)} 个渠道引用，请先在渠道管理中解绑或删除相关渠道",
        )

    await crud_agent.delete(db, agent_id)
    return Response.success(message="删除成功")


# ==================== 版本管理 ====================


@router.get("/{agent_id}/versions", summary="获取版本列表")
async def list_versions(
    agent_id: int,
    db: AsyncSession = Depends(get_db),
    admin_id: int = Depends(get_current_admin_id),
):
    import asyncio

    agent = await crud_agent.get(db, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent不存在")

    versions = await crud_agent_version.get_list(db, agent_id)
    result = await asyncio.gather(*[_enrich_version(v, db) for v in versions])
    return Response.success(data=list(result))


@router.post("/{agent_id}/versions", summary="创建新草稿版本")
async def create_version(
    agent_id: int,
    obj_in: AgentVersionCreate,
    db: AsyncSession = Depends(get_db),
    admin_id: int = Depends(get_current_admin_id),
):
    agent = await crud_agent.get(db, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent不存在")

    # 检查是否已有草稿
    existing_draft = await crud_agent_version.get_draft(db, agent_id)
    if existing_draft:
        raise HTTPException(
            status_code=400,
            detail="已存在草稿版本，请先发布再创建新版本",
        )

    version = await crud_agent_version.create(db, agent_id, obj_in)
    return Response.success(data=_version_to_out(version))


@router.post("/{agent_id}/publish", summary="发布草稿版本")
async def publish_version(
    agent_id: int,
    db: AsyncSession = Depends(get_db),
    admin_id: int = Depends(get_current_admin_id),
):
    agent = await crud_agent.get(db, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent不存在")

    draft = await crud_agent_version.get_draft(db, agent_id)
    if not draft:
        raise HTTPException(status_code=400, detail="没有可发布的草稿版本")

    version = await crud_agent_version.publish(
        db=db,
        agent_id=agent_id,
        version_id=draft.id,
    )

    logger.info(
        f"Agent版本发布成功 agent_id={agent_id} version_no={version.version_no}"
    )

    return Response.success(data=_version_to_out(version), message="发布成功")


@router.post("/{agent_id}/rollback/{version_id}", summary="回滚到指定版本")
async def rollback_version(
    agent_id: int,
    version_id: int,
    db: AsyncSession = Depends(get_db),
    admin_id: int = Depends(get_current_admin_id),
):
    agent = await crud_agent.get(db, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent不存在")

    version = await crud_agent_version.get(db, version_id)
    if not version:
        raise HTTPException(status_code=404, detail="版本不存在")
    if version.agent_id != agent_id:
        raise HTTPException(status_code=403, detail="该版本不属于此Agent")
    if version.status == 0:
        raise HTTPException(status_code=400, detail="草稿版本不能回滚")

    rolled_back = await crud_agent_version.rollback(
        db=db,
        agent_id=agent_id,
        version_id=version_id,
    )

    logger.info(f"Agent版本回滚成功 agent_id={agent_id} version_id={version_id}")

    return Response.success(data=_version_to_out(rolled_back), message="回滚成功")


# ==================== Agent配置 ====================


@router.get("/{agent_id}/config", summary="获取Agent配置")
async def get_agent_config(
    agent_id: int,
    db: AsyncSession = Depends(get_db),
    admin_id: int = Depends(get_current_admin_id),
):
    agent = await crud_agent.get(db, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent不存在")

    # ✅ 配置挂在版本下，优先取草稿版本配置
    version = await crud_agent_version.get_draft(db, agent_id)
    if not version:
        version = await crud_agent_version.get_published(db, agent_id)
    if not version:
        raise HTTPException(status_code=404, detail="Agent暂无版本，请先创建版本")

    config = await crud_agent_config.get_or_create(
        db=db,
        agent_version_id=version.id,
    )
    return Response.success(data=_config_to_out(config))


@router.put("/{agent_id}/config", summary="更新Agent配置")
async def update_agent_config(
    agent_id: int,
    obj_in: AgentConfigUpdate,
    db: AsyncSession = Depends(get_db),
    admin_id: int = Depends(get_current_admin_id),
):
    agent = await crud_agent.get(db, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent不存在")

    # ✅ 只能更新草稿版本的配置
    version = await crud_agent_version.get_draft(db, agent_id)
    if not version:
        raise HTTPException(
            status_code=400,
            detail="没有草稿版本，请先创建草稿版本再修改配置",
        )

    config = await crud_agent_config.update(
        db=db,
        agent_version_id=version.id,
        obj_in=obj_in,
    )

    logger.info(f"Agent配置更新成功 agent_id={agent_id}")
    return Response.success(
        data=_config_to_out(config),
        message="配置更新成功",
    )


# ==================== 工作流展示 ====================


@router.get("/{agent_id}/workflow-graph")
async def get_workflow_graph(
    agent_id: int,
    format: str = Query("mermaid", pattern="^(mermaid|ascii)$"),
    _: int = Depends(get_current_admin_id),
):
    """
    获取 Agent 工作流可视化图
    format=mermaid → 返回 Mermaid 格式（前端渲染）
    format=ascii   → 返回 ASCII 文本（调试用）
    """
    MERMAID_GRAPH = """graph TD
    __start__([用户消息]) --> emotion
    emotion{&nbsp;} -->|"情绪正常"| intent
    emotion{&nbsp;} -->|"情绪激动"| transfer
    intent{&nbsp;} -->|"工具意图"| tool
    intent{&nbsp;} -->|"RAG意图"| rag
    intent{&nbsp;} -->|"直接生成"| generate
    intent{&nbsp;} -->|"投诉/情绪激动"| transfer
    tool --> generate
    rag --> generate
    rag --> transfer
    generate --> confidence
    confidence{&nbsp;} -->|"置信通过"| __end__([结束])
    confidence{&nbsp;} -->|"连续未答≥3次"| transfer
    transfer --> __end__([结束])"""

    ASCII_GRAPH = """
┌─────────────────────────────────────────────────────────────────────┐
│                         Agent 工作流图                               │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│   __start__                                                         │
│       │                                                             │
│       ▼                                                             │
│   ┌───────────┐     ┌───────────┐     ┌───────────┐               │
│   │  emotion  │────▶│   intent  │────▶│    rag    │               │
│   │ 情绪检测  │     │ 意图识别  │     │ 知识库检索│               │
│   └───────────┘     └───────────┘     └─────┬─────┘               │
│       │                   │                 │                      │
│       │                   │          ┌──────┴──────┐              │
│       │                   │          ▼             ▼              │
│       │              ┌────┴────┐   ┌────────┐   ┌────────┐        │
│       │              │  tool   │   │generate│   │transfer│        │
│       │              │ 工具调用│   │生成回答│   │ 转人工 │        │
│       │              └────┬────┘   └────┬───┘   └────┬────┘        │
│       │                   │             │            │             │
│       │                   └──────┬──────┘            │             │
│       │                          ▼                   │             │
│       │                   ┌────────────┐             │             │
│       │                   │ confidence │             │             │
│       │                   │  置信度判断 │             │             │
│       │                   └─────┬──────┘             │             │
│       │                         │                    │             │
│       │            ┌────────────┴───────────┐        │             │
│       ▼            ▼                        ▼        ▼             │
│   __end__      __end__                  transfer   __end__          │
│                                                                     │
│   节点说明：                                                         │
│   • emotion   : 情绪检测，激动时直接转人工                            │
│   • intent    : 意图识别，判断是工具调用/RAG/直接生成                  │
│   • tool      : 工具调用，订单/物流/退款/商品查询                      │
│   • rag       : 知识库检索，BM25+向量混合检索                         │
│   • generate  : 生成回答，大模型基于上下文生成回答                     │
│   • confidence: 置信度判断，未通过则转人工                            │
│   • transfer  : 转人工节点（情绪激动/投诉/连续未答/关键词触发）         │
│                                                                     │
│   工具意图：ORDER_QUERY/ORDER_LIST/LOGISTICS_QUERY/REFUND_REQUEST/PRODUCT_QUERY │
│   RAG意图：GENERAL/UNKNOWN                                           │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
"""

    return Response.success(
        data={
            "agent_id": agent_id,
            "format": format,
            "graph": MERMAID_GRAPH if format == "mermaid" else ASCII_GRAPH,
        }
    )
