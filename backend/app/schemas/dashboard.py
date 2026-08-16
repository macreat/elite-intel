from datetime import date
from decimal import Decimal

from pydantic import BaseModel


class DashboardPeriod(BaseModel):
    start_date: date
    end_date: date


class DashboardSummary(BaseModel):
    total_income: Decimal
    total_expenses: Decimal
    net_balance: Decimal
    estimated_savings: Decimal
    savings_rate: float
    transaction_count: int
    period: DashboardPeriod


class CategoryBreakdown(BaseModel):
    category_id: int
    category_name: str
    total: Decimal
    percentage: float


class TimeseriesPoint(BaseModel):
    date: date
    income: Decimal
    expenses: Decimal
