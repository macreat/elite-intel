from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator, model_validator

from app.schemas.common import ORMBase


class ProductRead(ORMBase):
    id: int
    name: str
    category_id: int | None = None
    description: str | None
    active: bool
    invoice_price: Decimal | None = None
    local_price: Decimal | None = None
    currency_code: str = "COP"
    stock_qty: int | None = None
    created_at: datetime
    updated_at: datetime


class ProductCatalogItem(ProductRead):
    pass


class ProductCatalogListResponse(BaseModel):
    items: list[ProductCatalogItem]
    total: int
    page: int
    page_size: int


class StockUpdateRequest(BaseModel):
    stock: int | None = Field(default=None, ge=0)


class StockBulkItem(BaseModel):
    product_id: int
    stock: int | None = Field(default=None, ge=0)


class StockBulkRequest(BaseModel):
    items: list[StockBulkItem] = Field(min_length=1)


class StockBulkResponse(BaseModel):
    items: list[ProductRead]


class ProductCreate(BaseModel):
    name: str = Field(min_length=1)
    category_id: int | None = None
    active: bool = True
    invoice_price: Decimal | None = Field(default=None, ge=0)
    local_price: Decimal | None = Field(default=None, ge=0)
    stock_qty: int | None = Field(default=None, ge=0)


class ProductUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1)
    invoice_price: Decimal | None = Field(default=None, ge=0)
    local_price: Decimal | None = Field(default=None, ge=0)

    @field_validator("name")
    @classmethod
    def _name_not_blank(cls, value: str | None) -> str | None:
        if value is not None and not value.strip():
            raise ValueError("name must not be blank")
        return value


class PriceBulkItem(BaseModel):
    product_id: int
    invoice_price: Decimal | None = Field(default=None, ge=0)
    local_price: Decimal | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def _require_at_least_one_field(self):
        if self.invoice_price is None and self.local_price is None:
            raise ValueError("at least one of invoice_price or local_price is required")
        return self


class PriceBulkRequest(BaseModel):
    items: list[PriceBulkItem] = Field(min_length=1)


class PriceBulkResponse(BaseModel):
    items: list[ProductRead]
