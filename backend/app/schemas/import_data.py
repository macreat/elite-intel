from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel

from app.models.enums import ImportStatus, TransactionType


class ImportUploadResponse(BaseModel):
    batch_id: int
    status: ImportStatus
    columns_detected: list[str]
    suggested_mapping: dict[str, str]


class ImportMappingRequest(BaseModel):
    mapping: dict[str, str]


class ImportInvalidRow(BaseModel):
    row_number: int
    error_code: str
    message: str


class ImportPreviewRow(BaseModel):
    occurred_at: datetime
    transaction_type: TransactionType
    category_id: int
    description: str
    amount: Decimal
    product_id: int | None = None
    notes: str | None = None


class ImportMappingSummary(BaseModel):
    records_total: int
    records_valid: int
    records_invalid: int
    records_duplicate: int


class ImportMappingResponse(BaseModel):
    batch_id: int
    status: ImportStatus
    summary: ImportMappingSummary
    preview: list[ImportPreviewRow]
    invalid_rows: list[ImportInvalidRow]


class ImportConfirmResponse(BaseModel):
    batch_id: int
    status: ImportStatus
    records_inserted: int


class ImportBatchRead(BaseModel):
    id: int
    filename: str
    source_type: str
    status: ImportStatus
    records_total: int
    records_valid: int
    records_invalid: int
    records_duplicate: int
    records_inserted: int
    created_at: datetime
    updated_at: datetime


class ImportBatchDetail(BaseModel):
    id: int
    filename: str
    source_type: str
    status: ImportStatus
    records_total: int
    records_valid: int
    records_invalid: int
    records_duplicate: int
    records_inserted: int
    created_at: datetime
    updated_at: datetime
    rows_summary: dict[str, int]
