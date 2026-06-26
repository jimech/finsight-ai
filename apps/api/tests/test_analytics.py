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
from app.services.analytics import (
    AnalyticsDateRange,
    build_recurring_expenses,
    build_savings_opportunities,
    build_spending_summary,
)
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
    assert summary.recurring_expense_count == 0
    assert summary.estimated_recurring_total == 0.0
    assert summary.top_savings_opportunity is None


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


def _recurring_transactions():
    return [
        Transaction(
            id=uuid4(),
            user_id=uuid4(),
            date=date(2026, 1, 2),
            description="NETFLIX SUBSCRIPTION",
            merchant="Netflix",
            amount=Decimal("-18.99"),
            category="Subscriptions",
        ),
        Transaction(
            id=uuid4(),
            user_id=uuid4(),
            date=date(2026, 2, 2),
            description="NETFLIX SUBSCRIPTION",
            merchant="Netflix",
            amount=Decimal("-19.50"),
            category="Subscriptions",
        ),
        Transaction(
            id=uuid4(),
            user_id=uuid4(),
            date=date(2026, 3, 2),
            description="NETFLIX SUBSCRIPTION",
            merchant="Netflix",
            amount=Decimal("-18.99"),
            category="Subscriptions",
        ),
        Transaction(
            id=uuid4(),
            user_id=uuid4(),
            date=date(2026, 1, 15),
            description="PAYROLL",
            merchant="Acme Inc",
            amount=Decimal("3500.00"),
            category="Income",
        ),
        Transaction(
            id=uuid4(),
            user_id=uuid4(),
            date=date(2026, 1, 10),
            description="ONE TIME PURCHASE",
            merchant="Best Buy",
            amount=Decimal("-200.00"),
            category="Shopping",
        ),
    ]


def test_build_recurring_detects_similar_expenses():
    recurring = build_recurring_expenses(
        _recurring_transactions(),
        AnalyticsDateRange(),
    )
    assert len(recurring.items) == 1
    item = recurring.items[0]
    assert item.merchant_or_description == "Netflix"
    assert item.transaction_count == 3
    assert item.confidence == "high"
    assert item.average_amount == round((18.99 + 19.50 + 18.99) / 3, 2)
    assert item.category == "Subscriptions"


def test_build_recurring_ignores_income():
    recurring = build_recurring_expenses(
        _recurring_transactions(),
        AnalyticsDateRange(),
    )
    merchants = [item.merchant_or_description for item in recurring.items]
    assert "Acme Inc" not in merchants


def test_build_recurring_uses_description_without_merchant():
    transactions = [
        Transaction(
            id=uuid4(),
            user_id=uuid4(),
            date=date(2026, 1, 5),
            description="Gym Membership",
            merchant=None,
            amount=Decimal("-45.00"),
            category="Personal Care",
        ),
        Transaction(
            id=uuid4(),
            user_id=uuid4(),
            date=date(2026, 2, 5),
            description="Gym Membership",
            merchant=None,
            amount=Decimal("-45.00"),
            category="Personal Care",
        ),
    ]
    recurring = build_recurring_expenses(transactions, AnalyticsDateRange())
    assert len(recurring.items) == 1
    assert recurring.items[0].merchant_or_description == "Gym Membership"
    assert recurring.items[0].confidence == "medium"


def test_build_savings_excludes_essential_categories():
    transactions = [
        Transaction(
            id=uuid4(),
            user_id=uuid4(),
            date=date(2026, 1, 1),
            description="Rent",
            merchant="Landlord",
            amount=Decimal("-1500.00"),
            category="Rent",
        ),
        Transaction(
            id=uuid4(),
            user_id=uuid4(),
            date=date(2026, 1, 5),
            description="Dinner",
            merchant="Restaurant",
            amount=Decimal("-335.20"),
            category="Dining",
        ),
    ]
    savings = build_savings_opportunities(transactions, AnalyticsDateRange())
    categories = [item.category for item in savings.items]
    assert "Rent" not in categories
    assert "Dining" in categories
    dining = next(item for item in savings.items if item.category == "Dining")
    assert dining.suggested_reduction_percent == 20.0
    assert dining.potential_monthly_savings == round(335.20 * 0.20, 2)


def test_build_savings_top_5_sorted():
    categories = [
        ("Dining", Decimal("-500.00")),
        ("Coffee", Decimal("-100.00")),
        ("Shopping", Decimal("-300.00")),
        ("Entertainment", Decimal("-200.00")),
        ("Subscriptions", Decimal("-150.00")),
        ("Groceries", Decimal("-400.00")),
        ("Transportation", Decimal("-250.00")),
    ]
    transactions = [
        Transaction(
            id=uuid4(),
            user_id=uuid4(),
            date=date(2026, 1, index + 1),
            description=category,
            merchant=category,
            amount=amount,
            category=category,
        )
        for index, (category, amount) in enumerate(categories)
    ]
    savings = build_savings_opportunities(transactions, AnalyticsDateRange())
    assert len(savings.items) == 5
    savings_amounts = [item.potential_monthly_savings for item in savings.items]
    assert savings_amounts == sorted(savings_amounts, reverse=True)


def test_summary_includes_recurring_and_savings():
    summary = build_spending_summary(
        _recurring_transactions(),
        AnalyticsDateRange(),
    )
    assert summary.recurring_expense_count == 1
    assert summary.estimated_recurring_total > 0
    assert summary.top_savings_opportunity is not None


def test_get_recurring_requires_auth():
    client = TestClient(app)
    assert client.get("/transactions/recurring").status_code == 401


def test_get_savings_requires_auth():
    client = TestClient(app)
    assert client.get("/transactions/savings-opportunities").status_code == 401


def test_get_recurring_endpoint(auth_user_with_transactions):
    db, user, auth = auth_user_with_transactions
    app.dependency_overrides[get_current_user] = lambda: auth
    client = TestClient(app)
    try:
        response = client.get("/transactions/recurring")
        assert response.status_code == 200
        body = response.json()
        assert "items" in body
    finally:
        app.dependency_overrides.clear()


def test_get_savings_endpoint(auth_user_with_transactions):
    db, user, auth = auth_user_with_transactions
    app.dependency_overrides[get_current_user] = lambda: auth
    client = TestClient(app)
    try:
        response = client.get("/transactions/savings-opportunities")
        assert response.status_code == 200
        body = response.json()
        assert "items" in body
        assert len(body["items"]) <= 5
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
