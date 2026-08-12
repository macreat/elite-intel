"""create import batches

Revision ID: 004_create_import_batches
Revises: 003_create_products
Create Date: 2026-08-12
"""

import sqlalchemy as sa
from alembic import op


revision = "004_create_import_batches"
down_revision = "003_create_products"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "import_batches",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("source_type", sa.String(length=10), nullable=False),
        sa.Column("content_hash", sa.CHAR(length=64), nullable=False, unique=True),
        sa.Column("mapping_json", sa.JSON(), nullable=False),
        sa.Column("mapping_version", sa.String(length=20), nullable=False, server_default="v1"),
        sa.Column("parser_version", sa.String(length=20), nullable=False, server_default="v1"),
        sa.Column("currency_assumption", sa.String(length=3), nullable=False, server_default="ARS"),
        sa.Column("status", sa.Enum("PENDING", "VALIDATED", "CONFIRMED", "FAILED", name="import_status_enum", create_type=False), nullable=False),
        sa.Column("records_total", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("records_valid", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("records_invalid", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("records_duplicate", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("records_inserted", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("storage_path", sa.String(length=500), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )


def downgrade() -> None:
    op.drop_table("import_batches")
