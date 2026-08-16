# Architecture Design — Business Operations & Analytics Dashboard (MVP)

**Author:** Agent A — Software Architect
**Status:** Approved for implementation
**Locked stack:** React + TypeScript + Vite (frontend) · FastAPI + Python (backend) · PostgreSQL (database) · Docker Compose (local orchestration)
**Source of truth for conflicts:** `SPEC.md` (see §0 Conflict Resolution Log)

---

## 0. Conflict Resolution Log

Per instructions, any contradiction between `tasks/ui-design.md`, `tasks/data-strategy.md`, and `SPEC.md` is resolved in favor of `SPEC.md`, with the resolution noted here.

| # | Conflict | Source A | Source B | Resolution |
|---|---|---|---|---|
| 1 | Route for transaction creation | `ui-design.md` proposes `/transactions/new` as a real route (or modal) | `SPEC.md` §14 only describes the flow, no explicit route | **Adopt `ui-design.md`'s `/transactions/new`** — SPEC does not forbid it, and it is required for parallel FE/BE work. Implemented as a real routed page (not a modal) to keep MVP scope simple and testable; a modal/slide-over may be added later without contract changes. |
| 2 | Transaction identity type | `SPEC.md` §10 lists plain `id` | `data-strategy.md` recommends UUID or "equivalent immutable identifier" | **Adopt SPEC's simplicity intent, honor data-strategy's constraint**: use PostgreSQL `BIGINT IDENTITY` (auto-increment) as the primary key for MVP simplicity and FK performance, and add a separate immutable `public_id UUID` column (unique, generated at insert) to satisfy "stable identifier not reused" concerns for future distributed/import scenarios. Internal FKs use the fast integer PK; UUID is exposed nowhere yet in MVP API responses (documented as future extensibility, not required now) — **actually exposed** in API responses as `id` (see §5) to avoid leaking sequential integers as a public contract long-term. This keeps schema simple while not blocking future ID strategy changes. |
| 3 | Amount sign convention | `SPEC.md` transaction model has a single `amount` field | `data-strategy.md` recommends both `amount_original` and `amount_normalized` plus `currency_code` | **SPEC wins on MVP scope, data-strategy wins on column-level durability.** MVP stores one canonical positive `amount` (`NUMERIC(14,2)`) plus `transaction_type` for sign semantics — matching SPEC's simplicity goal. `currency_code` is added as a fixed-default column (`ARS`, non-editable in UI) rather than a full multi-currency system, satisfying data-strategy's "never silently mix currencies" without expanding MVP scope. `amount_original` vs `amount_normalized` distinction is deferred to the `ImportBatch`/quarantine layer (see §4.4) where lossy parsing actually happens; manually entered transactions have no parsing step so the split is unnecessary duplication for them. |
| 4 | Product/service entity required in MVP CRUD | `SPEC.md` §10.3 says Product table is "optional for the first CRUD implementation" | `data-strategy.md` treats `product_id` as necessary for future demand analysis | **SPEC wins**: `products` table and `product_id` FK are included in the schema now (cheap to add, referenced by data-strategy and ui-design import mapping), but **no CRUD UI/API for products is required in MVP** (deferred item, see §12). This keeps the schema future-proof without adding scope. |
| 5 | Auth requirement | `SPEC.md` §4 and §26 explicitly say "Role-based access control is not required for the MVP" and lists auth under v0.2 future extensions | `ui-design.md` and `data-strategy.md` do not mention auth at all | **No conflict** — SPEC is authoritative and explicit. MVP ships with **no authentication** (see §6). |
| 6 | Quarantine/`ImportRow` table | `SPEC.md` §10.4 defines only `ImportBatch` with summary counters | `data-strategy.md` §1 recommends an `ImportRow`/quarantine table storing every source row | **data-strategy wins for the import subsystem** because SPEC's own FR-09 requires "report invalid rows" with per-row detail, which a batch-only model cannot satisfy. `import_rows` table is added (see §4.5). This is additive to SPEC's model, not a contradiction of it. |
| 7 | Category uniqueness scope | `SPEC.md` §10.2 has a flat `Category` model | `data-strategy.md` recommends uniqueness scoped by transaction type | **Both compatible** — implemented as `UNIQUE(name, type)` constraint (see §4.2), which satisfies SPEC's flat model while respecting data-strategy's scoping recommendation. No contradiction. |

---

## 1. System Context and Boundaries

