from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.types import AuthenticatedUser
from app.db.session import get_db
from app.schemas.upload import TransactionUploadResponse, UploadListItem
from app.services.uploads import (
    CsvValidationError,
    list_user_uploads,
    process_transaction_csv_upload,
)
from app.services.users import get_or_create_user_from_auth

router = APIRouter(prefix="/uploads", tags=["uploads"])


def _validate_csv_filename(filename: Optional[str]) -> str:
    if not filename or not filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only .csv files are accepted",
        )
    return filename


@router.post("/transactions", response_model=TransactionUploadResponse)
async def upload_transactions(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    authenticated_user: AuthenticatedUser = Depends(get_current_user),
):
    filename = _validate_csv_filename(file.filename)
    user = get_or_create_user_from_auth(db, authenticated_user)
    content = await file.read()

    try:
        upload, imported_count = process_transaction_csv_upload(
            db, user, filename, content
        )
    except CsvValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    return TransactionUploadResponse(
        upload_id=upload.id,
        status=upload.status,
        transactions_imported=imported_count,
    )


@router.get("", response_model=list[UploadListItem])
def get_uploads(
    db: Session = Depends(get_db),
    authenticated_user: AuthenticatedUser = Depends(get_current_user),
):
    user = get_or_create_user_from_auth(db, authenticated_user)
    return list_user_uploads(db, user.id)
