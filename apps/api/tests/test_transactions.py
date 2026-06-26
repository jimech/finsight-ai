from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.auth import get_current_user
from app.core.types import AuthenticatedUser
from app.db.session import SessionLocal
from app.main import app
from app.models.transaction import Transaction
from app.models.uploaded_file import UploadedFile
from app.models.user import User
from app.services.uploads import parse_transactions_csv
from app.services.users import get_or_create_user_from_auth

FIXTURES_DIR = Path(__file__).parent / "fixtures"
SAMPLE_TRANSACTIONS_CSV = (FIXTURES_DIR / "sample_transactions.csv").read_text()


@pytest.fixture
def auth_user():
    db = SessionLocal()
    user = get_or_create_user_from_auth(
        db,
        AuthenticatedUser(
            clerk_user_id="user_transactions_test",
            email="transactions@test.com",
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

    db.query(Transaction).filter(Transaction.user_id == user.id).delete()
    db.query(UploadedFile).filter(UploadedFile.user_id == user.id).delete()
    db.query(User).filter(User.id == user.id).delete()
    db.commit()
    db.close()


@pytest.fixture
def other_user_transaction():
    db = SessionLocal()
    user = get_or_create_user_from_auth(
        db,
        AuthenticatedUser(
            clerk_user_id="user_transactions_other",
            email="other@test.com",
            claims={},
        ),
    )
    transaction = Transaction(
        user_id=user.id,
        date=date(2026, 1, 1),
        description="Other user txn",
        amount=Decimal("10.00"),
    )
    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    transaction_id = transaction.id

    yield transaction_id

    db.query(Transaction).filter(Transaction.user_id == user.id).delete()
    db.query(User).filter(User.id == user.id).delete()
    db.commit()
    db.close()


def test_get_transactions_requires_auth():
    client = TestClient(app)
    assert client.get("/transactions").status_code == 401


def test_get_transactions_returns_only_current_user(auth_user, other_user_transaction):
    db, user, auth = auth_user
    app.dependency_overrides[get_current_user] = lambda: auth
    client = TestClient(app)
    try:
        response = client.get("/transactions")
        assert response.status_code == 200
        body = response.json()
        assert body["total"] == 3
        assert len(body["items"]) == 3
        assert all(item["description"] != "Other user txn" for item in body["items"])
    finally:
        app.dependency_overrides.clear()


def test_get_transactions_pagination(auth_user):
    db, user, auth = auth_user
    app.dependency_overrides[get_current_user] = lambda: auth
    client = TestClient(app)
    try:
        response = client.get("/transactions?limit=2&offset=1")
        assert response.status_code == 200
        body = response.json()
        assert body["total"] == 3
        assert body["limit"] == 2
        assert body["offset"] == 1
        assert len(body["items"]) == 2
    finally:
        app.dependency_overrides.clear()


def test_get_transactions_filters(auth_user):
    db, user, auth = auth_user
    app.dependency_overrides[get_current_user] = lambda: auth
    client = TestClient(app)
    try:
        category_response = client.get("/transactions?category=Coffee")
        assert category_response.status_code == 200
        assert category_response.json()["total"] == 1

        merchant_response = client.get("/transactions?merchant=Trader")
        assert merchant_response.status_code == 200
        assert merchant_response.json()["total"] == 1

        date_response = client.get(
            "/transactions?start_date=2026-01-03&end_date=2026-01-03"
        )
        assert date_response.status_code == 200
        assert date_response.json()["total"] == 1
    finally:
        app.dependency_overrides.clear()


def test_patch_transaction_updates_allowed_fields(auth_user):
    db, user, auth = auth_user
    app.dependency_overrides[get_current_user] = lambda: auth
    client = TestClient(app)
    try:
        transaction_id = client.get("/transactions").json()["items"][0]["id"]
        response = client.patch(
            f"/transactions/{transaction_id}",
            json={"merchant": "Updated Merchant", "category": "Updated Category"},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["merchant"] == "Updated Merchant"
        assert body["category"] == "Updated Category"
    finally:
        app.dependency_overrides.clear()


def test_patch_transaction_ignores_unauthorized_fields(auth_user):
    db, user, auth = auth_user
    app.dependency_overrides[get_current_user] = lambda: auth
    client = TestClient(app)
    try:
        original = client.get("/transactions").json()["items"][0]
        response = client.patch(
            f"/transactions/{original['id']}",
            json={
                "merchant": "Edited Merchant",
                "amount": 9999,
                "description": "Hacked",
                "date": "2099-01-01",
            },
        )
        assert response.status_code == 200
        body = response.json()
        assert body["merchant"] == "Edited Merchant"
        assert float(body["amount"]) == float(original["amount"])
        assert body["description"] == original["description"]
        assert body["date"] == original["date"]
    finally:
        app.dependency_overrides.clear()


def test_patch_transaction_not_found_for_other_user(auth_user, other_user_transaction):
    db, user, auth = auth_user
    app.dependency_overrides[get_current_user] = lambda: auth
    client = TestClient(app)
    try:
        response = client.patch(
            f"/transactions/{other_user_transaction}",
            json={"category": "Nope"},
        )
        assert response.status_code == 404
    finally:
        app.dependency_overrides.clear()
