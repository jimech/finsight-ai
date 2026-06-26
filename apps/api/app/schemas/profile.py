from datetime import datetime
from typing import Literal, Optional, Tuple
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

CoachingTone = Literal["supportive", "direct", "playful"]
FinancialPriority = Literal[
    "save_money",
    "reduce_spending",
    "pay_down_debt",
    "build_emergency_fund",
    "understand_spending",
]

COACHING_TONES: Tuple[str, ...] = ("supportive", "direct", "playful")
FINANCIAL_PRIORITIES: Tuple[str, ...] = (
    "save_money",
    "reduce_spending",
    "pay_down_debt",
    "build_emergency_fund",
    "understand_spending",
)


class ProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str
    name: Optional[str] = None
    monthly_income: Optional[float] = None
    savings_goal: Optional[float] = None
    current_savings: Optional[float] = None
    financial_priority: Optional[str] = None
    coaching_tone: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class ProfileUpdate(BaseModel):
    name: Optional[str] = Field(default=None, max_length=255)
    monthly_income: Optional[float] = None
    savings_goal: Optional[float] = None
    current_savings: Optional[float] = None
    financial_priority: Optional[FinancialPriority] = None
    coaching_tone: Optional[CoachingTone] = None

    @field_validator("monthly_income", "savings_goal", "current_savings")
    @classmethod
    def validate_non_negative(cls, value: Optional[float]) -> Optional[float]:
        if value is not None and value < 0:
            raise ValueError("must be non-negative")
        return value
