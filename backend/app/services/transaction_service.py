import csv
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.enums import TransactionSource, TransactionType
from app.models.transaction import Transaction
from app.repositories.category_repository import CategoryRepository
from app.repositories.transaction_repository import TransactionRepository
from app.schemas.transaction import TransactionCreate, TransactionUpdate
from app.services.errors import EntityNotFoundError
from app.services.validation import validate_category_for_type, validate_positive_amount


class TransactionService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = TransactionRepository(db)
        self.categories = CategoryRepository(db)

    def list(
        self,
        *,
        start_date: datetime | None,
        end_date: datetime | None,
        type_filter: TransactionType | None,
        category_id: int | None,
        search: str | None,
        page: int,
        page_size: int,
    ):
        return self.repo.list(
            start_date=start_date,
            end_date=end_date,
            type_filter=type_filter,
            category_id=category_id,
            search=search,
            page=page,
            page_size=page_size,
        )

    def get(self, transaction_id: int) -> Transaction:
        model = self.repo.get(transaction_id)
        if model is None:
            raise EntityNotFoundError("transaction not found")
        return model

    def create(
        self,
        payload: TransactionCreate,
        *,
        source_type: TransactionSource = TransactionSource.MANUAL,
        import_batch_id=None,
        source_row_number=None,
        record_fingerprint=None,
        source_fingerprint=None,
        auto_commit: bool = True,
    ):
        category = self.categories.get(payload.category_id)
        if category is None:
            raise EntityNotFoundError("category not found")

        validate_category_for_type(category, payload.transaction_type)
        validate_positive_amount(Decimal(payload.amount))

        model = Transaction(
            occurred_at=self._as_utc(payload.occurred_at),
            transaction_type=payload.transaction_type,
            category_id=payload.category_id,
            description=payload.description.strip(),
            amount=payload.amount,
            product_id=payload.product_id,
            notes=payload.notes,
            source_type=source_type,
            import_batch_id=import_batch_id,
            source_row_number=source_row_number,
            record_fingerprint=record_fingerprint,
            source_fingerprint=source_fingerprint,
        )
        created = self.repo.create(model)
        if auto_commit:
            self.db.commit()
            try:
                # Persist to CSV ledger when auto-committed (manual operations)
                self._append_to_persist_csv(created)
            except Exception:
                # Don't raise on CSV persistence failures; DB commit is authoritative
                pass
        return created

    def _append_to_persist_csv(self, model: Transaction) -> None:
        path: Path = Path(settings.PERSIST_TRANSACTIONS_CSV)
        path.parent.mkdir(parents=True, exist_ok=True)
        write_header = not path.exists()
        # Fetch category name for human-friendly CSV
        try:
            category = self.categories.get(model.category_id)
            category_name = category.name if category is not None else ""
        except Exception:
            category_name = ""
        row = [
            model.occurred_at.astimezone(timezone.utc).strftime("%d/%m/%Y") if model.occurred_at else "",
            model.transaction_type,
            category_name,
            model.description or "",
            str(model.amount) if model.amount is not None else "",
        ]
        with path.open("a", encoding="utf-8", newline="") as fh:
            writer = csv.writer(fh)
            if write_header:
                writer.writerow(["Fecha", "Tipo", "Categoría", "Descripción", "Valor"])
            writer.writerow(row)

    def update(self, transaction_id: int, payload: TransactionUpdate):
        model = self.get(transaction_id)

        next_type = payload.transaction_type or model.transaction_type
        next_category = payload.category_id or model.category_id
        category = self.categories.get(next_category)
        if category is None:
            raise EntityNotFoundError("category not found")

        validate_category_for_type(category, next_type)
        if payload.amount is not None:
            validate_positive_amount(Decimal(payload.amount))

        if "occurred_at" in payload.model_fields_set:
            model.occurred_at = self._as_utc(payload.occurred_at)
        if "transaction_type" in payload.model_fields_set:
            model.transaction_type = payload.transaction_type
        if "category_id" in payload.model_fields_set:
            model.category_id = payload.category_id
        if "description" in payload.model_fields_set:
            model.description = payload.description.strip()
        if "amount" in payload.model_fields_set:
            model.amount = payload.amount
        if "product_id" in payload.model_fields_set:
            model.product_id = payload.product_id
        if "notes" in payload.model_fields_set:
            model.notes = payload.notes

        updated = self.repo.update(model)
        self.db.commit()
        return updated

    def delete(self, transaction_id: int):
        model = self.get(transaction_id)
        self.repo.delete(model)
        self.db.commit()

    @staticmethod
    def _as_utc(value: datetime | None) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)
