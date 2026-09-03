# backend/app/agent/nodes/chitchat.py
"""
闲聊快速回复节点

命中 IntentType.CHITCHAT 时直接返回预设友好回复，不走 RAG/LLM/置信度。
响应时间 <100ms，避免打招呼/答谢场景走完整 LLM 链路导致慢且答非所问。
"""
import random
from app.agent.state import AgentState, AgentAction, state_set_answer


# 各子类型的回复候选（随机选一条，避免重复感）
CHITCHAT_REPLIES = {
    "greeting": [
        "您好～我是灵犀智能客服小灵，有什么可以帮您？😊",
        "您好呀！很高兴为您服务～请告诉我您需要什么帮助？",
        "嗨～我是小灵，可以帮您查询订单、物流、商品信息等，请问有什么需求？",
        "您好！我是灵犀智能客服，您可以直接告诉我您想查询什么哦～",
    ],
    "thanks": [
        "不客气，很高兴能帮到您～有问题随时找我哦！",
        "不用谢～为您服务是我的荣幸，还有其他需要帮忙的吗？",
        "太客气啦，有任何问题随时召唤小灵～😊",
        "应该的应该的，期待下次为您服务！",
    ],
    "bye": [
        "再见～期待下次见到您，祝您生活愉快！",
        "拜拜～有问题随时回来找我哦，小灵一直都在！",
        "晚安，好梦～明天见！",
        "再见啦，祝您一切顺利！",
    ],
    "identity": [
        "我是灵犀智能客服小灵，可以帮您查询订单、物流、退款进度、商品信息等～请告诉我您需要什么帮助？",
        "我是 AI 客服小灵，24 小时在线为您服务～您可以问我订单、物流、商品相关问题。",
        "我是灵犀智能客服，擅长查询订单状态、物流轨迹、商品信息，也可以帮您发起退款～",
    ],
}

# 兜底（未匹配子类型时）
DEFAULT_REPLY = "您好～我是灵犀智能客服小灵，有什么可以帮您？"


async def chitchat_node(state: AgentState) -> dict:
    """
    闲聊回复节点：根据子类型随机返回预设回复，直接结束。

    流程：intent_node → chitchat_node → END
    不走 RAG / LLM / 置信度检测，响应 <100ms。
    """
    entities = state.get("extracted_entities") or {}
    sub_type = entities.get("chitchat_sub", "")

    replies = CHITCHAT_REPLIES.get(sub_type)
    answer = random.choice(replies) if replies else DEFAULT_REPLY

    print(f"[CHITCHAT] 闲聊分支 sub_type={sub_type} → 直接返回预设回复")

    return {
        **state_set_answer(answer=answer, source="chitchat", confidence=0.95),
        "llm_tokens_used": 0,
        # 闲聊是确定性回复，直接结束，不过置信度
        "next_action": AgentAction.END,
    }
