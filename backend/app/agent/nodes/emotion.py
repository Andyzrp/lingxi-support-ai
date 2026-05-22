# backend/app/agent/nodes/emotion.py
import logging
from typing import Optional
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from app.agent.state import AgentState, EmotionType, AgentAction, state_set_transfer
from app.config import settings

logger = logging.getLogger(__name__)


# ==================== 情绪检测配置 ====================

# 情绪激动触发转人工的阈值
ANGRY_TRANSFER_THRESHOLD = 0.85

# 负面情绪分数阈值（超过则记录，但不一定转人工）
NEGATIVE_THRESHOLD = 0.7


# ==================== 规则关键词 ====================

ANGRY_KEYWORDS = [
    "垃圾",
    "骗子",
    "骗人",
    "太差了",
    "极差",
    "投诉",
    "举报",
    "曝光",
    "维权",
    "律师",
    "气死",
    "愤怒",
    "混蛋",
    "坑爹",
    "坑人",
    "退款退款",
    "要退款",
    "必须退",
    "强烈要求",
    "你们这什么态度",
    "服务太差",
    "太不负责",
]

NEGATIVE_KEYWORDS = [
    "不满意",
    "失望",
    "差评",
    "不好",
    "质量差",
    "等了很久",
    "迟迟",
    "一直没有",
    "还没到",
    "怎么还没",
    "催一下",
    "赶紧",
    "尽快",
]

POSITIVE_KEYWORDS = [
    "谢谢",
    "感谢",
    "很好",
    "满意",
    "不错",
    "棒",
    "赞",
    "好评",
    "喜欢",
    "完美",
]


# ==================== 规则情绪检测 ====================


def _rule_based_emotion(query: str) -> Optional[dict]:
    """
    规则优先情绪检测（速度快，无需调用LLM）

    Args:
        query: 用户输入

    Returns:
        命中规则时返回dict，未命中返回None
    """
    query_lower = query.strip().lower()

    # 检测愤怒情绪
    angry_hits = [kw for kw in ANGRY_KEYWORDS if kw in query_lower]
    if angry_hits:
        score = min(0.7 + len(angry_hits) * 0.1, 1.0)
        return {
            "emotion": EmotionType.ANGRY,
            "emotion_score": round(score, 2),
            "reason": f"规则命中愤怒关键词: {angry_hits[:3]}",
        }

    # 检测负面情绪
    negative_hits = [kw for kw in NEGATIVE_KEYWORDS if kw in query_lower]
    if negative_hits:
        score = min(0.5 + len(negative_hits) * 0.1, 0.85)
        return {
            "emotion": EmotionType.NEGATIVE,
            "emotion_score": round(score, 2),
            "reason": f"规则命中负面关键词: {negative_hits[:3]}",
        }

    # 检测正面情绪
    positive_hits = [kw for kw in POSITIVE_KEYWORDS if kw in query_lower]
    if positive_hits:
        return {
            "emotion": EmotionType.POSITIVE,
            "emotion_score": 0.9,
            "reason": f"规则命中正面关键词: {positive_hits[:3]}",
        }

    return {
        "emotion": EmotionType.NEUTRAL,
        "emotion_score": 0.5,
        "reason": "规则未命中情绪关键词，默认中性",
    }


# ==================== LLM情绪检测 ====================

EMOTION_SYSTEM_PROMPT = """你是一个情绪检测助手，专门分析电商客服场景中用户的情绪状态。

请分析用户的消息，判断其情绪类型和强度。

情绪类型：
- positive: 正面情绪（满意、感谢、高兴）
- neutral: 中性情绪（普通咨询、无明显情绪）
- negative: 负面情绪（不满意、失望、担忧）
- angry: 愤怒情绪（强烈不满、投诉、威胁）

请严格按以下JSON格式返回，不要有任何其他内容：
{
  "emotion": "情绪类型",
  "emotion_score": 0.85,
  "reason": "简短说明"
}

emotion_score说明：
- 0.0~0.3: 情绪很弱
- 0.3~0.6: 情绪中等
- 0.6~0.85: 情绪较强
- 0.85~1.0: 情绪非常强烈"""


