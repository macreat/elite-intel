from datetime import datetime

from pydantic import BaseModel, Field

from app.models.enums import TransactionType
from app.schemas.common import ORMBase


class CategoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    type: TransactionType
    description: str | None = Field(default=None, max_length=255)


class CategoryUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=255)
    active: bool | None = None


class CategoryRead(ORMBase):
    id: int
    name: str
    type: TransactionType
    description: str | None
    active: bool
    created_at: datetime
    updated_at: datetime
