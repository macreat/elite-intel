# Database Management

SQLAlchemy session setup and Alembic schema migration files.

**Contents:**
- `session.py` - Database connection pool and engine configuration.
- `base.py` - Base class importing all ORM models for Alembic auto-generation.
- `migrations/` - Alembic migration scripts tracking database schema changes over time.

**Connects to:** PostgreSQL database instance and ORM models.
