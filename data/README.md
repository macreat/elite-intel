# Data Management Pipeline

Storage directories for historical Excel spreadsheets, raw transaction dumps, cleaned analytical datasets, and import batch files.

**Contents:**
- `raw/` - Unmodified original Excel/CSV files (e.g. historical Kardex records).
- `processed/` - Normalized, cleaned, and validated tabular data ready for database ingestion or ML training.
- `imports/` - Uploaded batch files during runtime import execution.

**Connects to:** ETL scripts in `scripts/` and backend import services in `backend/app/services/`.
