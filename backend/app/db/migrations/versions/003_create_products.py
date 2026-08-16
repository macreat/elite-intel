"""create products

Revision ID: 003_create_products
Revises: 002_create_categories
Create Date: 2026-08-12
"""

import sqlalchemy as sa
from alembic import op


revision = "003_create_products"
down_revision = "002_create_categories"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "products",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("category_id", sa.BigInteger(), sa.ForeignKey("categories.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("idx_products_category_id", "products", ["category_id"])


def downgrade() -> None:
    op.drop_index("idx_products_category_id", table_name="products")
    op.drop_table("products")
