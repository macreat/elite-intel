# Data Strategy for the MVP

This document defines the data contract and import strategy for the Business Operations & Analytics Dashboard MVP. It is aligned with SPEC.md sections 10, 11, 15, 16, 17, 18, and 19.

## Current data reality

The repository currently contains **no real source data files**. `data/raw`, `data/imports`, and `data/processed` contain only README files and `.gitkeep` placeholders. The strategy therefore targets expected Spanish-language CSV and Excel exports with columns such as `Fecha`, `Tipo`, `Categoría`, `Descripción`, and `Valor`.

`data/raw` is the immutable source archive. Runtime staging is persisted below the configured `IMPORT_STORAGE_DIR` volume so pending and validated batches survive backend container recreation. `data/processed` is for validated, standardized analytical extracts; neither staging nor processed output replaces the original source.

## 1. Canonical transaction model review

The transaction model in SPEC section 10 is a sound MVP starting point, but the following additions are required to keep it auditable and ML-ready:

| Field | Recommendation | Purpose |
|---|---|---|
| `id` | Stable UUID (or equivalent immutable database identifier) | Avoid using row numbers, descriptions, or category names as identity. |
| `occurred_at` | Timestamp with timezone when available; retain the source date/time precision | Preserve the business event time for ordering, day-of-week, seasonality, and timezone-safe analysis. |
| `source_date_raw` | Original date text/value as received | Permit audit and re-parsing when a source format is misunderstood. |
| `transaction_type` | Controlled value: `INCOME` or `EXPENSE` | Prevent inconsistent labels and support signed analytical measures. |
| `category_id` | Foreign key to `Category`; category names remain mutable display data | Preserve referential integrity when names are normalized or renamed. |
| `category_name_raw` | Original category label for imported records | Explain normalization decisions and support mapping corrections. |
| `description` | Original description, nullable only if the source has none | Retain useful text for search and future classification. |
| `amount_original` | Decimal value after lossless parsing, in source currency | Preserve the source monetary value. Never use binary floating point for money. |
| `amount_normalized` | Canonical positive decimal amount | Make aggregation consistent; transaction type determines income versus expense. |
| `currency_code` | ISO-like code, defaulted only by explicit business configuration | Avoid silently mixing currencies. |
| `product_id` | Nullable stable foreign key | Enable later product/service demand and profitability analysis. |
| `notes` | Nullable text | Preserve context that may explain anomalies. |
| `import_batch_id` | Nullable FK for imported records; required for imports | Trace every imported transaction to its source and validation result. |
| `source_row_number` | Original spreadsheet/CSV row number | Make invalid-row reports and audits actionable. |
| `record_fingerprint` | Deterministic hash of source identity fields | Support idempotency and duplicate detection. |
| `created_at`, `updated_at` | UTC timestamps managed by the application | Distinguish event time from ingestion and edit time. |

### Modeling decisions

- Store monetary values as fixed-precision decimals, not floats. Keep amounts positive in the transaction record; `transaction_type` supplies semantic direction. If signed values are later needed, derive them rather than replacing the source amount.
- Preserve both original and canonical representations for dates, categories, descriptions where relevant, and amounts. Normalization must be reversible or explainable.
- Add `ImportBatch` fields beyond SPEC section 10: immutable source filename, source type, content hash, storage reference, import timestamp, parser version, mapping version, currency assumption, status, totals, and error-report reference.
- Consider an `ImportRow`/quarantine table for every source row. It should store batch ID, source row number, raw row payload, normalized candidate payload, validation status, duplicate status, and error codes. This is preferable to discarding rejected data.
- Category and product relationships use IDs. Names are labels, not keys. Category uniqueness should be scoped by transaction type or represented by a canonical category taxonomy.
- Preserve provenance on manually entered records with a source type such as `MANUAL`; imported records use `CSV` or `EXCEL`.

## 2. CSV/Excel import pipeline

The pipeline is deliberately staged and never trains models directly from an unvalidated file:

