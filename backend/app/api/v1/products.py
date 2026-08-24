from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.product import (
    ProductRead,
    StockBulkRequest,
    StockBulkResponse,
    StockUpdateRequest,
)
from app.services.errors import EntityNotFoundError
from app.services.product_service import ProductService

router = APIRouter(prefix="/products", tags=["products"])


class ProductCreate(BaseModel):
    name: str
    category_id: int
    active: bool = True


@router.get("", response_model=list[ProductRead])
def list_products(category_id: int | None = None, active: bool | None = None, db: Session = Depends(get_db)):
    service = ProductService(db)
    return service.list(category_id=category_id, active=active)


@router.post("", status_code=status.HTTP_201_CREATED, response_model=ProductRead)
def create_product(payload: ProductCreate, db: Session = Depends(get_db)):
    service = ProductService(db)
    try:
        return service.create(name=payload.name, category_id=payload.category_id, active=payload.active)
    except EntityNotFoundError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/{product_id}", response_model=ProductRead)
def get_product(product_id: int, db: Session = Depends(get_db)):
    service = ProductService(db)
    product = service.get(product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="product not found")
    return product


@router.patch("/{product_id}/stock", response_model=ProductRead)
def update_product_stock(product_id: int, payload: StockUpdateRequest, db: Session = Depends(get_db)):
    service = ProductService(db)
    try:
        return service.update_stock(product_id, payload.stock)
    except EntityNotFoundError as exc:
        raise HTTPException(status_code=404, detail="product not found") from exc


@router.post("/stock/bulk", response_model=StockBulkResponse)
def bulk_update_stock(payload: StockBulkRequest, db: Session = Depends(get_db)):
    service = ProductService(db)
    items = [(item.product_id, item.stock) for item in payload.items]
    try:
        updated = service.bulk_update_stocks(items)
    except EntityNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return StockBulkResponse(items=updated)
