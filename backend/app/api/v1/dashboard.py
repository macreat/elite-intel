from datetime import date
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.enums import TransactionType
from app.schemas.dashboard import CategoryBreakdown, DashboardSummary, TimeseriesPoint
from app.services.calendar import InvalidCalendarTimezone, local_calendar_range
from app.services.dashboard_service import DashboardService

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


def _range(start_date: date, end_date: date, timezone_name: str):
    try:
        return local_calendar_range(start_date, end_date, timezone_name)
    except InvalidCalendarTimezone as exc:
        raise HTTPException(status_code=422, detail=f"invalid timezone: {timezone_name}") from exc


@router.get("/summary", response_model=DashboardSummary)
def get_summary(
    start_date: date,
    end_date: date,
    timezone_name: str = Query("UTC", alias="timezone"),
    db: Session = Depends(get_db),
):
    start, end = _range(start_date, end_date, timezone_name)
    service = DashboardService(db)
    data = service.summary(start_date=start, end_date=end)
    data["period"] = {"start_date": start_date, "end_date": end_date}
    return data


@router.get("/categories", response_model=list[CategoryBreakdown])
def get_categories(
    start_date: date,
    end_date: date,
    type: TransactionType | None = None,
    timezone_name: str = Query("UTC", alias="timezone"),
    db: Session = Depends(get_db),
):
    start, end = _range(start_date, end_date, timezone_name)
    service = DashboardService(db)
    return service.categories(start_date=start, end_date=end, type_filter=type)


@router.get("/timeseries", response_model=list[TimeseriesPoint])
def get_timeseries(
    start_date: date,
    end_date: date,
    granularity: Literal["day", "week", "month"] = "day",
    timezone_name: str = Query("UTC", alias="timezone"),
    db: Session = Depends(get_db),
):
    start, end = _range(start_date, end_date, timezone_name)
    service = DashboardService(db)
    return service.timeseries(
        start_date=start,
        end_date=end,
        timezone_name=timezone_name,
        granularity=granularity,
    )
