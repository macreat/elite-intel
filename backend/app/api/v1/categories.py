from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.enums import TransactionType
from app.schemas.category import CategoryCreate, CategoryRead, CategoryUpdate
from app.services.category_service import CategoryService

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("", response_model=list[CategoryRead])
def list_categories(type: TransactionType | None = None, active: bool | None = None, db: Session = Depends(get_db)):
    service = CategoryService(db)
    return service.list(type_filter=type, active=active)


@router.post("", status_code=status.HTTP_201_CREATED, response_model=CategoryRead)
def create_category(payload: CategoryCreate, db: Session = Depends(get_db)):
    service = CategoryService(db)
    return service.create(payload)


@router.put("/{category_id}", response_model=CategoryRead)
def update_category(category_id: int, payload: CategoryUpdate, db: Session = Depends(get_db)):
    service = CategoryService(db)
    return service.update(category_id, payload)


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(category_id: int, db: Session = Depends(get_db)):
    service = CategoryService(db)
    service.soft_delete(category_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
