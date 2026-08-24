#!/usr/bin/env python3
"""Idempotent desktop bootstrap for the Electron build.

The Docker/Postgres deployment runs `alembic upgrade head` (see
backend/Dockerfile). The desktop build uses SQLite instead, and the
migration history includes a Postgres-only step (pg_trgm), so alembic
cannot run against SQLite. This script creates the SQLite schema directly
from the SQLAlchemy models and seeds the price catalog on first run.

Safe to run on every app launch: table creation is a no-op once the
schema exists, and the catalog is only seeded when the products table
is empty.

Usage:
    python scripts/bootstrap_desktop.py
"""

from __future__ import annotations

import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from sqlalchemy.orm import sessionmaker  # noqa: E402

from app.core.config import settings  # noqa: E402
from app.db.base import Base  # noqa: E402
from app.db.session import engine  # noqa: E402
from app.models.product import Product  # noqa: E402


def main() -> int:
    Base.metadata.create_all(bind=engine)

    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    with SessionLocal() as session:
        has_products = session.query(Product).first() is not None

    if not has_products and settings.CATALOG_XLSX_PATH.exists():
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        import seed_catalog

        seed_catalog.run_seed(str(settings.CATALOG_XLSX_PATH), "Precios", dry_run=False)
        print("Bootstrap: seeded product catalog from xlsx")
    else:
        print(f"Bootstrap: schema ready (products seeded={has_products}, "
              f"catalog path exists={settings.CATALOG_XLSX_PATH.exists()})")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
