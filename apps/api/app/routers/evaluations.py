from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.types import AuthenticatedUser
from app.db.session import get_db
from app.schemas.evaluation import (
    AIRunListResponse,
    EvaluationListResponse,
    EvaluationResponse,
    EvaluationSubmit,
)
from app.services.evaluations import (
    list_user_ai_runs,
    list_user_evaluations,
    upsert_evaluation,
)
from app.services.users import get_or_create_user_from_auth

router = APIRouter(prefix="/admin", tags=["evaluations"])


@router.get("/ai-runs", response_model=AIRunListResponse)
def get_ai_runs(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    authenticated_user: AuthenticatedUser = Depends(get_current_user),
):
    user = get_or_create_user_from_auth(db, authenticated_user)
    items, total = list_user_ai_runs(db, user.id, limit, offset)
    return AIRunListResponse(
        items=items,
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/evaluations", response_model=EvaluationListResponse)
def get_evaluations(
    db: Session = Depends(get_db),
    authenticated_user: AuthenticatedUser = Depends(get_current_user),
):
    user = get_or_create_user_from_auth(db, authenticated_user)
    items, total = list_user_evaluations(db, user.id)
    return EvaluationListResponse(items=items, total=total)


@router.post("/evaluate/{ai_run_id}", response_model=EvaluationResponse)
def evaluate_ai_run(
    ai_run_id: UUID,
    body: EvaluationSubmit,
    db: Session = Depends(get_db),
    authenticated_user: AuthenticatedUser = Depends(get_current_user),
):
    user = get_or_create_user_from_auth(db, authenticated_user)
    evaluation = upsert_evaluation(db, user.id, ai_run_id, body)
    if evaluation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="AI run not found",
        )
    return evaluation
