"""Add pgvector extension and transaction_embeddings table.

Revision ID: c8f1a2b3d4e5
Revises: b2c4e8f91a3d
Create Date: 2026-06-25 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

revision: str = "c8f1a2b3d4e5"
down_revision: Union[str, None] = "b2c4e8f91a3d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

EMBEDDING_DIMENSIONS = 1536


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.create_table(
        "transaction_embeddings",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("transaction_id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("embedding", Vector(EMBEDDING_DIMENSIONS), nullable=False),
        sa.Column("searchable_text", sa.Text(), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["transaction_id"], ["transactions.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "transaction_id",
            name="uq_transaction_embeddings_transaction_id",
        ),
    )
    op.create_index(
        "ix_transaction_embeddings_user_id",
        "transaction_embeddings",
        ["user_id"],
    )
    op.create_index(
        "ix_transaction_embeddings_transaction_id",
        "transaction_embeddings",
        ["transaction_id"],
    )
    op.execute(
        """
        CREATE INDEX ix_transaction_embeddings_embedding_hnsw
        ON transaction_embeddings
        USING hnsw (embedding vector_cosine_ops)
        """
    )


def downgrade() -> None:
    op.drop_index(
        "ix_transaction_embeddings_embedding_hnsw",
        table_name="transaction_embeddings",
    )
    op.drop_index(
        "ix_transaction_embeddings_transaction_id",
        table_name="transaction_embeddings",
    )
    op.drop_index(
        "ix_transaction_embeddings_user_id",
        table_name="transaction_embeddings",
    )
    op.drop_table("transaction_embeddings")
