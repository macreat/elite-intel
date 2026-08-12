# FastAPI Application Package

Contains the modular backend components for routing, domain services, database models, and validation schemas.

**Contents:**
- `main.py` - FastAPI app initialization, middleware configuration, and lifecycle events.
- `api/` - HTTP endpoint routes and request handlers.
- `models/` - SQLAlchemy database ORM entity models.
- `schemas/` - Pydantic schemas for data serialization and request validation.
- `services/` - Business rule logic and analytical calculation routines.
- `repositories/` - Database CRUD query logic and data access abstraction.
- `db/` - Alembic database migrations and session setup.

**Connects to:** PostgreSQL database and frontend HTTP requests.
