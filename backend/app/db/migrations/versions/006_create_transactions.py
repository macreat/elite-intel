"""create transactions and indexes

Revision ID: 006_create_transactions
Revises: 005_create_import_rows
Create Date: 2026-08-12
"""

import sqlalchemy as sa
from alembic import op


revision = "006_create_transactions"
down_revision = "005_create_import_rows"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "transactions",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("source_date_raw", sa.String(length=50), nullable=True),
        sa.Column("transaction_type", sa.Enum("INCOME", "EXPENSE", name="transaction_type_enum", create_type=False), nullable=False),
        sa.Column("category_id", sa.BigInteger(), sa.ForeignKey("categories.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("category_name_raw", sa.String(length=150), nullable=True),
        sa.Column("description", sa.String(length=255), nullable=False),
        sa.Column("amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("currency_code", sa.String(length=3), nullable=False, server_default="ARS"),
        sa.Column("product_id", sa.BigInteger(), sa.ForeignKey("products.id", ondelete="RESTRICT"), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("source_type", sa.Enum("MANUAL", "CSV", "EXCEL", name="transaction_source_enum", create_type=False), nullable=False, server_default="MANUAL"),
        sa.Column("import_batch_id", sa.BigInteger(), sa.ForeignKey("import_batches.id"), nullable=True),
        sa.Column("source_row_number", sa.Integer(), nullable=True),
        sa.Column("record_fingerprint", sa.CHAR(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint("amount > 0", name="ck_transactions_amount_positive"),
    )
    op.create_index("idx_transactions_occurred_at", "transactions", ["occurred_at"])
    op.create_index("idx_transactions_type_occurred_at", "transactions", ["transaction_type", "occurred_at"])
    op.create_index("idx_transactions_category_id", "transactions", ["category_id"])
    op.create_index("idx_transactions_import_batch_id", "transactions", ["import_batch_id"])
    op.create_index("idx_transactions_fingerprint", "transactions", ["record_fingerprint"])


def downgrade() -> None:
    op.drop_index("idx_transactions_fingerprint", table_name="transactions")
    op.drop_index("idx_transactions_import_batch_id", table_name="transactions")
    op.drop_index("idx_transactions_category_id", table_name="transactions")
    op.drop_index("idx_transactions_type_occurred_at", table_name="transactions")
    op.drop_index("idx_transactions_occurred_at", table_name="transactions")
    op.drop_table("transactions")
