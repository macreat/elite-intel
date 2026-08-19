"""Add quantity column to transactions

Revision ID: 012_add_transaction_quantity
Revises: 011_catalog_product_prices
Create Date: 2026-08-19
"""

from alembic import op
import sqlalchemy as sa


revision = "012_add_transaction_quantity"
down_revision = "011_catalog_product_prices"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("transactions", sa.Column("quantity", sa.Integer(), nullable=False, server_default="1"))


def downgrade() -> None:
    op.drop_column("transactions", "quantity")
