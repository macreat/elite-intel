from datetime import datetime
from decimal import Decimal
from typing import Literal

from sqlalchemy.orm import Session

from app.models.enums import TransactionType
from app.repositories.transaction_repository import TransactionRepository

TimeseriesGranularity = Literal["day", "week", "month"]


class DashboardService:
    def __init__(self, db: Session):
        self.repo = TransactionRepository(db)

    def summary(self, *, start_date: datetime, end_date: datetime):
        return self.repo.dashboard_summary(start_date=start_date, end_date=end_date)

    def categories(self, *, start_date: datetime, end_date: datetime, type_filter: TransactionType | None):
        rows = self.repo.dashboard_categories(start_date=start_date, end_date=end_date, type_filter=type_filter)
        total = sum([row[2] for row in rows], start=Decimal("0"))
        items = []
        for category_id, category_name, amount in rows:
            pct = float(amount / total) if total else 0.0
            items.append(
                {
                    "category_id": int(category_id),
                    "category_name": category_name,
                    "total": amount,
                    "percentage": pct,
                }
            )
        return items

    def timeseries(
        self,
        *,
        start_date: datetime,
        end_date: datetime,
        timezone_name: str = "UTC",
        granularity: TimeseriesGranularity = "day",
    ):
        rows = self.repo.dashboard_timeseries(
            start_date=start_date,
            end_date=end_date,
            timezone_name=timezone_name,
            granularity=granularity,
        )
        return [{"date": row[0], "income": row[1], "expenses": row[2]} for row in rows]