```text
Upload -> immutable staging copy -> inspect -> map -> validate
       -> normalize -> deduplicate -> preview -> confirm
       -> persist valid records + quarantine invalid rows -> report
```

### File handling and source preservation

1. Copy the upload to a unique staging object without changing its bytes; calculate a SHA-256 content hash.
2. Record filename, extension, size, hash, uploader/context, received timestamp, and parser version in `ImportBatch`.
3. Read CSV with encoding detection (UTF-8 first, then a documented fallback such as Windows-1252) and delimiter detection. Read Excel worksheets without saving back to the workbook.
4. Do not overwrite, reformat, rename in place, or write into the uploaded source. The original source remains untouched in `data/raw` or the immutable staging store.
5. Generate normalized output separately in `data/processed` or the database after confirmation.

### Import identity contract

`record_fingerprint` is a semantic fingerprint of the normalized transaction payload, including the canonical UTC instant, type, category, description, amount, currency, and product.

Semantic fingerprints are duplicate candidates across different source batches, but are not unique by themselves because repeated rows in one source file may be legitimate separate transactions.

`source_fingerprint` is the exact source-row identity derived from the upload content hash and source row number.

Source fingerprints are unique and protect replay or concurrent confirmation of one source row without collapsing distinct rows from the same source.

The content-hash uniqueness rule rejects an exact file re-upload.

Confirmation serializes semantic checks across source batches and rolls back the entire batch when an equivalent real transaction already exists in another source context.

### Column detection and source mapping

Detection is case-insensitive, accent-insensitive, and whitespace-insensitive after creating a comparison key. It must retain the original header text for audit. Suggested aliases:

| Canonical field | Expected aliases |
|---|---|
| `occurred_at` | `Fecha`, `fecha`, `Date`, `Día`, `Fecha y hora` |
| `transaction_type` | `Tipo`, `tipo`, `Type`, `Movimiento`, `Ingreso/Egreso` |
| `category` | `Categoría`, `categoria`, `Category`, `Rubro` |
| `description` | `Descripción`, `descripcion`, `Description`, `Detalle`, `Concepto` |
| `amount` | `Valor`, `valor`, `Amount`, `Monto`, `Importe`, `Precio` |
| `product` | `Producto`, `Servicio`, `Producto/Servicio` |
| `notes` | `Notas`, `Observaciones`, `Comentario` |

- Require an explicit or confidently detected mapping for the five core fields. Never silently guess between two ambiguous columns.
- If multiple worksheets exist, inspect each sheet and require the operator to choose or confirm the transaction sheet.
- Show the mapping and sample rows in the preview. Store the accepted mapping JSON and mapping version on `ImportBatch`.
- Permit a user-supplied mapping when headers are absent or unusual; still validate the resulting canonical fields.

### Validation rules

Validation produces stable error codes and row-level messages. Invalid rows are not silently inserted.

**Required fields:** date, transaction type, category, description (unless an explicitly approved source lacks it), and amount. Empty strings count as missing after trimming.

**Types and values:**

- Date must parse as a real calendar date; reject impossible dates and ambiguous dates unless the selected locale/format resolves them. Preserve date-only values without inventing a time; use a configured business timezone.
- Transaction type must normalize to `INCOME` or `EXPENSE`; reject unknown values rather than treating them as income.
- Category must resolve to an active canonical category compatible with the transaction type. Unknown categories are quarantined or explicitly approved as new categories; they are never auto-created from a typo.
- Amount must be numeric, finite, strictly greater than zero, and within configured business bounds. Zero and negative values are rejected for this model; refunds/adjustments require an explicit future transaction type or documented policy.
- Description must be trimmed and bounded in length; preserve the original text separately when normalization changes it.
- Product/service identifiers are optional in MVP, but missing identifiers are a data-quality warning, not a reason to invent one.
- Reject rows with excessive extra columns only after reporting them; preserve their raw payload for diagnosis.

