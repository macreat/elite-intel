import csv
import hashlib
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
from app.models.category import Category
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

CSV_ONLY_ERROR_MESSAGE = "CSV/XLSX import: upload a .csv or .xlsx file"
ALLOWED_IMPORT_EXTENSIONS = {".csv", ".xlsx", ".xls"}
ALLOWED_IMPORT_CONTENT_TYPES = {
    "text/csv",
    "application/csv",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.template",
    "text/plain",
}
DOT_GROUPING_LOCALES = {"es_ar"}
AMOUNT_TEXT_PATTERN = re.compile(r"^[+-]?\d[\d.,]*$")
AMOUNT_QUANTUM = Decimal("0.01")
MAX_AMOUNT_FRACTIONAL_DIGITS = 2
KARDEX_CATEGORY_ALIASES = {
    "ahorro mensual": "Ahorro mensual",
    "ahorro pagar": "Ahorro pagar",
    "be movil": "Be Movil",
    "tigo": "Tigo",
    "fotocopias": "Fotocopias",
    "impresiones": "Impresiones",
    "scaner": "Escaneo",
    "papeleria": "Papelería",
    "papelería": "Papelería",
    "accesorios": "Accesorios",
    "internet": "Internet",
    "salida": "Otros",
    "pendientes": "Otros",
    "total": "Otros",
}
KARDEX_HEADER_KEYS = frozenset(KARDEX_CATEGORY_ALIASES.keys())
KARDEX_SKIP_HEADERS = frozenset({"pendientes", "total", "salida"})
KARDEX_COLUMN_CAP = 32
CSV_TEXT_ENCODINGS = ("utf-8", "cp1252")


