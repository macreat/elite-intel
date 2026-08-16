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
