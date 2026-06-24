import uuid
from typing import Optional

from sqlalchemy import Boolean, ForeignKey, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, CreatedAtMixin, uuid_primary_key


class Evaluation(Base, CreatedAtMixin):
    __tablename__ = "evaluations"

    id: Mapped[uuid.UUID] = uuid_primary_key()
    ai_run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("ai_runs.id"),
        nullable=False,
    )
    citation_score: Mapped[Optional[float]] = mapped_column(Numeric(5, 4), nullable=True)
    calculation_score: Mapped[Optional[float]] = mapped_column(Numeric(5, 4), nullable=True)
    groundedness_score: Mapped[Optional[float]] = mapped_column(Numeric(5, 4), nullable=True)
    hallucination_flag: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    safety_flag: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
