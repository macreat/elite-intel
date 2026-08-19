from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.product import ProductCatalogListResponse
from app.services.product_service import ProductService

router = APIRouter(prefix="/catalog", tags=["catalog"])


@router.get("", response_model=ProductCatalogListResponse)
def list_catalog(
    search: str | None = Query(None, max_length=150),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    service = ProductService(db)
    items, total = service.list_catalog(search=search, page=page, page_size=page_size)
    return ProductCatalogListResponse(items=items, total=total, page=page, page_size=page_size)
