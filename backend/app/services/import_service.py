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
from app.services.business_rules import resolve_accesorios_amount
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
DOT_GROUPING_LOCALES = {"es_ar", "es_co"}
AMOUNT_TEXT_PATTERN = re.compile(r"^[+-]?\d[\d.,]*$")
AMOUNT_QUANTUM = Decimal("0.01")
MAX_AMOUNT_FRACTIONAL_DIGITS = 2
KARDEX_CATEGORY_ALIASES = {
    "ahorro mensual": "Ahorro mensual",
    "ahorro pagar": "Ahorro para pagar",
    "ahorro para pagar": "Ahorro para pagar",
    "salidas": "Salidas",
    # Column B volume → BeMovilRemote (KPI-excluded). Manual net gains use BeMovileIncome only.
    "be movil": "BeMovilRemote",
    "bemovilremote": "BeMovilRemote",
    "bemovileincome": "BeMovileIncome",
    "tigo": "Tigo",
    "fotocopias": "Fotocopias",
    "impresiones": "Impresiones",
    "scaner": "Escaneo",
    "papeleria": "Papelería",
    "papelería": "Papelería",
    "accesorios": "Accesorios",
    "internet": "Internet",
    "salida": "Salidas",
    "pendientes": "Pendientes",
    "total": "Otros",
    "totalday": "Otros",
}
KARDEX_HEADER_KEYS = frozenset(KARDEX_CATEGORY_ALIASES.keys())
# Total / TOTALDAY corner columns are validation-only — never stored as transactions.
# Be Movil (column B) is tracked as BeMovilRemote volume, not skipped.
KARDEX_SKIP_HEADERS = frozenset({"total", "totalday"})
KARDEX_COLUMN_CAP = 32
CSV_TEXT_ENCODINGS = ("utf-8", "cp1252")
_BEMOVIL_PLACEHOLDER_RE = re.compile(r"^0+(\.0+)?$")


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


def _normalize_path(path: str | Path) -> Path:
    """
    Normalize user-provided paths, handling backslashes and WSL/UNC-style paths.
    - Replace leading "\\wsl.localhost\\Ubuntu\\" with "/home/" and convert backslashes to forward slashes.
    - If a UNC/network path (\\\\host\\share) that cannot be mapped is provided, raise ValueError instructing upload.
    Returns a pathlib.Path.
    """
    if isinstance(path, Path):
        p = path
    else:
        p = Path(str(path))
    text = str(p)
    # Handle WSL UNC style: \\wsl.localhost\Ubuntu\...
    if text.startswith("\\\\wsl.localhost\\Ubuntu\\") or text.startswith(r"\\wsl.localhost\\Ubuntu\\"):
        # strip leading slashes and the known prefix
        # split on backslash to preserve remainder
        parts = text.split("\\")
        # parts like ['', '', 'wsl.localhost', 'Ubuntu', 'home', 'user', ...]
        try:
            tail_index = parts.index("Ubuntu") + 1
            tail = "/".join(parts[tail_index:])
        except ValueError:
            tail = "".join(parts[4:])
        tail = tail.lstrip("/")
        if tail.startswith("home/"):
            normalized = "/" + tail
        else:
            normalized = "/home/" + tail if tail else "/home"
        return Path(normalized)
    # If other UNC paths (start with \\) are provided, reject and ask for upload
    if text.startswith("\\\\"):
        raise ValueError("UNC or network paths are not supported. Please upload the file instead of providing a network path.")
    # Convert backslashes to forward slashes for simple Windows-style paths
    if "\\" in text:
        text = text.replace("\\", "/")
    return Path(text)


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
    digits_stripped = re.sub(r"\d+$", "", normalized)
    if digits_stripped and digits_stripped != normalized and digits_stripped in KARDEX_HEADER_KEYS:
        return digits_stripped
    return None


def _is_bemovil_column_placeholder(header: str) -> bool:
    """Real kardex.xlsx often stores column B title as 0 / 0.0 instead of 'Be Movil'."""
    raw = str(header or "").strip()
    if not raw:
        return True
    # Match before label-normalization: '.' becomes a space in _normalize_label.
    if _BEMOVIL_PLACEHOLDER_RE.fullmatch(raw):
        return True
    normalized = _normalize_label(raw)
    if not normalized:
        return True
    return bool(_BEMOVIL_PLACEHOLDER_RE.fullmatch(normalized.replace(" ", ".")))


