from typing import Any, Dict
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.user import User
from app.services.analytics import (
    AnalyticsDateRange,
    get_recurring_expenses,
    get_savings_opportunities,
    get_spending_summary,
)
from app.services.profile import is_profile_complete


def get_profile_context_tool(db: Session, user_id: UUID) -> Dict[str, Any]:
    user = db.get(User, user_id)
    if user is None:
        return {"profile_complete": False}

    return {
        "name": user.name,
        "monthly_income": float(user.monthly_income)
        if user.monthly_income is not None
        else None,
        "savings_goal": float(user.savings_goal)
        if user.savings_goal is not None
        else None,
        "current_savings": float(user.current_savings)
        if user.current_savings is not None
        else None,
        "financial_priority": user.financial_priority,
        "coaching_tone": user.coaching_tone,
        "profile_complete": is_profile_complete(user),
    }


def get_spending_summary_tool(
    db: Session,
    user_id: UUID,
    date_range: AnalyticsDateRange,
) -> Dict[str, Any]:
    return get_spending_summary(db, user_id, date_range).model_dump(mode="json")


def get_recurring_expenses_tool(
    db: Session,
    user_id: UUID,
    date_range: AnalyticsDateRange,
) -> Dict[str, Any]:
    return get_recurring_expenses(db, user_id, date_range).model_dump(mode="json")


def get_savings_opportunities_tool(
    db: Session,
    user_id: UUID,
    date_range: AnalyticsDateRange,
) -> Dict[str, Any]:
    return get_savings_opportunities(db, user_id, date_range).model_dump(mode="json")
