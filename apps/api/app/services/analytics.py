from collections import defaultdict
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
import re
from typing import Dict, List, Optional, Tuple, Union
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.transaction import Transaction
from app.schemas.analytics import (
    CategoryBreakdownItem,
    CategoryBreakdownResponse,
    LargestExpenseItem,
    RecurringExpenseItem,
    RecurringExpensesResponse,
    SavingsOpportunitiesResponse,
    SavingsOpportunityItem,
    SpendingSummaryResponse,
    TopMerchantItem,
)

UNCATEGORIZED = "Uncategorized"
UNKNOWN_MERCHANT = "Unknown Merchant"

ESSENTIAL_CATEGORIES = {
    "rent",
    "mortgage",
    "utilities",
    "insurance",
    "loan payment",
    "debt payment",
}

HIGH_FLEX_CATEGORIES = {
    "dining",
    "coffee",
    "shopping",
    "entertainment",
    "subscriptions",
}

MEDIUM_FLEX_CATEGORIES = {
    "groceries",
    "transportation",
    "personal care",
}

SAVINGS_REASONS: Dict[str, str] = {
    "dining": "Dining is often flexible and can usually be reduced with planning.",
    "coffee": "Coffee spending is usually easy to trim with small habit changes.",
    "shopping": "Shopping purchases are often discretionary and can be reduced.",
    "entertainment": "Entertainment spending can usually be adjusted month to month.",
    "subscriptions": "Subscriptions are a common place to find recurring savings.",
    "groceries": "Groceries can often be optimized with meal planning and budgeting.",
    "transportation": "Transportation costs can sometimes be lowered with planning.",
    "personal care": "Personal care spending may have room for modest reductions.",
}


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


def _normalize_key(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip().lower())


def _grouping_key(transaction: Transaction) -> str:
    if transaction.merchant and transaction.merchant.strip():
        return _normalize_key(transaction.merchant)
    return _normalize_key(transaction.description)


def _display_group_name(transactions: List[Transaction]) -> str:
    first = transactions[0]
    if first.merchant and first.merchant.strip():
        return first.merchant.strip()
    return first.description.strip()


def _amounts_similar(amounts: List[float], threshold: float = 0.15) -> bool:
    if len(amounts) < 2:
        return False
    max_amount = max(amounts)
    min_amount = min(amounts)
    if max_amount == 0:
        return min_amount == 0
    return (max_amount - min_amount) / max_amount <= threshold


def _dates_recurring(dates: List[date]) -> bool:
    sorted_dates = sorted(dates)
    if len(sorted_dates) < 2:
        return False
    if len(sorted_dates) == 2:
        return (sorted_dates[1] - sorted_dates[0]).days >= 20
    gaps = [
        (sorted_dates[index + 1] - sorted_dates[index]).days
        for index in range(len(sorted_dates) - 1)
    ]
    return all(gap >= 20 for gap in gaps)


def _group_category(transactions: List[Transaction]) -> str:
    for transaction in transactions:
        if transaction.category and transaction.category.strip():
            return transaction.category.strip()
    return UNCATEGORIZED


def build_recurring_expenses(
    transactions: List[Transaction],
    date_range: AnalyticsDateRange,
) -> RecurringExpensesResponse:
    start_date, end_date = _effective_date_range(transactions, date_range)
    expenses = [transaction for transaction in transactions if transaction.amount < 0]
    grouped: Dict[str, List[Transaction]] = defaultdict(list)

    for transaction in expenses:
        grouped[_grouping_key(transaction)].append(transaction)

    items: List[RecurringExpenseItem] = []
    for group_transactions in grouped.values():
        if len(group_transactions) < 2:
            continue

        amounts = [abs(_to_float(transaction.amount)) for transaction in group_transactions]
        dates = [transaction.date for transaction in group_transactions]
        if not _amounts_similar(amounts) or not _dates_recurring(dates):
            continue

        average_amount = round(sum(amounts) / len(amounts), 2)
        items.append(
            RecurringExpenseItem(
                merchant_or_description=_display_group_name(group_transactions),
                average_amount=average_amount,
                transaction_count=len(group_transactions),
                first_seen=min(dates),
                last_seen=max(dates),
                confidence="high" if len(group_transactions) >= 3 else "medium",
                category=_group_category(group_transactions),
            )
        )

    items.sort(key=lambda item: item.average_amount, reverse=True)
    return RecurringExpensesResponse(
        start_date=start_date,
        end_date=end_date,
        items=items,
    )


def _is_essential_category(category: str) -> bool:
    return category.strip().lower() in ESSENTIAL_CATEGORIES


def _reduction_percent(category: str) -> float:
    normalized = category.strip().lower()
    if normalized in HIGH_FLEX_CATEGORIES:
        return 20.0
    if normalized in MEDIUM_FLEX_CATEGORIES:
        return 10.0
    return 5.0


def _savings_reason(category: str) -> str:
    normalized = category.strip().lower()
    return SAVINGS_REASONS.get(
        normalized,
        f"{category} may have room for modest spending reductions.",
    )


def build_savings_opportunities(
    transactions: List[Transaction],
    date_range: AnalyticsDateRange,
) -> SavingsOpportunitiesResponse:
    start_date, end_date = _effective_date_range(transactions, date_range)
    expenses = [transaction for transaction in transactions if transaction.amount < 0]
    grouped: Dict[str, float] = defaultdict(float)

    for transaction in expenses:
        category = (
            transaction.category.strip()
            if transaction.category and transaction.category.strip()
            else UNCATEGORIZED
        )
        if _is_essential_category(category):
            continue
        grouped[category] += abs(_to_float(transaction.amount))

    items: List[SavingsOpportunityItem] = []
    for category, current_spending in grouped.items():
        if current_spending <= 0:
            continue
        reduction_percent = _reduction_percent(category)
        potential_monthly_savings = round(
            current_spending * (reduction_percent / 100),
            2,
        )
        items.append(
            SavingsOpportunityItem(
                category=category,
                current_spending=round(current_spending, 2),
                suggested_reduction_percent=reduction_percent,
                potential_monthly_savings=potential_monthly_savings,
                reason=_savings_reason(category),
            )
        )

    items.sort(key=lambda item: item.potential_monthly_savings, reverse=True)
    return SavingsOpportunitiesResponse(
        start_date=start_date,
        end_date=end_date,
        items=items[:5],
    )


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

    recurring = build_recurring_expenses(transactions, date_range)
    savings = build_savings_opportunities(transactions, date_range)

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
        recurring_expense_count=len(recurring.items),
        estimated_recurring_total=round(
            sum(item.average_amount for item in recurring.items),
            2,
        ),
        top_savings_opportunity=savings.items[0] if savings.items else None,
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


def get_recurring_expenses(
    db: Session,
    user_id: UUID,
    date_range: AnalyticsDateRange,
) -> RecurringExpensesResponse:
    transactions = _fetch_user_transactions(db, user_id, date_range)
    return build_recurring_expenses(transactions, date_range)


def get_savings_opportunities(
    db: Session,
    user_id: UUID,
    date_range: AnalyticsDateRange,
) -> SavingsOpportunitiesResponse:
    transactions = _fetch_user_transactions(db, user_id, date_range)
    return build_savings_opportunities(transactions, date_range)
