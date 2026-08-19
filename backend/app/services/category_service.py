from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.category import Category
from app.models.enums import TransactionType
from app.repositories.category_repository import CategoryRepository
from app.schemas.category import CategoryCreate, CategoryUpdate
from app.services.errors import EntityNotFoundError, ValidationDomainError


class CategoryService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = CategoryRepository(db)

    def list(self, *, type_filter: TransactionType | None = None, active: bool | None = None):
        return self.repo.list(type_filter=type_filter, active=active)

    def _infer_type_from_name(self, name: str) -> TransactionType:
        normalized = name.strip().lower()
        # Business rule: only cash exits (salidas) and savings earmarked for payment (ahorro para pagar) are EXPENSE; everything else defaults to INCOME
        if 'salida' in normalized or 'ahorro para pagar' in normalized or 'ahorro pagar' in normalized:
            return TransactionType.EXPENSE
        return TransactionType.INCOME

    def create(self, payload: CategoryCreate):
        inferred_type = payload.type if payload.type is not None else self._infer_type_from_name(payload.name)
        model = Category(name=payload.name.strip(), type=inferred_type, description=payload.description)
        try:
            created = self.repo.create(model)
            self.db.commit()
            return created
        except IntegrityError as exc:
            self.db.rollback()
            raise ValidationDomainError("category already exists for this type") from exc

    def update(self, category_id: int, payload: CategoryUpdate):
        model = self.repo.get(category_id)
        if model is None:
            raise EntityNotFoundError("category not found")

        if payload.name is not None:
            model.name = payload.name.strip()
        if payload.description is not None:
            model.description = payload.description
        if payload.active is not None:
            model.active = payload.active

        try:
            updated = self.repo.update(model)
            self.db.commit()
            return updated
        except IntegrityError as exc:
            self.db.rollback()
            raise ValidationDomainError("category already exists for this type") from exc

    def soft_delete(self, category_id: int):
        model = self.repo.get(category_id)
        if model is None:
            raise EntityNotFoundError("category not found")
        model.active = False
        self.repo.update(model)
        self.db.commit()
