from datetime import datetime

from app.schemas.common import ORMBase


class ProductRead(ORMBase):
    id: int
    name: str
    category_id: int
    description: str | None
    active: bool
    created_at: datetime
    updated_at: datetime
