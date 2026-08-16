from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.product import Product


class ProductRepository:
    def __init__(self, db: Session):
        self.db = db

    def list(self, *, category_id: int | None = None, active: bool | None = None) -> list[Product]:
        stmt = select(Product)
        if category_id is not None:
            stmt = stmt.where(Product.category_id == category_id)
        if active is not None:
            stmt = stmt.where(Product.active == active)
        return list(self.db.scalars(stmt.order_by(Product.name)).all())
