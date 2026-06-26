from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.core.auth import get_current_user
from app.core.config import get_settings
from app.core.types import AuthenticatedUser
from app.db.session import SessionLocal
from app.main import app
from app.models.ai_run import AIRun
from app.models.evaluation import Evaluation
from app.models.transaction import Transaction
from app.models.uploaded_file import UploadedFile
from app.models.user import User
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
def auth_user_with_ai_runs():
    db = SessionLocal()
    user = get_or_create_user_from_auth(
        db,
        AuthenticatedUser(
            clerk_user_id="user_eval_test",
            email="eval@test.com",
            claims={},
        ),
    )
    auth = AuthenticatedUser(
        clerk_user_id=user.clerk_user_id,
        email=user.email,
        claims={},
    )

    for index in range(3):
        db.add(
            AIRun(
                user_id=user.id,
                prompt=f"Prompt {index}",
                response=f'{{"citations": [], "message": "Response {index}"}}',
                model="deterministic-fallback",
                latency_ms=100 + index,
                retrieval_count=0,
                tool_calls=[{"tool": "spending_summary", "output": {}}],
            )
        )
    db.commit()

    yield db, user, auth

    db.query(Evaluation).filter(
        Evaluation.ai_run_id.in_(
            db.query(AIRun.id).filter(AIRun.user_id == user.id)
        )
    ).delete(synchronize_session=False)
    db.query(AIRun).filter(AIRun.user_id == user.id).delete()
    db.query(User).filter(User.id == user.id).delete()
    db.commit()
    db.close()


def _create_ai_run_via_chat(auth_user_with_transactions):
    db, user, auth = auth_user_with_transactions
    app.dependency_overrides[get_current_user] = lambda: auth
    client = TestClient(app)
    try:
        response = client.post(
            "/chat",
            json={"message": "How can I save more money?"},
        )
        assert response.status_code == 200
        return db, user, auth, response.json()["ai_run_id"]
    finally:
        app.dependency_overrides.clear()


