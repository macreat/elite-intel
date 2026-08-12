import enum


class TransactionType(str, enum.Enum):
    INCOME = "INCOME"
    EXPENSE = "EXPENSE"


class TransactionSource(str, enum.Enum):
    MANUAL = "MANUAL"
    CSV = "CSV"
    EXCEL = "EXCEL"


class ImportStatus(str, enum.Enum):
    PENDING = "PENDING"
    VALIDATED = "VALIDATED"
    CONFIRMED = "CONFIRMED"
    FAILED = "FAILED"


class ImportRowStatus(str, enum.Enum):
    VALID = "VALID"
    INVALID = "INVALID"
    DUPLICATE = "DUPLICATE"
    SUSPICIOUS = "SUSPICIOUS"
    INSERTED = "INSERTED"
