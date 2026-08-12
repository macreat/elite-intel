from decimal import Decimal

from app.models.category import Category
from app.models.enums import TransactionType
from app.services.errors import CategoryTypeMismatchError, ValidationDomainError


def validate_positive_amount(amount: Decimal) -> None:
    if amount <= 0:
        raise ValidationDomainError("amount must be > 0")


def validate_category_for_type(category: Category, transaction_type: TransactionType) -> None:
    if not category.active:
        raise ValidationDomainError("category is inactive")
    if category.type != transaction_type:
        raise CategoryTypeMismatchError(
            f"Category '{category.name}' is not valid for {transaction_type.value} transactions."
        )
