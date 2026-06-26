from datetime import date, datetime
from typing import Any, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class Citation(BaseModel):
    source: str
    label: str


class ChatResponse(BaseModel):
    message: str
    citations: List[Citation]
    ai_run_id: UUID


class ChatHistoryMessage(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    role: str
    content: str
    citations: Optional[List[Any]] = None
    created_at: datetime


class ChatHistoryResponse(BaseModel):
    messages: List[ChatHistoryMessage]
