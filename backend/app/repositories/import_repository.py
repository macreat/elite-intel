from sqlalchemy import func, select
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

    def hash_exists(self, content_hash: str) -> bool:
        stmt = select(func.count()).select_from(ImportBatch).where(ImportBatch.content_hash == content_hash)
        return int(self.db.scalar(stmt) or 0) > 0
