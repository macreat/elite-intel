from decimal import Decimal


class DomainError(Exception):
    code = "DOMAIN_ERROR"

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class EntityNotFoundError(DomainError):
    code = "ENTITY_NOT_FOUND"


class CategoryTypeMismatchError(DomainError):
    code = "CATEGORY_TYPE_MISMATCH"


class ValidationDomainError(DomainError):
    code = "VALIDATION_ERROR"


class ImportStateError(DomainError):
    code = "IMPORT_STATE_ERROR"


class InsufficientStockError(DomainError):
    code = "INSUFFICIENT_STOCK"

    def __init__(self, product_id: int, requested: int, available: int | None):
        super().__init__(
            f"Insufficient stock for product {product_id}: requested {requested}, available {available}"
        )
        self.product_id = product_id
        self.requested = requested
        self.available = available
