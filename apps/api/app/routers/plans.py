from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.types import AuthenticatedUser
from app.db.session import get_db
from app.schemas.plan import MonthlyPlanRequest, MonthlyPlanResponse
from app.services.analytics import AnalyticsDateRange
from app.services.monthly_plan import generate_monthly_plan
from app.services.users import get_or_create_user_from_auth

router = APIRouter(prefix="/plans", tags=["plans"])


@router.post("/monthly", response_model=MonthlyPlanResponse)
def create_monthly_plan(
    body: MonthlyPlanRequest,
    db: Session = Depends(get_db),
    authenticated_user: AuthenticatedUser = Depends(get_current_user),
):
    user = get_or_create_user_from_auth(db, authenticated_user)
    date_range = AnalyticsDateRange(
        start_date=body.start_date,
        end_date=body.end_date,
    )
    return generate_monthly_plan(db, user.id, date_range)
