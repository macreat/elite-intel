"""seed BeMovilRemote + BeMovileIncome categories

Revision ID: 014_bemovil_categories
Revises: 013_switch_currency_to_cop
Create Date: 2026-08-20
"""

import sqlalchemy as sa
from alembic import op


revision = "014_bemovil_categories"
down_revision = "013_switch_currency_to_cop"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Rename legacy "Be Movil" (manual-era label) to BeMovileIncome when present.
    op.execute(
        sa.text(
            "UPDATE categories SET name = 'BeMovileIncome' "
            "WHERE name = 'Be Movil' AND type = 'INCOME' "
            "AND NOT EXISTS ("
            "  SELECT 1 FROM categories c2 "
            "  WHERE c2.name = 'BeMovileIncome' AND c2.type = 'INCOME'"
            ")"
        )
    )
    for name in ("BeMovilRemote", "BeMovileIncome"):
        op.execute(
            sa.text(
                "INSERT INTO categories (name, type, active) VALUES (:name, 'INCOME', true) "
                "ON CONFLICT (name, type) DO NOTHING"
            ).bindparams(name=name)
        )


def downgrade() -> None:
    op.execute(
        sa.text(
            "UPDATE categories SET name = 'Be Movil' "
            "WHERE name = 'BeMovileIncome' AND type = 'INCOME' "
            "AND NOT EXISTS ("
            "  SELECT 1 FROM categories c2 "
            "  WHERE c2.name = 'Be Movil' AND c2.type = 'INCOME'"
            ")"
        )
    )
    op.execute(sa.text("DELETE FROM categories WHERE name = 'BeMovilRemote' AND type = 'INCOME'"))
