from pydantic import BaseModel
from typing import List, Optional, Dict


# ==================== 核心指标 ====================
class DashboardSchema(BaseModel):
    total_sessions:      int
    today_sessions:      int
    compared_yesterday:  int
    ai_resolve_rate:     float
    transfer_rate:       float
    avg_response_ms:     Optional[float]
    satisfaction_score:  Optional[float]


# ==================== 会话量趋势 ====================
class SessionsTrendSchema(BaseModel):
    dates:          List[str]
    bot_sessions:   List[int]
    agent_sessions: List[int]
    human_sessions: List[int]


# ==================== 解决率趋势 ====================
class ResolveRateTrendSchema(BaseModel):
    dates:               List[str]
    bot_resolve_rate:    List[float]
    agent_resolve_rate:  List[float]
    overall_resolve_rate: List[float]


# ==================== 意图分布 ====================
class IntentItemSchema(BaseModel):
    intent: str
    count:  int
    rate:   float


# ==================== Top 未解决问题 ====================
class UnansweredItemSchema(BaseModel):
    question: str
    count:    int


# ==================== 满意度统计 ====================
class TagCountSchema(BaseModel):
    tag:   str
    count: int


class SatisfactionSchema(BaseModel):
    avg_score:           float
    total_evaluations:   int
    score_distribution:  Dict[str, int]
    top_tags:            List[TagCountSchema]