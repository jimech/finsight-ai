from datetime import date
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel


class MonthlyPlanRequest(BaseModel):
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class PlanTarget(BaseModel):
    monthly_savings_goal: float
    current_estimated_savings: float
    gap: float


class RecommendedCut(BaseModel):
    category: str
    current_spending: float
    recommended_cut: float
    reason: str


class WeeklyStep(BaseModel):
    week: int
    action: str


class PlanCitation(BaseModel):
    label: str
    source: str


class MonthlyPlanResponse(BaseModel):
    target: PlanTarget
    recommended_cuts: List[RecommendedCut]
    weekly_steps: List[WeeklyStep]
    assumptions: List[str]
    citations: List[PlanCitation]
    ai_run_id: UUID
