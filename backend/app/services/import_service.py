import csv
import hashlib
import io
import json
import re
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import pandas as pd
from dateutil import parser as date_parser
from fastapi import UploadFile
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.enums import ImportRowStatus, ImportStatus, TransactionSource, TransactionType
from app.models.import_batch import ImportBatch, ImportRow
from app.models.product import Product
from app.repositories.category_repository import CategoryRepository
from app.repositories.import_repository import ImportRepository
from app.schemas.import_data import (
    ImportConfirmResponse,
    ImportInvalidRow,
    ImportMappingRequest,
    ImportMappingResponse,
    ImportMappingSummary,
    ImportPreviewRow,
    ImportUploadResponse,
)
from app.schemas.transaction import TransactionCreate
from app.services.errors import ImportStateError, ValidationDomainError
from app.services.transaction_service import TransactionService


HEADER_ALIASES = {
    "occurred_at": ["fecha", "date", "dia", "fecha y hora"],
    "transaction_type": ["tipo", "type", "movimiento", "ingreso/egreso"],
    "category": ["categoria", "categoría", "category", "rubro"],
    "description": ["descripcion", "descripción", "description", "detalle", "concepto"],
    "amount": ["valor", "amount", "monto", "importe", "precio"],
    "product": ["producto", "servicio", "producto/servicio"],
    "notes": ["notas", "observaciones", "comentario"],
}

TYPE_ALIASES = {
    "ingreso": TransactionType.INCOME,
    "entrada": TransactionType.INCOME,
    "venta": TransactionType.INCOME,
    "income": TransactionType.INCOME,
    "egreso": TransactionType.EXPENSE,
    "salida": TransactionType.EXPENSE,
    "gasto": TransactionType.EXPENSE,
    "expense": TransactionType.EXPENSE,
}

CSV_ONLY_ERROR_MESSAGE = "CSV-only import: upload a .csv file"
ALLOWED_CSV_EXTENSIONS = {".csv"}
ALLOWED_CSV_CONTENT_TYPES = {
    "text/csv",
    "application/csv",
    "application/vnd.ms-excel",
    "text/plain",
}
DOT_GROUPING_LOCALES = {"es_ar"}
AMOUNT_TEXT_PATTERN = re.compile(r"^[+-]?\d[\d.,]*$")
AMOUNT_QUANTUM = Decimal("0.01")
MAX_AMOUNT_FRACTIONAL_DIGITS = 2


