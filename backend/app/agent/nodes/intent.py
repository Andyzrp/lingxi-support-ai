# backend/app/agent/nodes/intent.py
import logging
import json
from typing import Optional
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from app.agent.state import AgentState, IntentType, AgentAction
from app.config import settings

logger = logging.getLogger(__name__)


# ==================== LLM初始化 ====================


def _get_llm() -> ChatOpenAI:
    return ChatOpenAI(
        base_url=settings.LLM_BASE_URL,
        api_key=settings.LLM_API_KEY,
        model=settings.LLM_MODEL,
        temperature=0.0,
        max_tokens=256,
    )


# ==================== 意图识别Prompt ====================

INTENT_SYSTEM_PROMPT = """你是一个电商客服意图识别助手。
请分析用户的问题，识别其意图，并从以下类型中选择最匹配的一个：

意图类型：
- order_list: 订单列表查询（我有几个订单、所有订单、订单列表、最近订单）
- order_query: 订单详情查询（单个订单状态、订单号查订单）
- logistics_query: 物流相关查询（快递、发货、配送、签收）
- refund_request: 退款相关（申请退款、退货、售后）
- product_query: 商品相关咨询（商品信息、价格、库存、规格）
- complaint: 投诉建议（不满意、投诉、差评）
- general: 通用咨询（其他问题）
- unknown: 无法识别

同时提取用户问题中的关键实体：
- order_no: 订单号（格式通常为字母+数字组合）
- product_name: 商品名称
- logistics_no: 快递单号

请严格按以下JSON格式返回，不要有任何其他内容：
{
  "intent": "意图类型",
  "confidence": 0.95,
  "entities": {
    "order_no": null,
    "product_name": null,
    "logistics_no": null
  },
  "reason": "简短说明识别原因"
}"""


# ==================== 规则优先识别 ====================


def _rule_based_intent(query: str) -> Optional[dict]:
    """
    规则优先识别（速度快，无需调用LLM）

    覆盖高频明确意图，减少LLM调用次数

    Args:
        query: 用户问题

    Returns:
        命中规则时返回结果dict，未命中返回None
    """
    query_lower = query.strip().lower()

    # 物流查询关键词
    logistics_keywords = [
        "快递",
        "物流",
        "发货",
        "配送",
        "签收",
        "到哪了",
        "到了吗",
        "几天到",
        "运单",
        "快递单",
    ]
    for kw in logistics_keywords:
        if kw in query_lower:
            return {
                "intent": IntentType.LOGISTICS_QUERY,
                "confidence": 0.92,
                "entities": {},
                "reason": f"规则命中物流关键词: {kw}",
            }

    # 退款关键词
    refund_keywords = [
        "退款",
        "退货",
        "退钱",
        "申请退",
        "要退",
        "不想要了",
        "取消订单",
        "售后",
    ]
    for kw in refund_keywords:
        if kw in query_lower:
            return {
                "intent": IntentType.REFUND_REQUEST,
                "confidence": 0.93,
                "entities": {},
                "reason": f"规则命中退款关键词: {kw}",
            }

    # 订单列表查询关键词（需优先于单个订单匹配）
    order_list_keywords = [
        "几个订单",
        "多少订单",
        "所有订单",
        "我的订单",
        "全部订单",
        "订单列表",
        "最近订单",
    ]
    for kw in order_list_keywords:
        if kw in query_lower:
            return {
                "intent": IntentType.ORDER_LIST,
                "confidence": 0.92,
                "entities": {},
                "reason": f"规则命中订单列表关键词: {kw}",
            }

    # 订单查询关键词
    order_keywords = [
        "订单",
        "我买的",
        "我的单",
        "付款",
        "下单",
        "购买记录",
        "消费记录",
    ]
    for kw in order_keywords:
        if kw in query_lower:
            return {
                "intent": IntentType.ORDER_QUERY,
                "confidence": 0.90,
                "entities": {},
                "reason": f"规则命中订单关键词: {kw}",
            }

    # 商品查询关键词
    product_keywords = [
        "商品",
        "产品",
        "价格",
        "多少钱",
        "库存",
        "有货吗",
        "规格",
        "型号",
        "颜色",
        "尺寸",
    ]
    for kw in product_keywords:
        if kw in query_lower:
            return {
                "intent": IntentType.PRODUCT_QUERY,
                "confidence": 0.88,
                "entities": {},
                "reason": f"规则命中商品关键词: {kw}",
            }

    # 投诉关键词
    complaint_keywords = [
        "投诉",
        "差评",
        "不满意",
        "太差了",
        "垃圾",
        "骗人",
        "举报",
        "维权",
    ]
    for kw in complaint_keywords:
        if kw in query_lower:
            return {
                "intent": IntentType.COMPLAINT,
                "confidence": 0.91,
                "entities": {},
                "reason": f"规则命中投诉关键词: {kw}",
            }

    return None


# ==================== 实体提取 ====================


