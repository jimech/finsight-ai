from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.auth import get_current_user
from app.core.config import get_settings
from app.core.types import AuthenticatedUser
from app.db.session import SessionLocal
from app.main import app
from app.models.ai_run import AIRun
from app.models.chat_message import ChatMessage
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
def auth_user_with_transactions():
    db = SessionLocal()
    user = get_or_create_user_from_auth(
        db,
        AuthenticatedUser(
            clerk_user_id="user_chat_test",
            email="chat@test.com",
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

    db.query(ChatMessage).filter(ChatMessage.user_id == user.id).delete()
    db.query(AIRun).filter(AIRun.user_id == user.id).delete()
    db.query(Transaction).filter(Transaction.user_id == user.id).delete()
    db.query(UploadedFile).filter(UploadedFile.user_id == user.id).delete()
    db.query(User).filter(User.id == user.id).delete()
    db.commit()
    db.close()


def test_post_chat_requires_auth():
    client = TestClient(app)
    response = client.post("/chat", json={"message": "How can I save more?"})
    assert response.status_code == 401


def test_post_chat_ai_disabled_fallback(auth_user_with_transactions):
    db, user, auth = auth_user_with_transactions
    app.dependency_overrides[get_current_user] = lambda: auth
    client = TestClient(app)
    try:
        response = client.post(
            "/chat",
            json={"message": "How can I save more money this month?"},
        )
        assert response.status_code == 200
        body = response.json()
        assert "message" in body
        assert body["message"]
        assert "$91.96" in body["message"]
        assert len(body["citations"]) == 4
        assert body["ai_run_id"]

        ai_run = db.query(AIRun).filter(AIRun.id == body["ai_run_id"]).one()
        assert ai_run.user_id == user.id
        assert ai_run.model == "deterministic-fallback"
        assert ai_run.retrieval_count == 0
        assert ai_run.tool_calls is not None
        assert len(ai_run.tool_calls) == 4

        messages = (
            db.query(ChatMessage)
            .filter(ChatMessage.user_id == user.id)
            .order_by(ChatMessage.created_at.asc())
            .all()
        )
        assert len(messages) == 2
        assert messages[0].role == "user"
        assert messages[1].role == "assistant"
        assert messages[1].citations is not None
    finally:
        app.dependency_overrides.clear()


def test_get_chat_history_requires_auth():
    client = TestClient(app)
    assert client.get("/chat/history").status_code == 401


def test_get_chat_history_returns_only_current_user(auth_user_with_transactions):
    db, user, auth = auth_user_with_transactions
    other_user = get_or_create_user_from_auth(
        db,
        AuthenticatedUser(
            clerk_user_id="user_chat_other",
            email="other-chat@test.com",
            claims={},
        ),
    )
    db.add(
        ChatMessage(
            user_id=other_user.id,
            role="user",
            content="Other user message",
            citations=None,
        )
    )
    db.commit()

    app.dependency_overrides[get_current_user] = lambda: auth
    client = TestClient(app)
    try:
        client.post("/chat", json={"message": "What are my top categories?"})

        response = client.get("/chat/history")
        assert response.status_code == 200
        body = response.json()
        assert len(body["messages"]) == 2
        assert all("Other user message" not in msg["content"] for msg in body["messages"])
        assert body["messages"][0]["role"] == "user"
        assert body["messages"][-1]["role"] == "assistant"
    finally:
        app.dependency_overrides.clear()
        db.query(ChatMessage).filter(ChatMessage.user_id == other_user.id).delete()
        db.query(User).filter(User.id == other_user.id).delete()
        db.commit()
