from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.product import ProductRead
from app.services.product_service import ProductService

router = APIRouter(prefix="/products", tags=["products"])


@router.get("", response_model=list[ProductRead])
def list_products(category_id: int | None = None, active: bool | None = None, db: Session = Depends(get_db)):
    service = ProductService(db)
    return service.list(category_id=category_id, active=active)