def _extract_entities(query: str) -> dict:
    """
    从用户问题中提取关键实体（规则方式）

    Args:
        query: 用户问题

    Returns:
        实体dict
    """
    import re

    entities = {
        "order_no": None,
        "product_name": None,
        "logistics_no": None,
    }

    # 提取订单号（ORD开头 + 字母数字组合）
    order_pattern = r"ORD[A-Z0-9]{10,30}"
    order_match = re.search(order_pattern, query, re.IGNORECASE)
    if order_match:
        entities["order_no"] = order_match.group()

    # 提取快递单号（纯数字，10位以上）
    logistics_pattern = r"\b\d{10,20}\b"
    logistics_match = re.search(logistics_pattern, query)
    if logistics_match:
        entities["logistics_no"] = logistics_match.group()

    return entities


# ==================== LLM意图识别 ====================


async def _llm_intent(query: str, history: list) -> dict:
    """
    调用LLM识别意图（规则未命中时使用）

    Args:
        query: 用户问题
        history: 对话历史（最近2轮）

    Returns:
        意图识别结果dict
    """
    llm = _get_llm()

    # 构建历史上下文
    history_text = ""
    if history:
        recent = history[-4:]  # 最近2轮
        history_lines = []
        for msg in recent:
            role = "用户" if msg["role"] == "user" else "客服"
            history_lines.append(f"{role}：{msg['content']}")
        history_text = "\n".join(history_lines)

    user_content = f"用户问题：{query}"
    if history_text:
        user_content = f"对话历史：\n{history_text}\n\n{user_content}"

    try:
        response = await llm.ainvoke(
            [
                SystemMessage(content=INTENT_SYSTEM_PROMPT),
                HumanMessage(content=user_content),
            ]
        )

        raw = response.content.strip()

        # 清理可能的markdown代码块
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        raw = raw.strip()

        result = json.loads(raw)

        # 验证intent字段合法性
        intent_str = result.get("intent", "unknown")
        try:
            intent = IntentType(intent_str)
        except ValueError:
            intent = IntentType.UNKNOWN

        return {
            "intent": intent,
            "confidence": float(result.get("confidence", 0.7)),
            "entities": result.get("entities", {}),
            "reason": result.get("reason", ""),
        }

    except json.JSONDecodeError as e:
        logger.error(f"意图识别JSON解析失败: {e}, raw={response.content[:200]}")
        return {
            "intent": IntentType.UNKNOWN,
            "confidence": 0.5,
            "entities": {},
            "reason": "JSON解析失败",
        }
    except Exception as e:
        logger.error(f"LLM意图识别失败: {e}")
        return {
            "intent": IntentType.GENERAL,
            "confidence": 0.5,
            "entities": {},
            "reason": f"LLM调用失败: {str(e)}",
        }


# ==================== 意图识别节点 ====================


async def intent_node(state: AgentState) -> dict:
    """
    LangGraph 意图识别节点

    执行流程：
    1. 规则优先识别（速度快）
    2. 规则未命中 → 调用LLM识别
    3. 提取关键实体（订单号/商品名等）
    4. 根据意图决定下一步动作

    Args:
        state: 当前Agent状态

    Returns:
        状态更新dict
    """
    query = state["query"]
    history = state.get("history", [])

    logger.info(f"意图识别节点开始 query='{query}'")

    # ── Step1：规则优先 ──
    rule_result = _rule_based_intent(query)

    if rule_result:
        intent = rule_result["intent"]
        confidence = rule_result["confidence"]
        entities = rule_result.get("entities", {})
        logger.info(f"规则命中意图: {intent} confidence={confidence}")
    else:
        # ── Step2：LLM识别 ──
        llm_result = await _llm_intent(query, history)
        intent = llm_result["intent"]
        confidence = llm_result["confidence"]
        entities = llm_result.get("entities", {})
        logger.info(f"LLM识别意图: {intent} confidence={confidence}")

    # ── Step3：补充实体提取（规则方式） ──
    rule_entities = _extract_entities(query)
    for key, val in rule_entities.items():
        if val and not entities.get(key):
            entities[key] = val

    # ── Step4：决定下一步动作 ──
    next_action = _decide_next_action(intent)

    intent_repr = intent.value if intent else "None"
    print(
        f"[INTENT] 意图识别完成 → [{intent_repr}] "
        f"confidence={confidence:.4f} "
        f"entities={entities} "
        f"next_action={next_action}"
    )

    return {
        "intent": intent,
        "intent_confidence": confidence,
        "extracted_entities": entities,
        "next_action": next_action,
    }


def _decide_next_action(intent: IntentType) -> AgentAction:
    """
    根据意图决定下一步动作

    Args:
        intent: 识别到的意图

    Returns:
        下一步 AgentAction
    """
    # 需要调用工具的意图
    tool_intents = {
        IntentType.ORDER_QUERY,
        IntentType.ORDER_LIST,
        IntentType.LOGISTICS_QUERY,
        IntentType.REFUND_REQUEST,
        IntentType.PRODUCT_QUERY,
    }

    if intent in tool_intents:
        return AgentAction.RETRIEVE_RAG  # 先RAG再工具

    if intent == IntentType.COMPLAINT:
        return AgentAction.RETRIEVE_RAG  # 投诉先查知识库

    # 通用/未知 → 直接RAG
    return AgentAction.RETRIEVE_RAG
