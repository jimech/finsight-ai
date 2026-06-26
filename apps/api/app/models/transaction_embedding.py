import uuid
from typing import Any, Optional

from pgvector.sqlalchemy import Vector
from sqlalchemy import ForeignKey, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, CreatedAtMixin, uuid_primary_key

EMBEDDING_DIMENSIONS = 1536


class TransactionEmbedding(Base, CreatedAtMixin):
    __tablename__ = "transaction_embeddings"
    __table_args__ = (
        UniqueConstraint("transaction_id", name="uq_transaction_embeddings_transaction_id"),
    )

    id: Mapped[uuid.UUID] = uuid_primary_key()
    transaction_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("transactions.id"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    embedding: Mapped[list[float]] = mapped_column(
        Vector(EMBEDDING_DIMENSIONS),
        nullable=False,
    )
    searchable_text: Mapped[str] = mapped_column(Text, nullable=False)
    metadata_json: Mapped[Optional[Any]] = mapped_column(
        "metadata",
        JSON,
        nullable=True,
    )
