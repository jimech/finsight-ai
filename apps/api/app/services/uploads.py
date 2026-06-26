import csv
import io
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.transaction import Transaction
from app.models.uploaded_file import UploadedFile
from app.models.user import User

REQUIRED_COLUMNS = frozenset({"date", "description", "amount"})
OPTIONAL_COLUMNS = frozenset({"merchant", "category"})
ALLOWED_COLUMNS = REQUIRED_COLUMNS | OPTIONAL_COLUMNS
FILE_TYPE_TRANSACTIONS_CSV = "transactions_csv"
STATUS_PROCESSING = "processing"
STATUS_COMPLETED = "completed"
STATUS_FAILED = "failed"


class CsvValidationError(ValueError):
    pass


@dataclass(frozen=True)
class ParsedTransactionRow:
    date: date
    description: str
    amount: Decimal
    merchant: Optional[str]
    category: Optional[str]


def _parse_date(value: str, row_number: int) -> date:
    raw = value.strip()
    if not raw:
        raise CsvValidationError(f"Row {row_number}: date is required")

    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%m/%d/%y"):
        try:
            return datetime.strptime(raw, fmt).date()
        except ValueError:
            continue

    try:
        return date.fromisoformat(raw)
    except ValueError as exc:
        raise CsvValidationError(
            f"Row {row_number}: invalid date '{value.strip()}'"
        ) from exc


def _parse_amount(value: str, row_number: int) -> Decimal:
    raw = value.strip()
    if not raw:
        raise CsvValidationError(f"Row {row_number}: amount is required")

    normalized = raw.replace(",", "").replace("$", "")
    try:
        return Decimal(normalized)
    except InvalidOperation as exc:
        raise CsvValidationError(
            f"Row {row_number}: invalid amount '{value.strip()}'"
        ) from exc


def _normalize_header_field(field: Optional[str]) -> str:
    return (field or "").strip().lower()


def parse_transactions_csv(content: str) -> list[ParsedTransactionRow]:
    if not content.strip():
        raise CsvValidationError("CSV file is empty")

    reader = csv.DictReader(io.StringIO(content))
    if reader.fieldnames is None:
        raise CsvValidationError("CSV file is missing a header row")

    headers = {_normalize_header_field(name) for name in reader.fieldnames if name}
    missing = sorted(REQUIRED_COLUMNS - headers)
    if missing:
        raise CsvValidationError(
            f"CSV is missing required columns: {', '.join(missing)}"
        )

    unknown = headers - ALLOWED_COLUMNS
    if unknown:
        raise CsvValidationError(
            f"CSV contains unsupported columns: {', '.join(sorted(unknown))}"
        )

    rows: list[ParsedTransactionRow] = []
    for index, raw_row in enumerate(reader, start=2):
        if not any((value or "").strip() for value in raw_row.values()):
            continue

        row = {
            _normalize_header_field(key): (value or "").strip()
            for key, value in raw_row.items()
            if key is not None
        }

        description = row.get("description", "")
        if not description:
            raise CsvValidationError(f"Row {index}: description is required")

        rows.append(
            ParsedTransactionRow(
                date=_parse_date(row.get("date", ""), index),
                description=description,
                amount=_parse_amount(row.get("amount", ""), index),
                merchant=row.get("merchant") or None,
                category=row.get("category") or None,
            )
        )

    return rows


def list_user_uploads(db: Session, user_id: UUID) -> list[UploadedFile]:
    return list(
        db.scalars(
            select(UploadedFile)
            .where(UploadedFile.user_id == user_id)
            .order_by(UploadedFile.created_at.desc())
        )
    )


def process_transaction_csv_upload(
    db: Session,
    user: User,
    filename: str,
    content: bytes,
) -> tuple[UploadedFile, int]:
    if b"\x00" in content:
        raise CsvValidationError("File does not appear to be a valid CSV")

    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise CsvValidationError("CSV file must be UTF-8 encoded") from exc

    upload = UploadedFile(
        user_id=user.id,
        filename=filename,
        file_type=FILE_TYPE_TRANSACTIONS_CSV,
        status=STATUS_PROCESSING,
    )
    db.add(upload)
    db.flush()

    try:
        parsed_rows = parse_transactions_csv(text)
        for row in parsed_rows:
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

        upload.status = STATUS_COMPLETED
        upload.error_message = None
        db.commit()
        db.refresh(upload)
        if settings.embeddings_enabled:
            from app.services.embeddings import generate_missing_embeddings_for_user

            generate_missing_embeddings_for_user(db, user.id)
        return upload, len(parsed_rows)
    except CsvValidationError as exc:
        upload.status = STATUS_FAILED
        upload.error_message = str(exc)
        db.commit()
        db.refresh(upload)
        raise
