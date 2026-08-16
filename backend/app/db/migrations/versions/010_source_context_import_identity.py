"""allow repeated source rows while protecting exact source-row replay

Revision ID: 010_source_context_identity
Revises: 009_unique_import_fingerprints
Create Date: 2026-08-13
"""

import hashlib

from alembic import op
from sqlalchemy import CHAR, Column, inspect, text


revision = "010_source_context_identity"
down_revision = "009_unique_import_fingerprints"
branch_labels = None
depends_on = None


def upgrade() -> None:
    connection = op.get_bind()
    if _constraint_exists(connection, "uq_transactions_record_fingerprint"):
        op.drop_constraint("uq_transactions_record_fingerprint", "transactions", type_="unique")
    op.add_column("transactions", Column("source_fingerprint", CHAR(64), nullable=True))

    rows = connection.execute(
        text(
            "SELECT id, import_batch_id, source_row_number FROM transactions "
            "WHERE import_batch_id IS NOT NULL AND source_row_number IS NOT NULL"
        )
    )
    for transaction_id, batch_id, source_row_number in rows:
        source_identity = f"legacy-batch:{batch_id}:{source_row_number}"
        source_fingerprint = hashlib.sha256(source_identity.encode("utf-8")).hexdigest()
        connection.execute(
            text("UPDATE transactions SET source_fingerprint = :source_fingerprint WHERE id = :transaction_id"),
            {"source_fingerprint": source_fingerprint, "transaction_id": transaction_id},
        )

    op.create_unique_constraint("uq_transactions_source_fingerprint", "transactions", ["source_fingerprint"])


def _constraint_exists(connection, constraint_name: str) -> bool:
    return any(
        constraint.get("name") == constraint_name
        for constraint in inspect(connection).get_unique_constraints("transactions")
    )


def downgrade() -> None:
    op.drop_constraint("uq_transactions_source_fingerprint", "transactions", type_="unique")
    op.drop_column("transactions", "source_fingerprint")
    op.create_unique_constraint("uq_transactions_record_fingerprint", "transactions", ["record_fingerprint"])
