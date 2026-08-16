import csv
import io
import threading
from collections.abc import Generator
from concurrent.futures import ThreadPoolExecutor

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import NullPool

from app.api.deps import get_db
from app.db.base import Base
from app.main import app
from app.services.import_service import ImportService
from app.core.config import settings


@pytest.fixture()
def concurrent_client(tmp_path, monkeypatch) -> Generator[TestClient, None, None]:
    database_path = tmp_path / "concurrency.db"
    engine = create_engine(
        f"sqlite+pysqlite:///{database_path}",
        connect_args={"check_same_thread": False, "timeout": 30},
        poolclass=NullPool,
        future=True,
    )
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    monkeypatch.setattr(settings, "IMPORT_STORAGE_DIR", tmp_path / "imports")

    def override_get_db():
        session = session_factory()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app) as client:
            yield client
    finally:
        app.dependency_overrides.clear()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


def _csv_bytes() -> bytes:
    stream = io.StringIO()
    writer = csv.DictWriter(stream, fieldnames=["Fecha", "Tipo", "Categoría", "Descripción", "Valor"])
    writer.writeheader()
    writer.writerow(
        {
            "Fecha": "12/08/2026",
            "Tipo": "ingreso",
            "Categoría": "Impresiones",
            "Descripción": "Concurrent confirmation",
            "Valor": "12000",
        }
    )
    return stream.getvalue().encode("utf-8")


def test_concurrent_confirmation_requests_are_idempotent(concurrent_client, monkeypatch):
    category = concurrent_client.post("/api/v1/categories", json={"name": "Impresiones", "type": "INCOME"})
    assert category.status_code == 201

    upload = concurrent_client.post(
        "/api/v1/imports/transactions",
        files={"file": ("concurrent.csv", _csv_bytes(), "text/csv")},
    )
    assert upload.status_code == 201
    batch_id = upload.json()["batch_id"]

    mapping = concurrent_client.post(
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

    barrier = threading.Barrier(2)
    original_confirm = ImportService.confirm

    def synchronized_confirm(self, current_batch_id):
        barrier.wait(timeout=10)
        return original_confirm(self, current_batch_id)

    monkeypatch.setattr(ImportService, "confirm", synchronized_confirm)
    with ThreadPoolExecutor(max_workers=2) as executor:
        responses = list(
            executor.map(
                lambda _: concurrent_client.post(f"/api/v1/imports/{batch_id}/confirm"),
                range(2),
            )
        )

    assert [response.status_code for response in responses] == [200, 200]
    assert [response.json()["records_inserted"] for response in responses] == [1, 1]

    transactions = concurrent_client.get("/api/v1/transactions")
    assert transactions.status_code == 200
    assert transactions.json()["total"] == 1
