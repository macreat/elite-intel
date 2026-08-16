"""create enums

Revision ID: 001_create_enums
Revises:
Create Date: 2026-08-12
"""

from alembic import op


revision = "001_create_enums"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE TYPE transaction_type_enum AS ENUM ('INCOME', 'EXPENSE')")
    op.execute("CREATE TYPE transaction_source_enum AS ENUM ('MANUAL', 'CSV', 'EXCEL')")
    op.execute("CREATE TYPE import_status_enum AS ENUM ('PENDING', 'VALIDATED', 'CONFIRMED', 'FAILED')")
    op.execute("CREATE TYPE import_row_status_enum AS ENUM ('VALID', 'INVALID', 'DUPLICATE', 'SUSPICIOUS', 'INSERTED')")


def downgrade() -> None:
    op.execute("DROP TYPE import_row_status_enum")
    op.execute("DROP TYPE import_status_enum")
    op.execute("DROP TYPE transaction_source_enum")
    op.execute("DROP TYPE transaction_type_enum")
