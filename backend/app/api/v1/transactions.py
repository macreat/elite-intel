from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.enums import TransactionType
from app.schemas.transaction import TransactionCreate, TransactionListResponse, TransactionRead, TransactionUpdate
from app.services.calendar import InvalidCalendarTimezone, parse_transaction_boundary
from app.services.transaction_service import TransactionService

router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.get("", response_model=TransactionListResponse)
def list_transactions(
    start_date: str | None = None,
    end_date: str | None = None,
    type: TransactionType | None = None,
    category_id: int | None = None,
    search: str | None = None,
    page: int = 1,
    page_size: int = 20,
    timezone_name: str = Query("UTC", alias="timezone"),
    db: Session = Depends(get_db),
):
    try:
        parsed_start_date = parse_transaction_boundary(start_date, timezone_name, end_of_day=False)
        parsed_end_date = parse_transaction_boundary(end_date, timezone_name, end_of_day=True)
    except (InvalidCalendarTimezone, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    service = TransactionService(db)
    items, total = service.list(
        start_date=parsed_start_date,
        end_date=parsed_end_date,
        type_filter=type,
        category_id=category_id,
        search=search,
        page=page,
        page_size=page_size,
    )
    # Attach category_name from the relationship
    for item in items:
        item.category_name = item.category.name if item.category else None
    return TransactionListResponse(items=items, total=total, page=page, page_size=page_size)


@router.post("", status_code=status.HTTP_201_CREATED, response_model=TransactionRead)
def create_transaction(payload: TransactionCreate, db: Session = Depends(get_db)):
    service = TransactionService(db)
    tx = service.create(payload)
    tx.category_name = tx.category.name if tx.category else None
    return tx


@router.get("/{transaction_id}", response_model=TransactionRead)
def get_transaction(transaction_id: int, db: Session = Depends(get_db)):
    service = TransactionService(db)
    tx = service.get(transaction_id)
    tx.category_name = tx.category.name if tx.category else None
    return tx


@router.put("/{transaction_id}", response_model=TransactionRead)
def update_transaction(transaction_id: int, payload: TransactionUpdate, db: Session = Depends(get_db)):
    service = TransactionService(db)
    tx = service.update(transaction_id, payload)
    tx.category_name = tx.category.name if tx.category else None
    return tx


@router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_transaction(transaction_id: int, db: Session = Depends(get_db)):
    service = TransactionService(db)
    service.delete(transaction_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