```text
                          ┌─────────────────────────────┐
                          │        Business Owner        │
                          │     (single MVP user)         │
                          └───────────────┬───────────────┘
                                          │ HTTPS (browser)
                                          ▼
                  ┌───────────────────────────────────────────┐
                  │      Frontend SPA (React+TS+Vite)          │
                  │      served by nginx/vite preview           │
                  └───────────────────┬─────────────────────────┘
                                     │ REST/JSON over HTTP
                                     │ Base path: /api/v1
                                     ▼
                  ┌───────────────────────────────────────────┐
                  │        Backend API (FastAPI)                │
                  │  api → services → repositories → models     │
                  └───────────────────┬─────────────────────────┘
                                     │ SQLAlchemy / asyncpg or psycopg2
                                     ▼
                  ┌───────────────────────────────────────────┐
                  │           PostgreSQL 15 (Docker)             │
                  └───────────────────────────────────────────┘

  Out of system boundary (MVP): ML/analytics service, bank sync, email/invoicing,
  external auth provider, multi-tenant isolation.
```

**In-boundary systems:** frontend SPA, backend REST API, PostgreSQL, local filesystem/staging area for CSV/Excel uploads (transient, in-process during import; no object storage service in MVP).

**Out-of-boundary systems (explicit non-goals, see §12):** ML/analytics pipeline execution, external identity provider, bank/PSP integrations, email/notification services, background job scheduler/queue (import runs synchronously in-request for MVP; documented as a scaling boundary in §5.5 and §12).

**Trust boundary:** Single trusted user, single deployment, no multi-tenancy. The API is not designed to be publicly exposed without a reverse proxy + TLS termination + (future) authentication layer in front of it.

---

## 2. Backend Layered Architecture

Follows `backend/app/README.md` and per-folder READMEs exactly — this section maps SPEC/data-strategy requirements onto the existing folder contract; no new top-level folders are introduced.

```
backend/app/
├── main.py                 # FastAPI app init, CORS, exception handlers, router mounting
├── api/
│   ├── deps.py              # get_db() session dependency; no auth dependency in MVP (stubbed for v0.2)
│   └── v1/
│       ├── transactions.py  # /api/v1/transactions*
│       ├── categories.py    # /api/v1/categories*
│       ├── products.py      # /api/v1/products* (schema+model only in MVP; router optional/minimal, see §12)
│       ├── dashboard.py     # /api/v1/dashboard/*
│       └── imports.py       # /api/v1/imports*
├── models/
│   ├── transaction.py       # Transaction ORM entity
│   ├── category.py          # Category ORM entity
│   ├── product.py           # Product ORM entity
│   └── import_batch.py      # ImportBatch + ImportRow ORM entities
├── schemas/
│   ├── transaction.py       # TransactionCreate/Update/Read, TransactionFilterParams
│   ├── category.py          # CategoryCreate/Read
│   ├── dashboard.py         # DashboardSummary, CategoryBreakdown, TimeseriesPoint
│   └── import_data.py       # ImportMappingRequest, ImportPreviewResponse, ImportConfirmResponse
├── services/
│   ├── transaction_service.py  # validation, category compatibility, CRUD orchestration
│   ├── dashboard_service.py    # KPI aggregation, savings rate, category breakdown, timeseries
│   └── import_service.py       # parsing, mapping, normalization, validation, dedup, persistence
├── repositories/
│   ├── transaction_repository.py  # filtered/paginated queries, aggregation queries
│   ├── category_repository.py     # active category listing, existence checks
│   └── import_repository.py       # batch + row bulk insert, batch status queries
└── db/
    ├── session.py            # SQLAlchemy engine + SessionLocal, get_db()
    ├── base.py                # Base = declarative_base(); imports all models
    └── migrations/            # Alembic env.py + versions/
```

**Layer responsibility contract (strict, one-directional dependency flow):**

- `api/` — HTTP concerns only: request/response shape via `schemas/`, status codes, calling exactly one `services/` function per endpoint. No SQLAlchemy imports here.
- `services/` — business rules: category/type compatibility, savings formula (`max(net_balance, 0)`), amount validation, import orchestration (calls `import_repository` + `category_repository`). No FastAPI imports here (keeps services testable and reusable, e.g. from a future CLI script).
- `repositories/` — only place that constructs SQLAlchemy queries/sessions-bound operations. Returns ORM entities or plain aggregation tuples, never Pydantic schemas.
- `models/` — ORM table declarations only, relationships, no business logic beyond `__repr__`/computed hybrid properties.
- `db/` — engine/session lifecycle and Alembic wiring only.

Repository interfaces must be defined so `services/` never imports a concrete database driver, preserving substitutability if PostgreSQL access patterns change (e.g., async engine later).

