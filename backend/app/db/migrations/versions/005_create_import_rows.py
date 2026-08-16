"""create import rows

Revision ID: 005_create_import_rows
Revises: 004_create_import_batches
Create Date: 2026-08-12
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision = "005_create_import_rows"
down_revision = "004_create_import_batches"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "import_rows",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("import_batch_id", sa.BigInteger(), sa.ForeignKey("import_batches.id", ondelete="CASCADE"), nullable=False),
        sa.Column("source_row_number", sa.Integer(), nullable=False),
        sa.Column("raw_payload", sa.JSON(), nullable=False),
        sa.Column("normalized_payload", sa.JSON(), nullable=True),
        sa.Column("record_fingerprint", sa.CHAR(length=64), nullable=True),
        sa.Column(
            "status",
            postgresql.ENUM("VALID", "INVALID", "DUPLICATE", "SUSPICIOUS", "INSERTED", name="import_row_status_enum", create_type=False),
            nullable=False,
        ),
        sa.Column("error_code", sa.String(length=50), nullable=True),
        sa.Column("error_message", sa.String(length=500), nullable=True),
        sa.Column("transaction_id", sa.BigInteger(), nullable=True),
    )
    op.create_index("idx_import_rows_batch", "import_rows", ["import_batch_id"])
    op.create_index("idx_import_rows_fingerprint", "import_rows", ["record_fingerprint"])


def downgrade() -> None:
    op.drop_index("idx_import_rows_fingerprint", table_name="import_rows")
    op.drop_index("idx_import_rows_batch", table_name="import_rows")
    op.drop_table("import_rows")
