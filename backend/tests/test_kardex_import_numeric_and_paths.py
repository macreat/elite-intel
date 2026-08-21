import csv
from decimal import Decimal
from pathlib import Path

import pytest

from app.services.import_service import _normalize_path
from app.core.config import settings


def _csv_bytes(rows):
    import io

    stream = io.StringIO()
    writer = csv.DictWriter(stream, fieldnames=["Fecha", "Tipo", "Categoría", "Descripción", "Valor"])
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode("utf-8")


BASE_ROW = {
    "Fecha": "12/08/2026",
    "Tipo": "ingreso",
    "Categoría": "Impresiones",
    "Descripción": "Test",
    "Valor": "250000",
}


def test_parse_plain_digits_via_import_api(client):
    # create category expected by the import
    client.post("/api/v1/categories", json={"name": "Impresiones", "type": "INCOME"})

    content = _csv_bytes([BASE_ROW])
    upload = client.post(
        "/api/v1/imports/transactions",
        files={"file": ("plain_digits.csv", content, "text/csv")},
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
    assert preview[0]["amount"] == "250000.00"


def test_normalize_wsl_unc_path_does_not_crash():
    # A WSL UNC-style path should be normalized or raise a clear ValueError for unsupported UNC
    sample = r"\\wsl.localhost\\Ubuntu\\home\\lnxmacreat\\wsp\\projects\\eliteSystem\\repository\\elite-intel\\backend\\data\\kardex_august.csv"
    p = _normalize_path(sample)
    assert isinstance(p, Path)
    # It should reference the filename
    assert p.name == "kardex_august.csv"


def test_end_to_end_import_and_running_balance(client, monkeypatch, tmp_path):
    # Use real data file and assert computed running balance persists to CSV ledger
    # Ensure ledger is written to a temp file
    monkeypatch.setattr(settings, "PERSIST_TRANSACTIONS_CSV", tmp_path / "ledger.csv")

    # Seed a minimal category to satisfy mapping lookup when possible
    client.post("/api/v1/categories", json={"name": "Impresiones", "type": "INCOME"})

    # Create a tiny CSV with two rows to verify running balance computation deterministically
    rows = [
        {"Fecha": "01/01/2026", "Tipo": "ingreso", "Categoría": "Impresiones", "Descripción": "Seed A", "Valor": "1000"},
        {"Fecha": "02/01/2026", "Tipo": "egreso", "Categoría": "Impresiones", "Descripción": "Seed B", "Valor": "400"},
    ]
    from io import StringIO

    stream = StringIO()
    writer = csv.DictWriter(stream, fieldnames=["Fecha", "Tipo", "Categoría", "Descripción", "Valor"])
    writer.writeheader()
    writer.writerows(rows)
    content = stream.getvalue().encode("utf-8")

    upload = client.post(
        "/api/v1/imports/transactions",
        files={"file": ("tiny.csv", content, "text/csv")},
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

    confirm = client.post(f"/api/v1/imports/{batch_id}/confirm")
    assert confirm.status_code == 200

    # Expected final balance: 1000 - 400 = 600
    expected_final = Decimal("600.00")

    # Check ledger CSV last RunningBalance
    ledger = tmp_path / "ledger.csv"
    assert ledger.exists()
    last = None
    with ledger.open("r", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        for last in reader:
            pass
    assert last is not None
    assert "RunningBalance" in reader.fieldnames
    final = Decimal(last.get("RunningBalance") or "0").quantize(Decimal("0.01"))
    assert final == expected_final
