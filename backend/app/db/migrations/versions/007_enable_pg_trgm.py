"""enable pg_trgm and search index

Revision ID: 007_enable_pg_trgm
Revises: 006_create_transactions
Create Date: 2026-08-12
"""

from alembic import op


revision = "007_enable_pg_trgm"
down_revision = "006_create_transactions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_transactions_description_trgm "
        "ON transactions USING gin ((coalesce(description,'') || ' ' || coalesce(notes,'')) gin_trgm_ops)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_transactions_description_trgm")
