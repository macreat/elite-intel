from datetime import datetime, timezone

import pytest


def _seed_category(client, *, name: str, type_value: str):
    res = client.post("/api/v1/categories", json={"name": name, "type": type_value})
    assert res.status_code == 201
    return res.json()


def _seed_product(client, *, name: str, category_id: int):
    res = client.post(
        "/api/v1/products",
        json={"name": name, "category_id": category_id, "active": True},
    )
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
            "quantity": 1,
        },
    )
    assert create_income.status_code == 201
    tx_income = create_income.json()
    assert tx_income["quantity"] == 1

    create_expense = client.post(
        "/api/v1/transactions",
        json={
            "occurred_at": datetime(2026, 8, 2, 10, 0, tzinfo=timezone.utc).isoformat(),
            "transaction_type": "EXPENSE",
            "category_id": expense_cat["id"],
            "description": "Office rent",
            "amount": "200.00",
            "quantity": 5,
        },
    )
    assert create_expense.status_code == 201
    tx_expense = create_expense.json()
    assert tx_expense["quantity"] == 5

    listed = client.get("/api/v1/transactions?page=1&page_size=10")
    assert listed.status_code == 200
    payload = listed.json()
    assert payload["total"] == 2

    fetched = client.get(f"/api/v1/transactions/{tx_income['id']}")
    assert fetched.status_code == 200

    updated = client.put(
        f"/api/v1/transactions/{tx_expense['id']}",
        json={"description": "Office rent August", "notes": "updated", "product_id": None, "quantity": 2},
    )
    assert updated.status_code == 200
    assert updated.json()["description"] == "Office rent August"
    assert updated.json()["notes"] == "updated"
    assert updated.json()["product_id"] is None
    assert updated.json()["quantity"] == 2

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
            "quantity": 1,
        },
    )
    assert res.status_code == 400
    assert res.json()["error_code"] == "CATEGORY_TYPE_MISMATCH"


def test_stock_increases_on_expense(client):
    expense_cat = _seed_category(client, name="Inventory", type_value="EXPENSE")
    product = _seed_product(client, name="Widget", category_id=expense_cat["id"])

    res = client.post(
        "/api/v1/transactions",
        json={
            "occurred_at": datetime(2026, 8, 1, 10, 0, tzinfo=timezone.utc).isoformat(),
            "transaction_type": "EXPENSE",
            "category_id": expense_cat["id"],
            "description": "Buy widgets",
            "amount": "50.00",
            "quantity": 10,
            "product_id": product["id"],
        },
    )
    assert res.status_code == 201

    prod = client.get(f"/api/v1/products/{product['id']}").json()
    assert prod["stock_qty"] == 10


def test_stock_decreases_on_income(client):
    expense_cat = _seed_category(client, name="Inventory", type_value="EXPENSE")
    income_cat = _seed_category(client, name="Sales", type_value="INCOME")
    product = _seed_product(client, name="Widget", category_id=expense_cat["id"])

    client.post(
        "/api/v1/transactions",
        json={
            "occurred_at": datetime(2026, 8, 1, 10, 0, tzinfo=timezone.utc).isoformat(),
            "transaction_type": "EXPENSE",
            "category_id": expense_cat["id"],
            "description": "Buy widgets",
            "amount": "50.00",
            "quantity": 10,
            "product_id": product["id"],
        },
    )

    res = client.post(
        "/api/v1/transactions",
        json={
            "occurred_at": datetime(2026, 8, 2, 10, 0, tzinfo=timezone.utc).isoformat(),
            "transaction_type": "INCOME",
            "category_id": income_cat["id"],
            "description": "Sell widgets",
            "amount": "80.00",
            "quantity": 3,
            "product_id": product["id"],
        },
    )
    assert res.status_code == 201

    prod = client.get(f"/api/v1/products/{product['id']}").json()
    assert prod["stock_qty"] == 7


