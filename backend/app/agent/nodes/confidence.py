# backend/app/agent/nodes/confidence.py
import logging
from app.agent.state import (
    AgentState, AgentAction,
    state_set_transfer,
)

logger = logging.getLogger(__name__)

DEFAULT_CONFIDENCE_THRESHOLD = 0.6
DEFAULT_MAX_NO_ANSWER_COUNT = 3
NO_ANSWER_COUNT_KEY = "agent:no_answer_count:{conversation_id}"


async def _get_no_answer_count(conversation_id: int) -> int:
    from app.core.redis import redis_client
    key = NO_ANSWER_COUNT_KEY.format(conversation_id=conversation_id)
    try:
        val = await redis_client.get(key)
        return int(val) if val else 0
    except Exception as e:
        logger.error(f"获取未回答计数失败: {e}")
        return 0


async def _increment_no_answer_count(conversation_id: int) -> int:
    from app.core.redis import redis_client
    key = NO_ANSWER_COUNT_KEY.format(conversation_id=conversation_id)
    try:
        count = await redis_client.incr(key)
        await redis_client.expire(key, 3600)
        return count
    except Exception as e:
        logger.error(f"累加未回答计数失败: {e}")
        return 1


async def _reset_no_answer_count(conversation_id: int):
    from app.core.redis import redis_client
    key = NO_ANSWER_COUNT_KEY.format(conversation_id=conversation_id)
    try:
        await redis_client.delete(key)
    except Exception as e:
        logger.error(f"重置未回答计数失败: {e}")


def _evaluate_confidence(state: AgentState) -> tuple[float, bool]:
    confidence = state.get("confidence_score", 0.0)
    answer_source = state.get("answer_source", "")
    final_answer = state.get("final_answer", "")

    source_weight = {
        "tool": 1.0,
        "rag": 1.0,
        "keyword": 1.0,
        "llm": 0.9,
        "default": 0.0,
    }
    weight = source_weight.get(answer_source, 0.5)
    adjusted_confidence = confidence * weight

    if not final_answer or len(final_answer.strip()) < 5:
        return 0.0, False

    no_answer_phrases = [
        "暂时无法回答",
        "无法给出满意",
        "换个方式描述",
        "联系人工客服",
    ]
    if any(phrase in final_answer for phrase in no_answer_phrases):
        return 0.0, False

    passed = adjusted_confidence >= DEFAULT_CONFIDENCE_THRESHOLD

    logger.info(
        f"置信度评估 raw={confidence} source={answer_source} "
        f"weight={weight} adjusted={adjusted_confidence:.3f} "
        f"passed={passed}"
    )

    return round(adjusted_confidence, 3), passed


def _build_guided_no_answer_reply(
    state: AgentState,
    current_count: int,
    remaining: int,
) -> str:
    if current_count == 1:
        return (
            "非常抱歉，我暂时无法准确回答您的问题。\n"
            "您可以尝试：\n"
            "1. 换个方式描述您的问题\n"
            "2. 提供更多相关信息（如订单号）\n"
            "3. 或者告诉我您需要什么帮助"
        )
    return (
        "非常抱歉，我理解您的问题但暂时无法给出满意的答复。\n"
        "建议转接人工客服处理，人工客服将为您提供更专业的服务。\n\n"
        "请问是否需要转接人工客服？"
    )


async def confidence_node(state: AgentState) -> dict:
    conversation_id = state["conversation_id"]

    logger.info(
        f"置信度判断节点开始 "
        f"conversation_id={conversation_id}"
    )

    adjusted_confidence, passed = _evaluate_confidence(state)

    if passed:
        logger.info(
            f"置信度通过 confidence={adjusted_confidence} "
            f"conversation_id={conversation_id}"
        )
        await _reset_no_answer_count(conversation_id)
        return {
            "confidence_score": adjusted_confidence,
            "confidence_passed": True,
            "no_answer_count": 0,
            "next_action": AgentAction.END,
        }

    logger.info(
        f"置信度未通过 confidence={adjusted_confidence} "
        f"conversation_id={conversation_id}"
    )

    new_count = await _increment_no_answer_count(conversation_id)

    logger.info(
        f"未回答计数 count={new_count} "
        f"max={DEFAULT_MAX_NO_ANSWER_COUNT}"
    )

    if new_count >= DEFAULT_MAX_NO_ANSWER_COUNT:
        logger.info(
            f"连续未回答{new_count}次，触发转人工 "
            f"conversation_id={conversation_id}"
        )
        await _reset_no_answer_count(conversation_id)
        return {
            "confidence_score": adjusted_confidence,
            "confidence_passed": False,
            "no_answer_count": new_count,
            **state_set_transfer("no_answer"),
        }

    remaining = DEFAULT_MAX_NO_ANSWER_COUNT - new_count
    default_reply = _build_guided_no_answer_reply(
        state=state,
        current_count=new_count,
        remaining=remaining,
    )

    return {
        "confidence_score": adjusted_confidence,
        "confidence_passed": False,
        "no_answer_count": new_count,
        "final_answer": default_reply,
        "next_action": AgentAction.END,
    }