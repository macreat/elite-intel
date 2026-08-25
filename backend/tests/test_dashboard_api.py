from datetime import datetime, timezone

import pytest


def _cat(client, name: str, t: str):
    r = client.post("/api/v1/categories", json={"name": name, "type": t})
    assert r.status_code == 201
    return r.json()


def _tx(client, category_id: int, t: str, amount: str, occurred_at: str):
    r = client.post(
        "/api/v1/transactions",
        json={
            "occurred_at": occurred_at,
            "transaction_type": t,
            "category_id": category_id,
            "description": f"{t}-{amount}",
            "amount": amount,
        },
    )
    assert r.status_code == 201


def test_dashboard_math_and_savings_floor(client):
    income = _cat(client, "IncomeCat", "INCOME")
    expense = _cat(client, "ExpenseCat", "EXPENSE")

    _tx(client, income["id"], "INCOME", "1000.00", datetime(2026, 8, 1, tzinfo=timezone.utc).isoformat())
    _tx(client, income["id"], "INCOME", "300.00", datetime(2026, 8, 2, tzinfo=timezone.utc).isoformat())
    _tx(client, expense["id"], "EXPENSE", "200.00", datetime(2026, 8, 2, tzinfo=timezone.utc).isoformat())

    summary = client.get("/api/v1/dashboard/summary?start_date=2026-08-01&end_date=2026-08-31")
    assert summary.status_code == 200
    data = summary.json()
    assert data["total_income"] == "1300.00"
    assert data["total_expenses"] == "200.00"
    assert data["net_balance"] == "1100.00"
    # No savings-category transactions present -> estimated savings stays zero.
    assert data["estimated_savings"] == "0.00" or data["estimated_savings"] == 0
    assert data["savings_rate"] == 0
    assert data["transaction_count"] == 3

    cat_breakdown = client.get("/api/v1/dashboard/categories?start_date=2026-08-01&end_date=2026-08-31")
    assert cat_breakdown.status_code == 200
    assert len(cat_breakdown.json()) >= 2

    ts = client.get("/api/v1/dashboard/timeseries?start_date=2026-08-01&end_date=2026-08-31")
    assert ts.status_code == 200
    assert len(ts.json()) >= 2


def test_dashboard_zero_income_savings_rate_zero(client):
    expense = _cat(client, "OnlyExpense", "EXPENSE")
    _tx(client, expense["id"], "EXPENSE", "50.00", datetime(2026, 8, 2, tzinfo=timezone.utc).isoformat())

    summary = client.get("/api/v1/dashboard/summary?start_date=2026-08-01&end_date=2026-08-31")
    assert summary.status_code == 200
    data = summary.json()
    assert data["total_income"] == "0.00"
    assert data["total_expenses"] == "50.00"
    assert data["net_balance"] == "-50.00"
    assert data["estimated_savings"] == "0.00"
    assert data["savings_rate"] == 0


def test_dashboard_uses_utc_calendar_boundaries_for_offset_transactions(client):
    income = _cat(client, "OffsetIncome", "INCOME")
    _tx(client, income["id"], "INCOME", "75.00", "2026-08-20T23:30:00-04:00")

    previous_day = client.get("/api/v1/dashboard/summary?start_date=2026-08-20&end_date=2026-08-20")
    next_day = client.get("/api/v1/dashboard/summary?start_date=2026-08-21&end_date=2026-08-21")

    assert previous_day.status_code == 200
    assert previous_day.json()["transaction_count"] == 0
    assert next_day.status_code == 200
    assert next_day.json()["transaction_count"] == 1

    previous_transactions = client.get(
        "/api/v1/transactions?start_date=2026-08-20T00:00:00.000Z&end_date=2026-08-20T23:59:59.999Z"
    )
    next_transactions = client.get(
        "/api/v1/transactions?start_date=2026-08-21T00:00:00.000Z&end_date=2026-08-21T23:59:59.999Z"
    )
    assert previous_transactions.status_code == 200
    assert previous_transactions.json()["total"] == 0
    assert next_transactions.status_code == 200
    assert next_transactions.json()["total"] == 1