def test_no_stock_change_without_product(client):
    expense_cat = _seed_category(client, name="Rent", type_value="EXPENSE")
    product = _seed_product(client, name="Desk", category_id=expense_cat["id"])

    client.post(
        "/api/v1/transactions",
        json={
            "occurred_at": datetime(2026, 8, 1, 10, 0, tzinfo=timezone.utc).isoformat(),
            "transaction_type": "EXPENSE",
            "category_id": expense_cat["id"],
            "description": "Buy desk",
            "amount": "100.00",
            "quantity": 5,
            "product_id": product["id"],
        },
    )

    res = client.post(
        "/api/v1/transactions",
        json={
            "occurred_at": datetime(2026, 8, 2, 10, 0, tzinfo=timezone.utc).isoformat(),
            "transaction_type": "EXPENSE",
            "category_id": expense_cat["id"],
            "description": "Office rent",
            "amount": "200.00",
            "quantity": 1,
        },
    )
    assert res.status_code == 201

    prod = client.get(f"/api/v1/products/{product['id']}").json()
    assert prod["stock_qty"] == 5


def test_delete_reverses_stock(client):
    expense_cat = _seed_category(client, name="Inventory", type_value="EXPENSE")
    product = _seed_product(client, name="Widget", category_id=expense_cat["id"])

    res = client.post(
        "/api/v1/transactions",
        json={
            "occurred_at": datetime(2026, 8, 1, 10, 0, tzinfo=timezone.utc).isoformat(),
            "transaction_type": "EXPENSE",
            "category_id": expense_cat["id"],
            "description": "Buy widgets",
            "amount": "50.00",
            "quantity": 10,
            "product_id": product["id"],
        },
    )
    tx_id = res.json()["id"]

    client.delete(f"/api/v1/transactions/{tx_id}")

    prod = client.get(f"/api/v1/products/{product['id']}").json()
    assert prod["stock_qty"] == 0


def test_update_reverses_old_and_applies_new(client):
    expense_cat = _seed_category(client, name="Inventory", type_value="EXPENSE")
    product_a = _seed_product(client, name="Widget A", category_id=expense_cat["id"])
    product_b = _seed_product(client, name="Widget B", category_id=expense_cat["id"])

    res = client.post(
        "/api/v1/transactions",
        json={
            "occurred_at": datetime(2026, 8, 1, 10, 0, tzinfo=timezone.utc).isoformat(),
            "transaction_type": "EXPENSE",
            "category_id": expense_cat["id"],
            "description": "Buy A",
            "amount": "50.00",
            "quantity": 5,
            "product_id": product_a["id"],
        },
    )
    tx_id = res.json()["id"]

    res = client.put(
        f"/api/v1/transactions/{tx_id}",
        json={"product_id": product_b["id"], "quantity": 8},
    )
    assert res.status_code == 200

    prod_a = client.get(f"/api/v1/products/{product_a['id']}").json()
    assert prod_a["stock_qty"] == 0

    prod_b = client.get(f"/api/v1/products/{product_b['id']}").json()
    assert prod_b["stock_qty"] == 8


def test_insufficient_stock_returns_error(client):
    expense_cat = _seed_category(client, name="Inventory", type_value="EXPENSE")
    income_cat = _seed_category(client, name="Sales", type_value="INCOME")
    product = _seed_product(client, name="Widget", category_id=expense_cat["id"])

    client.post(
        "/api/v1/transactions",
        json={
            "occurred_at": datetime(2026, 8, 1, 10, 0, tzinfo=timezone.utc).isoformat(),
            "transaction_type": "EXPENSE",
            "category_id": expense_cat["id"],
            "description": "Buy widgets",
            "amount": "50.00",
            "quantity": 2,
            "product_id": product["id"],
        },
    )

    res = client.post(
        "/api/v1/transactions",
        json={
            "occurred_at": datetime(2026, 8, 2, 10, 0, tzinfo=timezone.utc).isoformat(),
            "transaction_type": "INCOME",
            "category_id": income_cat["id"],
            "description": "Sell too many",
            "amount": "80.00",
            "quantity": 5,
            "product_id": product["id"],
        },
    )
    assert res.status_code == 400
    assert res.json()["error_code"] == "INSUFFICIENT_STOCK"

    prod = client.get(f"/api/v1/products/{product['id']}").json()
    assert prod["stock_qty"] == 2
