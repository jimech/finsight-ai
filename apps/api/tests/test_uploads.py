import io
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
VALID_CSV = SAMPLE_TRANSACTIONS_CSV


@pytest.fixture
def auth_user():
    db = SessionLocal()
    user = get_or_create_user_from_auth(
        db,
        AuthenticatedUser(
            clerk_user_id="user_upload_test",
            email="upload@test.com",
            claims={},
        ),
    )
    auth = AuthenticatedUser(
        clerk_user_id=user.clerk_user_id,
        email=user.email,
        claims={},
    )
    yield db, user, auth
    db.query(Transaction).filter(Transaction.user_id == user.id).delete()
    db.query(UploadedFile).filter(UploadedFile.user_id == user.id).delete()
    db.query(User).filter(User.id == user.id).delete()
    db.commit()
    db.close()


def test_parse_transactions_csv_success():
    rows = parse_transactions_csv(VALID_CSV)
    assert len(rows) == 3
    assert rows[0].description == "STARBUCKS #123"
    assert str(rows[0].amount) == "-5.75"


def test_parse_transactions_csv_missing_columns():
    with pytest.raises(Exception, match="missing required columns"):
        parse_transactions_csv("description,amount\nfoo,1")


def test_parse_transactions_csv_invalid_date():
    with pytest.raises(Exception, match="invalid date"):
        parse_transactions_csv(
            "date,description,amount\nnot-a-date,Coffee,-1.00\n"
        )


def test_parse_transactions_csv_invalid_amount():
    with pytest.raises(Exception, match="invalid amount"):
        parse_transactions_csv(
            "date,description,amount\n2026-01-02,Coffee,abc\n"
        )


def test_upload_requires_auth():
    client = TestClient(app)
    response = client.post(
        "/uploads/transactions",
        files={"file": ("transactions.csv", VALID_CSV, "text/csv")},
    )
    assert response.status_code == 401


def test_upload_rejects_non_csv(auth_user):
    db, user, auth = auth_user
    app.dependency_overrides[get_current_user] = lambda: auth
    client = TestClient(app)
    try:
        response = client.post(
            "/uploads/transactions",
            files={"file": ("transactions.txt", "hello", "text/plain")},
        )
        assert response.status_code == 400
        assert "Only .csv files are accepted" in response.json()["detail"]
    finally:
        app.dependency_overrides.clear()


def test_upload_valid_csv_creates_records(auth_user):
    db, user, auth = auth_user
    app.dependency_overrides[get_current_user] = lambda: auth
    client = TestClient(app)
    try:
        response = client.post(
            "/uploads/transactions",
            files={"file": ("transactions.csv", VALID_CSV, "text/csv")},
        )
        assert response.status_code == 200, response.text
        body = response.json()
        assert body["status"] == "completed"
        assert body["transactions_imported"] == 3

        uploads = db.scalars(
            select(UploadedFile).where(UploadedFile.user_id == user.id)
        ).all()
        assert len(uploads) == 1
        assert uploads[0].status == "completed"

        transactions = db.scalars(
            select(Transaction).where(Transaction.user_id == user.id)
        ).all()
        assert len(transactions) == 3
        assert all(txn.source_file_id == uploads[0].id for txn in transactions)

        list_response = client.get("/uploads")
        assert list_response.status_code == 200
        assert len(list_response.json()) == 1
        assert list_response.json()[0]["filename"] == "transactions.csv"
    finally:
        app.dependency_overrides.clear()


def test_upload_invalid_csv_marks_failed(auth_user):
    db, user, auth = auth_user
    app.dependency_overrides[get_current_user] = lambda: auth
    client = TestClient(app)
    invalid_csv = "date,description,amount\nbad-date,Coffee,1.00\n"
    try:
        response = client.post(
            "/uploads/transactions",
            files={"file": ("transactions.csv", invalid_csv, "text/csv")},
        )
        assert response.status_code == 400
        upload = db.scalar(
            select(UploadedFile).where(UploadedFile.user_id == user.id)
        )
        assert upload is not None
        assert upload.status == "failed"
        assert upload.error_message is not None
    finally:
        app.dependency_overrides.clear()