def test_selected_local_calendar_dates_include_offset_transactions_for_dashboard_and_list(client):
    new_york_income = _cat(client, "New York Income", "INCOME")
    tokyo_income = _cat(client, "Tokyo Income", "INCOME")
    _tx(client, new_york_income["id"], "INCOME", "75.00", "2026-08-20T23:30:00-04:00")
    _tx(client, tokyo_income["id"], "INCOME", "125.00", "2026-08-20T00:30:00+09:00")

    new_york_query = (
        "start_date=2026-08-20&end_date=2026-08-20&timezone=America/New_York"
    )
    new_york_summary = client.get(f"/api/v1/dashboard/summary?{new_york_query}")
    new_york_transactions = client.get(f"/api/v1/transactions?{new_york_query}")
    assert new_york_summary.status_code == 200
    assert new_york_summary.json()["transaction_count"] == 1
    assert new_york_summary.json()["total_income"] == "75.00"
    assert new_york_transactions.status_code == 200
    assert new_york_transactions.json()["total"] == 1

    tokyo_query = "start_date=2026-08-20&end_date=2026-08-20&timezone=Asia/Tokyo"
    tokyo_summary = client.get(f"/api/v1/dashboard/summary?{tokyo_query}")
    tokyo_transactions = client.get(f"/api/v1/transactions?{tokyo_query}")
    assert tokyo_summary.status_code == 200
    assert tokyo_summary.json()["transaction_count"] == 1
    assert tokyo_summary.json()["total_income"] == "125.00"
    assert tokyo_transactions.status_code == 200
    assert tokyo_transactions.json()["total"] == 1


def test_dashboard_timeseries_uses_requested_timezone_calendar_buckets(client):
    new_york_income = _cat(client, "Timeseries New York Income", "INCOME")
    tokyo_income = _cat(client, "Timeseries Tokyo Income", "INCOME")
    _tx(client, new_york_income["id"], "INCOME", "75.00", "2026-08-20T23:30:00-04:00")
    _tx(client, tokyo_income["id"], "INCOME", "125.00", "2026-08-20T00:30:00+09:00")

    new_york = client.get(
        "/api/v1/dashboard/timeseries?start_date=2026-08-20&end_date=2026-08-20&timezone=America/New_York"
    )
    tokyo = client.get(
        "/api/v1/dashboard/timeseries?start_date=2026-08-20&end_date=2026-08-20&timezone=Asia/Tokyo"
    )

    assert new_york.status_code == 200
    assert new_york.json() == [{"date": "2026-08-20", "income": "75.00", "expenses": "0.00"}]
    assert tokyo.status_code == 200
    assert tokyo.json() == [{"date": "2026-08-20", "income": "125.00", "expenses": "0.00"}]


@pytest.mark.parametrize(
    ("granularity", "start_date", "end_date", "occurred_at", "expected_date"),
    [
        ("day", "2026-08-20", "2026-08-20", "2026-08-20T23:30:00-04:00", "2026-08-20"),
        ("week", "2026-08-17", "2026-08-23", "2026-08-20T23:30:00-04:00", "2026-08-17"),
        ("month", "2026-08-01", "2026-08-31", "2026-08-20T23:30:00-04:00", "2026-08-01"),
    ],
)
def test_dashboard_timeseries_honors_requested_granularity_and_timezone(
    client, granularity, start_date, end_date, occurred_at, expected_date
):
    income = _cat(client, f"Granularity {granularity}", "INCOME")
    _tx(client, income["id"], "INCOME", "75.00", occurred_at)

    response = client.get(
        "/api/v1/dashboard/timeseries",
        params={
            "start_date": start_date,
            "end_date": end_date,
            "granularity": granularity,
            "timezone": "America/New_York",
        },
    )

    assert response.status_code == 200
    assert response.json() == [{"date": expected_date, "income": "75.00", "expenses": "0.00"}]


def test_estimated_savings_sums_savings_categories(client):
    """Estimated savings = sum of INCOME transactions in savings categories (e.g. Ahorro mensual)."""
    ahorro = _cat(client, "Ahorro mensual", "INCOME")
    other_income = _cat(client, "Impresiones", "INCOME")
    expense = _cat(client, "Salidas", "EXPENSE")

    # Savings built up across days: 400k + 200k + 50k pattern, scaled down.
    _tx(client, ahorro["id"], "INCOME", "400.00", datetime(2026, 8, 1, tzinfo=timezone.utc).isoformat())
    _tx(client, ahorro["id"], "INCOME", "200.00", datetime(2026, 8, 18, tzinfo=timezone.utc).isoformat())
    _tx(client, ahorro["id"], "INCOME", "50.00", datetime(2026, 8, 19, tzinfo=timezone.utc).isoformat())
    _tx(client, other_income["id"], "INCOME", "1371.90", datetime(2026, 8, 5, tzinfo=timezone.utc).isoformat())
    _tx(client, expense["id"], "EXPENSE", "3425.00", datetime(2026, 8, 6, tzinfo=timezone.utc).isoformat())

    summary = client.get("/api/v1/dashboard/summary?start_date=2026-08-01&end_date=2026-08-31")
    assert summary.status_code == 200
    data = summary.json()
    assert data["estimated_savings"] == "650.00"
    assert round(data["savings_rate"], 6) == round(650 / 2021.9, 6)
    assert data["total_income"] == "2021.90"
