from sqlalchemy.orm import Session

from app.repositories.product_repository import ProductRepository


class ProductService:
    def __init__(self, db: Session):
        self.repo = ProductRepository(db)

    def list(self, *, category_id: int | None = None, active: bool | None = None):
        return self.repo.list(category_id=category_id, active=active)