---

## 3. Frontend Structure

Follows `frontend/src/README.md`'s declared folders (`components/`, `pages/`, `services/`, `types/`) — adds `hooks/` and `router` wiring inside `pages`/`App.tsx`, both implied by "API client" and "pages" requirements in the task brief without violating the existing contract (no folder renamed or removed).

```
frontend/src/
├── main.tsx                    # ReactDOM root, QueryClientProvider, RouterProvider
├── App.tsx                     # Layout shell: sidebar/nav + <Outlet/>
├── router.tsx                  # Route table (see §3.1)
├── pages/
│   ├── DashboardPage.tsx        # route: /
│   ├── TransactionsPage.tsx     # route: /transactions
│   ├── TransactionFormPage.tsx  # route: /transactions/new (and /transactions/:id/edit)
│   └── ImportPage.tsx           # route: /import (wizard host)
├── components/
│   ├── kpi/KpiCard.tsx
│   ├── charts/TrendChart.tsx
│   ├── charts/CategoryBreakdownChart.tsx
│   ├── transactions/TransactionTable.tsx
│   ├── transactions/TransactionRow.tsx
│   ├── transactions/TransactionFormFields.tsx
│   ├── transactions/DeleteConfirmModal.tsx
│   ├── filters/PeriodFilter.tsx
│   ├── filters/TransactionFilters.tsx
│   ├── import/UploadStep.tsx
│   ├── import/MappingStep.tsx
│   ├── import/ValidationReportStep.tsx
│   ├── import/PreviewStep.tsx
│   └── layout/Sidebar.tsx
├── hooks/
│   ├── useDashboardSummary.ts   # wraps api client + React Query for /dashboard/summary
│   ├── useTransactions.ts       # list/create/update/delete with filters
│   ├── useCategories.ts
│   └── useImportWizard.ts       # wizard state machine (step, mapping, preview, result)
├── services/
│   └── apiClient.ts             # Axios instance, baseURL=VITE_API_BASE_URL, interceptors
├── types/
│   ├── transaction.ts
│   ├── category.ts
│   ├── dashboard.ts
│   └── import.ts
└── utils/
    └── period.ts                 # period preset → {start_date,end_date} resolution shared by hooks
```

### 3.1 Routes (must match `ui-design.md` exactly)