def _canonical_utc_timestamp(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat(timespec="microseconds")


def _source_fingerprint(content_hash: str, source_row_number: int) -> str:
    source_identity = f"{content_hash}:{source_row_number}"
    return hashlib.sha256(source_identity.encode("utf-8")).hexdigest()


def _is_allowed_import_extension(suffix: str) -> bool:
    return suffix in ALLOWED_IMPORT_EXTENSIONS


def _normalize_upload_content_type(content_type: str | None) -> str:
    return (content_type or "").lower().strip()


def _is_allowed_import_content_type(content_type: str) -> bool:
    return not content_type or content_type in ALLOWED_IMPORT_CONTENT_TYPES


def _normalize_label(value: str) -> str:
    normalized = value.strip().lower()
    normalized = re.sub(r"[\u0300-\u036f]", "", normalized)
    normalized = re.sub(r"[^a-z0-9]+", " ", normalized)
    return " ".join(normalized.split())


def _clean_import_value(value) -> str:
    return "" if value is None else str(value).strip()


def _normalize_header(header: str) -> str:
    return re.sub(r"\s+", " ", header.strip().lower())


def _trim_csv_row(row) -> list[str]:
    cells = ["" if cell is None else str(cell).strip() for cell in row]
    while cells and cells[-1] == "":
        cells.pop()
    if len(cells) > KARDEX_COLUMN_CAP:
        cells = cells[:KARDEX_COLUMN_CAP]
    return cells


def _match_kardex_header(header: str) -> str | None:
    normalized = _normalize_label(header)
    if not normalized:
        return None
    if normalized in KARDEX_HEADER_KEYS:
        return normalized
    for key in KARDEX_HEADER_KEYS:
        if normalized.startswith(f"{key} "):
            return key
    return None


class ImportService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = ImportRepository(db)
        self.categories = CategoryRepository(db)
        self.transactions = TransactionService(db)
        settings.IMPORT_STORAGE_DIR.mkdir(parents=True, exist_ok=True)
        self._csv_encoding_cache: dict[str, str] = {}

    async def upload_transactions(self, file: UploadFile) -> ImportUploadResponse:
        content = await file.read()
        if len(content) > settings.IMPORT_MAX_FILE_SIZE_MB * 1024 * 1024:
            raise ValidationDomainError("file too large")

        suffix = Path(file.filename or "import.csv").suffix.lower() or ".csv"
        self._validate_import_upload(file=file, suffix=suffix)

        content_hash = hashlib.sha256(content).hexdigest()
        if self.repo.hash_exists(content_hash):
            raise ValidationDomainError("same file was already uploaded")

        storage_path = settings.IMPORT_STORAGE_DIR / f"{content_hash}{suffix}"
        storage_path.write_bytes(content)

        source_type = "CSV" if suffix in {".csv"} else "EXCEL"

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

    def _validate_import_upload(self, file: UploadFile, suffix: str) -> None:
        if not _is_allowed_import_extension(suffix):
            raise ValidationDomainError(CSV_ONLY_ERROR_MESSAGE)

        content_type = _normalize_upload_content_type(file.content_type)
        if not _is_allowed_import_content_type(content_type):
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
            # After DB commit, also persist inserted transactions to the CSV ledger
            try:
                for row in valid_rows:
                    if row.transaction_id:
                        try:
                            tx = self.transactions.get(row.transaction_id)
                            # TransactionService handles its own CSV append helper
                            if hasattr(self.transactions, "_append_to_persist_csv"):
                                try:
                                    self.transactions._append_to_persist_csv(tx)
                                except Exception:
                                    # CSV persistence failure should not block confirmation
                                    pass
                        except Exception:
                            # If fetching the transaction fails, skip it
                            continue
            except Exception:
                # Swallow any CSV persistence errors — DB commit is authoritative
                pass
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
            return self._detect_csv_columns(path)
        try:
            frame = pd.read_excel(path)
        except (TypeError, ValueError):
            return self._detect_csv_columns(path)
        trimmed_preview = [_trim_csv_row(row) for row in frame.head(50).fillna("").to_numpy().tolist()]
        if self._looks_like_kardex(trimmed_preview):
            return ["Fecha", "Tipo", "Categoría", "Descripción", "Valor"]
        return [str(c) for c in frame.columns]

    def _resolve_csv_encoding(self, path: Path) -> str:
        cache_key = str(path.resolve())
        cached = self._csv_encoding_cache.get(cache_key)
        if cached:
            return cached
        for encoding in CSV_TEXT_ENCODINGS:
            try:
                with path.open("r", encoding=encoding, newline="") as handle:
                    for _ in handle:
                        pass
                self._csv_encoding_cache[cache_key] = encoding
                return encoding
            except UnicodeDecodeError:
                continue
        raise ValidationDomainError("unable to decode CSV file")

    def _iter_trimmed_csv_rows(self, path: Path):
        encoding = self._resolve_csv_encoding(path)
        with path.open("r", encoding=encoding, newline="") as handle:
            for row in csv.reader(handle):
                yield _trim_csv_row(row)

    def _detect_csv_columns(self, path: Path) -> list[str]:
        if self._csv_path_looks_like_kardex(path):
            return ["Fecha", "Tipo", "Categoría", "Descripción", "Valor"]
        for row in self._iter_trimmed_csv_rows(path):
            return row
        return []

    def _read_rows(self, path: Path, source_type: str) -> list[dict]:
        if source_type == "CSV":
            return self._read_csv_rows(path)
        try:
            frame = pd.read_excel(path)
        except (TypeError, ValueError):
            return self._read_csv_rows(path)
        frame = frame.fillna("")
        trimmed_rows = [_trim_csv_row(row) for row in frame.to_numpy().tolist()]
        if self._looks_like_kardex(trimmed_rows):
            return self._read_kardex_rows(trimmed_rows)
        return frame.to_dict(orient="records")

    def _read_csv_rows(self, path: Path) -> list[dict]:
        if self._csv_path_looks_like_kardex(path):
            return self._read_kardex_rows(self._iter_trimmed_csv_rows(path))

        encoding = self._resolve_csv_encoding(path)
        with path.open("r", encoding=encoding, newline="") as handle:
            reader = csv.DictReader(handle)
            if reader.fieldnames is None:
                return []
            fieldnames = _trim_csv_row(reader.fieldnames)
            records: list[dict] = []
            for raw in reader:
                record = {
                    name: _clean_import_value(raw.get(name, ""))
                    for name in fieldnames
                    if name
                }
                if any(record.values()):
                    records.append(record)
            return records

    def _csv_path_looks_like_kardex(self, path: Path) -> bool:
        seen_ahorro = False
        seen_be_movil = False
        try:
            for row in self._iter_trimmed_csv_rows(path):
                for cell in row:
                    label = _normalize_label(cell)
                    if "ahorro mensual" in label:
                        seen_ahorro = True
                    if "be movil" in label:
                        seen_be_movil = True
                    if seen_ahorro and seen_be_movil:
                        return True
        except UnicodeDecodeError as exc:
            raise ValidationDomainError("unable to decode CSV file") from exc
        return False

    def _looks_like_kardex(self, rows: list[list[str]]) -> bool:
        if not rows:
            return False
        flattened = [cell for row in rows for cell in row if cell]
        seen_ahorro = any("ahorro mensual" in _normalize_label(cell) for cell in flattened)
        seen_be_movil = any("be movil" in _normalize_label(cell) for cell in flattened)
        return seen_ahorro and seen_be_movil

    def _looks_like_kardex_frame(self, frame: pd.DataFrame) -> bool:
        trimmed_rows = [_trim_csv_row(row) for row in frame.fillna("").to_numpy().tolist()]
        return self._looks_like_kardex(trimmed_rows)

    def _read_kardex_rows(self, rows) -> list[dict]:
        entries: list[dict] = []
        current_date = None
        current_header: list[str] = []

        for row in rows:
            if row is None:
                continue
            cells = _trim_csv_row(row)
            if not any(cells):
                continue
            if any(self._looks_like_date(cell) for cell in cells[:2]):
                current_date = next((cell for cell in cells if self._looks_like_date(cell)), None)
                continue
            if not current_date:
                continue
            if not current_header and any(_match_kardex_header(cell) == "ahorro mensual" for cell in cells):
                current_header = cells
                continue
            if not current_header:
                continue

            for index, header in enumerate(current_header):
                if index >= len(cells):
                    break
                header_key = _match_kardex_header(header)
                if header_key is None or header_key in KARDEX_SKIP_HEADERS:
                    continue
                raw_value = cells[index]
                if raw_value == "":
                    continue
                if header_key in {"ahorro mensual", "ahorro pagar"} and raw_value.lower() in {"nan", "none"}:
                    continue
                amount = self._parse_kardex_amount(raw_value)
                if amount is None or amount == 0:
                    continue
                label = KARDEX_CATEGORY_ALIASES.get(header_key, header or "Otros")
                tx_type = self._infer_kardex_type(header_key, amount)
                description_label = (header or label).strip() or "Otros"
                description = f"{description_label} - {current_date}"
                entries.append(
                    {
                        "Fecha": self._format_kardex_date(current_date),
                        "Tipo": tx_type.value,
                        "Categoría": label,
                        "Descripción": description,
                        "Valor": str(abs(amount)),
                    }
                )

        return entries

    def _infer_kardex_type(self, label: str, amount: Decimal) -> TransactionType:
        normalized = _normalize_label(label)
        if normalized in {"ahorro mensual", "ahorro pagar", "be movil", "tigo", "internet", "accesorios"}:
            return TransactionType.INCOME if amount > 0 else TransactionType.EXPENSE
        if normalized in {"fotocopias", "impresiones", "scaner", "papeleria", "salida"}:
            return TransactionType.EXPENSE
        return TransactionType.INCOME if amount > 0 else TransactionType.EXPENSE

    def _looks_like_date(self, value: str) -> bool:
        text = (value or "").strip()
        if not text or re.fullmatch(r"\d+", text):
            return False
        if "/" in text or "-" in text:
            try:
                date_parser.parse(text, dayfirst=False, yearfirst=False)
                return True
            except (TypeError, ValueError):
                try:
                    date_parser.parse(text, dayfirst=True)
                    return True
                except (TypeError, ValueError):
                    return False
        return False

    def _format_kardex_date(self, value: str) -> str:
        try:
            parsed = date_parser.parse(value, dayfirst=False, yearfirst=False)
        except (TypeError, ValueError):
            parsed = date_parser.parse(value, dayfirst=True)
        return parsed.strftime("%d/%m/%Y")

    def _parse_kardex_amount(self, raw: str) -> Decimal | None:
        if raw is None:
            return None
        text = str(raw).strip()
        if not text or text.lower() in {"nan", "none", "null"}:
            return None
        match = re.search(r"[-+]?\d[\d.\s,]*\d|[-+]?\d", text)
        if not match:
            return None
        candidate = match.group(0).replace(" ", "")
        if "," in candidate and "." in candidate:
            if candidate.rfind(",") > candidate.rfind("."):
                candidate = candidate.replace(".", "").replace(",", ".")
            else:
                candidate = candidate.replace(",", "")
        elif "," in candidate:
            if candidate.count(",") > 1 and len(candidate.split(",")[-1]) == 3:
                candidate = candidate.replace(",", "")
            else:
                candidate = candidate.replace(",", ".")
        try:
            value = Decimal(candidate)
        except InvalidOperation:
            return None
        if value == 0:
            return value
        return value.quantize(AMOUNT_QUANTUM)

    def _suggest_mapping(self, columns: list[str]) -> dict[str, str]:
        mapping: dict[str, str] = {}
        normalized = {_normalize_header(col): col for col in columns}
        for canonical, aliases in HEADER_ALIASES.items():
            for alias in aliases:
                key = _normalize_header(alias)
                if key in normalized:
                    mapping[canonical] = normalized[key]
                    break
        if not mapping and columns == ["Fecha", "Tipo", "Categoría", "Descripción", "Valor"]:
            mapping = {
                "occurred_at": "Fecha",
                "transaction_type": "Tipo",
                "category": "Categoría",
                "description": "Descripción",
                "amount": "Valor",
            }
        return mapping

    def _ensure_category_exists(self, category_name: str, transaction_type: TransactionType) -> str:
        name = (category_name or "Otros").strip()
        if not name:
            name = "Otros"
        normalized = _normalize_label(name)
        alias = KARDEX_CATEGORY_ALIASES.get(normalized, name)
        if not alias:
            alias = "Otros"

        existing = self.db.query(Category).filter(Category.name == alias, Category.type == transaction_type).first()
        if existing is not None:
            self.categories = CategoryRepository(self.db)
            return alias

        category = Category(name=alias, type=transaction_type, active=True)
        self.db.add(category)
        self.db.flush()
        self.categories = CategoryRepository(self.db)
        return alias

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
                fallback_name = self._ensure_category_exists(category_raw, tx_type)
                fallback_category = self.db.query(Category).filter(Category.name == fallback_name, Category.type == tx_type).first()
                category_id = fallback_category.id if fallback_category else None
                if category_id is None:
                    return {
                        "ok": False,
                        "error_code": "UNKNOWN_CATEGORY",
                        "message": "Unknown or type-incompatible category",
                    }
                category_index[(fallback_name.lower(), tx_type)] = category_id

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
