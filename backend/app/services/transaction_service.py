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
from app.services.business_rules import (
    is_kpi_excluded_income_category,
    resolve_accesorios_amount,
)
from app.services.errors import EntityNotFoundError, InsufficientStockError
from app.services.product_service import ProductService
from app.services.validation import validate_category_for_type, validate_positive_amount


class TransactionService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = TransactionRepository(db)
        self.categories = CategoryRepository(db)
        self.products = ProductService(db)

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

        quantity = payload.quantity
        product_id = payload.product_id

        amount, notes = resolve_accesorios_amount(category.name, Decimal(payload.amount), payload.notes)

        model = Transaction(
            occurred_at=self._as_utc(payload.occurred_at),
            transaction_type=payload.transaction_type,
            category_id=payload.category_id,
            description=payload.description.strip(),
            amount=amount,
            quantity=quantity,
            product_id=product_id,
            notes=notes,
            source_type=source_type,
            import_batch_id=import_batch_id,
            source_row_number=source_row_number,
            record_fingerprint=record_fingerprint,
            source_fingerprint=source_fingerprint,
        )
        created = self.repo.create(model)

        if product_id is not None:
            self._adjust_stock_on_create(product_id, payload.transaction_type, quantity)

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

        # Compute running balance: read previous balance if present, otherwise compute from file
        prev_balance = Decimal("0.00")
        last_row = None
        if path.exists():
            try:
                with path.open("r", encoding="utf-8", newline="") as rf:
                    reader = csv.DictReader(rf)
                    for last_row in reader:
                        pass
                    # If header includes RunningBalance, prefer it
                    if last_row and "RunningBalance" in reader.fieldnames:
                        try:
                            prev_balance = Decimal(last_row.get("RunningBalance") or "0").quantize(Decimal("0.01"))
                        except Exception:
                            prev_balance = Decimal("0.00")
                    else:
                        # Recompute by summing rows (best-effort); skip BeMovilRemote volume.
                        rf.seek(0)
                        running = Decimal("0.00")
                        for r in csv.DictReader(rf):
                            cat = (r.get("Categoría") or r.get("Categoria") or "").strip()
                            if is_kpi_excluded_income_category(cat):
                                continue
                            try:
                                amt = Decimal(r.get("Valor") or r.get("Valor ") or "0")
                            except Exception:
                                amt = Decimal("0.00")
                            ttype = r.get("Tipo") or ""
                            if ttype == TransactionType.INCOME.value:
                                running += amt
                            else:
                                running -= amt
                        prev_balance = running
            except Exception:
                prev_balance = Decimal("0.00")

        # Determine sign for current transaction (BeMovilRemote does not move net balance)
        try:
            amount = Decimal(str(model.amount))
        except Exception:
            amount = Decimal("0.00")
        if is_kpi_excluded_income_category(category_name):
            curr = prev_balance
        else:
            curr = prev_balance + (amount if model.transaction_type == TransactionType.INCOME.value else -amount)
        curr = curr.quantize(Decimal("0.01"))
        # Annotate model instance with running_balance for downstream consumers (not persisted to DB)
        try:
            setattr(model, "running_balance", curr)
        except Exception:
            pass

        row = [
            model.occurred_at.astimezone(timezone.utc).strftime("%d/%m/%Y") if model.occurred_at else "",
            model.transaction_type,
            category_name,
            model.description or "",
            str(model.amount) if model.amount is not None else "",
            str(curr),
        ]
        with path.open("a", encoding="utf-8", newline="") as fh:
            writer = csv.writer(fh)
            if write_header:
                writer.writerow(["Fecha", "Tipo", "Categoría", "Descripción", "Valor", "RunningBalance"])
            writer.writerow(row)
        # TODO: Persisting running balance to DB requires schema changes; for now we persist to CSV ledger and attach to returned model

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

        old_product_id = model.product_id
        old_type = model.transaction_type
        old_quantity = model.quantity

        new_product_id = payload.product_id if "product_id" in payload.model_fields_set else old_product_id
        new_type = payload.transaction_type if "transaction_type" in payload.model_fields_set else old_type
        new_quantity = payload.quantity if "quantity" in payload.model_fields_set else old_quantity

        if "occurred_at" in payload.model_fields_set:
            model.occurred_at = self._as_utc(payload.occurred_at)
        if "transaction_type" in payload.model_fields_set:
            model.transaction_type = payload.transaction_type
        if "category_id" in payload.model_fields_set:
            model.category_id = payload.category_id
        if "description" in payload.model_fields_set:
            model.description = payload.description.strip()
        if "quantity" in payload.model_fields_set:
            model.quantity = payload.quantity
        if "product_id" in payload.model_fields_set:
            model.product_id = payload.product_id

        # Resolve Accesorios 40% after category/amount/notes fields are known.
        next_notes = payload.notes if "notes" in payload.model_fields_set else model.notes
        if "amount" in payload.model_fields_set or "category_id" in payload.model_fields_set:
            raw_amount = Decimal(payload.amount) if "amount" in payload.model_fields_set else Decimal(model.amount)
            resolved_amount, resolved_notes = resolve_accesorios_amount(category.name, raw_amount, next_notes)
            model.amount = resolved_amount
            model.notes = resolved_notes
        elif "notes" in payload.model_fields_set:
            model.notes = payload.notes

        self._adjust_stock_on_update(
            old_product_id=old_product_id,
            old_type=old_type,
            old_quantity=old_quantity,
            new_product_id=new_product_id,
            new_type=new_type,
            new_quantity=new_quantity,
        )

        updated = self.repo.update(model)
        self.db.commit()
        return updated

    def delete(self, transaction_id: int):
        model = self.get(transaction_id)
        if model.product_id is not None:
            self._reverse_stock(model.product_id, model.transaction_type, model.quantity)
        self.repo.delete(model)
        self.db.commit()

    def _adjust_stock_on_create(self, product_id: int, transaction_type: TransactionType, quantity: int):
        product = self.products.get(product_id)
        if product is None:
            raise EntityNotFoundError("product not found")

        if product.stock_qty is None:
            product.stock_qty = 0

        if transaction_type == TransactionType.EXPENSE:
            product.stock_qty += quantity
        elif transaction_type == TransactionType.INCOME:
            if product.stock_qty < quantity:
                raise InsufficientStockError(product_id, quantity, product.stock_qty)
            product.stock_qty -= quantity

    def _adjust_stock_on_update(
        self,
        *,
        old_product_id: int | None,
        old_type: TransactionType,
        old_quantity: int,
        new_product_id: int | None,
        new_type: TransactionType,
        new_quantity: int,
    ):
        if old_product_id is not None:
            self._reverse_stock(old_product_id, old_type, old_quantity)

        if new_product_id is not None:
            self._apply_stock(new_product_id, new_type, new_quantity)

    def _reverse_stock(self, product_id: int, transaction_type: TransactionType, quantity: int):
        product = self.products.get(product_id)
        if product is None:
            raise EntityNotFoundError("product not found")

        if product.stock_qty is None:
            product.stock_qty = 0

        if transaction_type == TransactionType.EXPENSE:
            product.stock_qty -= quantity
        elif transaction_type == TransactionType.INCOME:
            product.stock_qty += quantity

    def _apply_stock(self, product_id: int, transaction_type: TransactionType, quantity: int):
        product = self.products.get(product_id)
        if product is None:
            raise EntityNotFoundError("product not found")

        if product.stock_qty is None:
            product.stock_qty = 0

        if transaction_type == TransactionType.EXPENSE:
            product.stock_qty += quantity
        elif transaction_type == TransactionType.INCOME:
            if product.stock_qty < quantity:
                raise InsufficientStockError(product_id, quantity, product.stock_qty)
            product.stock_qty -= quantity

    @staticmethod
    def _as_utc(value: datetime | None) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)
