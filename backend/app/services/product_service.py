from sqlalchemy.orm import Session

from app.repositories.product_repository import ProductRepository


class ProductService:
    def __init__(self, db: Session):
        self.repo = ProductRepository(db)

    def get(self, product_id: int):
        return self.repo.get(product_id)

    def create(self, *, name: str, category_id: int, active: bool = True):
        from app.models.product import Product

        product = Product(name=name, category_id=category_id, active=active)
        return self.repo.create(product)

    def list(self, *, category_id: int | None = None, active: bool | None = None):
        return self.repo.list(category_id=category_id, active=active)

    def list_catalog(self, *, search: str | None = None, page: int = 1, page_size: int = 20):
        return self.repo.list_catalog(search=search, page=page, page_size=page_size)
