from datetime import date
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.core.auth import get_current_user
from app.core.types import AuthenticatedUser
from app.db.session import SessionLocal
from app.main import app
from app.models.transaction import Transaction
from app.models.uploaded_file import UploadedFile
from app.models.user import User
from app.services.analytics import AnalyticsDateRange, build_spending_summary
from app.services.uploads import parse_transactions_csv
from app.services.users import get_or_create_user_from_auth

FIXTURES_DIR = Path(__file__).parent / "fixtures"
SAMPLE_TRANSACTIONS_CSV = (FIXTURES_DIR / "sample_transactions.csv").read_text()


@pytest.fixture
def auth_user_with_transactions():
    db = SessionLocal()
    user = get_or_create_user_from_auth(
        db,
        AuthenticatedUser(
            clerk_user_id="user_analytics_test",
            email="analytics@test.com",
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


def test_build_spending_summary_empty():
    summary = build_spending_summary([], AnalyticsDateRange())
    assert summary.transaction_count == 0
    assert summary.income_total == 0
    assert summary.spending_total == 0
    assert summary.net_cashflow == 0
    assert summary.category_breakdown == []
    assert summary.top_merchants == []
    assert summary.largest_expense is None


def test_build_spending_summary_metrics():
    transactions = [
        Transaction(
            id=uuid4(),
            user_id=uuid4(),
            date=date(2026, 1, 2),
            description="Coffee",
            merchant="Starbucks",
            amount=Decimal("-5.75"),
            category="Coffee",
        ),
        Transaction(
            id=uuid4(),
            user_id=uuid4(),
            date=date(2026, 1, 3),
            description="Payroll",
            merchant="Acme Inc",
            amount=Decimal("3500.00"),
            category="Income",
        ),
        Transaction(
            id=uuid4(),
            user_id=uuid4(),
            date=date(2026, 1, 4),
            description="Groceries",
            merchant=None,
            amount=Decimal("-86.21"),
            category=None,
        ),
    ]

    summary = build_spending_summary(transactions, AnalyticsDateRange())
    assert summary.income_total == 3500.0
    assert summary.spending_total == 91.96
    assert summary.net_cashflow == 3408.04
    assert summary.transaction_count == 3
    assert summary.uncategorized_count == 1
    assert summary.largest_expense is not None
    assert summary.largest_expense.amount == 86.21
    assert summary.largest_expense.merchant == "Unknown Merchant"
    assert summary.largest_expense.category == "Uncategorized"

    coffee = next(
        item for item in summary.category_breakdown if item.category == "Coffee"
    )
    assert coffee.amount == 5.75
    assert coffee.percentage_of_spending == round((5.75 / 91.96) * 100, 2)


def test_get_summary_requires_auth():
    client = TestClient(app)
    assert client.get("/transactions/summary").status_code == 401


def test_get_summary_scoped_to_user(auth_user_with_transactions):
    db, user, auth = auth_user_with_transactions
    app.dependency_overrides[get_current_user] = lambda: auth
    client = TestClient(app)
    try:
        response = client.get("/transactions/summary")
        assert response.status_code == 200
        body = response.json()
        assert body["transaction_count"] == 3
        assert body["income_total"] == 3500.0
        assert body["spending_total"] == 91.96
        assert body["net_cashflow"] == 3408.04
        assert len(body["category_breakdown"]) >= 2
        assert len(body["top_merchants"]) >= 2
    finally:
        app.dependency_overrides.clear()


def test_get_summary_date_filter(auth_user_with_transactions):
    db, user, auth = auth_user_with_transactions
    app.dependency_overrides[get_current_user] = lambda: auth
    client = TestClient(app)
    try:
        response = client.get(
            "/transactions/summary?start_date=2026-01-02&end_date=2026-01-02"
        )
        assert response.status_code == 200
        body = response.json()
        assert body["transaction_count"] == 1
        assert body["spending_total"] == 5.75
        assert body["income_total"] == 0
    finally:
        app.dependency_overrides.clear()


def test_get_categories_endpoint(auth_user_with_transactions):
    db, user, auth = auth_user_with_transactions
    app.dependency_overrides[get_current_user] = lambda: auth
    client = TestClient(app)
    try:
        response = client.get("/transactions/categories")
        assert response.status_code == 200
        body = response.json()
        assert len(body["items"]) >= 2
        assert body["items"][0]["amount"] >= body["items"][-1]["amount"]
    finally:
        app.dependency_overrides.clear()
