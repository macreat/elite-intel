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


class TestCatalogIncludesStock:
    def test_catalog_list_includes_stock_qty(self, client, db_session):
        _make_product(db_session, "LAPIZ NEGRO", invoice_price=100, local_price=200, stock_qty=7)
        _make_product(db_session, "CUADERNO A5", invoice_price=100, local_price=200, stock_qty=None)

        res = client.get("/api/v1/catalog")
        assert res.status_code == 200
        items = {item["name"]: item for item in res.json()["items"]}
        assert items["LAPIZ NEGRO"]["stock_qty"] == 7
        assert items["CUADERNO A5"]["stock_qty"] is None

    def test_product_detail_includes_stock_qty(self, client, db_session):
        product = _make_product(db_session, "BORRADOR BLANCO", stock_qty=3)
        res = client.get(f"/api/v1/products/{product.id}")
        assert res.status_code == 200
        assert res.json()["stock_qty"] == 3


class TestPatchProductStock:
    def test_patch_updates_stock(self, client, db_session):
        product = _make_product(db_session, "TIJERA", stock_qty=1)
        res = client.patch(f"/api/v1/products/{product.id}/stock", json={"stock": 12})
        assert res.status_code == 200
        body = res.json()
        assert body["id"] == product.id
        assert body["stock_qty"] == 12

    def test_patch_sets_stock_to_null(self, client, db_session):
        product = _make_product(db_session, "REGLA 30CM", stock_qty=4)
        res = client.patch(f"/api/v1/products/{product.id}/stock", json={"stock": None})
        assert res.status_code == 200
        assert res.json()["stock_qty"] is None

    def test_patch_zero_is_allowed(self, client, db_session):
        product = _make_product(db_session, "COLLA BARRA", stock_qty=5)
        res = client.patch(f"/api/v1/products/{product.id}/stock", json={"stock": 0})
        assert res.status_code == 200
        assert res.json()["stock_qty"] == 0

    @pytest.mark.parametrize("payload", [{"stock": -1}, {"stock": -10}])
    def test_patch_negative_stock_rejected_422(self, client, db_session, payload):
        product = _make_product(db_session, "PLUMON", stock_qty=2)
        res = client.patch(f"/api/v1/products/{product.id}/stock", json=payload)
        assert res.status_code == 422

    @pytest.mark.parametrize("payload", [{"stock": 1.5}, {"stock": "abc"}, {"stock": [1]}])
    def test_patch_non_integer_stock_rejected_422(self, client, db_session, payload):
        product = _make_product(db_session, "PORTAPLANAS", stock_qty=2)
        res = client.patch(f"/api/v1/products/{product.id}/stock", json=payload)
        assert res.status_code == 422

    def test_patch_unknown_product_404(self, client, db_session):
        res = client.patch("/api/v1/products/99999/stock", json={"stock": 5})
        assert res.status_code == 404


class TestBulkStockUpdate:
    def test_bulk_updates_many_and_returns_rows(self, client, db_session):
        p1 = _make_product(db_session, "BOLIGRAFO AZUL", stock_qty=1)
        p2 = _make_product(db_session, "BOLIGRAFO ROJO")
        p3 = _make_product(db_session, "LAPIZ MINE", stock_qty=9)

        res = client.post(
            "/api/v1/products/stock/bulk",
            json={"items": [
                {"product_id": p1.id, "stock": 10},
                {"product_id": p2.id, "stock": 0},
                {"product_id": p3.id, "stock": None},
            ]},
        )
        assert res.status_code == 200
        rows = {row["id"]: row for row in res.json()["items"]}
        assert rows[p1.id]["stock_qty"] == 10
        assert rows[p2.id]["stock_qty"] == 0
        assert rows[p3.id]["stock_qty"] is None

    def test_bulk_persists_changes(self, client, db_session):
        p1 = _make_product(db_session, "RESMA A4", stock_qty=2)
        res = client.post(
            "/api/v1/products/stock/bulk",
            json={"items": [{"product_id": p1.id, "stock": 33}]},
        )
        assert res.status_code == 200
        detail = client.get(f"/api/v1/products/{p1.id}")
        assert detail.json()["stock_qty"] == 33

    def test_bulk_unknown_id_rejects_without_partial_changes(self, client, db_session):
        p1 = _make_product(db_session, "CARPETA", stock_qty=6)
        res = client.post(
            "/api/v1/products/stock/bulk",
            json={"items": [
                {"product_id": p1.id, "stock": 50},
                {"product_id": 99999, "stock": 1},
            ]},
        )
        assert res.status_code == 404
        db_session.expire_all()
        refreshed = db_session.get(Product, p1.id)
        assert refreshed.stock_qty == 6

    def test_bulk_empty_items_rejected_422(self, client, db_session):
        res = client.post("/api/v1/products/stock/bulk", json={"items": []})
        assert res.status_code == 422

    def test_bulk_negative_stock_rejected_422(self, client, db_session):
        p1 = _make_product(db_session, "SOBRE MANILA")
        res = client.post(
            "/api/v1/products/stock/bulk",
            json={"items": [{"product_id": p1.id, "stock": -3}]},
        )
        assert res.status_code == 422

    def test_bulk_non_integer_stock_rejected_422(self, client, db_session):
        p1 = _make_product(db_session, "ESPIRAL")
        res = client.post(
            "/api/v1/products/stock/bulk",
            json={"items": [{"product_id": p1.id, "stock": 2.5}]},
        )
        assert res.status_code == 422