@pytest.fixture
def auth_user_with_transactions():
    db = SessionLocal()
    user = get_or_create_user_from_auth(
        db,
        AuthenticatedUser(
            clerk_user_id="user_eval_chat_test",
            email="eval-chat@test.com",
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

    db.query(Evaluation).filter(
        Evaluation.ai_run_id.in_(
            db.query(AIRun.id).filter(AIRun.user_id == user.id)
        )
    ).delete(synchronize_session=False)
    db.query(AIRun).filter(AIRun.user_id == user.id).delete()
    db.query(Transaction).filter(Transaction.user_id == user.id).delete()
    db.query(UploadedFile).filter(UploadedFile.user_id == user.id).delete()
    db.query(User).filter(User.id == user.id).delete()
    db.commit()
    db.close()


def test_get_ai_runs_requires_auth():
    client = TestClient(app)
    assert client.get("/admin/ai-runs").status_code == 401


def test_get_ai_runs_user_scoped(auth_user_with_ai_runs):
    db, user, auth = auth_user_with_ai_runs
    other_user = get_or_create_user_from_auth(
        db,
        AuthenticatedUser(
            clerk_user_id="user_eval_other",
            email="eval-other@test.com",
            claims={},
        ),
    )
    db.add(
        AIRun(
            user_id=other_user.id,
            prompt="Other user prompt",
            response="Other response",
            model="deterministic-fallback",
        )
    )
    db.commit()

    app.dependency_overrides[get_current_user] = lambda: auth
    client = TestClient(app)
    try:
        response = client.get("/admin/ai-runs")
        assert response.status_code == 200
        body = response.json()
        assert body["total"] == 3
        assert len(body["items"]) == 3
        assert all("Other user prompt" not in item["prompt"] for item in body["items"])
        assert body["items"][0]["suggested_scores"]["groundedness_score"] == 0.9
    finally:
        app.dependency_overrides.clear()
        db.query(AIRun).filter(AIRun.user_id == other_user.id).delete()
        db.query(User).filter(User.id == other_user.id).delete()
        db.commit()


def test_get_ai_runs_pagination(auth_user_with_ai_runs):
    db, user, auth = auth_user_with_ai_runs
    app.dependency_overrides[get_current_user] = lambda: auth
    client = TestClient(app)
    try:
        response = client.get("/admin/ai-runs?limit=2&offset=1")
        assert response.status_code == 200
        body = response.json()
        assert body["total"] == 3
        assert body["limit"] == 2
        assert body["offset"] == 1
        assert len(body["items"]) == 2
    finally:
        app.dependency_overrides.clear()


def test_get_evaluations_requires_auth():
    client = TestClient(app)
    assert client.get("/admin/evaluations").status_code == 401


def test_evaluate_ai_run_create_and_update(auth_user_with_ai_runs):
    db, user, auth = auth_user_with_ai_runs
    ai_run = db.query(AIRun).filter(AIRun.user_id == user.id).first()

    app.dependency_overrides[get_current_user] = lambda: auth
    client = TestClient(app)
    try:
        response = client.post(
            f"/admin/evaluate/{ai_run.id}",
            json={
                "citation_score": 0.9,
                "calculation_score": 0.8,
                "groundedness_score": 0.95,
                "hallucination_flag": False,
                "safety_flag": False,
            },
        )
        assert response.status_code == 200
        body = response.json()
        assert body["ai_run_id"] == str(ai_run.id)
        assert body["citation_score"] == 0.9

        update_response = client.post(
            f"/admin/evaluate/{ai_run.id}",
            json={
                "citation_score": 0.7,
                "calculation_score": 0.6,
                "groundedness_score": 0.75,
                "hallucination_flag": True,
                "safety_flag": False,
            },
        )
        assert update_response.status_code == 200
        updated = update_response.json()
        assert updated["citation_score"] == 0.7
        assert updated["hallucination_flag"] is True

        evaluations = client.get("/admin/evaluations")
        assert evaluations.status_code == 200
        assert evaluations.json()["total"] == 1

        runs = client.get("/admin/ai-runs")
        evaluated_run = next(
            item for item in runs.json()["items"] if item["id"] == str(ai_run.id)
        )
        assert evaluated_run["evaluation"] is not None
        assert evaluated_run["evaluation"]["citation_score"] == 0.7
    finally:
        app.dependency_overrides.clear()


def test_evaluate_ai_run_score_validation(auth_user_with_ai_runs):
    db, user, auth = auth_user_with_ai_runs
    ai_run = db.query(AIRun).filter(AIRun.user_id == user.id).first()

    app.dependency_overrides[get_current_user] = lambda: auth
    client = TestClient(app)
    try:
        response = client.post(
            f"/admin/evaluate/{ai_run.id}",
            json={
                "citation_score": 1.5,
                "calculation_score": 0.8,
                "groundedness_score": 0.9,
                "hallucination_flag": False,
                "safety_flag": False,
            },
        )
        assert response.status_code == 422
    finally:
        app.dependency_overrides.clear()


def test_cannot_evaluate_other_users_ai_run(auth_user_with_ai_runs):
    db, user, auth = auth_user_with_ai_runs
    other_user = get_or_create_user_from_auth(
        db,
        AuthenticatedUser(
            clerk_user_id="user_eval_block",
            email="eval-block@test.com",
            claims={},
        ),
    )
    other_run = AIRun(
        id=uuid4(),
        user_id=other_user.id,
        prompt="Private prompt",
        response="Private response",
        model="deterministic-fallback",
    )
    db.add(other_run)
    db.commit()

    app.dependency_overrides[get_current_user] = lambda: auth
    client = TestClient(app)
    try:
        response = client.post(
            f"/admin/evaluate/{other_run.id}",
            json={
                "citation_score": 0.5,
                "calculation_score": 0.5,
                "groundedness_score": 0.5,
                "hallucination_flag": False,
                "safety_flag": False,
            },
        )
        assert response.status_code == 404
    finally:
        app.dependency_overrides.clear()
        db.query(AIRun).filter(AIRun.user_id == other_user.id).delete()
        db.query(User).filter(User.id == other_user.id).delete()
        db.commit()
