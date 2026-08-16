import csv
import io
from pathlib import Path

import pytest

from app.core.config import settings
from app.models.import_batch import ImportBatch
from app.schemas.import_data import ImportMappingRequest
from app.services.import_service import ImportService


def _seed_categories(client):
    inc = client.post("/api/v1/categories", json={"name": "Impresiones", "type": "INCOME"})
    exp = client.post("/api/v1/categories", json={"name": "Servicios públicos", "type": "EXPENSE"})
    assert inc.status_code == 201
    assert exp.status_code == 201


def _csv_bytes(rows):
    stream = io.StringIO()
    writer = csv.DictWriter(stream, fieldnames=["Fecha", "Tipo", "Categoría", "Descripción", "Valor"])
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode("utf-8")


BASE_IMPORT_ROW = {
    "Fecha": "12/08/2026",
    "Tipo": "ingreso",
    "Categoría": "Impresiones",
    "Descripción": "20 color pages",
    "Valor": "12000",
}


def _import_row(**overrides):
    row = dict(BASE_IMPORT_ROW)
    row.update(overrides)
    return row


def _upload_transactions_file(client, filename="sample.csv", content_type="text/csv", rows=None):
    payload = _csv_bytes(rows or [_import_row()])
    return client.post(
        "/api/v1/imports/transactions",
        files={"file": (filename, payload, content_type)},
    )


