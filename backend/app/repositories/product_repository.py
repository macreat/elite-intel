from __future__ import annotations

from sqlalchemy import func, select
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

    def get(self, product_id: int) -> Product | None:
        return self.db.get(Product, product_id)

    def get_many(self, product_ids: list[int]) -> dict[int, Product]:
        if not product_ids:
            return {}
        stmt = select(Product).where(Product.id.in_(product_ids))
        return {product.id: product for product in self.db.scalars(stmt).all()}

    def create(self, product: Product) -> Product:
        self.db.add(product)
        self.db.flush()
        self.db.refresh(product)
        return product

    def first_category_id(self) -> int | None:
        from app.models.category import Category

        return self.db.scalar(select(Category.id).order_by(Category.id).limit(1))

    def get_or_create_default_category(self) -> int:
        from app.models.category import Category

        existing = self.first_category_id()
        if existing is not None:
            return existing
        category = Category(name="General", type="EXPENSE")
        self.db.add(category)
        self.db.flush()
        return category.id

    def list_catalog(
        self, *, search: str | None = None, page: int = 1, page_size: int = 20
    ) -> tuple[list[Product], int]:
        stmt = select(Product)
        if search:
            stmt = stmt.where(Product.name.ilike(f"%{search}%"))
        total = self.db.scalar(select(func.count()).select_from(stmt.subquery()))
        items = list(
            self.db.scalars(stmt.order_by(Product.name).offset((page - 1) * page_size).limit(page_size)).all()
        )
        return items, total
