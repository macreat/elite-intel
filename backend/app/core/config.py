import os
from pathlib import Path


class Settings:
    API_V1_PREFIX = "/api/v1"
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./elite.db")
    FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:3000")
    API_LOG_LEVEL = os.getenv("API_LOG_LEVEL", "info")
    IMPORT_MAX_FILE_SIZE_MB = int(os.getenv("IMPORT_MAX_FILE_SIZE_MB", "250"))
    IMPORT_DEFAULT_LOCALE = os.getenv("IMPORT_DEFAULT_LOCALE", "es_AR")
    IMPORT_DEFAULT_CURRENCY = os.getenv("IMPORT_DEFAULT_CURRENCY", "ARS")
    IMPORT_DEFAULT_TIMEZONE = os.getenv("IMPORT_DEFAULT_TIMEZONE", "UTC")
    IMPORT_STORAGE_DIR = Path(os.getenv("IMPORT_STORAGE_DIR", "/tmp/elite-imports"))
    PERSIST_TRANSACTIONS_CSV = Path(os.getenv("PERSIST_TRANSACTIONS_CSV", "data/raw/2026-2.csv"))


settings = Settings()