def _canonical_utc_timestamp(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat(timespec="microseconds")


def _source_fingerprint(content_hash: str, source_row_number: int) -> str:
    source_identity = f"{content_hash}:{source_row_number}"
    return hashlib.sha256(source_identity.encode("utf-8")).hexdigest()


def _is_allowed_csv_extension(suffix: str) -> bool:
    return suffix in ALLOWED_CSV_EXTENSIONS


def _normalize_upload_content_type(content_type: str | None) -> str:
    return (content_type or "").lower().strip()


def _is_allowed_csv_content_type(content_type: str) -> bool:
    return not content_type or content_type in ALLOWED_CSV_CONTENT_TYPES


def _clean_import_value(value) -> str:
    return "" if value is None else str(value).strip()


def _normalize_header(header: str) -> str:
    return re.sub(r"\s+", " ", header.strip().lower())


class ImportService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = ImportRepository(db)
        self.categories = CategoryRepository(db)
        self.transactions = TransactionService(db)
        settings.IMPORT_STORAGE_DIR.mkdir(parents=True, exist_ok=True)

    async def upload_transactions(self, file: UploadFile) -> ImportUploadResponse:
        content = await file.read()
        if len(content) > settings.IMPORT_MAX_FILE_SIZE_MB * 1024 * 1024:
            raise ValidationDomainError("file too large")

        suffix = Path(file.filename or "import.csv").suffix.lower() or ".csv"
        self._validate_csv_upload(file=file, suffix=suffix)

        content_hash = hashlib.sha256(content).hexdigest()
        if self.repo.hash_exists(content_hash):
            raise ValidationDomainError("same file was already uploaded")

        storage_path = settings.IMPORT_STORAGE_DIR / f"{content_hash}{suffix}"
        storage_path.write_bytes(content)

        source_type = "CSV"

        columns = self._detect_columns(storage_path, source_type)
        mapping = self._suggest_mapping(columns)

        batch = ImportBatch(
            filename=file.filename or storage_path.name,
            source_type=source_type,
            content_hash=content_hash,
            mapping_json={},
            status=ImportStatus.PENDING,
            storage_path=str(storage_path),
            currency_assumption=settings.IMPORT_DEFAULT_CURRENCY,
        )
        self.repo.create_batch(batch)
        self.db.commit()

        return ImportUploadResponse(
            batch_id=batch.id,
            status=batch.status,
            columns_detected=columns,
            suggested_mapping=mapping,
        )

    def _validate_csv_upload(self, file: UploadFile, suffix: str) -> None:
        if not _is_allowed_csv_extension(suffix):
            raise ValidationDomainError(CSV_ONLY_ERROR_MESSAGE)

        content_type = _normalize_upload_content_type(file.content_type)
        if not _is_allowed_csv_content_type(content_type):
            raise ValidationDomainError(CSV_ONLY_ERROR_MESSAGE)

    def apply_mapping(self, batch_id: int, request: ImportMappingRequest) -> ImportMappingResponse:
        batch = self.repo.get_batch(batch_id)
        if batch is None:
            raise ImportStateError("batch not found")
        if batch.status not in {ImportStatus.PENDING, ImportStatus.VALIDATED}:
            raise ImportStateError("batch cannot be mapped in current status")

        rows = self._read_rows(Path(batch.storage_path), batch.source_type)
        core = ["occurred_at", "transaction_type", "category", "description", "amount"]
        for key in core:
            if key not in request.mapping:
                raise ValidationDomainError(f"missing required mapping field: {key}")

        status_rows: list[ImportRow] = []
        preview: list[ImportPreviewRow] = []
        invalids: list[ImportInvalidRow] = []
        category_map = self._category_index()
        dup_count = 0
        valid_count = 0
        invalid_count = 0

        # clear previous rows if remapping
        old_rows = self.repo.list_rows(batch_id)
        for old in old_rows:
            self.db.delete(old)
        self.db.flush()

        for idx, raw in enumerate(rows, start=1):
            result = self._normalize_row(raw, request.mapping, category_map)
            if result["ok"] is False:
                error_code = result["error_code"]
                message = result["message"]
                invalid_count += 1
                invalids.append(ImportInvalidRow(row_number=idx, error_code=error_code, message=message))
                status_rows.append(
                    ImportRow(
                        import_batch_id=batch_id,
                        source_row_number=idx,
                        raw_payload=raw,
                        normalized_payload=None,
                        status=ImportRowStatus.INVALID,
                        error_code=error_code,
                        error_message=message,
                    )
                )
                continue

            payload = result["payload"]
            fingerprint = result["fingerprint"]
            if self.repo.fingerprint_exists(fingerprint):
                dup_count += 1
                status_rows.append(
                    ImportRow(
                        import_batch_id=batch_id,
                        source_row_number=idx,
                        raw_payload=raw,
                        normalized_payload=payload,
                        record_fingerprint=fingerprint,
                        status=ImportRowStatus.DUPLICATE,
                        error_code="DUPLICATE",
                        error_message="Duplicate record",
                    )
                )
                continue

            valid_count += 1
            status_rows.append(
                ImportRow(
                    import_batch_id=batch_id,
                    source_row_number=idx,
                    raw_payload=raw,
                    normalized_payload=payload,
                    record_fingerprint=fingerprint,
                    status=ImportRowStatus.VALID,
                )
            )
            if len(preview) < 10:
                preview.append(ImportPreviewRow(**payload))

        self.repo.add_rows(status_rows)
        batch.mapping_json = request.mapping
        batch.status = ImportStatus.VALIDATED
        batch.records_total = len(rows)
        batch.records_valid = valid_count
        batch.records_invalid = invalid_count
        batch.records_duplicate = dup_count
        self.db.commit()

        return ImportMappingResponse(
            batch_id=batch_id,
            status=batch.status,
            summary=ImportMappingSummary(
                records_total=batch.records_total,
                records_valid=batch.records_valid,
                records_invalid=batch.records_invalid,
                records_duplicate=batch.records_duplicate,
            ),
            preview=preview,
            invalid_rows=invalids,
        )

    def confirm(self, batch_id: int) -> ImportConfirmResponse:
        batch = self.repo.get_batch_for_update(batch_id)
        if batch is None:
            raise ImportStateError("batch not found")
        if batch.status == ImportStatus.CONFIRMED:
            return ImportConfirmResponse(batch_id=batch_id, status=batch.status, records_inserted=batch.records_inserted)
        if batch.status != ImportStatus.VALIDATED:
            raise ImportStateError("batch must be VALIDATED before confirmation")

        valid_rows = self.repo.list_valid_rows(batch_id)
        inserted = 0
        try:
            for row in valid_rows:
                payload = row.normalized_payload or {}
                if row.record_fingerprint:
                    self.repo.lock_semantic_fingerprint(row.record_fingerprint)
                    if self.repo.fingerprint_exists_for_other_batch(row.record_fingerprint, batch_id):
                        self.db.rollback()
                        raise ImportStateError("equivalent transaction already exists; rolled back")
                tx_payload = TransactionCreate(**payload)
                tx = self.transactions.create(
                    tx_payload,
                    source_type=TransactionSource.CSV if batch.source_type == "CSV" else TransactionSource.EXCEL,
                    import_batch_id=batch_id,
                    source_row_number=row.source_row_number,
                    record_fingerprint=row.record_fingerprint,
                    source_fingerprint=_source_fingerprint(batch.content_hash, row.source_row_number),
                    auto_commit=False,
                )
                row.transaction_id = tx.id
                row.status = ImportRowStatus.INSERTED
                inserted += 1

            batch.status = ImportStatus.CONFIRMED
            batch.records_inserted = inserted
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            confirmed_batch = self.repo.get_batch(batch_id)
            if confirmed_batch is not None and confirmed_batch.status == ImportStatus.CONFIRMED:
                return ImportConfirmResponse(
                    batch_id=batch_id,
                    status=confirmed_batch.status,
                    records_inserted=confirmed_batch.records_inserted,
                )
            raise ImportStateError("import confirmation failed; rolled back") from exc
        except Exception as exc:
            self.db.rollback()
            raise ImportStateError("import confirmation failed; rolled back") from exc

        return ImportConfirmResponse(batch_id=batch_id, status=batch.status, records_inserted=inserted)

    def _detect_columns(self, path: Path, source_type: str) -> list[str]:
        if source_type == "CSV":
            for encoding in ("utf-8", "cp1252"):
                try:
                    with path.open("r", encoding=encoding, newline="") as f:
                        reader = csv.reader(f)
                        return next(reader)
                except UnicodeDecodeError:
                    continue
            raise ValidationDomainError("unable to decode CSV file")
        frame = pd.read_excel(path)
        return [str(c) for c in frame.columns]

    def _read_rows(self, path: Path, source_type: str) -> list[dict]:
        if source_type == "CSV":
            content = None
            for encoding in ("utf-8", "cp1252"):
                try:
                    content = path.read_text(encoding=encoding)
                    break
                except UnicodeDecodeError:
                    continue
            if content is None:
                raise ValidationDomainError("unable to decode CSV file")
            reader = csv.DictReader(io.StringIO(content))
            return [dict(row) for row in reader]
        frame = pd.read_excel(path)
        frame = frame.fillna("")
        return frame.to_dict(orient="records")

    def _suggest_mapping(self, columns: list[str]) -> dict[str, str]:
        mapping: dict[str, str] = {}
        normalized = {_normalize_header(col): col for col in columns}
        for canonical, aliases in HEADER_ALIASES.items():
            for alias in aliases:
                key = _normalize_header(alias)
                if key in normalized:
                    mapping[canonical] = normalized[key]
                    break
        return mapping

    def _category_index(self) -> dict[tuple[str, TransactionType], int]:
        result = {}
        for cat in self.categories.list(active=True):
            result[(cat.name.strip().lower(), cat.type)] = cat.id
        return result

    def _normalize_type(self, raw: str) -> TransactionType | None:
        value = raw.strip().upper()
        if value in {"INGRESO", "ENTRADA", "VENTA"}:
            return TransactionType.INCOME
        if value in {"EGRESO", "SALIDA", "GASTO"}:
            return TransactionType.EXPENSE
        if value in (TransactionType.INCOME.value, TransactionType.EXPENSE.value):
            return TransactionType(value)
        mapped = TYPE_ALIASES.get(raw.strip().lower())
        return mapped

    def _parse_amount(self, raw: str) -> Decimal:
        value = raw.strip()
        if not value or not AMOUNT_TEXT_PATTERN.fullmatch(value):
            raise ValidationDomainError("invalid amount")

        sign = "-" if value.startswith("-") else ""
        unsigned = value.lstrip("+-")
        locale = settings.IMPORT_DEFAULT_LOCALE.lower().replace("-", "_")
        decimal_separator = "," if locale in DOT_GROUPING_LOCALES else "."
        grouping_separator = "." if locale in DOT_GROUPING_LOCALES else ","

        def grouped_integer(text: str) -> bool:
            groups = text.split(grouping_separator)
            return len(groups) > 1 and 1 <= len(groups[0]) <= 3 and all(
                len(group) == 3 for group in groups[1:]
            )

        if decimal_separator in unsigned and grouping_separator in unsigned:
            if unsigned.count(decimal_separator) != 1:
                raise ValidationDomainError("invalid amount")
            integer, fraction = unsigned.rsplit(decimal_separator, 1)
            if not fraction or not grouped_integer(integer):
                raise ValidationDomainError("invalid amount")
            normalized = integer.replace(grouping_separator, "") + "." + fraction
        elif grouping_separator in unsigned:
            if grouped_integer(unsigned):
                normalized = unsigned.replace(grouping_separator, "")
            elif locale in DOT_GROUPING_LOCALES and unsigned.count(grouping_separator) == 1:
                integer, fraction = unsigned.split(grouping_separator)
                if not integer or not fraction or (len(fraction) == 3 and len(integer) <= 3):
                    raise ValidationDomainError("invalid amount")
                normalized = integer + "." + fraction
            else:
                raise ValidationDomainError("invalid amount")
        elif decimal_separator in unsigned:
            if unsigned.count(decimal_separator) != 1:
                raise ValidationDomainError("invalid amount")
            integer, fraction = unsigned.split(decimal_separator)
            if not integer or not fraction:
                raise ValidationDomainError("invalid amount")
            normalized = integer + "." + fraction
        else:
            normalized = unsigned

        cleaned = sign + normalized

        try:
            amount = Decimal(cleaned)
        except InvalidOperation as exc:
            raise ValidationDomainError("invalid amount") from exc
        if amount <= 0:
            raise ValidationDomainError("amount must be positive")
        if amount.as_tuple().exponent < -MAX_AMOUNT_FRACTIONAL_DIGITS:
            raise ValidationDomainError("amount has more than two fractional digits")
        return amount.quantize(AMOUNT_QUANTUM)

    def _parse_date(self, raw: str) -> datetime:
        try:
            parsed = date_parser.parse(str(raw), dayfirst=True)
            if parsed.tzinfo is not None:
                return parsed
            try:
                business_timezone = ZoneInfo(settings.IMPORT_DEFAULT_TIMEZONE)
            except ZoneInfoNotFoundError as exc:
                raise ValidationDomainError("invalid import timezone") from exc
            return parsed.replace(tzinfo=business_timezone)
        except (ValueError, TypeError) as exc:
            raise ValidationDomainError("invalid date") from exc

    def _normalize_row(self, raw: dict, mapping: dict[str, str], category_index: dict[tuple[str, TransactionType], int]):
        try:
            date_raw = _clean_import_value(raw.get(mapping["occurred_at"], ""))
            type_raw = _clean_import_value(raw.get(mapping["transaction_type"], ""))
            category_raw = _clean_import_value(raw.get(mapping["category"], ""))
            description = _clean_import_value(raw.get(mapping["description"], ""))
            amount_raw = _clean_import_value(raw.get(mapping["amount"], ""))
            product_raw = _clean_import_value(raw.get(mapping.get("product", ""), ""))
            notes = _clean_import_value(raw.get(mapping.get("notes", ""), "")) or None

            if not date_raw:
                return {"ok": False, "error_code": "MISSING_DATE", "message": "Missing date"}
            if not type_raw:
                return {"ok": False, "error_code": "MISSING_TYPE", "message": "Missing transaction type"}
            if not category_raw:
                return {"ok": False, "error_code": "MISSING_CATEGORY", "message": "Missing category"}
            if not description:
                return {"ok": False, "error_code": "MISSING_DESCRIPTION", "message": "Missing description"}
            if not amount_raw:
                return {"ok": False, "error_code": "MISSING_AMOUNT", "message": "Missing amount"}

            tx_type = self._normalize_type(type_raw)
            if tx_type is None:
                return {"ok": False, "error_code": "INVALID_TYPE", "message": "Invalid transaction type"}

            category_key = (category_raw.lower(), tx_type)
            category_id = category_index.get(category_key)
            if category_id is None:
                return {
                    "ok": False,
                    "error_code": "UNKNOWN_CATEGORY",
                    "message": "Unknown or type-incompatible category",
                }

            occurred_at = self._parse_date(date_raw)
            amount = self._parse_amount(amount_raw)

            product_id = int(product_raw) if product_raw.isdigit() else None
            if product_id is not None:
                product = self.db.get(Product, product_id)
                if product is None:
                    return {"ok": False, "error_code": "UNKNOWN_PRODUCT", "message": "Unknown product"}

            canonical_occurred_at = _canonical_utc_timestamp(occurred_at)
            payload = {
                "occurred_at": canonical_occurred_at,
                "transaction_type": tx_type.value,
                "category_id": category_id,
                "description": description,
                "amount": str(amount),
                "product_id": product_id,
                "notes": notes,
            }
            fingerprint = hashlib.sha256(
                json.dumps(
                    {
                        "occurred_at": canonical_occurred_at,
                        "transaction_type": payload["transaction_type"],
                        "category_id": category_id,
                        "description": description,
                        "amount": payload["amount"],
                        "currency_code": settings.IMPORT_DEFAULT_CURRENCY,
                        "product_id": product_id,
                    },
                    sort_keys=True,
                ).encode("utf-8")
            ).hexdigest()
            return {"ok": True, "payload": payload, "fingerprint": fingerprint}
        except ValidationDomainError as exc:
            message = str(exc)
            if "amount" in message and "positive" in message:
                return {"ok": False, "error_code": "NON_POSITIVE_AMOUNT", "message": "Amount must be positive"}
            if "amount" in message:
                return {"ok": False, "error_code": "INVALID_AMOUNT", "message": "Invalid amount"}
            if "date" in message:
                return {"ok": False, "error_code": "INVALID_DATE", "message": "Invalid date"}
            return {"ok": False, "error_code": "INVALID_ROW", "message": message}