### Normalization rules

Normalize only the canonical copy and retain the raw source value.

- Trim leading/trailing whitespace, collapse repeated internal whitespace where safe, and normalize Unicode for comparison.
- Category matching is accent-insensitive and case-insensitive, then uses an explicit alias dictionary. For example, `fotocopia`, `Fotocopias`, `FOTOCOPIA`, and `copias` map to canonical **Fotocopias**. Do not use fuzzy matching without an operator-visible review because an incorrect category changes business metrics.
- Normalize transaction aliases such as `ingreso`, `entrada`, `venta` to `INCOME`, and `egreso`, `salida`, `gasto` to `EXPENSE` only through an explicit, versioned mapping.
- Parse dates using the selected locale and supported formats (`DD/MM/YYYY`, `D/M/YYYY`, ISO `YYYY-MM-DD`, and Excel serial dates). Reject ambiguous values such as `01/02/2026` when locale is unknown. Store the canonical timestamp/date and original representation.
- Parse amounts after removing currency symbols and thousands separators according to the selected locale. Support examples such as `$12.000`, `12.000,50`, `12,000.50`, and `12000`, but require a locale/format choice when separators are ambiguous. Store currency separately and never infer a decimal scale silently.
- Normalize newline/control characters in descriptions while preserving meaningful text; do not lower-case the stored display description.
- Keep a version number for category aliases, type mappings, date parser, and amount parser so a future reprocessing run is reproducible.

### Duplicate detection and idempotency

Use layered detection, with an explicit status rather than automatic deletion:

1. Exact source duplicate: same `ImportBatch` and source row number, or same file content hash already successfully imported.
2. Record fingerprint: hash normalized source identity fields (event date/time, type, category ID, description, amount, currency, product, and source context).
3. Cross-batch exact match: compare the fingerprint against existing transactions. Mark as duplicate and exclude from insertion by default.
4. Suspicious near-duplicate: same date, type, category, amount, and highly similar description. Flag for review; do not merge automatically.

The preview must show inserted, skipped-duplicate, suspicious, valid-pending-confirmation, and invalid counts. A confirmed re-import of the same file must be idempotent. Manual records and legitimate repeated sales must remain distinguishable through source context, timestamp, and description.

### Invalid-row reporting and confirmation

Provide a downloadable and API-readable report containing batch ID, source row number, original values, normalized candidate values, status, error code, human-readable message, and suggested correction. The preview must show totals and representative errors before confirmation. Persist invalid rows/quarantine records even when no valid rows are imported. Import confirmation inserts only valid, non-duplicate rows in one transaction or clearly reports partial failure with retry-safe behavior.

## 3. Data quality checklist (SPEC section 16)

Run this checklist at import time and before each analytical/ML dataset release:

- [ ] **Missing dates:** count null/unparseable dates; report affected rows; verify date range and timezone assumptions.
- [ ] **Missing categories:** count missing/unresolved categories; ensure every accepted transaction has a valid category ID.
- [ ] **Duplicate transactions:** report exact and suspicious duplicates separately; verify repeated legitimate transactions are not removed.
- [ ] **Invalid monetary values:** reject non-numeric, zero, negative, infinite, or ambiguously parsed values; reconcile totals before and after normalization.
- [ ] **Inconsistent category names:** compare raw labels to canonical taxonomy; review new aliases and unknown categories.
- [ ] **Inconsistent date formats:** report format distribution and ambiguous dates; verify parsed dates against source samples.
- [ ] **Outliers:** flag unusually high amounts, volumes, or daily totals for review without deleting them automatically; retain an outlier reason/status.
- [ ] **Incorrect transaction types:** verify every type is `INCOME` or `EXPENSE` and category compatibility is valid.
- [ ] **Missing product/service identifiers:** measure missingness by category and batch; treat as a warning in MVP and a future product-analytics gap.
- [ ] **Traceability:** every imported row is linked to an `ImportBatch` and source row; every rejection has an error reason.
- [ ] **Completeness and reconciliation:** compare source row counts and source totals with valid, invalid, duplicate, and inserted counts; investigate unexplained differences.
- [ ] **Historical completeness:** document periods with no records so “zero activity” is not confused with missing data.

