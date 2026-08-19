from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel

from app.schemas.common import ORMBase


class ProductRead(ORMBase):
    id: int
    name: str
    category_id: int
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