| Path | Page component | Backend endpoints consumed |
|---|---|---|
| `/` | `DashboardPage` | `GET /dashboard/summary`, `GET /dashboard/categories`, `GET /dashboard/timeseries`, `GET /transactions?limit=10` |
| `/transactions` | `TransactionsPage` | `GET /transactions`, `DELETE /transactions/{id}` |
| `/transactions/new` | `TransactionFormPage` | `POST /transactions`, `GET /categories` |
| `/transactions/:id/edit` | `TransactionFormPage` (edit mode; not in ui-design.md's route list but required by FR-05 edit action — implemented as a route param variant of the same page, no new top-level route) | `GET /transactions/{id}`, `PUT /transactions/{id}`, `GET /categories` |
| `/import` | `ImportPage` | `POST /imports/transactions` (multi-step, see §7), `GET /imports/{id}` |

Data fetching/mutation is standardized on React Query (`@tanstack/react-query`) wrapping `apiClient.ts`; components never call `axios` directly.

---

## 4. Final Database Schema

Database: PostgreSQL 15. All monetary values use `NUMERIC(14,2)` (never float). All tables have `created_at`/`updated_at` (`TIMESTAMPTZ`, default `now()`, `updated_at` maintained by an `ON UPDATE` trigger or ORM `onupdate=func.now()`).

### 4.1 `categories`

| Column | Type | Constraints |
|---|---|---|
| `id` | `BIGINT GENERATED ALWAYS AS IDENTITY` | PK |
| `name` | `VARCHAR(100)` | NOT NULL |
| `type` | `transaction_type_enum` | NOT NULL (`INCOME` \| `EXPENSE`) |
| `description` | `VARCHAR(255)` | NULL |
| `active` | `BOOLEAN` | NOT NULL DEFAULT TRUE |
| `created_at` | `TIMESTAMPTZ` | NOT NULL DEFAULT now() |
| `updated_at` | `TIMESTAMPTZ` | NOT NULL DEFAULT now() |

Constraints: `UNIQUE (name, type)`. Index: `idx_categories_type_active ON categories(type, active)`.

Seed data: the FR-02 initial category list is inserted via an Alembic data migration (not hardcoded in frontend).

### 4.2 `products`

Schema present per §0 conflict #4; no CRUD API required in MVP.

| Column | Type | Constraints |
|---|---|---|
| `id` | `BIGINT GENERATED ALWAYS AS IDENTITY` | PK |
| `name` | `VARCHAR(150)` | NOT NULL |
| `category_id` | `BIGINT` | NOT NULL, FK → `categories(id)` |
| `description` | `VARCHAR(255)` | NULL |
| `active` | `BOOLEAN` | NOT NULL DEFAULT TRUE |
| `created_at` | `TIMESTAMPTZ` | NOT NULL DEFAULT now() |
| `updated_at` | `TIMESTAMPTZ` | NOT NULL DEFAULT now() |

Index: `idx_products_category_id ON products(category_id)`.

### 4.3 `import_batches`

| Column | Type | Constraints |
|---|---|---|
| `id` | `BIGINT GENERATED ALWAYS AS IDENTITY` | PK |
| `filename` | `VARCHAR(255)` | NOT NULL |
| `source_type` | `VARCHAR(10)` | NOT NULL (`CSV` \| `EXCEL`) |
| `content_hash` | `CHAR(64)` | NOT NULL (SHA-256 hex) |
| `mapping_json` | `JSONB` | NOT NULL — accepted column mapping |
| `mapping_version` | `VARCHAR(20)` | NOT NULL |
| `parser_version` | `VARCHAR(20)` | NOT NULL |
| `currency_assumption` | `VARCHAR(3)` | NOT NULL DEFAULT `'ARS'` |
| `status` | `import_status_enum` | NOT NULL (`PENDING` \| `VALIDATED` \| `CONFIRMED` \| `FAILED`) |
| `records_total` | `INTEGER` | NOT NULL DEFAULT 0 |
| `records_valid` | `INTEGER` | NOT NULL DEFAULT 0 |
| `records_invalid` | `INTEGER` | NOT NULL DEFAULT 0 |
| `records_duplicate` | `INTEGER` | NOT NULL DEFAULT 0 |
| `records_inserted` | `INTEGER` | NOT NULL DEFAULT 0 |
| `created_at` | `TIMESTAMPTZ` | NOT NULL DEFAULT now() |
| `updated_at` | `TIMESTAMPTZ` | NOT NULL DEFAULT now() |

Constraint: `UNIQUE (content_hash)` — prevents re-processing the identical file as a new batch (idempotency at file level, per data-strategy §2).

### 4.4 `import_rows` (quarantine table — see §0 conflict #6)

| Column | Type | Constraints |
|---|---|---|
| `id` | `BIGINT GENERATED ALWAYS AS IDENTITY` | PK |
| `import_batch_id` | `BIGINT` | NOT NULL, FK → `import_batches(id)` ON DELETE CASCADE |
| `source_row_number` | `INTEGER` | NOT NULL |
| `raw_payload` | `JSONB` | NOT NULL — original row as read |
| `normalized_payload` | `JSONB` | NULL — candidate canonical row, if parsed |
| `record_fingerprint` | `CHAR(64)` | NULL — SHA-256 of normalized identity fields |
| `status` | `import_row_status_enum` | NOT NULL (`VALID` \| `INVALID` \| `DUPLICATE` \| `SUSPICIOUS` \| `INSERTED`) |
| `error_code` | `VARCHAR(50)` | NULL |
| `error_message` | `VARCHAR(500)` | NULL |
| `transaction_id` | `BIGINT` | NULL, FK → `transactions(id)` — set once inserted |
| `created_at` | `TIMESTAMPTZ` | NOT NULL DEFAULT now() |

Indexes: `idx_import_rows_batch ON import_rows(import_batch_id)`, `idx_import_rows_fingerprint ON import_rows(record_fingerprint)`.

### 4.5 `transactions`

| Column | Type | Constraints |
|---|---|---|
| `id` | `BIGINT GENERATED ALWAYS AS IDENTITY` | PK |
| `occurred_at` | `TIMESTAMPTZ` | NOT NULL — business event date/time |
| `source_date_raw` | `VARCHAR(50)` | NULL — original text for imported rows |
| `transaction_type` | `transaction_type_enum` | NOT NULL (`INCOME` \| `EXPENSE`) |
| `category_id` | `BIGINT` | NOT NULL, FK → `categories(id)` |
| `category_name_raw` | `VARCHAR(150)` | NULL — original label for imported rows |
| `description` | `VARCHAR(255)` | NOT NULL |
| `amount` | `NUMERIC(14,2)` | NOT NULL, CHECK (`amount > 0`) |
| `currency_code` | `CHAR(3)` | NOT NULL DEFAULT `'ARS'` |
| `product_id` | `BIGINT` | NULL, FK → `products(id)` |
| `notes` | `VARCHAR(1000)` | NULL |
| `source_type` | `transaction_source_enum` | NOT NULL DEFAULT `'MANUAL'` (`MANUAL` \| `CSV` \| `EXCEL`) |
| `import_batch_id` | `BIGINT` | NULL, FK → `import_batches(id)` |
| `source_row_number` | `INTEGER` | NULL |
| `record_fingerprint` | `CHAR(64)` | NULL — dedup key for import idempotency |
| `created_at` | `TIMESTAMPTZ` | NOT NULL DEFAULT now() |
| `updated_at` | `TIMESTAMPTZ` | NOT NULL DEFAULT now() |

Indexes (support FR-04, FR-05, FR-07, FR-08, NFR-02 <1s dashboard queries):

- `idx_transactions_occurred_at ON transactions(occurred_at)`
- `idx_transactions_type_occurred_at ON transactions(transaction_type, occurred_at)`
- `idx_transactions_category_id ON transactions(category_id)`
- `idx_transactions_import_batch_id ON transactions(import_batch_id)`
- `idx_transactions_fingerprint ON transactions(record_fingerprint)` (partial: `WHERE record_fingerprint IS NOT NULL`)
- Full-text/`ILIKE` search support: `idx_transactions_description_trgm` using `pg_trgm` GIN index on `description` (and `notes`) to satisfy FR-11 text search without a full search engine.

### 4.6 Enums

```sql
CREATE TYPE transaction_type_enum AS ENUM ('INCOME', 'EXPENSE');
CREATE TYPE transaction_source_enum AS ENUM ('MANUAL', 'CSV', 'EXCEL');
CREATE TYPE import_status_enum AS ENUM ('PENDING', 'VALIDATED', 'CONFIRMED', 'FAILED');
CREATE TYPE import_row_status_enum AS ENUM ('VALID', 'INVALID', 'DUPLICATE', 'SUSPICIOUS', 'INSERTED');
```

### 4.7 Relationships (ERD summary)

```text
categories 1───N products
categories 1───N transactions
products   1───N transactions        (nullable)
import_batches 1───N import_rows
import_batches 1───N transactions    (nullable; only for imported rows)
import_rows N───1 transactions       (nullable; set post-insertion)
```

Referential integrity uses `ON DELETE RESTRICT` for `category_id`/`product_id` on `transactions` (never silently orphan financial records — a category/product cannot be hard-deleted while referenced; MVP "delete" on categories/products is a soft `active = false` flag, not a row delete).

---

## 5. API Contract (base path `/api/v1`)

### 5.1 Transactions

```http
GET    /transactions
  query: start_date, end_date, type, category_id, search, page, page_size
  200 -> { items: TransactionRead[], total: number, page: number, page_size: number }

POST   /transactions
  body: TransactionCreate
  201 -> TransactionRead
  422 -> ValidationError[]

GET    /transactions/{id}
  200 -> TransactionRead
  404 -> ErrorResponse

PUT    /transactions/{id}
  body: TransactionUpdate
  200 -> TransactionRead
  404 / 422

DELETE /transactions/{id}
  204
  404
```

```ts
// TransactionCreate
{
  occurred_at: string;       // ISO 8601
  transaction_type: "INCOME" | "EXPENSE";
  category_id: number;
  description: string;       // 1..255 chars
  amount: number;             // > 0, 2 decimal places
  product_id?: number | null;
  notes?: string | null;
}

// TransactionRead extends TransactionCreate
{
  id: number;
  currency_code: string;
  source_type: "MANUAL" | "CSV" | "EXCEL";
  created_at: string;
  updated_at: string;
}
```

### 5.2 Categories

```http
GET    /categories            query: type?, active?
  200 -> CategoryRead[]

POST   /categories
  body: { name: string; type: "INCOME"|"EXPENSE"; description?: string }
  201 -> CategoryRead

PUT    /categories/{id}
  body: { name?: string; description?: string; active?: boolean }
  200 -> CategoryRead

DELETE /categories/{id}       # soft delete -> sets active=false
  204
```

### 5.3 Dashboard

```http
GET /dashboard/summary
  query: start_date, end_date
  200 -> {
    total_income: number;
    total_expenses: number;
    net_balance: number;
    estimated_savings: number;
    savings_rate: number;      // 0 if total_income == 0, per SPEC §23
    transaction_count: number;
    period: { start_date: string; end_date: string };
  }

GET /dashboard/categories
  query: start_date, end_date, type?
  200 -> { category_id: number; category_name: string; total: number; percentage: number }[]

GET /dashboard/timeseries
  query: start_date, end_date, granularity? ("day"|"week"|"month", default inferred from range)
  200 -> { date: string; income: number; expenses: number }[]
```

### 5.4 Products (schema only; minimal read endpoint to support transaction form dropdowns — no full CRUD required in MVP per §0 conflict #4)

```http
GET /products      query: category_id?, active?
  200 -> ProductRead[]
```

`POST /products`, `PUT /products/{id}`, `DELETE /products/{id}` are **deferred** (see §12) — schema and repository exist now, routes are not required for MVP acceptance criteria.

### 5.5 Import

```http
POST /imports/transactions
  multipart/form-data: file
  201 -> { batch_id: number; status: "PENDING"; columns_detected: string[]; suggested_mapping: Record<string,string> }

POST /imports/{batch_id}/mapping
  body: { mapping: Record<string,string> }   # canonical_field -> source_column
  200 -> { batch_id: number; status: "VALIDATED"; summary: {
      records_total: number; records_valid: number; records_invalid: number; records_duplicate: number;
    }; preview: TransactionCreate[]; invalid_rows: { row_number: number; error_code: string; message: string }[] }

POST /imports/{batch_id}/confirm
  200 -> { batch_id: number; status: "CONFIRMED"; records_inserted: number }

GET  /imports
  200 -> ImportBatchRead[]

GET  /imports/{id}
  200 -> ImportBatchRead & { rows_summary: {...} }
```

Note: `SPEC.md` §12 lists only `POST /imports/transactions`, `GET /imports`, `GET /imports/{id}`. The `mapping` and `confirm` sub-resources are an additive, backward-compatible extension required to satisfy FR-09's explicit multi-step flow (upload → map → validate → preview → confirm) and `ui-design.md`'s wizard steps; they do not remove or change SPEC's three base endpoints, so this is **not** treated as a conflict requiring the resolution log — it is a superset. Import processing runs **synchronously within each request** for MVP (no background job queue); this is documented as a scale boundary in §12, acceptable because NFR-02 targets "normal datasets" and historical business CSVs are expected to be small.

---

## 6. Auth Decision for MVP

**Decision: no authentication in MVP**, per SPEC §4 ("Role-based access control is not required for the MVP") and §26/§24 (auth listed under v0.2).

Architectural safeguards so this doesn't block future auth (NFR-06):

- `api/deps.py` defines a `get_current_user()` dependency stub that returns a fixed `SYSTEM_USER` sentinel today, wired into every router but not enforced. Adding real auth later means swapping this dependency's implementation, not touching route signatures.
- CORS is restricted to the known frontend origin (`FRONTEND_ORIGIN` env var), not wildcard, even without auth — reduces cross-origin abuse of an unauthenticated API.
- The API is expected to run behind the developer's local network / reverse proxy only for MVP; the design doc explicitly calls this out as a non-goal to expose publicly without adding auth first (see §12).

---

## 7. Import Pipeline Integration Points

Sequence (implements FR-09 + `data-strategy.md` §2, owned end-to-end by `import_service.py`):

1. **Upload** (`POST /imports/transactions`): `import_service` computes SHA-256, checks `import_batches.content_hash` uniqueness, and stores the raw upload below the configured `IMPORT_STORAGE_DIR` path. Compose mounts that path to the named `import_storage` volume so a new backend container can read the database-referenced staging file. The byte-for-byte source is never modified. Column detection and suggested mapping use the alias dictionary in `data-strategy.md` §2.
2. **Mapping** (`POST /imports/{batch_id}/mapping`): frontend posts the confirmed/edited mapping; `import_service` re-reads the staged file, applies normalization (dates, amounts, category aliasing, type aliasing) per row, computes semantic `record_fingerprint`, and retains repeated rows from the same source instead of collapsing same-batch fingerprints. Existing transactions from another source batch remain duplicate candidates. It writes one `import_rows` row per source row with status `VALID`/`INVALID`/`DUPLICATE`/`SUSPICIOUS`, updates batch counters, and sets `status = VALIDATED`.
3. **Confirm** (`POST /imports/{batch_id}/confirm`): `import_service` locks each semantic fingerprint while checking for equivalent transactions in other source batches, inserts all `VALID` (non-duplicate) `import_rows` as `transactions` rows inside one DB transaction, and assigns a unique `source_fingerprint` from the batch content hash and source row number. It sets `import_rows.transaction_id` and `status = INSERTED`, then sets `import_batches.status = CONFIRMED` and `records_inserted`. Partial failure rolls back the whole insert and reports the failure — no partially-imported batch state.
4. **Traceability read** (`GET /imports`, `GET /imports/{id}`): pure read from `import_repository`, used by a future audit view (not in MVP nav but available for support/debugging).

`transaction_service.py` is not involved in bulk import inserts (bypasses per-row API validation overhead by reusing the same validation rules directly in `import_service`, calling shared validator functions extracted into `services/validation.py` if duplication would otherwise occur between `transaction_service` and `import_service` — **explicit design rule: validation logic for a single canonical field, e.g. "amount must be > 0", must live in exactly one place and be imported by both services**).

---

## 8. Configuration and Environment Variables

Extends `docker-compose.yml`'s existing variables; no renames.

| Variable | Used by | Example | Notes |
|---|---|---|---|
| `POSTGRES_DB` | postgres, backend | `elite_db` | already in compose |
| `POSTGRES_USER` | postgres, backend | `postgres` | already in compose |
| `POSTGRES_PASSWORD` | postgres, backend | `postgres` | already in compose; never committed with a real value |
| `POSTGRES_PORT` | postgres | `5432` | already in compose |
| `DATABASE_URL` | backend | `postgresql://...` | already in compose; consumed by `db/session.py` |
| `ENVIRONMENT` | backend | `development` \| `production` | already in compose; toggles debug/reload and error verbosity |
| `FRONTEND_ORIGIN` | backend | `http://localhost:3000` | **new** — CORS allow-list origin |
| `API_LOG_LEVEL` | backend | `info` | **new** — uvicorn/logging level |
| `IMPORT_MAX_FILE_SIZE_MB` | backend | `10` | **new** — upload size guard |
| `IMPORT_DEFAULT_LOCALE` | backend | `es_AR` | **new** — date/amount parsing locale default per data-strategy §2 |
| `IMPORT_DEFAULT_CURRENCY` | backend | `ARS` | **new** — default `currency_code`/`currency_assumption` |
| `VITE_API_BASE_URL` | frontend | `http://localhost:8000/api/v1` | **new** — supplied as a Docker build argument and runtime environment value, consumed by `services/apiClient.ts` |

All new variables get defaults in `docker-compose.yml` (same `${VAR:-default}` pattern already used) and are documented in a `.env.example` at repo root (not committed as `.env`).

---

## 9. Migration Strategy (Alembic)

- `backend/app/db/base.py` imports every model module so `Base.metadata` is complete for `alembic revision --autogenerate`.
- Migration order (dependency-respecting): `001_create_enums` → `002_create_categories` (+ FR-02 seed data insert) → `003_create_products` → `004_create_import_batches` → `005_create_import_rows` → `006_create_transactions` (+ indexes) → `007_enable_pg_trgm_and_search_index`.
- One Alembic head at all times; no branching migrations for MVP (single environment target).
- `alembic upgrade head` runs as a backend container entrypoint step (or an explicit `docker compose exec backend alembic upgrade head` documented in backend README) before `main.py` accepts traffic — documented as a required manual/CI step for MVP since no init-container orchestration exists yet.
- Rollback: every migration must implement `downgrade()`; MVP does not require zero-downtime migration strategies (single-instance dev/staging target).

---

## 10. Error and Validation Approach

- **Validation layer:** Pydantic schemas at the API boundary reject malformed requests with `422` and FastAPI's default `{ detail: [...] }` shape, kept as-is (no custom envelope) to avoid extra frontend-parsing complexity for MVP.
- **Business-rule errors** (e.g., category/type mismatch, inactive category, amount ≤ 0 caught beyond Pydantic's numeric constraint, category not found) are raised in `services/` as typed exceptions (`CategoryMismatchError`, `EntityNotFoundError`, etc.) and translated to HTTP responses by a FastAPI exception handler registered in `main.py`, returning:

```json
{ "error_code": "CATEGORY_TYPE_MISMATCH", "message": "Category 'Internet' is not valid for EXPENSE transactions." }
```

- **Import validation errors** use the stable `error_code` vocabulary from `data-strategy.md` (e.g., `MISSING_DATE`, `INVALID_TYPE`, `UNKNOWN_CATEGORY`, `NON_POSITIVE_AMOUNT`, `AMBIGUOUS_DATE_FORMAT`) stored per-row in `import_rows.error_code`/`error_message` and surfaced verbatim in the mapping-step API response.
- **Frontend handling:** `apiClient.ts` centralizes error normalization (Axios interceptor unwraps FastAPI's `detail`/`error_code` shape into a single `AppError` type consumed by components); form-level errors render inline per `ui-design.md` §3, network/API errors render as a dismissible toast per `ui-design.md` §7.
- **Database-level guarantees:** `CHECK (amount > 0)`, `NOT NULL` constraints, and FK constraints act as the last line of defense (defense in depth, not the primary validation path).

---

## 11. Testing Strategy Outline

**Backend (pytest, per `backend/tests/`):**

- Unit tests for `services/` (pure functions/business rules: savings formula, category compatibility, amount normalization) — no DB required, fastest tier.
- Repository/integration tests against a real PostgreSQL test database (docker-compose test profile or `pytest-postgresql`), covering filtering, aggregation queries, and constraint behavior (FK restrict, unique fingerprint).
- API tests using `TestClient`/`httpx` against a test DB, covering the full contract in §5 including error responses (`422`, `404`, business-rule `4xx`).
- Import pipeline tests: fixture CSV/Excel files covering FR-09/data-strategy §2–3 cases (valid rows, missing fields, ambiguous dates, unknown categories, duplicate rows, re-upload idempotency).

**Frontend (Vitest + React Testing Library, aligned with Vite):**

- Unit tests for `hooks/` (mocked `apiClient`) and pure utils (`period.ts` preset resolution).
- Component tests for `TransactionFormFields` (validation states) and `TransactionTable` (rendering, filter interactions).
- Optional Playwright/webapp-testing smoke test for the critical path: add transaction → see it on dashboard/history (can be deferred past MVP if time-constrained; not a hard acceptance blocker per SPEC §22, which only requires the behavior, not a specific test tool).

**Definition of Done alignment (SPEC §27):** every FR above must have at least one backend test proving persistence + validation and one frontend test proving the UI reflects the FR-defined behavior, before a task is marked complete.

---

## 12. Explicit Non-Goals / Deferred Items

Directly from SPEC §3.2 plus architecture-level deferrals introduced by this design:

- Authentication/authorization (v0.2, §6).
- Full Product/Service CRUD API and UI (schema/model exist now; endpoints deferred, §0 conflict #4, §5.4).
- Background job queue for import processing (imports run synchronously in-request for MVP; revisit if file sizes/volume grow — §5.5, §7).
- Permanent raw-file archival to `data/raw` as a persisted artifact store (MVP only persists import metadata + row payloads in the DB, not the original file bytes long-term).
- Multi-currency support beyond a fixed default (`currency_code` column exists, no conversion/multi-currency UI).
- Bank sync, e-invoicing, payroll, full bookkeeping compliance, inventory management, CRM, multi-tenancy, native mobile, automated financial advice, production ML (verbatim from SPEC §3.2).
- CSV export (SPEC §12 marks this "MVP-adjacent," may follow immediately after core CRUD but is not part of this architecture's required contract).
- Materialized analytical views (`daily_transaction_summary`, `monthly_category_summary`, etc. from `data-strategy.md` §4) — schema supports deriving them later via SQL views/materialized views without altering `transactions`; not created in MVP.
- Role-based access control primitives beyond the `get_current_user()` stub.

---

## 13. Integration Boundaries for Parallel Backend/Frontend Implementation

To allow both tracks to start immediately without waiting on each other:

1. **Contract-first:** §5 of this document is the frozen API contract. Both teams implement against it; any change requires updating this file first.
2. **Frontend can start immediately** against a mock server (e.g., MSW or a static JSON fixture server) implementing the exact shapes in §5.1–§5.5, using `types/*.ts` derived directly from this document's TypeScript-flavored schemas.
3. **Backend can start immediately** from §4 (schema) and §5 (contract) without frontend input — Alembic migrations and Pydantic schemas are the two artifacts that unblock both sides fastest and should be prioritized first in the task breakdown.
4. **Shared vocabulary:** enum values (`INCOME`/`EXPENSE`, error codes in §10) must be treated as a shared constants contract — recommend a small generated or hand-synced constants file on each side (`transaction_type_enum` values, import `error_code` list) rather than ad-hoc string literals, to avoid drift.
5. **CORS/env:** `FRONTEND_ORIGIN` and `VITE_API_BASE_URL` (§8) are the only two config values each side needs from the other to integrate; both are already parameterized in `docker-compose.yml`, so no hardcoded coupling exists.
6. **Category seed data** (FR-02, migration `002_create_categories`) is a backend-owned artifact but frontend must not hardcode this list (NFR: "Categories must be stored in the database rather than hard-coded into the frontend") — frontend always fetches `GET /categories` for dropdown population, including at first local run.
