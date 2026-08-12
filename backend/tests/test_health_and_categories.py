def test_health_endpoints(client):
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"

    res_v1 = client.get("/api/v1/health")
    assert res_v1.status_code == 200
    assert res_v1.json()["status"] == "ok"


def test_category_soft_delete(client):
    created = client.post("/api/v1/categories", json={"name": "TempCat", "type": "INCOME"})
    assert created.status_code == 201
    cat_id = created.json()["id"]

    deleted = client.delete(f"/api/v1/categories/{cat_id}")
    assert deleted.status_code == 204

    active = client.get("/api/v1/categories?active=true")
    assert active.status_code == 200
    names = {item["name"] for item in active.json()}
    assert "TempCat" not in names
