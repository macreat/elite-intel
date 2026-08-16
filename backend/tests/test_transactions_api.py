from datetime import datetime, timezone


def _seed_category(client, *, name: str, type_value: str):
    res = client.post("/api/v1/categories", json={"name": name, "type": type_value})
    assert res.status_code == 201
    return res.json()


def test_transaction_crud_and_filters(client):
    income_cat = _seed_category(client, name="Salary", type_value="INCOME")
    expense_cat = _seed_category(client, name="Rent", type_value="EXPENSE")

    create_income = client.post(
        "/api/v1/transactions",
        json={
            "occurred_at": datetime(2026, 8, 1, 10, 0, tzinfo=timezone.utc).isoformat(),
            "transaction_type": "INCOME",
            "category_id": income_cat["id"],
            "description": "Consulting",
            "amount": "1000.00",
            "notes": "monthly",
        },
    )
    assert create_income.status_code == 201
    tx_income = create_income.json()

    create_expense = client.post(
        "/api/v1/transactions",
        json={
            "occurred_at": datetime(2026, 8, 2, 10, 0, tzinfo=timezone.utc).isoformat(),
            "transaction_type": "EXPENSE",
            "category_id": expense_cat["id"],
            "description": "Office rent",
            "amount": "200.00",
        },
    )
    assert create_expense.status_code == 201
    tx_expense = create_expense.json()

    listed = client.get("/api/v1/transactions?page=1&page_size=10")
    assert listed.status_code == 200
    payload = listed.json()
    assert payload["total"] == 2

    fetched = client.get(f"/api/v1/transactions/{tx_income['id']}")
    assert fetched.status_code == 200

    updated = client.put(
        f"/api/v1/transactions/{tx_expense['id']}",
        json={"description": "Office rent August", "notes": "updated", "product_id": None},
    )
    assert updated.status_code == 200
    assert updated.json()["description"] == "Office rent August"
    assert updated.json()["notes"] == "updated"
    assert updated.json()["product_id"] is None

    filtered = client.get(f"/api/v1/transactions?type=INCOME&category_id={income_cat['id']}&search=Consult")
    assert filtered.status_code == 200
    assert filtered.json()["total"] == 1

    deleted = client.delete(f"/api/v1/transactions/{tx_income['id']}")
    assert deleted.status_code == 204

    after_delete = client.get("/api/v1/transactions")
    assert after_delete.status_code == 200
    assert after_delete.json()["total"] == 1


def test_transaction_category_type_guard(client):
    income_cat = _seed_category(client, name="Sales", type_value="INCOME")
    res = client.post(
        "/api/v1/transactions",
        json={
            "occurred_at": datetime(2026, 8, 1, 10, 0, tzinfo=timezone.utc).isoformat(),
            "transaction_type": "EXPENSE",
            "category_id": income_cat["id"],
            "description": "Wrong type",
            "amount": "10.00",
        },
    )
    assert res.status_code == 400
    assert res.json()["error_code"] == "CATEGORY_TYPE_MISMATCH"