## 4. Analytical dimensions and feature-friendly views

The operational schema should remain normalized, while read-only views or materialized extracts make analysis efficient and reproducible. At minimum, expose:

### Dimensions

- Calendar date, year, quarter, month, week, and business timezone.
- Day of week and weekend/weekday flag.
- Transaction type, canonical category, category hierarchy (when introduced), product/service, and source type.
- Import batch, provenance, data-quality status, and currency.
- Optional future dimensions: supplier, location, channel, customer segment, promotion, and payment method.

### Feature-friendly views

- `daily_transaction_summary`: daily income, expenses, net balance, transaction count, average amount, and category/type breakdown.
- `monthly_category_summary`: monthly income/expense totals, counts, shares, and month-over-month changes by category.
- `category_performance`: period totals, average transaction value, active days, trend, and data-quality indicators.
- `transaction_features`: one row per transaction with calendar features, normalized amount, type indicators, category/product IDs, and provenance.
- `daily_category_features`: one row per date/category/product combination, including zero-filled dates when the analysis period is explicitly known.
- `rolling_metrics`: 7-day, 28-day, and 90-day rolling sums/means/counts, calculated using only prior or current observations as defined by the forecasting use case.

Feature views must be deterministic, documented, reproducible from canonical transactions, and free of future leakage. Store definitions/version metadata rather than persisting opaque, hand-edited aggregates.

## 5. MVP storage requirements for Levels 1–4 and future ML

The MVP does not implement ML, but it must store enough evidence to make later analytics possible:

| Future capability | MVP data that must exist now |
|---|---|
| Level 1 descriptive | Complete transaction event date, type, amount, category ID, currency, and stable transaction ID; queryable daily/monthly aggregates. |
| Level 2 diagnostic | Original and canonical category, description/notes, product/service reference when known, import provenance, and immutable timestamps to explain changes and investigate anomalies. |
| Level 3 predictive | A continuous historical time axis, transaction counts and amounts by day/category/product, known missing-data periods, calendar dimensions, and reproducible aggregation windows. |
| Level 4 prescriptive | Revenue and expense history, category/product performance, trend and seasonality inputs, data-quality flags, and explainable metric definitions; recommendations remain decision support, not autonomous decisions. |
| Forecasting | Event time, category/product granularity, zero-activity versus unknown periods, prior-period measures, rolling aggregates, and enough history to define train/validation/test time splits without leakage. |
| Classification | Stable categorical IDs, day-of-week/month/season derivations, transaction volume and revenue features, previous-period revenue, rolling averages, and labels defined separately from input features. |
| Investment support | Income, expense, net balance, category evolution, product/service performance, provenance, outlier flags, and evidence links back to source transactions and batches. |

The MVP must also retain: raw source values, normalized values, parser/mapping versions, validation status, error details, duplicate decisions, currency assumptions, and source file hashes. This makes future experiments auditable and allows a model result to be explained back to business evidence.

## Acceptance criteria for this strategy

- [ ] `tasks/data-strategy.md` is the implementation reference for schema and import work.
- [ ] The schema preserves stable IDs, event timestamps, original values, normalized values, and import provenance.
- [ ] CSV/Excel imports detect/map Spanish-language headers, validate and normalize safely, report invalid rows, and never mutate source files.
- [ ] Duplicate handling is idempotent and reviewable rather than destructive.
- [ ] The SPEC section 16 checklist is executable as a repeatable quality review.
- [ ] Analytical views can derive calendar dimensions, category aggregates, and rolling metrics without changing the transaction source of truth.
- [ ] Levels 1–4 analytics and future forecasting/classification can be built from stored MVP data without inventing historical facts.
