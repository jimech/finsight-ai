from dataclasses import dataclass
from datetime import date
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.transaction import Transaction
from app.schemas.transaction import TransactionUpdate


@dataclass(frozen=True)
class TransactionListParams:
    limit: int = 50
    offset: int = 0
    category: Optional[str] = None
    merchant: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None


def _apply_filters(
    query,
    params: TransactionListParams,
):
    if params.category:
        query = query.where(Transaction.category.ilike(params.category))
    if params.merchant:
        query = query.where(Transaction.merchant.ilike(f"%{params.merchant}%"))
    if params.start_date:
        query = query.where(Transaction.date >= params.start_date)
    if params.end_date:
        query = query.where(Transaction.date <= params.end_date)
    return query


def list_user_transactions(
    db: Session,
    user_id: UUID,
    params: TransactionListParams,
) -> Tuple[List[Transaction], int]:
    base_query = select(Transaction).where(Transaction.user_id == user_id)
    filtered_query = _apply_filters(base_query, params)

    total = db.scalar(select(func.count()).select_from(filtered_query.subquery())) or 0

    items = list(
        db.scalars(
            filtered_query.order_by(
                Transaction.date.desc(),
                Transaction.created_at.desc(),
            )
            .limit(params.limit)
            .offset(params.offset)
        )
    )
    return items, total


def get_user_transaction(
    db: Session,
    user_id: UUID,
    transaction_id: UUID,
) -> Optional[Transaction]:
    return db.scalar(
        select(Transaction).where(
            Transaction.id == transaction_id,
            Transaction.user_id == user_id,
        )
    )


def update_user_transaction(
    db: Session,
    transaction: Transaction,
    data: TransactionUpdate,
) -> Transaction:
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(transaction, field, value)

    db.commit()
    db.refresh(transaction)
    return transaction
