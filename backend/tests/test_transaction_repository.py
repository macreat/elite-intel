from datetime import datetime, timezone
from decimal import Decimal

import pytest

from app.models.category import Category
from app.models.enums import TransactionType
from app.models.transaction import Transaction
from app.repositories.transaction_repository import TransactionRepository


@pytest.mark.parametrize(
    ("granularity", "expected_bucket"),
    [("day", "2026-08-20"), ("week", "2026-08-17"), ("month", "2026-08-01")],
)
def test_repository_timeseries_uses_requested_granularity_and_local_bucket_label(
    db_session, granularity, expected_bucket
):
    category = Category(name=f"Repository {granularity}", type=TransactionType.INCOME)
    db_session.add(category)
    db_session.flush()
    db_session.add(
        Transaction(
            occurred_at=datetime(2026, 8, 21, 3, 30, tzinfo=timezone.utc),
            transaction_type=TransactionType.INCOME,
            category_id=category.id,
            description="Timezone-aware bucket",
            amount=Decimal("75.00"),
            currency_code="USD",
        )
    )
    db_session.commit()

    rows = TransactionRepository(db_session).dashboard_timeseries(
        start_date=datetime(2026, 8, 1, tzinfo=timezone.utc),
        end_date=datetime(2026, 8, 31, 23, 59, 59, tzinfo=timezone.utc),
        timezone_name="America/New_York",
        granularity=granularity,
    )

    assert rows == [(expected_bucket, Decimal("75.00"), Decimal("0.00"))]
