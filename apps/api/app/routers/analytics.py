from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.types import AuthenticatedUser
from app.db.session import get_db
from app.schemas.analytics import (
    CategoryBreakdownResponse,
    RecurringExpensesResponse,
    SavingsOpportunitiesResponse,
    SpendingSummaryResponse,
)
from app.services.analytics import (
    AnalyticsDateRange,
    get_category_breakdown,
    get_recurring_expenses,
    get_savings_opportunities,
    get_spending_summary,
)
from app.services.users import get_or_create_user_from_auth

router = APIRouter(prefix="/transactions", tags=["analytics"])


@router.get("/summary", response_model=SpendingSummaryResponse)
def transactions_summary(
    start_date: Optional[date] = Query(default=None),
    end_date: Optional[date] = Query(default=None),
    db: Session = Depends(get_db),
    authenticated_user: AuthenticatedUser = Depends(get_current_user),
):
    user = get_or_create_user_from_auth(db, authenticated_user)
    date_range = AnalyticsDateRange(start_date=start_date, end_date=end_date)
    return get_spending_summary(db, user.id, date_range)


@router.get("/categories", response_model=CategoryBreakdownResponse)
def transactions_categories(
    start_date: Optional[date] = Query(default=None),
    end_date: Optional[date] = Query(default=None),
    db: Session = Depends(get_db),
    authenticated_user: AuthenticatedUser = Depends(get_current_user),
):
    user = get_or_create_user_from_auth(db, authenticated_user)
    date_range = AnalyticsDateRange(start_date=start_date, end_date=end_date)
    return get_category_breakdown(db, user.id, date_range)


@router.get("/recurring", response_model=RecurringExpensesResponse)
def transactions_recurring(
    start_date: Optional[date] = Query(default=None),
    end_date: Optional[date] = Query(default=None),
    db: Session = Depends(get_db),
    authenticated_user: AuthenticatedUser = Depends(get_current_user),
):
    user = get_or_create_user_from_auth(db, authenticated_user)
    date_range = AnalyticsDateRange(start_date=start_date, end_date=end_date)
    return get_recurring_expenses(db, user.id, date_range)


@router.get("/savings-opportunities", response_model=SavingsOpportunitiesResponse)
def transactions_savings_opportunities(
    start_date: Optional[date] = Query(default=None),
    end_date: Optional[date] = Query(default=None),
    db: Session = Depends(get_db),
    authenticated_user: AuthenticatedUser = Depends(get_current_user),
):
    user = get_or_create_user_from_auth(db, authenticated_user)
    date_range = AnalyticsDateRange(start_date=start_date, end_date=end_date)
    return get_savings_opportunities(db, user.id, date_range)
