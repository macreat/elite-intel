"""Add product price catalog columns

Revision ID: 011_catalog_product_prices
Revises: 010_source_context_identity
Create Date: 2026-08-19
"""

from alembic import op
import sqlalchemy as sa


revision = "011_catalog_product_prices"
down_revision = "010_source_context_identity"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("products", sa.Column("invoice_price", sa.Numeric(14, 2), nullable=True))
    op.add_column("products", sa.Column("local_price", sa.Numeric(14, 2), nullable=True))
    op.add_column("products", sa.Column("currency_code", sa.String(3), nullable=False, server_default="COP"))
    op.add_column("products", sa.Column("stock_qty", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("products", "stock_qty")
    op.drop_column("products", "currency_code")
    op.drop_column("products", "local_price")
    op.drop_column("products", "invoice_price")
