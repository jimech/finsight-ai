from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.core.auth import get_current_user
from app.core.config import get_settings
from app.core.types import AuthenticatedUser
from app.db.session import SessionLocal
from app.main import app
from app.models.transaction import Transaction
from app.models.transaction_embedding import TransactionEmbedding
from app.models.uploaded_file import UploadedFile
from app.models.user import User
from app.services.embeddings import (
    build_searchable_text,
    generate_embedding_vector,
    generate_missing_embeddings_for_user,
)
from app.services.retrieval import search_user_transactions
from app.services.uploads import parse_transactions_csv
from app.services.users import get_or_create_user_from_auth

FIXTURES_DIR = Path(__file__).parent / "fixtures"
SAMPLE_TRANSACTIONS_CSV = (FIXTURES_DIR / "sample_transactions.csv").read_text()


@pytest.fixture(autouse=True)
def embeddings_disabled():
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture
def auth_user_with_transactions():
    db = SessionLocal()
    user = get_or_create_user_from_auth(
        db,
        AuthenticatedUser(
            clerk_user_id=f"user_retrieval_test_{uuid4()}",
            email=f"retrieval-{uuid4()}@test.com",
            claims={},
        ),
    )
    auth = AuthenticatedUser(
        clerk_user_id=user.clerk_user_id,
        email=user.email,
        claims={},
    )

    upload = UploadedFile(
        user_id=user.id,
        filename="sample.csv",
        file_type="transactions_csv",
        status="completed",
    )
    db.add(upload)
    db.flush()

    for row in parse_transactions_csv(SAMPLE_TRANSACTIONS_CSV):
        db.add(
            Transaction(
                user_id=user.id,
                source_file_id=upload.id,
                date=row.date,
                description=row.description,
                merchant=row.merchant,
                amount=row.amount,
                category=row.category,
            )
        )
    db.commit()

    yield db, user, auth

    db.query(TransactionEmbedding).filter(
        TransactionEmbedding.user_id == user.id
    ).delete()
    db.query(Transaction).filter(Transaction.user_id == user.id).delete()
    db.query(UploadedFile).filter(UploadedFile.user_id == user.id).delete()
    db.query(User).filter(User.id == user.id).delete()
    db.commit()
    db.close()


def test_transaction_embedding_model_exists():
    from app.models.transaction_embedding import TransactionEmbedding as Model

    assert Model.__tablename__ == "transaction_embeddings"


def test_migration_file_exists():
    migration = (
        Path(__file__).parent.parent
        / "alembic"
        / "versions"
        / "c8f1a2b3d4e5_add_transaction_embeddings_pgvector.py"
    )
    assert migration.exists()
    content = migration.read_text()
    assert "CREATE EXTENSION IF NOT EXISTS vector" in content
    assert "transaction_embeddings" in content


def test_fake_embedding_generation_without_openai():
    vector = generate_embedding_vector("coffee spending at starbucks")
    assert len(vector) == 1536
    assert vector != generate_embedding_vector("rent payment")


def test_generate_embeddings_requires_auth():
    client = TestClient(app)
    response = client.post("/transactions/embeddings/generate")
    assert response.status_code == 401


def test_generate_embeddings_creates_rows_for_current_user(auth_user_with_transactions):
    db, user, auth = auth_user_with_transactions
    app.dependency_overrides[get_current_user] = lambda: auth
    client = TestClient(app)
    try:
        response = client.post("/transactions/embeddings/generate")
        assert response.status_code == 200
        body = response.json()
        tx_count = db.scalar(
            select(func.count())
            .select_from(Transaction)
            .where(Transaction.user_id == user.id)
        )
        assert body["generated"] == tx_count
        assert body["skipped"] == 0

        count = db.scalar(
            select(TransactionEmbedding.id)
            .where(TransactionEmbedding.user_id == user.id)
            .limit(1)
        )
        assert count is not None

        second = client.post("/transactions/embeddings/generate")
        assert second.json()["generated"] == 0
        assert second.json()["skipped"] == tx_count
    finally:
        app.dependency_overrides.clear()


