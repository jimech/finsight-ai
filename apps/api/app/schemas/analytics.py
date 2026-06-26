from datetime import date
from typing import List, Literal, Optional
from uuid import UUID

from pydantic import BaseModel


class CategoryBreakdownItem(BaseModel):
    category: str
    amount: float
    transaction_count: int
    percentage_of_spending: float


class TopMerchantItem(BaseModel):
    merchant: str
    amount: float
    transaction_count: int


class LargestExpenseItem(BaseModel):
    id: UUID
    date: date
    description: str
    merchant: str
    amount: float
    category: str


class RecurringExpenseItem(BaseModel):
    merchant_or_description: str
    average_amount: float
    transaction_count: int
    first_seen: date
    last_seen: date
    confidence: Literal["high", "medium"]
    category: str


class SavingsOpportunityItem(BaseModel):
    category: str
    current_spending: float
    suggested_reduction_percent: float
    potential_monthly_savings: float
    reason: str


class SpendingSummaryResponse(BaseModel):
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    transaction_count: int
    income_total: float
    spending_total: float
    net_cashflow: float
    average_transaction_amount: float
    largest_expense: Optional[LargestExpenseItem] = None
    category_breakdown: List[CategoryBreakdownItem]
    top_merchants: List[TopMerchantItem]
    uncategorized_count: int
    recurring_expense_count: int = 0
    estimated_recurring_total: float = 0.0
    top_savings_opportunity: Optional[SavingsOpportunityItem] = None


class CategoryBreakdownResponse(BaseModel):
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    items: List[CategoryBreakdownItem]


class RecurringExpensesResponse(BaseModel):
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    items: List[RecurringExpenseItem]


class SavingsOpportunitiesResponse(BaseModel):
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    items: List[SavingsOpportunityItem]
