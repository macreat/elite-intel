"""Tests for Accesorios 40% profit and BeMovilRemote / BeMovileIncome semantics."""

from datetime import datetime, timezone
from decimal import Decimal

from app.services.business_rules import (
    BEMOVIL_REMOTE_CATEGORY,
    BEMOVILE_INCOME_CATEGORY,
    resolve_accesorios_amount,
)
from app.services.import_service import ImportService


def _seed_category(client, *, name: str, type_value: str = "INCOME"):
    res = client.post("/api/v1/categories", json={"name": name, "type": type_value})
    assert res.status_code == 201
    return res.json()


def test_resolve_accesorios_amount_applies_forty_percent_profit():
    profit, notes = resolve_accesorios_amount("Accesorios", Decimal("190000"), None)
    assert profit == Decimal("76000.00")
    assert notes == "accesorios_gross=190000.00"


def test_resolve_accesorios_amount_is_idempotent_when_already_converted():
    first, notes = resolve_accesorios_amount("Accesorios", Decimal("190000"), None)
    second, notes2 = resolve_accesorios_amount("Accesorios", first, notes)
    assert second == first == Decimal("76000.00")
    assert notes2 == notes


def test_manual_accesorios_transaction_stores_forty_percent_profit(client):
    cat = _seed_category(client, name="Accesorios")
    created = client.post(
        "/api/v1/transactions",
        json={
            "occurred_at": datetime(2026, 8, 15, 12, 0, tzinfo=timezone.utc).isoformat(),
            "transaction_type": "INCOME",
            "category_id": cat["id"],
            "description": "Accesorios sale",
            "amount": "190000.00",
        },
    )
    assert created.status_code == 201
    body = created.json()
    assert body["amount"] == "76000.00"
    assert "accesorios_gross=190000.00" in (body.get("notes") or "")

    summary = client.get("/api/v1/dashboard/summary?start_date=2026-08-01&end_date=2026-08-31")
    assert summary.status_code == 200
    assert summary.json()["total_income"] == "76000.00"
    assert summary.json()["net_balance"] == "76000.00"


def test_import_accesorios_csv_applies_forty_percent(client):
    _seed_category(client, name="Accesorios")
    content = (
        "Fecha,Tipo,Categoría,Descripción,Valor\n"
        "15/08/2026,INCOME,Accesorios,gross accessories,190000\n"
    ).encode("utf-8")
    upload = client.post(
        "/api/v1/imports/transactions",
        files={"file": ("accesorios.csv", content, "text/csv")},
    )
    assert upload.status_code == 201
    batch_id = upload.json()["batch_id"]
    mapping = client.post(
        f"/api/v1/imports/{batch_id}/mapping",
        json={
            "mapping": {
                "occurred_at": "Fecha",
                "transaction_type": "Tipo",
                "category": "Categoría",
                "description": "Descripción",
                "amount": "Valor",
            }
        },
    )
    assert mapping.status_code == 200
    preview = mapping.json()["preview"]
    assert preview[0]["amount"] == "76000.00"

    confirm = client.post(f"/api/v1/imports/{batch_id}/confirm")
    assert confirm.status_code == 200

    summary = client.get("/api/v1/dashboard/summary?start_date=2026-08-01&end_date=2026-08-31")
    assert summary.json()["total_income"] == "76000.00"


def test_bemovil_remote_does_not_inflate_income_kpis(client):
    remote = _seed_category(client, name=BEMOVIL_REMOTE_CATEGORY)
    income = _seed_category(client, name="Fotocopias")
    manual = _seed_category(client, name=BEMOVILE_INCOME_CATEGORY)

    for cat, amount in (
        (remote, "50000.00"),
        (income, "1300.00"),
        (manual, "2000.00"),
    ):
        res = client.post(
            "/api/v1/transactions",
            json={
                "occurred_at": datetime(2026, 8, 10, 12, 0, tzinfo=timezone.utc).isoformat(),
                "transaction_type": "INCOME",
                "category_id": cat["id"],
                "description": f"{cat['name']} entry",
                "amount": amount,
            },
        )
        assert res.status_code == 201

    summary = client.get("/api/v1/dashboard/summary?start_date=2026-08-01&end_date=2026-08-31")
    assert summary.status_code == 200
    data = summary.json()
    # BeMovilRemote excluded; Fotocopias + BeMovileIncome count
    assert data["total_income"] == "3300.00"
    assert data["net_balance"] == "3300.00"
    assert data["transaction_count"] == 3

    categories = client.get(
        "/api/v1/dashboard/categories?start_date=2026-08-01&end_date=2026-08-31&type=INCOME"
    ).json()
    names = {row["category_name"] for row in categories}
    assert BEMOVIL_REMOTE_CATEGORY not in names
    assert "Fotocopias" in names
    assert BEMOVILE_INCOME_CATEGORY in names

    timeseries = client.get(
        "/api/v1/dashboard/timeseries?start_date=2026-08-01&end_date=2026-08-31"
    ).json()
    total_income = sum(Decimal(point["income"]) for point in timeseries)
    assert total_income == Decimal("3300.00")


def test_kardex_be_movil_column_maps_to_bemovil_remote_not_bemovile_income(db_session):
    service = ImportService(db_session)
    entries = service._read_kardex_rows(
        [
            ["08/01/2026", "", "", "", ""],
            ["Ahorro mensual", "Be Movil 700", "Fotocopias", "Total"],
            ["1000", "9900", "1500", "12400"],
        ]
    )
    by_cat = {e["Categoría"]: e for e in entries}
    assert "BeMovilRemote" in by_cat
    assert by_cat["BeMovilRemote"]["Valor"] == "9900.00"
    assert all(e["Categoría"] != BEMOVILE_INCOME_CATEGORY for e in entries)
