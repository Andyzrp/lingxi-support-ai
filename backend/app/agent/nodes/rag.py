# backend/app/agent/nodes/rag.py
import logging
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.state import (
    AgentState,
    AgentAction,
    RagResult,
    state_set_error,
)
from app.services.bot.faq import process_faq
from app.crud.knowledge import crud_knowledge_item

logger = logging.getLogger(__name__)


# ==================== RAG检索节点 ====================


async def rag_node(state: AgentState, db: AsyncSession) -> dict:
    """
    LangGraph RAG检索节点

    执行流程：
    1. 调用 process_faq（含关键词干预+混合检索）
    2. 命中 → 构建 rag_context 注入Prompt
    3. 未命中 → 根据意图决定是否调用工具
    4. 关键词触发转人工 → 直接转人工

    Args:
        state: 当前Agent状态
        db: 数据库Session

    Returns:
        状态更新dict
    """
    query = state["query"]
    bot_id = state["bot_id"]
    intent = state.get("intent")
    extracted_entities = state.get("extracted_entities", {})

    logger.info(f"RAG检索节点开始 query='{query}' bot_id={bot_id} intent={intent}")

    try:
        # ── Step1：关键词干预（最高优先级）──
        from app.services.bot.keyword import process_keyword_intervention

        keyword_hit, need_transfer = await process_keyword_intervention(
            query=query,
            bot_id=bot_id,
            db=db,
        )

        # 关键词触发转人工
        if need_transfer:
            logger.info(f"RAG节点：关键词触发转人工 query='{query}'")
            return {
                "need_transfer": True,
                "transfer_reason": "keyword",
                "next_action": AgentAction.TRANSFER,
                "rag_results": [],
                "rag_context": None,
            }

        # 关键词命中固定话术
        if keyword_hit:
            rag_result = RagResult(
                item_id=keyword_hit.item_id,
                title=keyword_hit.title,
                answer=keyword_hit.answer,
                answer_type=keyword_hit.answer_type,
                score=keyword_hit.score,
                matched_question=keyword_hit.matched_question,
            )
            rag_context = _build_rag_context([rag_result])
            print(f"[RAG] 关键词命中 item_id={rag_result.item_id}")
            return {
                "rag_results": [rag_result],
                "rag_context": rag_context,
                "next_action": AgentAction.GENERATE,
            }

        # ── Step2：直接调用vectorizer.search_similar获取原始检索结果（不设阈值）──
        from app.services.knowledge.vectorizer import search_similar
        from app.crud.bot import crud_bot
        from app.crud.knowledge import crud_knowledge_item

        # 获取Bot配置
        bot = await crud_bot.get(db, bot_id)
        if not bot:
            print(f"[RAG] Bot不存在 bot_id={bot_id}")
            return {
                "rag_results": [],
                "rag_context": None,
                "next_action": AgentAction.GENERATE,
            }

        kb_id = bot.knowledge_base_id
        # 直接调用search_similar，获取top_k条结果，不设score_threshold
        vector_hits = await search_similar(
            query=query,
            kb_id=kb_id,
            top_k=5,  # 获取更多结果
            score_threshold=0.0,  # 不过滤，所有结果都返回
        )

        print(f"[RAG] 向量检索返回 {len(vector_hits)} 条结果")

        if not vector_hits:
            print(f"[RAG] ❌ 无检索结果 query='{query}'")
            return {
                "rag_results": [],
                "rag_context": None,
                "next_action": _decide_next_action_after_rag(
                    intent=intent,
                    rag_hit=False,
                    extracted_entities=extracted_entities,
                ),
            }

        # 查询所有检索结果的知识详情，构建列表
        rag_results = []
        for hit in vector_hits:
            item = await crud_knowledge_item.get(db, hit["item_id"])
            if not item:
                continue
            rag_result = RagResult(
                item_id=item.id,
                title=item.title,
                answer=item.answer_content or "",
                answer_type=item.answer_type,
                score=hit.get("vector_score", hit.get("score", 0)),
                matched_question=hit.get("question", ""),
            )
            rag_results.append(rag_result)
            print(
                f"[RAG] 候选知识 {len(rag_results)}: {rag_result['title']} (score={rag_result['score']:.4f})"
            )

        if not rag_results:
            print(f"[RAG] ❌ 所有知识条目均不存在")
            return {
                "rag_results": [],
                "rag_context": None,
                "next_action": _decide_next_action_after_rag(
                    intent=intent,
                    rag_hit=False,
                    extracted_entities=extracted_entities,
                ),
            }

        print(f"[RAG] 共 {len(rag_results)} 条候选知识，传给LLM判断")

        print(f"[RAG] 知识标题: {rag_result['title']}")
        print(f"[RAG] 知识答案: {rag_result['answer'][:100]}...")

        rag_context = _build_rag_context([rag_result])

        return {
            "rag_results": [rag_result],
            "rag_context": rag_context,
            "next_action": _decide_next_action_after_rag(
                intent=intent,
                rag_hit=True,  # 标记为有结果，让LLM自己判断
                extracted_entities=extracted_entities,
            ),
        }

    except Exception as e:
        import traceback

        logger.error(f"RAG检索节点异常: {e}\n{traceback.format_exc()}")
        try:
            await db.rollback()
        except Exception:
            pass
        return {
            "rag_results": [],
            "rag_context": None,
            "next_action": AgentAction.GENERATE,
            "error": f"RAG检索失败: {str(e)}",
        }


