import hashlib
import math
from typing import Dict, List, Optional, Set, Tuple
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.transaction import Transaction
from app.models.transaction_embedding import EMBEDDING_DIMENSIONS, TransactionEmbedding

MetadataDict = Dict[str, object]


def build_searchable_text(transaction: Transaction) -> str:
    return " | ".join(
        [
            f"date: {transaction.date.isoformat()}",
            f"description: {transaction.description}",
            f"merchant: {transaction.merchant or 'unknown'}",
            f"amount: {float(transaction.amount)}",
            f"category: {transaction.category or 'uncategorized'}",
        ]
    )


def build_embedding_metadata(transaction: Transaction) -> MetadataDict:
    return {
        "date": transaction.date.isoformat(),
        "description": transaction.description,
        "merchant": transaction.merchant,
        "amount": float(transaction.amount),
        "category": transaction.category,
    }


def _fake_embedding(text: str, dimensions: int = EMBEDDING_DIMENSIONS) -> List[float]:
    vector = [0.0] * dimensions
    tokens = [token for token in text.lower().split() if token]
    if not tokens:
        tokens = [text.lower()]

    for token in tokens:
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        base_index = int.from_bytes(digest[:4], "big") % dimensions
        for offset, byte in enumerate(digest):
            index = (base_index + offset) % dimensions
            vector[index] += byte / 255.0

    norm = math.sqrt(sum(value * value for value in vector)) or 1.0
    return [value / norm for value in vector]


def _openai_embedding(text: str) -> List[float]:
    if not settings.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY is not configured")

    from openai import OpenAI

    client = OpenAI(api_key=settings.openai_api_key)
    response = client.embeddings.create(
        model=settings.embedding_model,
        input=text,
    )
    return response.data[0].embedding


def generate_embedding_vector(text: str) -> List[float]:
    if settings.embeddings_enabled:
        return _openai_embedding(text)
    return _fake_embedding(text)


def _existing_embedding_transaction_ids(
    db: Session,
    user_id: UUID,
) -> Set[UUID]:
    return set(
        db.scalars(
            select(TransactionEmbedding.transaction_id).where(
                TransactionEmbedding.user_id == user_id
            )
        )
    )


def generate_missing_embeddings_for_user(
    db: Session,
    user_id: UUID,
) -> Tuple[int, int]:
    existing_ids = _existing_embedding_transaction_ids(db, user_id)
    transactions = list(
        db.scalars(select(Transaction).where(Transaction.user_id == user_id))
    )

    generated = 0
    skipped = 0
    for transaction in transactions:
        if transaction.id in existing_ids:
            skipped += 1
            continue

        searchable_text = build_searchable_text(transaction)
        embedding = generate_embedding_vector(searchable_text)
        db.add(
            TransactionEmbedding(
                transaction_id=transaction.id,
                user_id=user_id,
                embedding=embedding,
                searchable_text=searchable_text,
                metadata_json=build_embedding_metadata(transaction),
            )
        )
        generated += 1

    if generated:
        db.commit()

    return generated, skipped
