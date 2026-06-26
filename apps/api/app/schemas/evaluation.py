from datetime import datetime
from typing import Any, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class EvaluationSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    citation_score: Optional[float] = None
    calculation_score: Optional[float] = None
    groundedness_score: Optional[float] = None
    hallucination_flag: bool
    safety_flag: bool
    created_at: datetime


class SuggestedScores(BaseModel):
    citation_score: float
    calculation_score: float
    groundedness_score: float
    hallucination_flag: bool
    safety_flag: bool


class AIRunItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    prompt: str
    response: Optional[str] = None
    model: Optional[str] = None
    latency_ms: Optional[int] = None
    estimated_cost: Optional[float] = None
    retrieval_count: Optional[int] = None
    tool_calls: Optional[Any] = None
    created_at: datetime
    evaluation: Optional[EvaluationSummary] = None
    suggested_scores: Optional[SuggestedScores] = None


class AIRunListResponse(BaseModel):
    items: List[AIRunItem]
    total: int
    limit: int
    offset: int


class EvaluationItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    ai_run_id: UUID
    citation_score: Optional[float] = None
    calculation_score: Optional[float] = None
    groundedness_score: Optional[float] = None
    hallucination_flag: bool
    safety_flag: bool
    created_at: datetime


class EvaluationListResponse(BaseModel):
    items: List[EvaluationItem]
    total: int


class EvaluationSubmit(BaseModel):
    citation_score: float = Field(..., ge=0.0, le=1.0)
    calculation_score: float = Field(..., ge=0.0, le=1.0)
    groundedness_score: float = Field(..., ge=0.0, le=1.0)
    hallucination_flag: bool
    safety_flag: bool


class EvaluationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    ai_run_id: UUID
    citation_score: Optional[float] = None
    calculation_score: Optional[float] = None
    groundedness_score: Optional[float] = None
    hallucination_flag: bool
    safety_flag: bool
    created_at: datetime
