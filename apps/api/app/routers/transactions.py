from datetime import date
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.types import AuthenticatedUser
from app.db.session import get_db
from app.schemas.transaction import (
    TransactionItem,
    TransactionListResponse,
    TransactionUpdate,
)
from app.services.transactions import (
    TransactionListParams,
    get_user_transaction,
    list_user_transactions,
    update_user_transaction,
)
from app.services.users import get_or_create_user_from_auth

router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.get("", response_model=TransactionListResponse)
def get_transactions(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    category: Optional[str] = Query(default=None),
    merchant: Optional[str] = Query(default=None),
    start_date: Optional[date] = Query(default=None),
    end_date: Optional[date] = Query(default=None),
    db: Session = Depends(get_db),
    authenticated_user: AuthenticatedUser = Depends(get_current_user),
):
    user = get_or_create_user_from_auth(db, authenticated_user)
    params = TransactionListParams(
        limit=limit,
        offset=offset,
        category=category,
        merchant=merchant,
        start_date=start_date,
        end_date=end_date,
    )
    items, total = list_user_transactions(db, user.id, params)
    return TransactionListResponse(
        items=items,
        total=total,
        limit=limit,
        offset=offset,
    )


@router.patch("/{transaction_id}", response_model=TransactionItem)
def patch_transaction(
    transaction_id: UUID,
    data: TransactionUpdate,
    db: Session = Depends(get_db),
    authenticated_user: AuthenticatedUser = Depends(get_current_user),
):
    user = get_or_create_user_from_auth(db, authenticated_user)
    transaction = get_user_transaction(db, user.id, transaction_id)
    if transaction is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found",
        )

    return update_user_transaction(db, transaction, data)
