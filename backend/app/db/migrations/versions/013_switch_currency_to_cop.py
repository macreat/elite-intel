"""switch platform default currency from ARS to COP

Revision ID: 013_switch_currency_to_cop
Revises: 012_add_transaction_quantity
Create Date: 2026-08-19
"""

from alembic import op


revision = "013_switch_currency_to_cop"
down_revision = "012_add_transaction_quantity"
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
