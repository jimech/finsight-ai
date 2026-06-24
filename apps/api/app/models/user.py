import uuid
from typing import Optional

from sqlalchemy import Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, uuid_primary_key


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = uuid_primary_key()
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    monthly_income: Mapped[Optional[float]] = mapped_column(Numeric(12, 2), nullable=True)
    savings_goal: Mapped[Optional[float]] = mapped_column(Numeric(12, 2), nullable=True)
    current_savings: Mapped[Optional[float]] = mapped_column(Numeric(12, 2), nullable=True)
    financial_priority: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    coaching_tone: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
