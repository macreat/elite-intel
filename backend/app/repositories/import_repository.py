from sqlalchemy import func, or_, select, text
from sqlalchemy.orm import Session

from app.models.enums import ImportRowStatus
from app.models.import_batch import ImportBatch, ImportRow
from app.models.transaction import Transaction


class ImportRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_batch(self, batch: ImportBatch) -> ImportBatch:
        self.db.add(batch)
        self.db.flush()
        self.db.refresh(batch)
        return batch

    def get_batch(self, batch_id: int) -> ImportBatch | None:
        return self.db.get(ImportBatch, batch_id)

    def get_batch_for_update(self, batch_id: int) -> ImportBatch | None:
        stmt = select(ImportBatch).where(ImportBatch.id == batch_id).with_for_update()
        return self.db.scalar(stmt)

    def list_batches(self) -> list[ImportBatch]:
        stmt = select(ImportBatch).order_by(ImportBatch.created_at.desc())
        return list(self.db.scalars(stmt).all())

    def add_rows(self, rows: list[ImportRow]) -> None:
        self.db.add_all(rows)
        self.db.flush()

    def list_rows(self, batch_id: int) -> list[ImportRow]:
        stmt = select(ImportRow).where(ImportRow.import_batch_id == batch_id).order_by(ImportRow.source_row_number)
        return list(self.db.scalars(stmt).all())

    def list_valid_rows(self, batch_id: int) -> list[ImportRow]:
        stmt = (
            select(ImportRow)
            .where(ImportRow.import_batch_id == batch_id, ImportRow.status == ImportRowStatus.VALID)
            .order_by(ImportRow.source_row_number)
        )
        return list(self.db.scalars(stmt).all())

    def fingerprint_exists(self, fingerprint: str) -> bool:
        stmt = select(func.count()).select_from(Transaction).where(Transaction.record_fingerprint == fingerprint)
        return int(self.db.scalar(stmt) or 0) > 0

    def lock_semantic_fingerprint(self, fingerprint: str) -> None:
        if self.db.bind is None or self.db.bind.dialect.name != "postgresql":
            return
        lock_key = int(fingerprint[:16], 16)
        if lock_key >= 2**63:
            lock_key -= 2**64
        self.db.execute(text("SELECT pg_advisory_xact_lock(:lock_key)"), {"lock_key": lock_key})

    def fingerprint_exists_for_other_batch(self, fingerprint: str, batch_id: int) -> bool:
        stmt = select(func.count()).select_from(Transaction).where(
            Transaction.record_fingerprint == fingerprint,
            or_(Transaction.import_batch_id.is_(None), Transaction.import_batch_id != batch_id),
        )
        return int(self.db.scalar(stmt) or 0) > 0

    def hash_exists(self, content_hash: str) -> bool:
        stmt = select(func.count()).select_from(ImportBatch).where(ImportBatch.content_hash == content_hash)
        return int(self.db.scalar(stmt) or 0) > 0
