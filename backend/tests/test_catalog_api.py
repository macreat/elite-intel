import pytest

from app.models.product import Product


def _make_product(db, name, **kwargs):
    cat = _ensure_category(db)
    cat_id = kwargs.pop("category_id", cat.id)
    product = Product(name=name, category_id=cat_id, **kwargs)
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


def _seed_products(db, count=149):
    """Seed exactly count products for pagination tests."""
    cat = _ensure_category(db)
    products = []
    for i in range(1, count + 1):
        p = Product(name=f"Product {i:03d}", category_id=cat.id)
        db.add(p)
        products.append(p)
    db.commit()
    return products


def _ensure_category(db_session):
    """Create a dummy category if none exists (needed for FK)."""
    from app.models.category import Category
    cat = db_session.query(Category).first()
    if not cat:
        cat = Category(name="Test", type="EXPENSE")
        db_session.add(cat)
        db_session.commit()
        db_session.refresh(cat)
    return cat


def test_empty_envelope(client, db_session):
    _ensure_category(db_session)
    res = client.get("/api/v1/catalog")
    assert res.status_code == 200
    body = res.json()
    assert body["items"] == []
    assert body["total"] == 0
    assert body["page"] == 1
    assert body["page_size"] == 20


def test_seeded_first_page_defaults(client, db_session):
    cat = _ensure_category(db_session)
    _seed_products(db_session, count=149)
    res = client.get("/api/v1/catalog")
    assert res.status_code == 200
    body = res.json()
    assert len(body["items"]) == 20
    assert body["total"] == 149
    assert body["page"] == 1
    assert body["page_size"] == 20


def test_ilike_search(client, db_session):
    cat = _ensure_category(db_session)
    db_session.add_all([
        Product(name="LAPIZ NEGRO", category_id=cat.id),
        Product(name="LAPIZ ROJO", category_id=cat.id),
        Product(name="CUADERNO A5", category_id=cat.id),
    ])
    db_session.commit()

    res = client.get("/api/v1/catalog?search=lapiz")
    assert res.status_code == 200
    body = res.json()
    names = {item["name"] for item in body["items"]}
    assert "LAPIZ NEGRO" in names
    assert "LAPIZ ROJO" in names
    assert body["total"] == 2


def test_no_results(client, db_session):
    _ensure_category(db_session)
    _seed_products(db_session, count=5)
    res = client.get("/api/v1/catalog?search=cuaderno+a5")
    assert res.status_code == 200
    body = res.json()
    assert body["items"] == []
    assert body["total"] == 0


def test_page_beyond_last(client, db_session):
    _ensure_category(db_session)
    _seed_products(db_session, count=149)
    res = client.get("/api/v1/catalog?page=99")
    assert res.status_code == 200
    body = res.json()
    assert body["items"] == []
    assert body["total"] == 149


def test_null_price_items_listed(client, db_session):
    cat = _ensure_category(db_session)
    p = Product(name="PTE Item", category_id=cat.id, invoice_price=None, local_price=None)
    db_session.add(p)
    db_session.commit()

    res = client.get("/api/v1/catalog?search=PTE")
    assert res.status_code == 200
    body = res.json()
    assert len(body["items"]) == 1
    assert body["items"][0]["invoice_price"] is None
    assert body["items"][0]["local_price"] is None


@pytest.mark.parametrize(
    "params",
    [
        "?page=0",
        "?page_size=0",
        "?page_size=101",
        "?search=" + "x" * 151,
    ],
)
def test_422_on_bad_pagination(client, db_session, params):
    _ensure_category(db_session)
    res = client.get(f"/api/v1/catalog{params}")
    assert res.status_code == 422
