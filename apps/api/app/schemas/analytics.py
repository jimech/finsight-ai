from datetime import date
from typing import List, Optional
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


class CategoryBreakdownResponse(BaseModel):
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    items: List[CategoryBreakdownItem]
