import pytest

from app.models.product import Product


def _ensure_category(db_session):
    from app.models.category import Category

    cat = db_session.query(Category).first()
    if not cat:
        cat = Category(name="Test", type="EXPENSE")
        db_session.add(cat)
        db_session.commit()
        db_session.refresh(cat)
    return cat


def _make_product(db_session, name, **kwargs):
    cat = _ensure_category(db_session)
    product = Product(name=name, category_id=cat.id, **kwargs)
    db_session.add(product)
    db_session.commit()
    db_session.refresh(product)
    return product


class TestPatchProductFields:
    def test_patch_invoice_price_only(self, client, db_session):
        product = _make_product(db_session, "LAPIZ NEGRO", invoice_price=100, local_price=200)

        res = client.patch(f"/api/v1/products/{product.id}", json={"invoice_price": 150})

        assert res.status_code == 200
        body = res.json()
        assert body["id"] == product.id
        assert float(body["invoice_price"]) == 150
        assert float(body["local_price"]) == 200

    def test_patch_local_price_only(self, client, db_session):
        product = _make_product(db_session, "CUADERNO A5", invoice_price=100, local_price=200)

        res = client.patch(f"/api/v1/products/{product.id}", json={"local_price": 250})

        assert res.status_code == 200
        body = res.json()
        assert float(body["invoice_price"]) == 100
        assert float(body["local_price"]) == 250

    def test_patch_name_and_both_prices(self, client, db_session):
        product = _make_product(db_session, "BORRADOR", invoice_price=50, local_price=90)

        res = client.patch(
            f"/api/v1/products/{product.id}",
            json={"name": "BORRADOR BLANCO", "invoice_price": 55, "local_price": 99},
        )

        assert res.status_code == 200
        body = res.json()
        assert body["name"] == "BORRADOR BLANCO"
        assert float(body["invoice_price"]) == 55
        assert float(body["local_price"]) == 99

    def test_patch_persists_changes(self, client, db_session):
        product = _make_product(db_session, "TIJERA", invoice_price=10, local_price=20)

        res = client.patch(f"/api/v1/products/{product.id}", json={"invoice_price": 12})
        assert res.status_code == 200

        detail = client.get(f"/api/v1/products/{product.id}")
        assert float(detail.json()["invoice_price"]) == 12

    def test_patch_unknown_product_404(self, client, db_session):
        res = client.patch("/api/v1/products/99999", json={"invoice_price": 1})
        assert res.status_code == 404

    @pytest.mark.parametrize(
        "payload",
        [
            {"invoice_price": -1},
            {"local_price": -5},
            {"invoice_price": -0.01},
            {"invoice_price": "abc"},
            {"local_price": [1]},
            {"name": ""},
            {"name": "   "},
        ],
    )
    def test_patch_invalid_values_rejected_422(self, client, db_session, payload):
        product = _make_product(db_session, "REGLA", invoice_price=10, local_price=20)

        res = client.patch(f"/api/v1/products/{product.id}", json=payload)

        assert res.status_code == 422
        db_session.expire_all()
        refreshed = db_session.get(Product, product.id)
        assert float(refreshed.invoice_price) == 10


