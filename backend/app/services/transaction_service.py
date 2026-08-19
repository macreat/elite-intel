from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.enums import TransactionSource, TransactionType
from app.models.transaction import Transaction
from app.repositories.category_repository import CategoryRepository
from app.repositories.transaction_repository import TransactionRepository
from app.schemas.transaction import TransactionCreate, TransactionUpdate
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

        model = Transaction(
            occurred_at=self._as_utc(payload.occurred_at),
            transaction_type=payload.transaction_type,
            category_id=payload.category_id,
            description=payload.description.strip(),
            amount=payload.amount,
            quantity=quantity,
            product_id=product_id,
            notes=payload.notes,
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
        return created

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
        if "amount" in payload.model_fields_set:
            model.amount = payload.amount
        if "quantity" in payload.model_fields_set:
            model.quantity = payload.quantity
        if "product_id" in payload.model_fields_set:
            model.product_id = payload.product_id
        if "notes" in payload.model_fields_set:
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
