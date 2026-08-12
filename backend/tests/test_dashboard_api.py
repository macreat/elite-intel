from datetime import datetime, timezone


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
    assert data["estimated_savings"] == "1100.00"
    assert round(data["savings_rate"], 6) == round(1100 / 1300, 6)
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
    assert data["estimated_savings"] == "0"
    assert data["savings_rate"] == 0
