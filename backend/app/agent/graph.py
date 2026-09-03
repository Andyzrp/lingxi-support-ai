# backend/app/agent/graph.py
import logging
from typing import Optional
from langgraph.graph import StateGraph, END
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.state import (
    AgentState,
    AgentAction,
    create_initial_state,
    MessageItem,
    IntentType,
)
from app.agent.nodes.emotion import emotion_node
from app.agent.nodes.intent import intent_node
from app.agent.nodes.rag import rag_node
from app.agent.nodes.generate import generate_node
from app.agent.nodes.confidence import confidence_node
from app.agent.tools.order import query_order, query_orders
from app.agent.tools.logistics import query_logistics
from app.agent.tools.refund import apply_refund, check_refund_eligibility
from app.agent.tools.product import query_product, query_hot_products

logger = logging.getLogger(__name__)


# ==================== 工具调用节点 ====================


async def tool_node(state: AgentState, db: AsyncSession) -> dict:
    """
    工具调用节点

    根据意图决定调用哪个工具：
    - order_query    → query_order
    - logistics_query → query_logistics
    - refund_request → check_refund_eligibility + apply_refund
    - product_query  → query_product

    Args:
        state: 当前Agent状态
        db: 数据库Session

    Returns:
        状态更新dict
    """
    from app.agent.state import IntentType

    intent = state.get("intent")
    user_id = state.get("user_id")
    entities = state.get("extracted_entities", {})
    order_no = entities.get("order_no")
    product_name = entities.get("product_name")

    logger.info(
        f"工具调用节点开始 intent={intent} user_id={user_id} entities={entities}"
    )

    tool_results = []

    try:
        # ── 订单查询 ──
        if intent == IntentType.ORDER_QUERY:
            result = await query_order(
                db=db,
                user_id=user_id,
                order_no=order_no,
            )
            tool_results.append(result)

        # ── 订单列表查询（7天内） ──
        elif intent == IntentType.ORDER_LIST:
            result = await query_orders(
                db=db,
                user_id=user_id,
            )
            tool_results.append(result)

        # ── 物流查询 ──
        elif intent == IntentType.LOGISTICS_QUERY:
            result = await query_logistics(
                db=db,
                user_id=user_id,
                order_no=order_no,
            )
            tool_results.append(result)

        # ── 退款查询 ──
        elif intent == IntentType.REFUND_REQUEST:
            result = await check_refund_eligibility(
                db=db,
                user_id=user_id,
                order_no=order_no,
            )
            tool_results.append(result)

        # ── 商品查询 ──
        elif intent == IntentType.PRODUCT_QUERY:
            if product_name:
                result = await query_product(
                    db=db,
                    product_name=product_name,
                )
            else:
                result = await query_hot_products(db=db)
            tool_results.append(result)

        else:
            logger.info(f"意图 {intent} 无需调用工具")

    except Exception as e:
        logger.error(f"工具调用异常: {e}")
        from app.agent.state import ToolResult

        tool_results.append(
            ToolResult(
                tool_name="unknown",
                success=False,
                data=None,
                error_msg=f"工具调用失败: {str(e)}",
            )
        )

    logger.info(f"工具调用完成，共{len(tool_results)}个结果")

    return {
        "tool_results": tool_results,
        "next_action": AgentAction.GENERATE,
    }


# ==================== 转人工节点 ====================


async def transfer_node(state: AgentState) -> dict:
    """
    转人工节点

    执行流程：
    1. 记录转人工原因
    2. 生成转人工提示语
    3. 标记会话需要切换身份

    Args:
        state: 当前Agent状态

    Returns:
        状态更新dict
    """
    transfer_reason = state.get("transfer_reason", "unknown")
    emotion = state.get("emotion")

    reason_text_map = {
        "emotion": "检测到您情绪激动",
        "no_answer": "连续多次未能解答您的问题",
        "keyword": "您的问题需要人工处理",
        "user_request": "您主动申请了人工客服",
        "tool_fail": "操作执行失败需要人工介入",
        "unknown": "当前问题需要人工处理",
    }

    reason_text = reason_text_map.get(transfer_reason, "当前问题需要人工处理")

    transfer_messages = [
        f"非常抱歉，{reason_text}。",
        "正在为您转接人工客服，请稍候...",
        "人工客服将继续为您提供服务，感谢您的耐心等待。",
    ]

    final_answer = "\n".join(transfer_messages)

    logger.info(f"转人工节点执行 reason={transfer_reason} emotion={emotion}")

    return {
        "final_answer": final_answer,
        "need_transfer": True,
        "transfer_reason": transfer_reason,
        "next_action": AgentAction.END,
    }