def test_generate_embeddings_user_scoped(auth_user_with_transactions):
    db, user, auth = auth_user_with_transactions
    other_user = get_or_create_user_from_auth(
        db,
        AuthenticatedUser(
            clerk_user_id=f"user_retrieval_other_{uuid4()}",
            email=f"retrieval-other-{uuid4()}@test.com",
            claims={},
        ),
    )
    other_tx = Transaction(
        user_id=other_user.id,
        date=parse_transactions_csv(SAMPLE_TRANSACTIONS_CSV)[0].date,
        description="PRIVATE",
        merchant="Secret",
        amount=-10,
        category="Other",
    )
    db.add(other_tx)
    db.commit()

    generate_missing_embeddings_for_user(db, other_user.id)

    tx_count = db.scalar(
        select(func.count()).select_from(Transaction).where(Transaction.user_id == user.id)
    )
    app.dependency_overrides[get_current_user] = lambda: auth
    client = TestClient(app)
    try:
        client.post("/transactions/embeddings/generate")
        other_embeddings = db.scalars(
            select(TransactionEmbedding).where(
                TransactionEmbedding.user_id == other_user.id
            )
        ).all()
        current_embeddings = db.scalars(
            select(TransactionEmbedding).where(TransactionEmbedding.user_id == user.id)
        ).all()
        assert len(other_embeddings) == 1
        assert len(current_embeddings) == tx_count
        assert all("PRIVATE" not in item.searchable_text for item in current_embeddings)
    finally:
        app.dependency_overrides.clear()
        db.query(TransactionEmbedding).filter(
            TransactionEmbedding.user_id == other_user.id
        ).delete()
        db.query(Transaction).filter(Transaction.user_id == other_user.id).delete()
        db.query(User).filter(User.id == other_user.id).delete()
        db.commit()


def test_search_endpoint_requires_auth():
    client = TestClient(app)
    response = client.post("/transactions/search", json={"query": "coffee"})
    assert response.status_code == 401


def test_search_works_in_fake_mode(auth_user_with_transactions):
    db, user, auth = auth_user_with_transactions
    generate_missing_embeddings_for_user(db, user.id)

    app.dependency_overrides[get_current_user] = lambda: auth
    client = TestClient(app)
    try:
        response = client.post(
            "/transactions/search",
            json={"query": "coffee starbucks", "top_k": 3},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["embeddings_enabled"] is False
        assert len(body["results"]) >= 1
        assert any(
            "coffee" in result["category"].lower()
            or "starbucks" in (result["merchant"] or "").lower()
            for result in body["results"]
        )
        assert body["results"][0]["citation_label"]
    finally:
        app.dependency_overrides.clear()


def test_search_service_user_scoped(auth_user_with_transactions):
    db, user, auth = auth_user_with_transactions
    generate_missing_embeddings_for_user(db, user.id)

    results = search_user_transactions(db, user.id, "groceries trader", top_k=5)
    assert results
    assert all(result.transaction_id for result in results)


def test_upload_still_works_when_embeddings_disabled(auth_user_with_transactions):
    db, user, auth = auth_user_with_transactions
    app.dependency_overrides[get_current_user] = lambda: auth
    client = TestClient(app)
    try:
        response = client.post(
            "/uploads/transactions",
            files={"file": ("sample.csv", SAMPLE_TRANSACTIONS_CSV, "text/csv")},
        )
        assert response.status_code == 200
        assert response.json()["transactions_imported"] == 3
    finally:
        app.dependency_overrides.clear()


def test_build_searchable_text_includes_fields(auth_user_with_transactions):
    db, user, auth = auth_user_with_transactions
    transaction = db.scalars(
        select(Transaction).where(Transaction.user_id == user.id)
    ).first()
    text = build_searchable_text(transaction)
    assert transaction.description in text
    assert transaction.category in text
