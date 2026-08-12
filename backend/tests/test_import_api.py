import csv
import io


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
    content = _csv_bytes(
        [
            {
                "Fecha": "12/08/2026",
                "Tipo": "ingreso",
                "Categoría": "Impresiones",
                "Descripción": "A",
                "Valor": "100",
            }
        ]
    )

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
