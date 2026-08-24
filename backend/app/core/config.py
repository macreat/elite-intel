import os
from pathlib import Path


class Settings:
    API_V1_PREFIX = "/api/v1"
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./elite.db")
    FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:3000")
    API_LOG_LEVEL = os.getenv("API_LOG_LEVEL", "info")
    IMPORT_MAX_FILE_SIZE_MB = int(os.getenv("IMPORT_MAX_FILE_SIZE_MB", "250"))
    IMPORT_DEFAULT_LOCALE = os.getenv("IMPORT_DEFAULT_LOCALE", "es_CO")
    IMPORT_DEFAULT_CURRENCY = os.getenv("IMPORT_DEFAULT_CURRENCY", "COP")
    IMPORT_DEFAULT_TIMEZONE = os.getenv("IMPORT_DEFAULT_TIMEZONE", "UTC")
    IMPORT_STORAGE_DIR = Path(os.getenv("IMPORT_STORAGE_DIR", "/tmp/elite-imports"))
    PERSIST_TRANSACTIONS_CSV = Path(os.getenv("PERSIST_TRANSACTIONS_CSV", "data/raw/2026-2.csv"))
    CATALOG_XLSX_PATH = Path(
        os.getenv("CATALOG_XLSX_PATH", "/app/data/raw/PRECIOS_PRODUCTOS_PAPELERIA.xlsx")
    )
    # Directory holding the built frontend (frontend/dist). When set and present,
    # the backend serves the dashboard itself so the Electron desktop build can
    # load everything from a single origin (http://127.0.0.1:<port>/).
    STATIC_DIR = os.getenv("STATIC_DIR")


settings = Settings()