async def _llm_emotion(query: str, history: list) -> dict:
    """
    调用LLM检测情绪（规则未命中时使用）

    Args:
        query: 用户问题
        history: 对话历史（最近2轮）

    Returns:
        情绪检测结果dict
    """
    import json

    llm = ChatOpenAI(
        base_url=settings.LLM_BASE_URL,
        api_key=settings.LLM_API_KEY,
        model=settings.LLM_MODEL,
        temperature=0.0,
        max_tokens=128,
    )

    # 构建历史上下文
    history_text = ""
    if history:
        recent = history[-4:]
        lines = []
        for msg in recent:
            role = "用户" if msg["role"] == "user" else "客服"
            lines.append(f"{role}：{msg['content']}")
        history_text = "\n".join(lines)

    user_content = f"用户消息：{query}"
    if history_text:
        user_content = f"对话历史：\n{history_text}\n\n{user_content}"

    try:
        response = await llm.ainvoke(
            [
                SystemMessage(content=EMOTION_SYSTEM_PROMPT),
                HumanMessage(content=user_content),
            ]
        )

        raw = response.content.strip()

        # 清理markdown代码块
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        raw = raw.strip()

        try:
            result = json.loads(raw)
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(
                f"情绪检测JSON解析失败，尝试正则提取: {e}\n原始内容: {raw[:200]}"
            )
            import re

            em = re.search(r'"emotion"\s*:\s*"(\w+)"', raw)
            sc = re.search(r'"emotion_score"\s*:\s*([\d.]+)', raw)
            if em:
                try:
                    emotion = EmotionType(em.group(1))
                except ValueError:
                    emotion = EmotionType.NEUTRAL
                return {
                    "emotion": emotion,
                    "emotion_score": float(sc.group(1)) if sc else 0.5,
                    "reason": "正则提取",
                }
            return {
                "emotion": EmotionType.NEUTRAL,
                "emotion_score": 0.5,
                "reason": "解析失败，默认中性",
            }

        # 验证emotion字段合法性
        emotion_str = result.get("emotion", "neutral")
        try:
            emotion = EmotionType(emotion_str)
        except ValueError:
            emotion = EmotionType.NEUTRAL

        return {
            "emotion": emotion,
            "emotion_score": float(result.get("emotion_score", 0.5)),
            "reason": result.get("reason", ""),
        }

    except Exception as e:
        logger.error(f"情绪检测JSON解析失败: {e}")
        return {
            "emotion": EmotionType.NEUTRAL,
            "emotion_score": 0.3,
            "reason": "JSON解析失败，默认中性",
        }
    except Exception as e:
        logger.error(f"LLM情绪检测失败: {e}")
        return {
            "emotion": EmotionType.NEUTRAL,
            "emotion_score": 0.3,
            "reason": f"LLM调用失败: {str(e)}",
        }


# ==================== 情绪检测节点 ====================


async def emotion_node(state: AgentState) -> dict:
    """
    LangGraph 情绪检测节点

    执行流程：
    1. 规则关键词优先检测（速度快）
    2. 规则未命中 → 调用LLM检测
    3. 判断是否触发转人工
    4. 更新状态并决定下一步动作

    Args:
        state: 当前Agent状态

    Returns:
        状态更新dict
    """
    query = state["query"]
    history = state.get("history", [])

    logger.info(f"情绪检测节点开始 query='{query}'")

    # ── Step1：规则优先检测 ──
    rule_result = _rule_based_emotion(query)

    if rule_result:
        emotion = rule_result["emotion"]
        emotion_score = rule_result["emotion_score"]
        logger.info(
            f"规则命中情绪: {emotion} "
            f"score={emotion_score} "
            f"reason={rule_result['reason']}"
        )
    else:
        # ── Step2：LLM检测 ──
        llm_result = await _llm_emotion(query, history)
        emotion = llm_result["emotion"]
        emotion_score = llm_result["emotion_score"]
        logger.info(f"LLM检测情绪: {emotion} score={emotion_score}")

    # ── Step3：判断是否触发转人工 ──
    need_transfer_by_emotion = (
        emotion == EmotionType.ANGRY and emotion_score >= ANGRY_TRANSFER_THRESHOLD
    )

    if need_transfer_by_emotion:
        logger.info(f"情绪激动触发转人工 emotion={emotion} score={emotion_score}")
        return {
            "emotion": emotion,
            "emotion_score": emotion_score,
            "need_transfer_by_emotion": True,
            **state_set_transfer("emotion"),
        }

    # ── Step4：正常流程，进入意图识别 ──
    logger.info(
        f"情绪检测完成 emotion={emotion} score={emotion_score} need_transfer=False"
    )

    return {
        "emotion": emotion,
        "emotion_score": emotion_score,
        "need_transfer_by_emotion": False,
        "next_action": AgentAction.RECOGNIZE_INTENT,
    }