# ==================== 路由函数 ====================


def route_after_emotion(state: AgentState) -> str:
    """情绪检测后的路由"""
    next_action = state.get("next_action")

    if next_action == AgentAction.TRANSFER:
        return "transfer"

    return "intent"


TOOL_INTENTS = {
    IntentType.ORDER_QUERY,
    IntentType.ORDER_LIST,
    IntentType.LOGISTICS_QUERY,
    IntentType.REFUND_REQUEST,
    IntentType.PRODUCT_QUERY,
}

RAG_INTENTS = {
    IntentType.GENERAL,
    IntentType.UNKNOWN,
}


def route_after_intent(state: AgentState) -> str:
    """意图识别后的路由：三独立分支"""
    intent = state.get("intent")
    intent_repr = repr(intent)

    print(f"[ROUTE] ├─ 意图路由判断: intent={intent_repr}")

    if intent is None:
        print(f"[ROUTE] └─ → [generate]  无意图，直接生成分支")
        return "generate"

    if intent == IntentType.COMPLAINT or state.get("need_transfer_by_emotion"):
        print(f"[ROUTE] └─ → [transfer]  转人工")
        return "transfer"

    # 闲聊快速通道：直接返回预设回复，不走 RAG/LLM/置信度
    if intent == IntentType.CHITCHAT:
        print(f"[ROUTE] └─ → [chitchat]   闲聊快速通道")
        return "chitchat"

    if intent in TOOL_INTENTS:
        print(f"[ROUTE] └─ → [tool]      工具调用分支")
        return "tool"

    if intent in RAG_INTENTS:
        print(f"[ROUTE] └─ → [rag]       知识库检索分支")
        return "rag"

    print(f"[ROUTE] └─ → [generate]  直接生成分支")
    return "generate"


def route_after_rag(state: AgentState) -> str:
    """RAG检索后的路由：直接生成或转人工"""
    next_action = state.get("next_action")

    if next_action == AgentAction.TRANSFER:
        return "transfer"

    return "generate"


def route_after_tool(state: AgentState) -> str:
    """工具调用后的路由"""
    return "generate"


def route_after_generate(state: AgentState) -> str:
    """生成回答后的路由"""
    next_action = state.get("next_action")

    if next_action == AgentAction.TRANSFER:
        return "transfer"

    return "confidence"


def route_after_confidence(state: AgentState) -> str:
    """置信度判断后的路由"""
    next_action = state.get("next_action")

    if next_action == AgentAction.TRANSFER:
        return "transfer"

    return END


# ==================== 构建工作流图 ====================


