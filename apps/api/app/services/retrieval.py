from typing import List
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.transaction import Transaction
from app.models.transaction_embedding import TransactionEmbedding
from app.schemas.retrieval import TransactionSearchResult
from app.services.embeddings import generate_embedding_vector


def _citation_label(transaction: Transaction) -> str:
    merchant = transaction.merchant.strip() if transaction.merchant else None
    label_subject = merchant or transaction.description
    return f"Transaction on {transaction.date.isoformat()}: {label_subject}"


def search_user_transactions(
    db: Session,
    user_id: UUID,
    query: str,
    top_k: int,
) -> List[TransactionSearchResult]:
    embedding_count = db.scalar(
        select(TransactionEmbedding.id)
        .where(TransactionEmbedding.user_id == user_id)
        .limit(1)
    )
    if embedding_count is None:
        return []

    query_embedding = generate_embedding_vector(query)
    distance = TransactionEmbedding.embedding.cosine_distance(query_embedding)

    rows = db.execute(
        select(Transaction, distance.label("distance"))
        .join(
            TransactionEmbedding,
            TransactionEmbedding.transaction_id == Transaction.id,
        )
        .where(TransactionEmbedding.user_id == user_id)
        .order_by(distance)
        .limit(top_k)
    ).all()

    results: List[TransactionSearchResult] = []
    for transaction, cosine_distance in rows:
        similarity_score = None
        if cosine_distance is not None:
            similarity_score = round(max(0.0, 1.0 - float(cosine_distance)), 4)

        results.append(
            TransactionSearchResult(
                transaction_id=transaction.id,
                date=transaction.date.isoformat(),
                description=transaction.description,
                merchant=transaction.merchant,
                amount=float(transaction.amount),
                category=transaction.category,
                similarity_score=similarity_score,
                citation_label=_citation_label(transaction),
            )
        )

    return results


def embeddings_available_for_user(db: Session, user_id: UUID) -> bool:
    return (
        db.scalar(
            select(TransactionEmbedding.id)
            .where(TransactionEmbedding.user_id == user_id)
            .limit(1)
        )
        is not None
    )
