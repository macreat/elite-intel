# Repositories Layer

Encapsulates raw SQLAlchemy database queries and database operations behind clean repository interfaces.

**Contents:**
- `transaction_repository.py` - Queries for filtering, listing, and aggregating financial transactions.
- `category_repository.py` - Category persistence and active listing queries.
- `import_repository.py` - Import batch logging and bulk insertion operations.

**Connects to:** Services layer and SQLAlchemy database session.
