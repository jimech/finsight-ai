from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class TransactionUploadResponse(BaseModel):
    upload_id: UUID
    status: str
    transactions_imported: int


class UploadListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    filename: str
    file_type: str
    status: str
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime
