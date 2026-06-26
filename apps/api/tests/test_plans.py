from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.auth import get_current_user
from app.core.config import get_settings
from app.core.types import AuthenticatedUser
from app.db.session import SessionLocal
from app.main import app
from app.models.ai_run import AIRun
from app.models.transaction import Transaction
from app.models.uploaded_file import UploadedFile
from app.models.user import User
from app.services.monthly_plan import build_deterministic_monthly_plan
from app.services.finance_tools import (
    get_profile_context_tool,
    get_savings_opportunities_tool,
    get_spending_summary_tool,
)
from app.services.analytics import AnalyticsDateRange
from app.services.uploads import parse_transactions_csv
from app.services.users import get_or_create_user_from_auth

FIXTURES_DIR = Path(__file__).parent / "fixtures"
SAMPLE_TRANSACTIONS_CSV = (FIXTURES_DIR / "sample_transactions.csv").read_text()


@pytest.fixture(autouse=True)
def ai_disabled():
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture
def auth_user_with_transactions():
    db = SessionLocal()
    user = get_or_create_user_from_auth(
        db,
        AuthenticatedUser(
            clerk_user_id="user_plan_test",
            email="plan@test.com",
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

    db.query(AIRun).filter(AIRun.user_id == user.id).delete()
    db.query(Transaction).filter(Transaction.user_id == user.id).delete()
    db.query(UploadedFile).filter(UploadedFile.user_id == user.id).delete()
    db.query(User).filter(User.id == user.id).delete()
    db.commit()
    db.close()


@pytest.fixture
def auth_user_without_transactions():
    db = SessionLocal()
    user = get_or_create_user_from_auth(
        db,
        AuthenticatedUser(
            clerk_user_id="user_plan_empty",
            email="plan-empty@test.com",
            claims={},
        ),
    )
    auth = AuthenticatedUser(
        clerk_user_id=user.clerk_user_id,
        email=user.email,
        claims={},
    )
    db.commit()

    yield db, user, auth

    db.query(AIRun).filter(AIRun.user_id == user.id).delete()
    db.query(User).filter(User.id == user.id).delete()
    db.commit()
    db.close()


def test_post_monthly_plan_requires_auth():
    client = TestClient(app)
    response = client.post("/plans/monthly", json={})
    assert response.status_code == 401


def test_post_monthly_plan_ai_disabled(auth_user_with_transactions):
    db, user, auth = auth_user_with_transactions
    app.dependency_overrides[get_current_user] = lambda: auth
    client = TestClient(app)
    try:
        response = client.post("/plans/monthly", json={})
        assert response.status_code == 200
        body = response.json()

        assert "target" in body
        assert "recommended_cuts" in body
        assert "weekly_steps" in body
        assert "assumptions" in body
        assert "citations" in body
        assert body["ai_run_id"]

        assert len(body["weekly_steps"]) == 4
        assert len(body["citations"]) >= 4
        assert body["target"]["monthly_savings_goal"] >= 0

        groceries_cut = next(
            item for item in body["recommended_cuts"] if item["category"] == "Groceries"
        )
        assert groceries_cut["current_spending"] == 86.21
        assert groceries_cut["recommended_cut"] == 8.62

        ai_run = db.query(AIRun).filter(AIRun.id == body["ai_run_id"]).one()
        assert ai_run.user_id == user.id
        assert ai_run.model == "deterministic-fallback"
        assert ai_run.retrieval_count == 0
        assert len(ai_run.tool_calls) == 4
    finally:
        app.dependency_overrides.clear()


def test_post_monthly_plan_numbers_from_analytics(auth_user_with_transactions):
    db, user, auth = auth_user_with_transactions
    date_range = AnalyticsDateRange()
    tool_outputs = {
        "profile_context": get_profile_context_tool(db, user.id),
        "spending_summary": get_spending_summary_tool(db, user.id, date_range),
        "recurring_expenses": {"items": []},
        "savings_opportunities": get_savings_opportunities_tool(
            db, user.id, date_range
        ),
    }
    plan = build_deterministic_monthly_plan(tool_outputs)

    app.dependency_overrides[get_current_user] = lambda: auth
    client = TestClient(app)
    try:
        response = client.post("/plans/monthly", json={})
        body = response.json()
        assert body["target"]["current_estimated_savings"] == round(
            plan["target"].current_estimated_savings,
            2,
        )
        assert len(body["recommended_cuts"]) == len(plan["recommended_cuts"])
    finally:
        app.dependency_overrides.clear()


def test_post_monthly_plan_limited_data(auth_user_without_transactions):
    db, user, auth = auth_user_without_transactions
    app.dependency_overrides[get_current_user] = lambda: auth
    client = TestClient(app)
    try:
        response = client.post("/plans/monthly", json={})
        assert response.status_code == 200
        body = response.json()
        assert body["recommended_cuts"] == []
        assert len(body["weekly_steps"]) == 4
        assert any("limited" in item.lower() or "upload" in item.lower() for item in body["assumptions"] + [step["action"] for step in body["weekly_steps"]])
    finally:
        app.dependency_overrides.clear()


def test_post_monthly_plan_user_scoped(auth_user_with_transactions):
    db, user, auth = auth_user_with_transactions
    other_user = get_or_create_user_from_auth(
        db,
        AuthenticatedUser(
            clerk_user_id="user_plan_other",
            email="plan-other@test.com",
            claims={},
        ),
    )

    app.dependency_overrides[get_current_user] = lambda: auth
    client = TestClient(app)
    try:
        response = client.post("/plans/monthly", json={})
        ai_run_id = response.json()["ai_run_id"]
        ai_run = db.query(AIRun).filter(AIRun.id == ai_run_id).one()
        assert ai_run.user_id == user.id
        assert ai_run.user_id != other_user.id
    finally:
        app.dependency_overrides.clear()
        db.query(AIRun).filter(AIRun.user_id == other_user.id).delete()
        db.query(User).filter(User.id == other_user.id).delete()
        db.commit()