def build_graph(db: AsyncSession) -> StateGraph:
    """
    构建 LangGraph 工作流图

    节点执行顺序（意图识别后三分支）：
    emotion → intent → tool → generate → confidence → [transfer?] → END          （订单/物流/退款/商品意图）
    emotion → intent → rag → generate → confidence → [transfer?] → END           （通用/未知意图）
    emotion → intent → generate → confidence → [transfer?] → END                 （投诉/无意图，或情绪触发转人工）

    Args:
        db: 数据库Session（注入到需要DB的节点）

    Returns:
        编译后的 StateGraph
    """
    # 创建状态图
    graph = StateGraph(AgentState)

    # ── 注册节点 ──

    # 情绪检测节点
    graph.add_node(
        "emotion",
        emotion_node,
    )

    # 意图识别节点
    graph.add_node(
        "intent",
        intent_node,
    )

    # RAG检索节点（需要db）
    async def _rag_node(state: AgentState) -> dict:
        return await rag_node(state, db)

    graph.add_node("rag", _rag_node)

    # 工具调用节点（需要db）
    async def _tool_node(state: AgentState) -> dict:
        return await tool_node(state, db)

    graph.add_node("tool", _tool_node)

    # 生成回答节点
    graph.add_node(
        "generate",
        generate_node,
    )

    # 置信度判断节点
    graph.add_node(
        "confidence",
        confidence_node,
    )

    # 转人工节点
    graph.add_node(
        "transfer",
        transfer_node,
    )

    # 闲聊快速回复节点
    from app.agent.nodes.chitchat import chitchat_node

    graph.add_node("chitchat", chitchat_node)

    # ── 设置入口节点 ──
    graph.set_entry_point("emotion")

    # ── 注册条件边 ──

    # 情绪检测 → 意图识别 or 转人工
    graph.add_conditional_edges(
        "emotion",
        route_after_emotion,
        {
            "intent": "intent",
            "transfer": "transfer",
        },
    )

    # 意图识别 → 工具 or RAG or 生成 or 闲聊 or 转人工
    graph.add_conditional_edges(
        "intent",
        route_after_intent,
        {
            "tool": "tool",
            "rag": "rag",
            "generate": "generate",
            "chitchat": "chitchat",
            "transfer": "transfer",
        },
    )

    # 闲聊 → 直接结束（确定性回复，不走后续流程）
    graph.add_edge("chitchat", END)

    # RAG检索 → 工具调用 or 生成 or 转人工
    graph.add_conditional_edges(
        "rag",
        route_after_rag,
        {
            "tool": "tool",
            "generate": "generate",
            "transfer": "transfer",
        },
    )

    # 工具调用 → 生成
    graph.add_conditional_edges(
        "tool",
        route_after_tool,
        {
            "generate": "generate",
        },
    )

    # 生成回答 → 置信度判断 or 转人工
    graph.add_conditional_edges(
        "generate",
        route_after_generate,
        {
            "confidence": "confidence",
            "transfer": "transfer",
        },
    )

    # 置信度判断 → 结束 or 转人工
    graph.add_conditional_edges(
        "confidence",
        route_after_confidence,
        {
            END: END,
            "transfer": "transfer",
        },
    )

    # 转人工 → 结束
    graph.add_edge("transfer", END)

    return graph.compile()


# ==================== 对外调用入口 ====================


def build_agent_graph() -> StateGraph:
    """
    构建 Agent 工作流图（不含DB依赖，用于可视化）
    """
    graph = StateGraph(AgentState)

    graph.add_node("emotion", emotion_node)
    graph.add_node("intent", intent_node)

    async def _rag_node(state: AgentState) -> dict:
        from app.agent.nodes.rag import rag_node

        return await rag_node(state, None)

    async def _tool_node(state: AgentState) -> dict:
        return await tool_node(state, None)

    graph.add_node("rag", _rag_node)
    graph.add_node("tool", _tool_node)
    graph.add_node("generate", generate_node)
    graph.add_node("confidence", confidence_node)
    graph.add_node("transfer", transfer_node)

    # 闲聊快速回复节点
    from app.agent.nodes.chitchat import chitchat_node

    graph.add_node("chitchat", chitchat_node)

    graph.set_entry_point("emotion")

    graph.add_conditional_edges(
        "emotion",
        route_after_emotion,
        {"intent": "intent", "transfer": "transfer"},
    )

    graph.add_conditional_edges(
        "intent",
        route_after_intent,
        {"rag": "rag", "chitchat": "chitchat", "transfer": "transfer"},
    )

    # 闲聊 → 直接结束
    graph.add_edge("chitchat", END)

    graph.add_conditional_edges(
        "rag",
        route_after_rag,
        {"tool": "tool", "generate": "generate", "transfer": "transfer"},
    )

    graph.add_conditional_edges(
        "tool",
        route_after_tool,
        {"generate": "generate"},
    )

    graph.add_conditional_edges(
        "generate",
        route_after_generate,
        {"confidence": "confidence", "transfer": "transfer"},
    )

    graph.add_conditional_edges(
        "confidence",
        route_after_confidence,
        {END: END, "transfer": "transfer"},
    )

    graph.add_edge("transfer", END)

    return graph.compile()


