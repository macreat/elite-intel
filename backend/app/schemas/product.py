from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field

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
