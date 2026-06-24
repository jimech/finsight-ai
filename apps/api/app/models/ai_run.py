import uuid
from typing import Any, Optional

from sqlalchemy import ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, CreatedAtMixin, uuid_primary_key


class AIRun(Base, CreatedAtMixin):
    __tablename__ = "ai_runs"

    id: Mapped[uuid.UUID] = uuid_primary_key()
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
    )
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    response: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    model: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    latency_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    estimated_cost: Mapped[Optional[float]] = mapped_column(Numeric(10, 6), nullable=True)
    retrieval_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    tool_calls: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)
