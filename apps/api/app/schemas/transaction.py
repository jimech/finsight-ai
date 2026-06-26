from datetime import date, datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class TransactionItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    date: date
    description: str
    merchant: Optional[str] = None
    amount: float
    category: Optional[str] = None
    source_file_id: Optional[UUID] = None
    created_at: datetime


class TransactionListResponse(BaseModel):
    items: List[TransactionItem]
    total: int
    limit: int
    offset: int


class TransactionUpdate(BaseModel):
    model_config = ConfigDict(extra="ignore")

    merchant: Optional[str] = Field(default=None, max_length=255)
    category: Optional[str] = Field(default=None, max_length=100)
