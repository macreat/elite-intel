# Domain Services

Encapsulates core business rules, KPI calculations, savings rate formulas, and ETL import validation.

**Contents:**
- `transaction_service.py` - Transaction processing and category validation logic.
- `dashboard_service.py` - Revenue, expense, net balance, and savings aggregation logic.
- `import_service.py` - Excel/CSV file parsing, column mapping, and record sanitization.

**Connects to:** Repositories layer for database access and API routes for requests.