def test_import_rejects_non_csv_upload_with_csv_only_message(client):
    _seed_categories(client)

    upload = _upload_transactions_file(
        client,
        filename="sample.xlsx",
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

    assert upload.status_code == 400
    body = upload.json()
    assert body["error_code"] == "VALIDATION_ERROR"
    assert "csv" in body["message"].lower()


def test_import_rejects_csv_extension_with_non_csv_content_type(client):
    _seed_categories(client)

    upload = _upload_transactions_file(client, content_type="application/json")

    assert upload.status_code == 400
    body = upload.json()
    assert body["error_code"] == "VALIDATION_ERROR"
    assert "csv" in body["message"].lower()


def test_import_accepts_csv_upload_under_csv_only_contract(client):
    _seed_categories(client)

    upload = _upload_transactions_file(client)

    assert upload.status_code == 201
    batch_id = upload.json()["batch_id"]

    detail = client.get(f"/api/v1/imports/{batch_id}")
    assert detail.status_code == 200
    assert detail.json()["source_type"] == "CSV"


def test_import_accepts_csv_upload_with_uppercase_extension(client):
    _seed_categories(client)

    upload = _upload_transactions_file(client, filename="SAMPLE.CSV")

    assert upload.status_code == 201
    batch_id = upload.json()["batch_id"]

    detail = client.get(f"/api/v1/imports/{batch_id}")
    assert detail.status_code == 200
    assert detail.json()["source_type"] == "CSV"


@pytest.mark.parametrize("content_type", ["application/vnd.ms-excel", "text/plain"])
def test_import_accepts_csv_upload_with_supported_csv_content_types(client, content_type):
    _seed_categories(client)

    upload = _upload_transactions_file(client, content_type=content_type)

    assert upload.status_code == 201
    batch_id = upload.json()["batch_id"]

    detail = client.get(f"/api/v1/imports/{batch_id}")
    assert detail.status_code == 200
    assert detail.json()["source_type"] == "CSV"


def test_import_validation_and_all_or_nothing_confirm(client):
    _seed_categories(client)

    content = _csv_bytes(
        [
            {
                "Fecha": "12/08/2026",
                "Tipo": "ingreso",
                "Categoría": "Impresiones",
                "Descripción": "20 color pages",
                "Valor": "12000",
            },
            {
                "Fecha": "13/08/2026",
                "Tipo": "egreso",
                "Categoría": "Servicios públicos",
                "Descripción": "Power bill",
                "Valor": "-500",
            },
        ]
    )

    upload = client.post(
        "/api/v1/imports/transactions",
        files={"file": ("sample.csv", content, "text/csv")},
    )
    assert upload.status_code == 201
    payload = upload.json()
    batch_id = payload["batch_id"]

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
    mapped = mapping.json()
    assert mapped["status"] == "VALIDATED"
    assert mapped["summary"]["records_total"] == 2
    assert mapped["summary"]["records_valid"] == 1
    assert mapped["summary"]["records_invalid"] == 1
    assert mapped["invalid_rows"][0]["error_code"] in {"NON_POSITIVE_AMOUNT", "INVALID_AMOUNT"}

    before = client.get("/api/v1/transactions")
    assert before.status_code == 200
    assert before.json()["total"] == 0

    confirm = client.post(f"/api/v1/imports/{batch_id}/confirm")
    assert confirm.status_code == 200
    assert confirm.json()["records_inserted"] == 1
    assert confirm.json()["status"] == "CONFIRMED"

    after = client.get("/api/v1/transactions")
    assert after.status_code == 200
    assert after.json()["total"] == 1


def test_import_does_not_mutate_source_bytes(client):
    _seed_categories(client)
    content = _csv_bytes([_import_row(Descripción="A", Valor="100")])

    upload = client.post(
        "/api/v1/imports/transactions",
        files={"file": ("bytes.csv", content, "text/csv")},
    )
    assert upload.status_code == 201
    batch_id = upload.json()["batch_id"]

    detail = client.get(f"/api/v1/imports/{batch_id}")
    assert detail.status_code == 200

    remap = client.post(
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
    assert remap.status_code == 200

    # same content must be treated as duplicate file hash if reuploaded
    second = client.post(
        "/api/v1/imports/transactions",
        files={"file": ("bytes.csv", content, "text/csv")},
    )
    assert second.status_code == 400


def test_import_mapping_accepts_occurred_at_when_date_detection_is_absent(client):
    _seed_categories(client)
    stream = io.StringIO()
    writer = csv.DictWriter(stream, fieldnames=["When occurred", "Tipo", "Categoría", "Descripción", "Valor"])
    writer.writeheader()
    writer.writerow(
        {
            "When occurred": "12/08/2026",
            "Tipo": "ingreso",
            "Categoría": "Impresiones",
            "Descripción": "Custom date mapping",
            "Valor": "12000",
        }
    )

    upload = client.post(
        "/api/v1/imports/transactions",
        files={"file": ("custom-date.csv", stream.getvalue().encode("utf-8"), "text/csv")},
    )
    assert upload.status_code == 201
    uploaded = upload.json()
    assert "occurred_at" not in uploaded["suggested_mapping"]

    mapping = client.post(
        f"/api/v1/imports/{uploaded['batch_id']}/mapping",
        json={
            "mapping": {
                "occurred_at": "When occurred",
                "transaction_type": "Tipo",
                "category": "Categoría",
                "description": "Descripción",
                "amount": "Valor",
            }
        },
    )

    assert mapping.status_code == 200
    assert mapping.json()["preview"][0]["description"] == "Custom date mapping"


def test_import_parses_argentine_thousands_amount_using_configured_locale(client):
    _seed_categories(client)

    upload = _upload_transactions_file(client, rows=[_import_row(Valor="1.234")])
    assert upload.status_code == 201

    mapping = client.post(
        f"/api/v1/imports/{upload.json()['batch_id']}/mapping",
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
    assert mapping.json()["preview"][0]["amount"] == "1234.00"


def test_import_keeps_argentine_decimal_amount_value(client):
    _seed_categories(client)

    upload = _upload_transactions_file(client, rows=[_import_row(Valor="1234.56")])
    assert upload.status_code == 201

    mapping = client.post(
        f"/api/v1/imports/{upload.json()['batch_id']}/mapping",
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
    assert mapping.json()["preview"][0]["amount"] == "1234.56"


def test_import_rejects_malformed_amount_instead_of_stripping_text(client):
    _seed_categories(client)

    upload = _upload_transactions_file(client, rows=[_import_row(Valor="12abc34")])
    assert upload.status_code == 201

    mapping = client.post(
        f"/api/v1/imports/{upload.json()['batch_id']}/mapping",
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
    assert mapping.json()["summary"]["records_invalid"] == 1
    assert mapping.json()["invalid_rows"][0]["error_code"] == "INVALID_AMOUNT"


def test_import_parses_us_thousands_amount_using_configured_locale(client, monkeypatch):
    from app.core.config import settings

    _seed_categories(client)
    monkeypatch.setattr(settings, "IMPORT_DEFAULT_LOCALE", "en_US")

    upload = _upload_transactions_file(client, rows=[_import_row(Valor="1,234")])
    assert upload.status_code == 201

    mapping = client.post(
        f"/api/v1/imports/{upload.json()['batch_id']}/mapping",
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
    assert mapping.json()["preview"][0]["amount"] == "1234.00"


def test_import_confirmation_rejects_cross_batch_duplicate_atomically(client):
    _seed_categories(client)
    first = _upload_transactions_file(client, filename="first.csv", rows=[_import_row(Descripción="Same record")])
    second = _upload_transactions_file(
        client,
        filename="second.csv",
        rows=[_import_row(Descripción="Must roll back"), _import_row(Descripción=" Same record ")],
    )
    assert first.status_code == 201
    assert second.status_code == 201

    mapping_payload = {
        "mapping": {
            "occurred_at": "Fecha",
            "transaction_type": "Tipo",
            "category": "Categoría",
            "description": "Descripción",
            "amount": "Valor",
        }
    }
    first_mapping = client.post(f"/api/v1/imports/{first.json()['batch_id']}/mapping", json=mapping_payload)
    second_mapping = client.post(f"/api/v1/imports/{second.json()['batch_id']}/mapping", json=mapping_payload)
    assert first_mapping.status_code == 200
    assert second_mapping.status_code == 200
    assert second_mapping.json()["summary"]["records_valid"] == 2

    first_confirm = client.post(f"/api/v1/imports/{first.json()['batch_id']}/confirm")
    assert first_confirm.status_code == 200
    assert first_confirm.json()["records_inserted"] == 1

    second_confirm = client.post(f"/api/v1/imports/{second.json()['batch_id']}/confirm")
    assert second_confirm.status_code == 400
    assert second_confirm.json()["error_code"] == "IMPORT_STATE_ERROR"

    transactions = client.get("/api/v1/transactions")
    assert transactions.status_code == 200
    assert transactions.json()["total"] == 1


def test_import_fingerprint_normalizes_equivalent_timezone_offsets(client):
    _seed_categories(client)
    first = _upload_transactions_file(
        client,
        filename="offset-first.csv",
        rows=[_import_row(Fecha="2026-08-20T23:30:00-04:00", Descripción="Equivalent instant")],
    )
    second = _upload_transactions_file(
        client,
        filename="offset-second.csv",
        rows=[_import_row(Fecha="2026-08-21T03:30:00+00:00", Descripción="Equivalent instant")],
    )
    assert first.status_code == 201
    assert second.status_code == 201

    mapping_payload = {
        "mapping": {
            "occurred_at": "Fecha",
            "transaction_type": "Tipo",
            "category": "Categoría",
            "description": "Descripción",
            "amount": "Valor",
        }
    }
    first_mapping = client.post(f"/api/v1/imports/{first.json()['batch_id']}/mapping", json=mapping_payload)
    second_mapping = client.post(f"/api/v1/imports/{second.json()['batch_id']}/mapping", json=mapping_payload)
    assert first_mapping.status_code == 200
    assert second_mapping.status_code == 200

    first_confirm = client.post(f"/api/v1/imports/{first.json()['batch_id']}/confirm")
    assert first_confirm.status_code == 200
    assert first_confirm.json()["records_inserted"] == 1

    second_remap = client.post(f"/api/v1/imports/{second.json()['batch_id']}/mapping", json=mapping_payload)
    assert second_remap.status_code == 200
    assert second_remap.json()["summary"]["records_valid"] == 0
    assert second_remap.json()["summary"]["records_duplicate"] == 1

    second_confirm = client.post(f"/api/v1/imports/{second.json()['batch_id']}/confirm")
    assert second_confirm.status_code == 200
    assert second_confirm.json()["records_inserted"] == 0

    transactions = client.get("/api/v1/transactions")
    assert transactions.status_code == 200
    assert transactions.json()["total"] == 1


@pytest.mark.parametrize(
    ("business_timezone", "expected_utc"),
    [
        ("America/New_York", "2026-08-12T04:00:00Z"),
        ("Asia/Tokyo", "2026-08-11T15:00:00Z"),
    ],
)
def test_import_date_only_values_use_configured_business_timezone(client, monkeypatch, business_timezone, expected_utc):
    _seed_categories(client)
    monkeypatch.setattr(settings, "IMPORT_DEFAULT_TIMEZONE", business_timezone)

    upload = _upload_transactions_file(client, rows=[_import_row(Fecha="12/08/2026")])
    assert upload.status_code == 201

    mapping = client.post(
        f"/api/v1/imports/{upload.json()['batch_id']}/mapping",
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
    assert mapping.json()["preview"][0]["occurred_at"] == expected_utc


def test_import_preserves_repeated_rows_in_one_source_and_replays_safely(client):
    _seed_categories(client)
    content = _csv_bytes([_import_row(Descripción="Repeated legitimate row"), _import_row(Descripción="Repeated legitimate row")])

    upload = client.post(
        "/api/v1/imports/transactions",
        files={"file": ("repeated.csv", content, "text/csv")},
    )
    assert upload.status_code == 201
    batch_id = upload.json()["batch_id"]
    mapping_payload = {
        "mapping": {
            "occurred_at": "Fecha",
            "transaction_type": "Tipo",
            "category": "Categoría",
            "description": "Descripción",
            "amount": "Valor",
        }
    }

    mapping = client.post(f"/api/v1/imports/{batch_id}/mapping", json=mapping_payload)
    assert mapping.status_code == 200
    assert mapping.json()["summary"] == {
        "records_total": 2,
        "records_valid": 2,
        "records_invalid": 0,
        "records_duplicate": 0,
    }

    first_confirm = client.post(f"/api/v1/imports/{batch_id}/confirm")
    assert first_confirm.status_code == 200
    assert first_confirm.json()["records_inserted"] == 2

    replay_confirm = client.post(f"/api/v1/imports/{batch_id}/confirm")
    assert replay_confirm.status_code == 200
    assert replay_confirm.json()["records_inserted"] == 2
    assert client.get("/api/v1/transactions").json()["total"] == 2


def test_staged_batch_recovers_after_import_service_recreation(client, db_session, tmp_path, monkeypatch):
    _seed_categories(client)
    monkeypatch.setattr(settings, "IMPORT_STORAGE_DIR", tmp_path / "persistent-imports")

    upload = _upload_transactions_file(client, filename="recoverable.csv")
    assert upload.status_code == 201
    batch_id = upload.json()["batch_id"]
    batch = db_session.get(ImportBatch, batch_id)
    assert batch is not None
    assert Path(batch.storage_path).exists()

    mapping_payload = {
        "mapping": {
            "occurred_at": "Fecha",
            "transaction_type": "Tipo",
            "category": "Categoría",
            "description": "Descripción",
            "amount": "Valor",
        }
    }
    recreated_service = ImportService(db_session)
    mapped = recreated_service.apply_mapping(batch_id, ImportMappingRequest(mapping=mapping_payload["mapping"]))
    assert mapped.status.value == "VALIDATED"
    db_session.expire_all()

    validated_recreated_service = ImportService(db_session)
    confirmed = validated_recreated_service.confirm(batch_id)
    assert confirmed.records_inserted == 1


def test_import_marks_absent_mapped_description_as_missing(client):
    _seed_categories(client)
    content = (
        "Fecha,Tipo,Categoría,Valor,Descripción\n"
        "12/08/2026,ingreso,Impresiones,12000\n"
    ).encode("utf-8")

    upload = client.post(
        "/api/v1/imports/transactions",
        files={"file": ("missing-description.csv", content, "text/csv")},
    )
    assert upload.status_code == 201

    mapping = client.post(
        f"/api/v1/imports/{upload.json()['batch_id']}/mapping",
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
    body = mapping.json()
    assert body["summary"]["records_invalid"] == 1
    assert body["invalid_rows"] == [{"row_number": 1, "error_code": "MISSING_DESCRIPTION", "message": "Missing description"}]
    assert "None" not in body["invalid_rows"][0]["message"]


def _amount_mapping_payload():
    return {
        "mapping": {
            "occurred_at": "Fecha",
            "transaction_type": "Tipo",
            "category": "Categoría",
            "description": "Descripción",
            "amount": "Valor",
        }
    }


def test_import_rejects_amounts_with_more_than_two_fractional_digits(client, monkeypatch):
    _seed_categories(client)
    monkeypatch.setattr(settings, "IMPORT_DEFAULT_LOCALE", "es_AR")

    upload = _upload_transactions_file(client, filename="excess-precision.csv", rows=[_import_row(Valor="1234,567")])
    assert upload.status_code == 201

    mapping = client.post(f"/api/v1/imports/{upload.json()['batch_id']}/mapping", json=_amount_mapping_payload())

    assert mapping.status_code == 200
    body = mapping.json()
    assert body["summary"] == {
        "records_total": 1,
        "records_valid": 0,
        "records_invalid": 1,
        "records_duplicate": 0,
    }
    assert body["invalid_rows"] == [{"row_number": 1, "error_code": "INVALID_AMOUNT", "message": "Invalid amount"}]


def test_import_rejects_sub_cent_amount_before_confirmation(client, monkeypatch):
    _seed_categories(client)
    monkeypatch.setattr(settings, "IMPORT_DEFAULT_LOCALE", "es_AR")

    upload = _upload_transactions_file(client, filename="sub-cent.csv", rows=[_import_row(Valor="0,004")])
    assert upload.status_code == 201

    mapping = client.post(f"/api/v1/imports/{upload.json()['batch_id']}/mapping", json=_amount_mapping_payload())
    assert mapping.status_code == 200
    assert mapping.json()["summary"]["records_invalid"] == 1
    assert mapping.json()["invalid_rows"][0]["error_code"] == "INVALID_AMOUNT"

    confirmation = client.post(f"/api/v1/imports/{upload.json()['batch_id']}/confirm")

    assert confirmation.status_code == 200
    assert confirmation.json()["records_inserted"] == 0
    assert client.get("/api/v1/transactions").json()["total"] == 0


@pytest.mark.parametrize(
    ("locale", "raw_amount", "expected_amount"),
    [
        ("es_AR", "1.234", "1234.00"),
        ("es_AR", "1.234,56", "1234.56"),
        ("en_US", "1,234", "1234.00"),
        ("en_US", "1,234.56", "1234.56"),
    ],
)
def test_import_accepts_locale_grouped_whole_and_cent_amounts(
    client, monkeypatch, locale, raw_amount, expected_amount
):
    _seed_categories(client)
    monkeypatch.setattr(settings, "IMPORT_DEFAULT_LOCALE", locale)

    upload = _upload_transactions_file(client, filename=f"grouped-{locale}-{raw_amount}.csv", rows=[_import_row(Valor=raw_amount)])
    assert upload.status_code == 201

    mapping = client.post(f"/api/v1/imports/{upload.json()['batch_id']}/mapping", json=_amount_mapping_payload())

    assert mapping.status_code == 200
    assert mapping.json()["summary"]["records_valid"] == 1
    assert mapping.json()["preview"][0]["amount"] == expected_amount


def test_import_confirmation_only_inserts_rows_with_storage_safe_amounts(client, monkeypatch):
    _seed_categories(client)
    monkeypatch.setattr(settings, "IMPORT_DEFAULT_LOCALE", "es_AR")

    upload = _upload_transactions_file(
        client,
        filename="confirmation-precision-safety.csv",
        rows=[_import_row(Descripción="Rejected precise amount", Valor="10,999"), _import_row(Valor="20.99")],
    )
    assert upload.status_code == 201

    mapping = client.post(f"/api/v1/imports/{upload.json()['batch_id']}/mapping", json=_amount_mapping_payload())
    assert mapping.status_code == 200
    assert mapping.json()["summary"] == {
        "records_total": 2,
        "records_valid": 1,
        "records_invalid": 1,
        "records_duplicate": 0,
    }

    confirmation = client.post(f"/api/v1/imports/{upload.json()['batch_id']}/confirm")

    assert confirmation.status_code == 200
    assert confirmation.json()["records_inserted"] == 1
    transactions = client.get("/api/v1/transactions")
    assert transactions.status_code == 200
    assert transactions.json()["total"] == 1
    assert transactions.json()["items"][0]["amount"] == "20.99"
