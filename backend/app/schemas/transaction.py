from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator

from app.models.enums import TransactionSource, TransactionType
from app.schemas.common import ORMBase


class TransactionCreate(BaseModel):
    occurred_at: datetime
    transaction_type: TransactionType
    category_id: int
    description: str = Field(min_length=1, max_length=255)
    amount: Decimal = Field(gt=0)
    quantity: int = Field(default=1, ge=1)
    product_id: int | None = None
    notes: str | None = Field(default=None, max_length=1000)

    @field_validator("amount")
    @classmethod
    def ensure_positive(cls, value: Decimal):
        if value <= 0:
            raise ValueError("amount must be positive")
        return value


class TransactionUpdate(BaseModel):
    occurred_at: datetime | None = None
    transaction_type: TransactionType | None = None
    category_id: int | None = None
    description: str | None = Field(default=None, min_length=1, max_length=255)
    amount: Decimal | None = Field(default=None, gt=0)
    quantity: int | None = Field(default=None, ge=1)
    product_id: int | None = None
    notes: str | None = Field(default=None, max_length=1000)


class TransactionRead(ORMBase):
    id: int
    occurred_at: datetime
    transaction_type: TransactionType
    category_id: int
    description: str
    amount: Decimal
    quantity: int
    product_id: int | None
    notes: str | None
    currency_code: str
    source_type: TransactionSource
    created_at: datetime
    updated_at: datetime


class TransactionListResponse(BaseModel):
    items: list[TransactionRead]
    total: int
    page: int
    page_size: int
