from datetime import datetime

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.enums import TransactionType
from app.schemas.transaction import TransactionCreate, TransactionListResponse, TransactionRead, TransactionUpdate
from app.services.transaction_service import TransactionService

router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.get("", response_model=TransactionListResponse)
def list_transactions(
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    type: TransactionType | None = None,
    category_id: int | None = None,
    search: str | None = None,
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
):
    service = TransactionService(db)
    items, total = service.list(
        start_date=start_date,
        end_date=end_date,
        type_filter=type,
        category_id=category_id,
        search=search,
        page=page,
        page_size=page_size,
    )
    return TransactionListResponse(items=items, total=total, page=page, page_size=page_size)


@router.post("", status_code=status.HTTP_201_CREATED, response_model=TransactionRead)
def create_transaction(payload: TransactionCreate, db: Session = Depends(get_db)):
    service = TransactionService(db)
    return service.create(payload)


@router.get("/{transaction_id}", response_model=TransactionRead)
def get_transaction(transaction_id: int, db: Session = Depends(get_db)):
    service = TransactionService(db)
    return service.get(transaction_id)


@router.put("/{transaction_id}", response_model=TransactionRead)
def update_transaction(transaction_id: int, payload: TransactionUpdate, db: Session = Depends(get_db)):
    service = TransactionService(db)
    return service.update(transaction_id, payload)


@router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_transaction(transaction_id: int, db: Session = Depends(get_db)):
    service = TransactionService(db)
    service.delete(transaction_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