# ==================== 构建RAG上下文 ====================


def _build_rag_context(rag_results: List[RagResult]) -> str:
    """
    将RAG检索结果格式化为Prompt上下文

    Args:
        rag_results: RAG检索结果列表

    Returns:
        格式化后的上下文字符串
    """
    if not rag_results:
        return ""

    lines = ["以下是知识库中找到的相关信息：", ""]

    for i, result in enumerate(rag_results, 1):
        lines.append(f"【参考资料{i}】")
        lines.append(f"问题：{result['title']}")
        lines.append(f"答案：{result['answer']}")
        lines.append("")

    lines.append("请基于以上参考资料回答用户的问题。")
    return "\n".join(lines)


# ==================== 路由决策 ====================


def _decide_next_action_after_rag(
    intent,
    rag_hit: bool,
    extracted_entities: dict,
) -> AgentAction:
    """
    RAG检索后决定下一步动作

    决策规则：
    ┌─────────────────────────────────────────────┐
    │ 意图           │ RAG命中 │ 有实体 │ 下一步   │
    ├────────────────┼─────────┼────────┼──────────│
    │ order_query    │ 任意    │ 任意   │ CALL_TOOL│
    │ logistics_query│ 任意    │ 任意   │ CALL_TOOL│
    │ refund_request │ 任意    │ 任意   │ CALL_TOOL│
    │ product_query  │ 未命中  │ 有名称 │ CALL_TOOL│
    │ 其他           │ 命中    │ 任意   │ GENERATE │
    │ 其他           │ 未命中  │ 任意   │ GENERATE │
    └─────────────────────────────────────────────┘

    Args:
        intent: 意图类型
        rag_hit: 是否命中RAG
        extracted_entities: 提取的实体

    Returns:
        AgentAction
    """
    from app.agent.state import IntentType

    # 订单/物流/退款 → 必须调用工具
    tool_required_intents = {
        IntentType.ORDER_QUERY,
        IntentType.LOGISTICS_QUERY,
        IntentType.REFUND_REQUEST,
    }

    if intent in tool_required_intents:
        return AgentAction.CALL_TOOL

    # 商品查询 → 有商品名称才调工具
    if intent == IntentType.PRODUCT_QUERY:
        has_product_name = bool(extracted_entities.get("product_name"))
        if has_product_name:
            return AgentAction.CALL_TOOL

    # 其他情况 → 直接生成
    return AgentAction.GENERATE
