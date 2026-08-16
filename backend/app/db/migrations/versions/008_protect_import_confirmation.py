"""protect import confirmation from duplicate row inserts

Revision ID: 008_protect_import_confirmation
Revises: 007_enable_pg_trgm
Create Date: 2026-08-12
"""

from alembic import op
from sqlalchemy import text


revision = "008_protect_import_confirmation"
down_revision = "007_enable_pg_trgm"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Historical confirmation races could create multiple transactions for one
    # imported source row. Keep the earliest persisted created_at value as the
    # canonical record, use id as a deterministic tie-breaker, rewire
    # import_rows to it, and remove only the later duplicates. This is an
    # intentional data decision: the earliest committed row wins so the
    # cleanup preserves one complete transaction.
    #
    # Do not deduplicate record_fingerprint here. A semantic fingerprint is
    # allowed to repeat in distinct source contexts, and revision 010 changes
    # the identity model after this compatibility revision.
    _deduplicate_import_transactions(op.get_bind())
    op.create_unique_constraint(
        "uq_transactions_import_batch_row",
        "transactions",
        ["import_batch_id", "source_row_number"],
    )


def _deduplicate_import_transactions(connection) -> None:
    _deduplicate_by_key(
        connection,
        key_columns=("import_batch_id", "source_row_number"),
        where_clause="import_batch_id IS NOT NULL AND source_row_number IS NOT NULL",
    )


def _deduplicate_by_key(connection, *, key_columns: tuple[str, ...], where_clause: str) -> None:
    columns = ", ".join(key_columns)
    order = ", ".join((*key_columns, "created_at", "id"))
    result = connection.execute(
        text(
            f"SELECT id, {columns} FROM transactions "
            f"WHERE {where_clause} ORDER BY {order}"
        )
    )

    canonical_ids: dict[tuple[object, ...], int] = {}
    for row in result:
        transaction_id = row[0]
        key = tuple(row[index + 1] for index in range(len(key_columns)))
        canonical_id = canonical_ids.setdefault(key, transaction_id)
        if transaction_id == canonical_id:
            continue

        connection.execute(
            text(
                "UPDATE import_rows SET transaction_id = :canonical_id "
                "WHERE transaction_id = :duplicate_id"
            ),
            {"canonical_id": canonical_id, "duplicate_id": transaction_id},
        )
        connection.execute(
            text("DELETE FROM transactions WHERE id = :duplicate_id"),
            {"duplicate_id": transaction_id},
        )


def downgrade() -> None:
    op.drop_constraint("uq_transactions_import_batch_row", "transactions", type_="unique")
