from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.types import AuthenticatedUser
from app.db.session import get_db
from app.schemas.chat import ChatHistoryResponse, ChatRequest, ChatResponse
from app.services.ai_orchestrator import get_chat_history, process_chat_message
from app.services.analytics import AnalyticsDateRange
from app.services.users import get_or_create_user_from_auth

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
def post_chat(
    body: ChatRequest,
    db: Session = Depends(get_db),
    authenticated_user: AuthenticatedUser = Depends(get_current_user),
):
    user = get_or_create_user_from_auth(db, authenticated_user)
    date_range = AnalyticsDateRange(
        start_date=body.start_date,
        end_date=body.end_date,
    )
    return process_chat_message(
        db,
        user.id,
        body.message,
        date_range,
    )


@router.get("/history", response_model=ChatHistoryResponse)
def chat_history(
    db: Session = Depends(get_db),
    authenticated_user: AuthenticatedUser = Depends(get_current_user),
):
    user = get_or_create_user_from_auth(db, authenticated_user)
    messages = get_chat_history(db, user.id)
    return ChatHistoryResponse(messages=messages)
