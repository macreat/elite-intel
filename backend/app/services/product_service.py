from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from app.core.config import settings
from app.repositories.product_repository import ProductRepository
from app.services.errors import EntityNotFoundError

logger = logging.getLogger(__name__)


def _export_stock_to_catalog(products) -> None:
    """Best-effort mirror of stock changes into the source xlsx catalog.

    The DB is the source of truth: any export failure is logged as a
    warning and never propagated to the caller.
    """
    try:
        from app.services.catalog_export import sync_stocks_to_catalog

        counts = sync_stocks_to_catalog(settings.CATALOG_XLSX_PATH, products)
        logger.info(
            "catalog export: %s updated, %s skipped (%s)",
            counts["updated"],
            counts["skipped"],
            settings.CATALOG_XLSX_PATH,
        )
    except (OSError, PermissionError, ValueError):
        logger.warning(
            "catalog export failed for %s", settings.CATALOG_XLSX_PATH, exc_info=True
        )


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

    def update_stock(self, product_id: int, stock: int | None):
        product = self.repo.get(product_id)
        if product is None:
            raise EntityNotFoundError("product not found")
        product.stock_qty = stock
        self.repo.db.commit()
        self.repo.db.refresh(product)
        _export_stock_to_catalog([product])
        return product

    def bulk_update_stocks(self, items: list[tuple[int, int | None]]) -> list:
        """Set stock for many products atomically; raises before any write
        if any product id is unknown."""
        ids = [product_id for product_id, _ in items]
        found = self.repo.get_many(ids)
        missing = sorted(set(ids) - set(found))
        if missing:
            raise EntityNotFoundError(f"unknown products: {missing}")
        updated = []
        for product_id, stock in items:
            product = found[product_id]
            product.stock_qty = stock
            updated.append(product)
        self.repo.db.commit()
        for product in updated:
            self.repo.db.refresh(product)
        _export_stock_to_catalog(updated)  # single save for the whole batch
        return updated