def _resolve_kardex_header_key(index: int, head: str) -> str | None:
    header_key = _match_kardex_header(head)
    if header_key is not None:
        return header_key
    # Positional column B (index 1): Be Movil volume when title is blank/numeric placeholder.
    if index == 1 and _is_bemovil_column_placeholder(head):
        return "be movil"
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
        path = _normalize_path(path)
        if not path.exists():
            raise ValueError("File path does not exist. Please upload the file instead of providing a network/UNC path.")
        if source_type == "CSV":
            return self._detect_csv_columns(path)
        try:
            frame = pd.read_excel(path, header=None)
        except (TypeError, ValueError):
            return self._detect_csv_columns(path)
        trimmed_preview = [_trim_csv_row(row) for row in frame.head(50).fillna("").to_numpy().tolist()]
        if self._looks_like_kardex(trimmed_preview):
            return ["Fecha", "Tipo", "Categoría", "Descripción", "Valor"]
        return [str(c) for c in frame.columns]

    def _resolve_csv_encoding(self, path: Path) -> str:
        path = _normalize_path(path)
        if not path.exists():
            raise ValueError("File path does not exist. Please upload the file instead of providing a network/UNC path.")
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
        path = _normalize_path(path)
        if not path.exists():
            raise ValueError("File path does not exist. Please upload the file instead of providing a network/UNC path.")
        encoding = self._resolve_csv_encoding(path)
        with path.open("r", encoding=encoding, newline="") as handle:
            for row in csv.reader(handle):
                yield _trim_csv_row(row)

    def _detect_csv_columns(self, path: Path) -> list[str]:
        path = _normalize_path(path)
        if not path.exists():
            raise ValueError("File path does not exist. Please upload the file instead of providing a network/UNC path.")
        if self._csv_path_looks_like_kardex(path):
            return ["Fecha", "Tipo", "Categoría", "Descripción", "Valor"]
        for row in self._iter_trimmed_csv_rows(path):
            return row
        return []

    def _read_rows(self, path: Path, source_type: str) -> list[dict]:
        path = _normalize_path(path)
        if not path.exists():
            raise ValueError("File path does not exist. Please upload the file instead of providing a network/UNC path.")
        if source_type == "CSV":
            return self._read_csv_rows(path)
        try:
            frame = pd.read_excel(path, header=None)
        except (TypeError, ValueError):
            return self._read_csv_rows(path)
        frame = frame.fillna("")
        trimmed_rows = [_trim_csv_row(row) for row in frame.to_numpy().tolist()]
        if self._looks_like_kardex(trimmed_rows):
            return self._read_kardex_rows(trimmed_rows)
        return frame.to_dict(orient="records")

    def _read_csv_rows(self, path: Path) -> list[dict]:
        path = _normalize_path(path)
        if not path.exists():
            raise ValueError("File path does not exist. Please upload the file instead of providing a network/UNC path.")
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
        path = _normalize_path(path)
        if not path.exists():
            # If the path doesn't exist, treat it as not a kardex path rather than crashing
            return False
        try:
            return self._looks_like_kardex(list(self._iter_trimmed_csv_rows(path)))
        except UnicodeDecodeError as exc:
            raise ValidationDomainError("unable to decode CSV file") from exc

    def _looks_like_kardex(self, rows: list[list[str]]) -> bool:
        if not rows:
            return False
        flattened = [cell for row in rows for cell in row if cell]
        labels = [_normalize_label(cell) for cell in flattened]
        seen_ahorro = any("ahorro mensual" in label for label in labels)
        seen_be_movil = any("be movil" in label for label in labels)
        seen_sales = any(
            any(token in label for token in ("fotocopias", "accesorios", "impresiones", "papeleria", "papelería"))
            for label in labels
        )
        seen_total = any(label == "total" or label.startswith("total") for label in labels)
        # Layout signature covers xlsx where column B title is a numeric placeholder (0).
        return (seen_ahorro and seen_be_movil) or (seen_ahorro and seen_sales and seen_total)

    def _looks_like_kardex_frame(self, frame: pd.DataFrame) -> bool:
        trimmed_rows = [_trim_csv_row(row) for row in frame.fillna("").to_numpy().tolist()]
        return self._looks_like_kardex(trimmed_rows)

    def _read_kardex_rows(self, rows) -> list[dict]:
        """Parse the kardex pivot layout into flat transactions.

        Layout per day (date row, then a header row, then data rows, then a
        subtotal row that recapitulates each category's daily sum):
          - The per-day subtotal row is NOT a transaction and is dropped.
          - 'Total' / Total-day corner columns are ignored (validation-only).
          - Column B 'Be Movil' maps to BeMovilRemote volume tracking (excluded
            from normal income KPIs in dashboard summary / timeseries).
          - Accesorios gross is later converted to 40% profit on normalize/create.
          - Column semantics: sales columns are INCOME, savings/outflow
            columns (Pendientes, Ahorro para pagar, Salidas, Tigo, Ahorro
            mensual) are EXPENSE.
          - BeMovileIncome is never auto-derived here; humans enter it manually.
        """
        entries: list[dict] = []
        # Group rows by day, skipping blank rows and header rows.
        day_groups: list[tuple[str | None, list[list[str]]]] = []
        current_date: str | None = None
        current_group: list[list[str]] = []
        current_header: list[str] = []

        def _flush_group():
            nonlocal current_group, current_header
            if current_header and current_group:
                day_groups.append((current_date, current_header, current_group))
            current_group = []
            current_header = []

        for row in rows:
            if row is None:
                continue
            cells = _trim_csv_row(row)
            if not any(cells):
                continue
            if any(self._looks_like_date(cell) for cell in cells[:2]):
                _flush_group()
                current_date = next((cell for cell in cells if self._looks_like_date(cell)), None)
                current_header = []
                continue
            if not current_header and any(_match_kardex_header(cell) == "ahorro mensual" for cell in cells):
                _flush_group()
                current_header = cells
                continue
            if current_header:
                current_group.append(cells)

        _flush_group()

        for block_index, (day_date, header, group) in enumerate(day_groups):
            # Drop the per-day subtotal row for completed days. Every day block
            # except the last one in the file is a completed day (followed by
            # the next date); the final block is still open and has no corner.
            data_rows = group[:-1] if block_index < len(day_groups) - 1 else group

            # Columns from 'Total' / 'TOTALDAY' onward are corner/cumulative
            # columns (and a trailing running-total column on some days), never
            # transactions. Column B may be titled 0 / 0.0 instead of Be Movil.
            header_columns: list[tuple[int, str, str]] = []
            for index, head in enumerate(header):
                header_key = _resolve_kardex_header_key(index, head)
                if header_key in KARDEX_SKIP_HEADERS:
                    break
                if header_key is None:
                    continue
                header_columns.append((index, head, header_key))

            for cells in data_rows:
                for index, head, header_key in header_columns:
                    if index >= len(cells):
                        break
                    raw_value = cells[index]
                    if raw_value == "":
                        continue
                    label = KARDEX_CATEGORY_ALIASES.get(header_key, head or "Otros")
                    if header_key in {"salida", "salidas"}:
                        amounts = [
                            amount
                            for candidate in re.findall(r"[-+]?\d[\d.\s,]*\d|[-+]?\d", raw_value)
                            if (amount := self._parse_kardex_amount(candidate)) is not None and amount != 0
                        ]
                        if not amounts:
                            continue
                        description = raw_value.strip() or (head or label).strip() or "Otros"
                        for amount in amounts:
                            tx_type = self._infer_kardex_type(header_key, amount)
                            entries.append(
                                {
                                    "Fecha": self._format_kardex_date(day_date),
                                    "Tipo": tx_type.value,
                                    "Categoría": label,
                                    "Descripción": description,
                                    "Valor": str(abs(amount)),
                                }
                            )
                        continue
                    amount = self._parse_kardex_amount(raw_value)
                    if amount is None or amount == 0:
                        continue
                    tx_type = self._infer_kardex_type(header_key, amount)
                    description_label = (
                        label if header_key == "be movil" else ((head or label).strip() or "Otros")
                    )
                    description = f"{description_label} - {self._format_kardex_date(day_date)}"
                    entries.append(
                        {
                            "Fecha": self._format_kardex_date(day_date),
                            "Tipo": tx_type.value,
                            "Categoría": label,
                            "Descripción": description,
                            "Valor": str(abs(amount)),
                        }
                    )

        return entries

    def _infer_kardex_type(self, label: str, amount: Decimal) -> TransactionType:
        """Business rule: sales columns are INCOME; savings/outflow columns
        (Pendientes, Ahorro para pagar, Salidas, Tigo) are EXPENSE.
        Ahorro mensual is INCOME. Amount sign is ignored."""
        normalized = _normalize_label(label)
        if normalized in {
            "salida",
            "salidas",
            "ahorro pagar",
            "ahorro para pagar",
            "pendientes",
            "tigo",
        }:
            return TransactionType.EXPENSE
        return TransactionType.INCOME

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
        # Remove simple currency words like 'pesos' (case-insensitive)
        text = re.sub(r"(?i)\bpesos\b", "", text).strip()
        # If the text is a plain integer string like '250000', accept it as COP whole units
        if re.fullmatch(r"\d+", text):
            try:
                return Decimal(text).quantize(AMOUNT_QUANTUM)
            except InvalidOperation:
                return None
        # Fallback to older, more permissive parsing for other numeric formats
        match = re.search(r"[-+]?\d[\d.\s,]*\d|[-+]?\d", text)
        if not match:
            return None
        candidate = match.group(0).replace(" ", "")
        has_dot = "." in candidate
        has_comma = "," in candidate
        if has_dot and has_comma:
            last_pos = max(candidate.rfind("."), candidate.rfind(","))
            last_sep = candidate[last_pos]
            if len(candidate[last_pos + 1 :]) <= 2:
                if last_sep == ",":
                    candidate = candidate.replace(".", "").replace(",", ".")
                else:
                    candidate = candidate.replace(",", "")
            else:
                candidate = candidate.replace(".", "").replace(",", "")
        elif has_dot:
            last_pos = candidate.rfind(".")
            fractional = candidate[last_pos + 1 :]
            if len(fractional) == 3:
                candidate = candidate.replace(".", "")
            else:
                candidate = candidate[:last_pos].replace(".", "") + "." + fractional
        elif has_comma:
            last_pos = candidate.rfind(",")
            fractional = candidate[last_pos + 1 :]
            if len(fractional) == 3:
                candidate = candidate.replace(",", "")
            else:
                candidate = candidate[:last_pos].replace(",", "") + "." + fractional
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

            category_model = self.db.get(Category, category_id)
            category_name = category_model.name if category_model is not None else category_raw
            amount, notes = resolve_accesorios_amount(category_name, amount, notes)

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
