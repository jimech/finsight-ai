from collections import defaultdict
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import List, Optional, Tuple, Union
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.transaction import Transaction
from app.schemas.analytics import (
    CategoryBreakdownItem,
    CategoryBreakdownResponse,
    LargestExpenseItem,
    SpendingSummaryResponse,
    TopMerchantItem,
)

UNCATEGORIZED = "Uncategorized"
UNKNOWN_MERCHANT = "Unknown Merchant"


@dataclass(frozen=True)
class AnalyticsDateRange:
    start_date: Optional[date] = None
    end_date: Optional[date] = None


def _to_float(value: Union[Decimal, float]) -> float:
    return float(value)


def _fetch_user_transactions(
    db: Session,
    user_id: UUID,
    date_range: AnalyticsDateRange,
) -> List[Transaction]:
    query = select(Transaction).where(Transaction.user_id == user_id)
    if date_range.start_date:
        query = query.where(Transaction.date >= date_range.start_date)
    if date_range.end_date:
        query = query.where(Transaction.date <= date_range.end_date)
    return list(db.scalars(query.order_by(Transaction.date.asc())))


def _effective_date_range(
    transactions: List[Transaction],
    date_range: AnalyticsDateRange,
) -> Tuple[Optional[date], Optional[date]]:
    if date_range.start_date or date_range.end_date:
        return date_range.start_date, date_range.end_date
    if not transactions:
        return None, None
    dates = [transaction.date for transaction in transactions]
    return min(dates), max(dates)


def _build_category_breakdown(
    expenses: List[Transaction],
    spending_total: float,
) -> List[CategoryBreakdownItem]:
    grouped: dict[str, dict[str, float | int]] = defaultdict(
        lambda: {"amount": 0.0, "transaction_count": 0}
    )

    for transaction in expenses:
        category = transaction.category.strip() if transaction.category else UNCATEGORIZED
        if not category:
            category = UNCATEGORIZED
        grouped[category]["amount"] = float(grouped[category]["amount"]) + abs(
            _to_float(transaction.amount)
        )
        grouped[category]["transaction_count"] = int(
            grouped[category]["transaction_count"]
        ) + 1

    items = [
        CategoryBreakdownItem(
            category=category,
            amount=round(data["amount"], 2),
            transaction_count=int(data["transaction_count"]),
            percentage_of_spending=round(
                (data["amount"] / spending_total) * 100, 2
            )
            if spending_total > 0
            else 0.0,
        )
        for category, data in grouped.items()
    ]
    return sorted(items, key=lambda item: item.amount, reverse=True)


def _build_top_merchants(expenses: List[Transaction]) -> List[TopMerchantItem]:
    grouped: dict[str, dict[str, float | int]] = defaultdict(
        lambda: {"amount": 0.0, "transaction_count": 0}
    )

    for transaction in expenses:
        merchant = (
            transaction.merchant.strip()
            if transaction.merchant
            else UNKNOWN_MERCHANT
        )
        if not merchant:
            merchant = UNKNOWN_MERCHANT
        grouped[merchant]["amount"] = float(grouped[merchant]["amount"]) + abs(
            _to_float(transaction.amount)
        )
        grouped[merchant]["transaction_count"] = int(
            grouped[merchant]["transaction_count"]
        ) + 1

    items = [
        TopMerchantItem(
            merchant=merchant,
            amount=round(data["amount"], 2),
            transaction_count=int(data["transaction_count"]),
        )
        for merchant, data in grouped.items()
    ]
    return sorted(items, key=lambda item: item.amount, reverse=True)


def _count_uncategorized(expenses: List[Transaction]) -> int:
    return sum(1 for transaction in expenses if not transaction.category)


def build_spending_summary(
    transactions: List[Transaction],
    date_range: AnalyticsDateRange,
) -> SpendingSummaryResponse:
    start_date, end_date = _effective_date_range(transactions, date_range)
    transaction_count = len(transactions)

    income_total = round(
        sum(_to_float(t.amount) for t in transactions if t.amount > 0),
        2,
    )
    spending_total = round(
        abs(sum(_to_float(t.amount) for t in transactions if t.amount < 0)),
        2,
    )
    net_cashflow = round(income_total - spending_total, 2)
    average_transaction_amount = round(
        sum(_to_float(t.amount) for t in transactions) / transaction_count,
        2,
    ) if transaction_count else 0.0

    expenses = [t for t in transactions if t.amount < 0]
    largest_expense = None
    if expenses:
        largest = min(expenses, key=lambda t: t.amount)
        largest_expense = LargestExpenseItem(
            id=largest.id,
            date=largest.date,
            description=largest.description,
            merchant=largest.merchant.strip()
            if largest.merchant and largest.merchant.strip()
            else UNKNOWN_MERCHANT,
            amount=round(abs(_to_float(largest.amount)), 2),
            category=largest.category.strip()
            if largest.category and largest.category.strip()
            else UNCATEGORIZED,
        )

    return SpendingSummaryResponse(
        start_date=start_date,
        end_date=end_date,
        transaction_count=transaction_count,
        income_total=income_total,
        spending_total=spending_total,
        net_cashflow=net_cashflow,
        average_transaction_amount=average_transaction_amount,
        largest_expense=largest_expense,
        category_breakdown=_build_category_breakdown(expenses, spending_total),
        top_merchants=_build_top_merchants(expenses),
        uncategorized_count=_count_uncategorized(expenses),
    )


def get_spending_summary(
    db: Session,
    user_id: UUID,
    date_range: AnalyticsDateRange,
) -> SpendingSummaryResponse:
    transactions = _fetch_user_transactions(db, user_id, date_range)
    return build_spending_summary(transactions, date_range)


def get_category_breakdown(
    db: Session,
    user_id: UUID,
    date_range: AnalyticsDateRange,
) -> CategoryBreakdownResponse:
    transactions = _fetch_user_transactions(db, user_id, date_range)
    start_date, end_date = _effective_date_range(transactions, date_range)
    expenses = [t for t in transactions if t.amount < 0]
    spending_total = abs(sum(_to_float(t.amount) for t in expenses))
    return CategoryBreakdownResponse(
        start_date=start_date,
        end_date=end_date,
        items=_build_category_breakdown(expenses, spending_total),
    )
