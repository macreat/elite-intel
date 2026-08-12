from datetime import date, datetime, time

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.enums import TransactionType
from app.schemas.dashboard import CategoryBreakdown, DashboardSummary, TimeseriesPoint
from app.services.dashboard_service import DashboardService

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


def _range(start_date: date, end_date: date):
    return datetime.combine(start_date, time.min), datetime.combine(end_date, time.max)


@router.get("/summary", response_model=DashboardSummary)
def get_summary(start_date: date, end_date: date, db: Session = Depends(get_db)):
    start, end = _range(start_date, end_date)
    service = DashboardService(db)
    data = service.summary(start_date=start, end_date=end)
    data["period"] = {"start_date": start_date, "end_date": end_date}
    return data


@router.get("/categories", response_model=list[CategoryBreakdown])
def get_categories(start_date: date, end_date: date, type: TransactionType | None = None, db: Session = Depends(get_db)):
    start, end = _range(start_date, end_date)
    service = DashboardService(db)
    return service.categories(start_date=start, end_date=end, type_filter=type)


@router.get("/timeseries", response_model=list[TimeseriesPoint])
def get_timeseries(start_date: date, end_date: date, granularity: str | None = None, db: Session = Depends(get_db)):
    del granularity
    start, end = _range(start_date, end_date)
    service = DashboardService(db)
    return service.timeseries(start_date=start, end_date=end)
