# backend/app/agent/state.py
from typing import Optional, List, Any
from typing_extensions import TypedDict, Annotated
from enum import Enum
import operator


# ==================== 枚举定义 ====================


class IntentType(str, Enum):
    """用户意图类型"""

    ORDER_QUERY = "order_query"  # 订单查询
    ORDER_LIST = "order_list"  # 订单列表查询
    LOGISTICS_QUERY = "logistics_query"  # 物流查询
    REFUND_REQUEST = "refund_request"  # 退款申请
    PRODUCT_QUERY = "product_query"  # 商品咨询
    COMPLAINT = "complaint"  # 投诉
    GENERAL = "general"  # 通用咨询
    UNKNOWN = "unknown"  # 未知意图


class EmotionType(str, Enum):
    """情绪类型"""

    POSITIVE = "positive"  # 正面情绪
    NEUTRAL = "neutral"  # 中性情绪
    NEGATIVE = "negative"  # 负面情绪
    ANGRY = "angry"  # 愤怒（需特殊处理）


class AgentAction(str, Enum):
    """Agent下一步动作"""

    DETECT_EMOTION = "detect_emotion"  # 检测情绪
    RECOGNIZE_INTENT = "recognize_intent"  # 识别意图
    RETRIEVE_RAG = "retrieve_rag"  # RAG检索
    CALL_TOOL = "call_tool"  # 调用工具
    GENERATE = "generate"  # 生成回答
    CHECK_CONFIDENCE = "check_confidence"  # 检查置信度
    TRANSFER = "transfer"  # 转人工
    END = "end"  # 结束


# ==================== 消息格式 ====================


class MessageItem(TypedDict):
    """对话历史消息"""

    role: str  # user / assistant / system
    content: str  # 消息内容


class ToolResult(TypedDict):
    """工具调用结果"""

    tool_name: str  # 工具名称
    success: bool  # 是否成功
    data: Any  # 返回数据（可能包含 card_type 和 card_data）
    error_msg: Optional[str]  # 错误信息


class RagResult(TypedDict):
    """RAG检索结果"""

    item_id: int
    title: str
    answer: str
    answer_type: int
    score: float
    matched_question: str


# ==================== Agent 状态定义 ====================


class AgentState(TypedDict):
    """
    LangGraph Agent 全局状态

    整个工作流中所有节点共享这个状态
    节点读取需要的字段，写入自己产生的字段
    """

    # ── 输入信息 ──
    query: str
    """当前用户问题"""

    conversation_id: int
    """会话ID"""

    user_id: Optional[int]
    """用户ID（已登录时有值）"""

    bot_id: int
    """Bot ID"""

    agent_id: int
    """Agent ID"""

    channel_token: str
    """渠道Token"""

    # ── 对话历史 ──
    history: List[MessageItem]
    """最近N轮对话历史（已格式化为 role/content 格式）"""

    # ── 用户信息摘要 ──
    user_summary: Optional[str]
    """用户基本信息+最近订单摘要（注入Prompt用）"""

    # ── 情绪检测结果 ──
    emotion: Optional[EmotionType]
    """检测到的情绪类型"""

    emotion_score: float
    """情绪强度分数 0-1"""

    need_transfer_by_emotion: bool
    """是否因情绪激动触发转人工"""

    # ── 意图识别结果 ──
    intent: Optional[IntentType]
    """识别到的意图"""

    intent_confidence: float
    """意图置信度 0-1"""

    extracted_entities: dict
    """从query中提取的实体，如订单号、商品名等
    示例：{"order_no": "ORD20240101001", "product_name": "手机"}
    """

    # ── RAG检索结果 ──
    rag_results: List[RagResult]
    """RAG检索结果列表"""

    rag_context: Optional[str]
    """格式化后的RAG上下文（注入Prompt用）"""

    # ── 工具调用 ──
    tool_calls: List[str]
    """计划调用的工具列表"""

    tool_results: List[ToolResult]
    """工具调用结果列表（使用operator.add累积）"""

    # ── 生成结果 ──
    generated_answer: Optional[str]
    """大模型生成的回答"""

    answer_source: Optional[str]
    """回答来源：rag / tool / llm / keyword"""

    # ── 置信度判断 ──
    confidence_score: float
    """最终置信度分数 0-1"""

    confidence_passed: bool
    """是否通过置信度阈值"""

    no_answer_count: int
    """连续未回答次数（从Redis读取）"""

    # ── 最终输出 ──
    final_answer: Optional[str]
    """最终输出给用户的回答"""

    need_transfer: bool
    """是否需要转人工"""

    transfer_reason: Optional[str]
    """转人工原因：emotion / no_answer / user_request / tool_fail"""

    # ── 流程控制 ──
    next_action: Optional[AgentAction]
    """下一步执行的动作（路由判断用）"""

    error: Optional[str]
    """错误信息（节点执行异常时记录）"""

    # ── 元信息 ──
    llm_tokens_used: int
    """本次调用消耗的Token数"""

    elapsed_ms: float
    """总耗时（毫秒）"""


# ==================== 初始状态工厂 ====================


def create_initial_state(
    query: str,
    conversation_id: int,
    bot_id: int,
    agent_id: int,
    channel_token: str,
    history: Optional[List[MessageItem]] = None,
    user_id: Optional[int] = None,
    user_summary: Optional[str] = None,
) -> AgentState:
    """
    创建Agent初始状态

    每次用户发消息，调用此函数初始化状态
    再交给 LangGraph 工作流处理
    """
    return AgentState(
        # 输入信息
        query=query,
        conversation_id=conversation_id,
        user_id=user_id,
        bot_id=bot_id,
        agent_id=agent_id,
        channel_token=channel_token,
        # 对话历史
        history=history or [],
        user_summary=user_summary,
        # 情绪检测（待填充）
        emotion=None,
        emotion_score=0.0,
        need_transfer_by_emotion=False,
        # 意图识别（待填充）
        intent=None,
        intent_confidence=0.0,
        extracted_entities={},
        # RAG检索（待填充）
        rag_results=[],
        rag_context=None,
        # 工具调用（待填充）
        tool_calls=[],
        tool_results=[],
        # 生成结果（待填充）
        generated_answer=None,
        answer_source=None,
        # 置信度（待填充）
        confidence_score=0.0,
        confidence_passed=False,
        no_answer_count=0,
        # 最终输出（待填充）
        final_answer=None,
        need_transfer=False,
        transfer_reason=None,
        # 流程控制
        next_action=None,
        error=None,
        # 元信息
        llm_tokens_used=0,
        elapsed_ms=0.0,
    )


# ==================== 状态更新辅助函数 ====================


def state_set_transfer(
    reason: str,
) -> dict:
    """
    生成触发转人工的状态更新
    在任意节点中调用：return state_set_transfer("emotion")
    """
    return {
        "need_transfer": True,
        "transfer_reason": reason,
        "next_action": AgentAction.TRANSFER,
    }


def state_set_answer(
    answer: str,
    source: str,
    confidence: float = 1.0,
) -> dict:
    """
    生成设置最终答案的状态更新
    在generate节点中调用
    """
    return {
        "generated_answer": answer,
        "final_answer": answer,
        "answer_source": source,
        "confidence_score": confidence,
        "confidence_passed": True,
        "next_action": AgentAction.END,
    }


def state_set_error(error_msg: str) -> dict:
    """记录错误并结束流程"""
    return {
        "error": error_msg,
        "next_action": AgentAction.END,
    }
