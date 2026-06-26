from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class EmbeddingGenerateResponse(BaseModel):
    generated: int
    skipped: int


class TransactionSearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500)
    top_k: int = Field(default=5, ge=1, le=20)


class TransactionSearchResult(BaseModel):
    transaction_id: UUID
    date: str
    description: str
    merchant: Optional[str] = None
    amount: float
    category: Optional[str] = None
    similarity_score: Optional[float] = None
    citation_label: str


class TransactionSearchResponse(BaseModel):
    query: str
    results: List[TransactionSearchResult]
    embeddings_enabled: bool
