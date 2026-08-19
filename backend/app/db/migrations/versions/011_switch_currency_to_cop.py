"""switch platform default currency from ARS to COP

Revision ID: 011_switch_currency_to_cop
Revises: 010_source_context_identity
Create Date: 2026-08-19
"""

from alembic import op


revision = "011_switch_currency_to_cop"
down_revision = "010_source_context_identity"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE transactions ALTER COLUMN currency_code SET DEFAULT 'COP'")
    op.execute("ALTER TABLE import_batches ALTER COLUMN currency_assumption SET DEFAULT 'COP'")
    op.execute("UPDATE transactions SET currency_code = 'COP'")
    op.execute("UPDATE import_batches SET currency_assumption = 'COP'")


def downgrade() -> None:
    op.execute("UPDATE import_batches SET currency_assumption = 'ARS'")
    op.execute("UPDATE transactions SET currency_code = 'ARS'")
    op.execute("ALTER TABLE import_batches ALTER COLUMN currency_assumption SET DEFAULT 'ARS'")
    op.execute("ALTER TABLE transactions ALTER COLUMN currency_code SET DEFAULT 'ARS'")