async def run_agent(
    query: str,
    conversation_id: int,
    bot_id: int,
    agent_id: int,
    channel_token: str,
    db: AsyncSession,
    history: Optional[list] = None,
    user_id: Optional[int] = None,
    user_summary: Optional[str] = None,
) -> dict:
    """
    Agent工作流对外调用入口

    每次用户发消息调用一次，返回Agent的处理结果

    Args:
        query: 用户问题
        conversation_id: 会话ID
        bot_id: Bot ID
        agent_id: Agent ID
        channel_token: 渠道Token
        db: 数据库Session
        history: 对话历史列表
        user_id: 用户ID（已登录时有值）
        user_summary: 用户信息摘要

    Returns:
        {
            "final_answer": str,        最终回答
            "need_transfer": bool,      是否转人工
            "transfer_reason": str,     转人工原因
            "answer_source": str,       回答来源
            "intent": str,              识别到的意图
            "emotion": str,             检测到的情绪
            "confidence_score": float,  置信度
            "elapsed_ms": float,        耗时
        }
    """
    import time

    start_time = time.time()

    print(
        f"[GRAPH] 🤖 Agent工作流启动 "
        f"query='{query}' conversation_id={conversation_id} bot_id={bot_id}"
    )

    # ── 构建初始状态 ──
    initial_state = create_initial_state(
        query=query,
        conversation_id=conversation_id,
        bot_id=bot_id,
        agent_id=agent_id,
        channel_token=channel_token,
        history=history or [],
        user_id=user_id,
        user_summary=user_summary,
    )

    # ── 构建并执行工作流 ──
    print(f"[GRAPH] ├─ 构建工作流图")
    try:
        graph = build_graph(db)
        print(f"[GRAPH] ├─ 执行工作流...")
        final_state = await graph.ainvoke(initial_state)
        print(f"[GRAPH] └─ 工作流执行完成")

    except Exception as e:
        logger.error(f"Agent工作流执行异常: {e}")
        elapsed_ms = round((time.time() - start_time) * 1000, 2)
        return {
            "final_answer": "非常抱歉，系统出现异常，请稍后重试或联系人工客服。",
            "need_transfer": False,
            "transfer_reason": None,
            "answer_source": "error",
            "intent": None,
            "emotion": None,
            "confidence_score": 0.0,
            "elapsed_ms": elapsed_ms,
            "error": str(e),
        }

    elapsed_ms = round((time.time() - start_time) * 1000, 2)

    # ── 提取卡片数据 ──
    tool_results = final_state.get("tool_results", [])
    card_type = None
    card_data = None
    for tr in tool_results:
        if tr.get("success") and tr.get("data"):
            data = tr["data"]
            if isinstance(data, dict):
                if data.get("card_type") == "order":
                    card_type = "order"
                    card_data = data.get("card_data")
                    break
                elif data.get("card_type") == "order_list":
                    card_type = "order_list"
                    card_data = data.get("card_data")
                    break
                elif data.get("card_type") == "orders_list":
                    card_type = "orders_list"
                    card_data = data.get("card_data")
                    break
                elif data.get("card_type") == "logistics":
                    card_type = "logistics"
                    card_data = data.get("card_data")
                    break
                elif data.get("card_type") == "product_list":
                    card_type = "product_list"
                    card_data = data.get("card_data")
                    break

    # ── 提取结果 ──
    result = {
        "final_answer": final_state.get("final_answer", ""),
        "need_transfer": final_state.get("need_transfer", False),
        "transfer_reason": final_state.get("transfer_reason"),
        "answer_source": final_state.get("answer_source", "unknown"),
        "intent": (
            final_state.get("intent").value if final_state.get("intent") else None
        ),
        "emotion": (
            final_state.get("emotion").value if final_state.get("emotion") else None
        ),
        "confidence_score": final_state.get("confidence_score", 0.0),
        "llm_tokens_used": final_state.get("llm_tokens_used", 0),
        "elapsed_ms": elapsed_ms,
        "error": final_state.get("error"),
        "tool_results": tool_results,
    }

    if card_type and card_data:
        result["card_type"] = card_type
        result["card_data"] = card_data

    logger.info(
        f"Agent工作流完成 "
        f"answer_source={result['answer_source']} "
        f"need_transfer={result['need_transfer']} "
        f"elapsed_ms={elapsed_ms}ms"
    )

    return result
