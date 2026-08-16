"""create categories with seed

Revision ID: 002_create_categories
Revises: 001_create_enums
Create Date: 2026-08-12
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision = "002_create_categories"
down_revision = "001_create_enums"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "categories",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("type", postgresql.ENUM("INCOME", "EXPENSE", name="transaction_type_enum", create_type=False), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("name", "type", name="uq_categories_name_type"),
    )
    op.create_index("idx_categories_type_active", "categories", ["type", "active"])

    income = [
        "Papelería",
        "Accesorios",
        "Internet",
        "Recargas",
        "Impresiones",
        "Fotocopias",
        "Escaneo",
        "Servicios digitales",
        "Otros",
    ]
    expense = ["Proveedores", "Servicios públicos", "Inventario", "Transporte", "Mantenimiento", "Otros"]

    for name in income:
        op.execute(
            sa.text(
                "INSERT INTO categories (name, type, active) VALUES (:name, 'INCOME', true) "
                "ON CONFLICT (name, type) DO NOTHING"
            ).bindparams(name=name)
        )
    for name in expense:
        op.execute(
            sa.text(
                "INSERT INTO categories (name, type, active) VALUES (:name, 'EXPENSE', true) "
                "ON CONFLICT (name, type) DO NOTHING"
            ).bindparams(name=name)
        )


def downgrade() -> None:
    op.drop_index("idx_categories_type_active", table_name="categories")
    op.drop_table("categories")
