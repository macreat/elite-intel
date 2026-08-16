from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.category import Category
from app.models.enums import TransactionType


class CategoryRepository:
    def __init__(self, db: Session):
        self.db = db

    def list(self, *, type_filter: TransactionType | None = None, active: bool | None = None) -> list[Category]:
        stmt = select(Category)
        if type_filter is not None:
            stmt = stmt.where(Category.type == type_filter)
        if active is not None:
            stmt = stmt.where(Category.active == active)
        return list(self.db.scalars(stmt.order_by(Category.name)).all())

    def get(self, category_id: int) -> Category | None:
        return self.db.get(Category, category_id)

    def create(self, category: Category) -> Category:
        self.db.add(category)
        self.db.flush()
        self.db.refresh(category)
        return category

    def update(self, category: Category) -> Category:
        self.db.add(category)
        self.db.flush()
        self.db.refresh(category)
        return category
