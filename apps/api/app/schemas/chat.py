from datetime import date, datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class Citation(BaseModel):
    source: str
    label: str
    transaction_id: Optional[UUID] = None
    date: Optional[str] = None
    description: Optional[str] = None
    merchant: Optional[str] = None
    amount: Optional[float] = None
    category: Optional[str] = None


class ChatResponse(BaseModel):
    message: str
    citations: List[Citation]
    ai_run_id: UUID


class ChatHistoryMessage(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    role: str
    content: str
    citations: Optional[List[Citation]] = None
    created_at: datetime


class ChatHistoryResponse(BaseModel):
    messages: List[ChatHistoryMessage]