class TestBulkPricesUpdate:
    def test_bulk_updates_many_and_returns_rows(self, client, db_session):
        p1 = _make_product(db_session, "BOLIGRAFO AZUL", invoice_price=100, local_price=200)
        p2 = _make_product(db_session, "BOLIGRAFO ROJO")
        p3 = _make_product(db_session, "LAPIZ MINE", invoice_price=300, local_price=500)

        res = client.post(
            "/api/v1/products/prices/bulk",
            json={
                "items": [
                    {"product_id": p1.id, "invoice_price": 110},
                    {"product_id": p2.id, "invoice_price": 120, "local_price": 220},
                    {"product_id": p3.id, "local_price": 550},
                ]
            },
        )

        assert res.status_code == 200
        rows = {row["id"]: row for row in res.json()["items"]}
        assert float(rows[p1.id]["invoice_price"]) == 110
        assert float(rows[p2.id]["invoice_price"]) == 120
        assert float(rows[p2.id]["local_price"]) == 220
        assert float(rows[p3.id]["local_price"]) == 550

    def test_bulk_only_provided_field_changes(self, client, db_session):
        p1 = _make_product(db_session, "RESMA A4", invoice_price=100, local_price=200)

        res = client.post(
            "/api/v1/products/prices/bulk",
            json={"items": [{"product_id": p1.id, "invoice_price": 130}]},
        )

        assert res.status_code == 200
        row = res.json()["items"][0]
        assert float(row["invoice_price"]) == 130
        assert float(row["local_price"]) == 200

    def test_bulk_persists_changes(self, client, db_session):
        p1 = _make_product(db_session, "CARPETA", invoice_price=80, local_price=160)

        res = client.post(
            "/api/v1/products/prices/bulk",
            json={"items": [{"product_id": p1.id, "invoice_price": 88, "local_price": 168}]},
        )
        assert res.status_code == 200

        detail = client.get(f"/api/v1/products/{p1.id}")
        assert float(detail.json()["invoice_price"]) == 88
        assert float(detail.json()["local_price"]) == 168

    def test_bulk_unknown_id_rejects_without_partial_changes(self, client, db_session):
        p1 = _make_product(db_session, "SOBRE MANILA", invoice_price=60, local_price=120)

        res = client.post(
            "/api/v1/products/prices/bulk",
            json={
                "items": [
                    {"product_id": p1.id, "invoice_price": 70},
                    {"product_id": 99999, "local_price": 5},
                ]
            },
        )

        assert res.status_code == 404
        db_session.expire_all()
        refreshed = db_session.get(Product, p1.id)
        assert float(refreshed.invoice_price) == 60
        assert float(refreshed.local_price) == 120

    def test_bulk_empty_items_rejected_422(self, client, db_session):
        res = client.post("/api/v1/products/prices/bulk", json={"items": []})
        assert res.status_code == 422

    @pytest.mark.parametrize(
        "item",
        [
            {"product_id": 1},
            {"product_id": 1, "invoice_price": None, "local_price": None},
        ],
    )
    def test_bulk_item_without_fields_rejected_422(self, client, db_session, item):
        res = client.post("/api/v1/products/prices/bulk", json={"items": [item]})
        assert res.status_code == 422

    @pytest.mark.parametrize(
        "item",
        [
            {"product_id": 1, "invoice_price": -3},
            {"product_id": 1, "local_price": -1.5},
            {"product_id": 1, "invoice_price": "cheap"},
        ],
    )
    def test_bulk_invalid_prices_rejected_422(self, client, db_session, item):
        res = client.post("/api/v1/products/prices/bulk", json={"items": [item]})
        assert res.status_code == 422


class TestCreateProductWithPrices:
    def test_create_with_prices_and_stock(self, client, db_session):
        cat = _ensure_category(db_session)

        res = client.post(
            "/api/v1/products",
            json={
                "name": "PLUMON NUEVO",
                "category_id": cat.id,
                "invoice_price": 2500,
                "local_price": 4200,
                "stock_qty": 15,
            },
        )

        assert res.status_code == 201
        body = res.json()
        assert body["name"] == "PLUMON NUEVO"
        assert float(body["invoice_price"]) == 2500
        assert float(body["local_price"]) == 4200
        assert body["stock_qty"] == 15

    def test_create_defaults_category_when_missing(self, client, db_session):
        res = client.post(
            "/api/v1/products",
            json={"name": "SIN CATEGORIA", "invoice_price": 100, "local_price": 200},
        )

        assert res.status_code == 201
        assert res.json()["category_id"] is not None

    def test_create_negative_price_rejected_422(self, client, db_session):
        cat = _ensure_category(db_session)
        res = client.post(
            "/api/v1/products",
            json={"name": "MALO", "category_id": cat.id, "invoice_price": -1},
        )
        assert res.status_code == 422

    def test_create_empty_name_rejected_422(self, client, db_session):
        cat = _ensure_category(db_session)
        res = client.post("/api/v1/products", json={"name": "", "category_id": cat.id})
        assert res.status_code == 422

    def test_create_negative_stock_rejected_422(self, client, db_session):
        cat = _ensure_category(db_session)
        res = client.post(
            "/api/v1/products",
            json={"name": "STOCK MALO", "category_id": cat.id, "stock_qty": -2},
        )
        assert res.status_code == 422
