# Tasks: MVP Integration Hardening

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | 220-360 |
| 400-line budget risk | Medium |
| Chained PRs recommended | No |
| Suggested split | Single PR with 3 work-unit commits |
| Delivery strategy | ask-on-risk |
| Chain strategy | feature-branch-chain (resolved override) |

Decision needed before apply: Resolved (split chained)
Chained PRs recommended: No
Chain strategy: feature-branch-chain
400-line budget risk: Medium

### Suggested Work Units

| Unit | Goal | Likely PR | Focused test command | Runtime harness | Rollback boundary |
|------|------|-----------|----------------------|-----------------|-------------------|
| 1 | Enforce backend CSV-only contract with failing-first tests | PR 1 (commit slice A) | `cd backend && pytest tests/test_import_api.py -k "csv or import"` | `docker compose up -d && curl http://localhost:8000/api/v1/health` | Revert `backend/app/services/import_service.py` + related assertions in `backend/tests/test_import_api.py` |
| 2 | Align frontend import UX copy/input to CSV-only scope | PR 1 (commit slice B) | `cd frontend && npm run build && npx tsc --noEmit` | Open `/import` and attempt `.xlsx` selection (must be blocked/rejected) | Revert `frontend/src/components/import/UploadStep.tsx` only |
| 3 | Record evidence-bound acceptance checklist updates | PR 1 (commit slice C) | `cd backend && pytest` | `/api/v1` smoke run on compose stack with evidence timestamps | Revert `tasks/mvp-implementation.md` and checklist evidence edits only |

## Phase 1: Foundation / RED Baseline

- [x] 1.1 In `backend/tests/test_import_api.py`, add RED tests for non-CSV upload rejection (`400`) and CSV-only error wording.
- [x] 1.2 In `backend/tests/test_import_api.py`, add RED test proving valid `.csv` upload still follows the existing success path.
- [x] 1.3 In `.env.example`, align DB URL guidance with compose/psycopg runtime expectations if mismatch is found during baseline verification.

## Phase 2: Core Implementation / GREEN

- [x] 2.1 Update `backend/app/services/import_service.py` to accept CSV only (extension/content-type checks) and reject non-CSV deterministically.
- [x] 2.2 Ensure backend validation messaging remains explicitly CSV-only across the import upload path in `backend/app/services/import_service.py`.
- [x] 2.3 Update `frontend/src/components/import/UploadStep.tsx` to enforce CSV-only UI contract (`accept` filter + user-facing copy).

## Phase 3: Integration / Verification Evidence

- [x] 3.1 Run `cd backend && pytest tests/test_import_api.py -k "csv or import"` to turn RED→GREEN and capture command output as evidence.
- [x] 3.2 Run live stack verification (`docker compose up -d`, health/migrations, `/api/v1` smoke, CORS check) and capture dated evidence.
- [x] 3.3 Run frontend gates (`cd frontend && npm run build` and `cd frontend && npx tsc --noEmit`) plus manual `/import` smoke.

## Phase 4: REFACTOR / Acceptance Boundaries / Commit Hygiene

- [x] 4.1 Refactor import validation/test fixtures for clarity without broadening scope in `backend/app/services/import_service.py` and `backend/tests/test_import_api.py`.
- [x] 4.2 Update `tasks/mvp-implementation.md` §5: check only evidence-backed items from this run; keep unproven criteria unchecked.
- [x] 4.3 Ensure acceptance wording in `tasks/mvp-implementation.md` reflects CSV-only scope (remove Excel claims).
- [x] 4.4 Prepare conventional commit slices by work unit: backend contract+tests, frontend CSV UX, acceptance evidence/docs.

> Threat-matrix note: design matrix rows are all marked `N/A`; no additional threat-specific RED tasks are required for this change.

## Phase 5: Approved Verification-Blocker Remediation

- [x] 5.1 Replace source-string-only frontend contract assertions with Playwright runtime coverage that renders the production `UploadStep` path, verifies the CSV-only picker/copy, and exercises file-selection state.
- [x] 5.2 Parameterize the Compose frontend host binding with documented `FRONTEND_PORT`, map it to the existing nginx container port `80`, and preserve the default Postgres/frontend host ports and CORS origin behavior.
- [x] 5.3 Run the complete backend suite, frontend build/typecheck, runtime frontend test, and full alternate-port Compose smoke with direct evidence for frontend, backend, and Postgres readiness.

### Remediation Work Units

| Unit | Goal | Focused test command | Runtime harness | Rollback boundary |
|------|------|----------------------|-----------------|-------------------|
| 4 | Prove the CSV-only UploadStep contract at runtime | `cd backend && pytest tests/test_frontend_upload_step_contract.py` -> 2 passed | The test starts Vite, launches headless Chromium, opens `/import`, and asserts rendered copy, `accept=".csv"`, disabled/enabled upload state, and selected filename | Revert `backend/tests/test_frontend_upload_step_contract.py` only; no production frontend behavior is removed |
| 5 | Make the full Compose stack conflict-free on configurable host ports | `cd backend && pytest tests/test_compose_port_contract.py` -> 2 passed | `POSTGRES_PORT=55433 FRONTEND_PORT=43000 docker compose up -d --build` -> `elite_postgres` healthy, `elite_backend` up on `8000`, `elite_frontend` up on `43000->80`; Alembic at `007_enable_pg_trgm (head)` | Revert `docker-compose.yml` and `backend/tests/test_compose_port_contract.py`; container ports and API code remain unchanged |
| 6 | Re-run complete acceptance gates and capture direct evidence | `cd backend && pytest` -> 18 passed; `cd frontend && npm run build` -> pass; `cd frontend && npx tsc --noEmit` -> pass | Compose health/API/frontend checks and CORS preflight run against the same alternate-port stack -> all passed | Revert only remediation evidence sections in this task artifact and `apply-progress.md` |

## Phase 6: Authorized Scope Expansion - Confirmed Critical Remediation

- Incremental review forecast: 260-380 authored lines across four independent blocker work units plus evidence.
- 400-line budget risk: Medium.
- Delivery strategy: ask-on-risk with the already resolved `feature-branch-chain` boundary.
- Decision needed before apply: Resolved by the explicit authorized scope expansion and session delivery settings.

- [x] 6.1 Make import confirmation atomic and idempotent under concurrent duplicate requests with row locking, a database uniqueness constraint, and a concurrency regression test.
- [x] 6.2 Configure the nginx frontend image with SPA fallback for direct navigation and refresh of client routes.
- [x] 6.3 Align the import mapping UI with the backend `occurred_at` contract and add backend plus browser end-to-end regression coverage for absent/custom date detection.
- [x] 6.4 Make date-only/timestamp formatting, date input payloads, and edit initialization timezone-safe with negative-offset browser regression coverage.
- [x] 6.5 Re-run the complete backend suite, frontend build/typecheck, runtime frontend tests, database migration, and alternate-port Compose/browser smoke without changing the documented warning follow-ups.

### Critical Remediation Work Units

| Unit | Goal | Focused test command | Runtime harness | Rollback boundary |
|------|------|----------------------|-----------------|-------------------|
| 7 | Protect import confirmation against duplicate concurrent commits | `cd backend && pytest tests/test_import_confirmation_concurrency.py` | Two concurrent HTTP confirmations against the Postgres-backed Compose service; both return `200/CONFIRMED/1`, one transaction exists | Revert `backend/app/services/import_service.py`, `backend/app/repositories/import_repository.py`, `backend/app/models/transaction.py`, migration `008_protect_import_confirmation.py`, and its tests |
| 8 | Serve the SPA entrypoint for nginx client routes | `cd backend && pytest tests/test_frontend_spa_fallback_contract.py` | Alternate-port Compose frontend browser smoke opens `/import`, `/transactions`, and `/transactions/new` directly with HTTP 200 and rendered route headings | Revert `frontend/nginx.conf`, its Dockerfile copy instruction, and the SPA contract test |
| 9 | Submit `occurred_at` from the import mapping UI | `cd backend && pytest tests/test_import_api.py::test_import_mapping_accepts_occurred_at_when_date_detection_is_absent tests/test_frontend_upload_step_contract.py::test_import_mapping_submits_backend_occurred_at_key` | Browser import flow sends a custom date mapping through the frontend to the backend validation endpoint | Revert `frontend/src/components/import/MappingStep.tsx` and the added mapping regression tests |
| 10 | Preserve calendar dates across timezone boundaries | `cd backend && pytest tests/test_frontend_upload_step_contract.py::test_transaction_edit_preserves_calendar_date_in_negative_offset_locale` | Headless Chromium in `America/Los_Angeles` loads an edit timestamp and submits UTC midnight for the selected calendar date | Revert `frontend/src/utils/format.ts`, `frontend/src/components/transactions/TransactionFormFields.tsx`, and the timezone regression test | 

## Phase 7: Authorized Scope Expansion - Five Critical Findings

- Incremental review forecast: 300-390 authored lines across five focused behavior work units plus cumulative evidence.
- 400-line budget risk: Medium.
- Delivery strategy: ask-on-risk with the already resolved `feature-branch-chain` boundary.
- Decision needed before apply: Resolved by the explicit user authorization in this apply session.

- [x] 7.1 Make migration `008_protect_import_confirmation.py` upgrade-safe by deterministically retaining the lowest transaction id for each historical `(import_batch_id, source_row_number)` duplicate, rewiring `import_rows`, deleting later duplicates, and documenting the data decision.
- [x] 7.2 Fix DashboardPage transaction requests to send inclusive UTC datetime boundaries accepted by the backend transaction endpoint.
- [x] 7.3 Make `frontend/src/utils/period.ts` return calendar-date-stable inclusive boundaries in UTC-negative browser timezones.
- [x] 7.4 Parse locale-aware Argentine thousands values such as `1.234` as `1234.00` under `es_AR` while preserving decimal values such as `1234.56`.
- [x] 7.5 Treat absent or null mapped descriptions as missing validation values and never as the literal string `None`.
- [x] 7.6 Re-run the complete backend suite, frontend build/typecheck, runtime browser tests, migration upgrade smoke, and alternate-port Compose/API smoke with exact cumulative evidence.

### Critical Finding Work Units

| Unit | Goal | Focused test command | Runtime harness | Rollback boundary |
|------|------|----------------------|-----------------|-------------------|
| 12 | Upgrade historical import data safely before enforcing uniqueness | `cd backend && pytest tests/test_import_migration_upgrade.py` | Temporary Postgres on host port `55434`: migrate to `007`, seed duplicate transactions, migrate to `head`, assert one canonical row and rewired import row | Revert `backend/app/db/migrations/versions/008_protect_import_confirmation.py` and `backend/tests/test_import_migration_upgrade.py` |
| 13 | Prevent DashboardPage transaction requests from returning 422 | `cd backend && pytest tests/test_frontend_upload_step_contract.py -k dashboard_transaction` | Alternate-port Compose browser opens `/` and asserts transaction request status is not 422 with UTC datetime query values | Revert `frontend/src/services/apiClient.ts` and the Dashboard request regression test |
| 14 | Preserve inclusive period dates across timezone boundaries | `cd backend && pytest tests/test_frontend_upload_step_contract.py -k custom_period` | Headless Chromium in `America/Los_Angeles` selects `2026-08-15` through `2026-08-20` and observes unchanged API query dates | Revert `frontend/src/utils/period.ts` and the period timezone regression test |
| 15 | Parse configured `es_AR` amounts and invalid descriptions correctly | `cd backend && pytest tests/test_import_api.py -k "argentine or absent_mapped_description"` | Alternate-port Compose API smoke validates `1.234 -> 1234.00` and missing description returns `MISSING_DESCRIPTION` | Revert the amount/value normalization changes in `backend/app/services/import_service.py` and related API tests |
| 16 | Re-run all acceptance gates without changing follow-up warnings | `cd backend && pytest`; `cd frontend && npm run build`; `cd frontend && npx tsc --noEmit` | `POSTGRES_PORT=55433 FRONTEND_PORT=43000 docker compose up -d --build`, health/API/CORS/Alembic/browser smoke | Revert only the Phase 7 evidence additions in this file and `apply-progress.md`; behavior units remain independently revertible |

### Follow-up Warnings Preserved

- Vite bundle-size warning, generalized Postgres pytest fixture, obsolete Compose `version` warning, empty CSV handling, missing frontend test dependencies, staged-file persistence, and concurrent upload deduplication remain follow-up items unless separately authorized.

## Phase 8: Authorized Scope Expansion - Latest Critical Findings

- Incremental review forecast: 220-340 authored lines across four focused behavior work units plus cumulative evidence.
- 400-line budget risk: Medium.
- Delivery strategy: ask-on-risk with the already resolved `feature-branch-chain` boundary.
- Decision needed before apply: Resolved by the explicit user authorization in this apply session.

- [x] 8.1 Reject malformed monetary text without stripping arbitrary characters, while preserving `es_AR` and `en_US` thousands parsing.
- [x] 8.2 Prevent cross-batch duplicate confirmation with database-backed fingerprint uniqueness and preserve all-or-nothing rollback.
- [x] 8.3 Make migration 008 retain the earliest persisted commit/order row with deterministic tie-breaking and coherent references/counters.
- [x] 8.4 Align frontend and backend calendar boundaries for local browser/business dates, including UTC-negative and positive-offset coverage.
- [x] 8.5 Run complete acceptance gates and append exact evidence without changing unrelated warning follow-ups.

### Latest Critical Finding Work Units

| Unit | Goal | Focused test command | Runtime harness | Rollback boundary |
|---|---|---|---|---|
| 17 | Reject malformed amounts and preserve locale-aware grouping | `cd backend && pytest tests/test_import_api.py -k "malformed_amount or us_thousands or argentine"` | Alternate-port Compose API mapping smoke with configured `es_AR` and `12abc34`; `en_US` is covered by the focused API regression with a settings override | Revert amount parser changes and these import API regressions only |
| 18 | Enforce cross-batch fingerprint uniqueness atomically | `cd backend && pytest tests/test_import_api.py -k cross_batch_duplicate` | Two distinct CSV batches mapped before confirmation, then confirmed against Postgres; second batch rolls back with one persisted transaction | Revert fingerprint uniqueness model/migrations, confirmation handling, and cross-batch regression |
| 19 | Canonicalize migration rows by persisted order signal | `cd backend && pytest tests/test_import_migration_upgrade.py` | Temporary or alternate-port Postgres upgrade from revision 007 with inverted ids/timestamps, relationship rewiring, and counter checks | Revert migration cleanup/migration 009 and migration upgrade regressions |
| 20 | Preserve calendar boundaries across browser timezones | `cd backend && pytest tests/test_frontend_upload_step_contract.py -k "calendar_date or custom_period"` | Browser tests in `America/Los_Angeles` and `Asia/Tokyo`, plus API dashboard boundary smoke | Revert frontend date helpers, dashboard UTC range handling, transaction UTC normalization, and timezone regressions |

### Follow-up Warnings Preserved

- Vite bundle-size warning, generalized Postgres pytest fixture, obsolete Compose `version` warning, empty CSV handling, missing frontend test dependencies, and staged-file persistence remain follow-up items.

## Phase 9: Authorized Scope Expansion - Final Two Critical Blockers

- Incremental review forecast: 180-260 authored lines across two behavior work units plus cumulative evidence.
- 400-line budget risk: Medium.
- Delivery strategy: ask-on-risk with the already resolved `feature-branch-chain` boundary.
- Decision needed before apply: Resolved by the explicit final remediation authorization in this apply session.
- Scope is limited to canonical transaction fingerprint timestamps and local calendar-date filtering.

- [x] 9.1 Normalize imported transaction fingerprint timestamps to canonical UTC before hashing and reject equivalent offset representations as duplicates across import batches.
- [x] 9.2 Define and implement one local calendar-boundary contract from frontend period utilities through API clients, backend endpoints, repositories, and regression tests.
- [x] 9.3 Run strict TDD focused tests, the complete backend suite, frontend build/typecheck, runtime browser tests, and alternate-port Compose/API smoke with exact cumulative evidence.

### Final Calendar-Boundary Contract

- Persisted transaction timestamps and repository comparison bounds are UTC instants.
- A date-only `start_date` or `end_date` filter represents the selected local calendar date in the IANA timezone supplied by the `timezone` query parameter.
- The backend converts the local start-of-day and end-of-day boundaries to UTC before repository filtering.
- The `timezone` parameter defaults to `UTC` for direct API consumers that do not provide a local timezone.
- The frontend period utilities emit date-only local calendar strings, and the API client supplies the browser's resolved IANA timezone without converting date-only values to UTC midnight.
- Full timestamp transaction filters remain supported as exact instants and are normalized to UTC before repository comparison.

### Final Critical Remediation Work Units

| Unit | Goal | Focused test command | Runtime harness | Rollback boundary |
|---|---|---|---|---|
| 22 | Canonicalize equivalent imported timestamps before fingerprint hashing | `cd backend && pytest tests/test_import_api.py -k "fingerprint or cross_batch_duplicate"` -> 2 passed | Alternate-port Compose API imports two distinct CSV batches with `-04:00` and `+00:00` representations of one instant, confirms the first, and confirms the second as one duplicate with zero new inserts | Revert `_canonical_utc_timestamp` and canonical fingerprint payload use in `backend/app/services/import_service.py` plus the equivalent-offset regression test; existing fingerprint uniqueness and confirmation atomicity remain otherwise unchanged |
| 23 | Apply the local calendar-boundary contract to dashboard and transaction filtering | `cd backend && pytest tests/test_dashboard_api.py -k "calendar or offset"` -> 2 passed; browser contract filter -> 3 passed | Alternate-port Compose API verifies `America/New_York` and `Asia/Tokyo` selected dates include their offset timestamps; Compose browser smoke opens `/import`, `/transactions`, and `/transactions/new` directly | Revert `backend/app/services/calendar.py`, dashboard/transaction endpoint timezone handling, repository UTC-bound normalization, frontend calendar range/API-client changes, and their regression assertions; persisted UTC timestamps and unrelated filtering remain intact |
| 24 | Re-run all acceptance gates and preserve warning follow-ups | `cd backend && pytest` -> 39 passed; `cd frontend && npm run build` -> pass; `cd frontend && npx tsc --noEmit` -> pass; `git diff --check` -> pass | `POSTGRES_PORT=55435 FRONTEND_PORT=43001 docker compose up -d --build`; Postgres healthy, backend health passed, frontend routes returned 200, Alembic at `009_unique_import_fingerprints (head)`, API and browser smoke passed | Revert only the Phase 9 evidence additions in this task artifact and `apply-progress.md`; behavior and regression files remain independently revertible under Units 22-23 |

### Follow-up Warnings Preserved

- Vite bundle-size warning, generalized Postgres pytest fixture, obsolete Compose `version` warning, empty CSV handling, missing frontend test dependencies, staged-file persistence, and concurrent upload deduplication remain follow-up items.

## Phase 10: Authorized Scope Expansion - Five Confirmed CRITICAL Findings

- Incremental review forecast: 300-390 authored lines across five focused behavior work units plus cumulative evidence.
- 400-line budget risk: Medium.
- Delivery strategy: ask-on-risk with the already resolved `feature-branch-chain` boundary.
- Decision needed before apply: Resolved by the explicit authorized scope expansion in this apply session.
- Scope is limited to source-context import identity, staged-file persistence, containerized frontend API configuration, date-only form persistence, and timezone-aware dashboard timeseries buckets.

- [x] 10.1 Preserve legitimate repeated source rows while making exact source-row replay idempotent and equivalent cross-source transactions deterministic duplicates; document the two-key identity contract and add regression coverage.
- [x] 10.2 Persist staged import files through backend container recreation with an explicit Compose volume contract and validate pending and validated batch recovery.
- [x] 10.3 Make the frontend API base configurable at image build time and container runtime, wire `VITE_API_BASE_URL` through Docker/Compose, and add build/runtime contract coverage.
- [x] 10.4 Serialize date-only transaction form values as local-midnight instants under the browser's IANA timezone and verify save/retrieval calendar-date stability.
- [x] 10.5 Pass the requested IANA timezone into dashboard timeseries aggregation so buckets use local calendar dates.
- [x] 10.6 Re-run strict TDD focused tests, the complete backend suite, frontend build/typecheck, browser tests, migration/Compose recreation smoke, and relevant API checks with exact cumulative evidence.

### Confirmed Critical Finding Work Units

| Unit | Goal | Focused test command | Runtime harness | Rollback boundary |
|---|---|---|---|---|
| 25 | Define two-key import identity and preserve repeated source rows without cross-source duplicates | `cd backend && pytest tests/test_import_api.py -k "preserves_repeated_rows or cross_batch_duplicate or fingerprint"` | Compose Postgres imports a CSV containing identical rows, confirms both rows, replays the batch, then confirms an equivalent row from another source and verifies no accidental insert | Revert the source-context fingerprint model/migration, import confirmation checks, identity documentation, and mapped regression cases only |
| 26 | Recover pending and validated staged batches after backend recreation | `cd backend && pytest tests/test_import_api.py -k staged_batch` plus `pytest tests/test_compose_port_contract.py -k storage` | Upload a pending batch, recreate backend while retaining the named volume, map it; repeat with a validated batch and confirm it | Revert the backend `import_storage` volume mapping, storage contract test, and recovery regression only |
| 27 | Configure frontend API base at build and runtime | `cd backend && pytest tests/test_frontend_api_config_contract.py` plus runtime browser config test | Build/serve the frontend with a non-local API base, inject runtime config, and verify browser requests target the configured API origin | Revert frontend runtime-config bootstrap, API client resolution, Docker/Compose wiring, and configuration regressions only |
| 28 | Preserve selected local calendar dates on transaction form save and retrieval | `cd backend && pytest tests/test_frontend_upload_step_contract.py -k "transaction_edit or new_transaction_form"` | Browser contexts in `America/Los_Angeles` and `Asia/Tokyo` save a selected date and assert the emitted instant maps back to that same local date | Revert the date-only form serialization/retrieval helpers and browser regressions only |
| 29 | Aggregate dashboard timeseries by requested local calendar date | `cd backend && pytest tests/test_dashboard_api.py -k timeseries` | Compose API creates offset transactions and verifies `America/New_York` and `Asia/Tokyo` timeseries buckets | Revert timezone propagation through dashboard service/repository and its API regression only |
| 30 | Re-run all acceptance gates and preserve unrelated warning follow-ups | `cd backend && pytest`; `cd frontend && npm run build`; `cd frontend && npx tsc --noEmit`; `git diff --check` | Alternate-port Compose build, Postgres migration, backend recreation with named staging volume, frontend configured-origin browser smoke, API checks, and direct route checks | Revert only Phase 10 evidence additions in this task artifact and `apply-progress.md`; behavior units remain independently revertible under Units 25-29 |

### Phase 10 Identity Contract

- `record_fingerprint` is the semantic fingerprint of normalized transaction content, including the canonical UTC instant, transaction type, category, description, amount, currency, and product.
- A repeated row in one uploaded source is legitimate when its source context differs; mapping MUST retain every source row and MUST NOT collapse same-batch semantic fingerprints.
- `source_fingerprint` is the deterministic exact-source identity derived from the immutable upload content hash and source row number. It is unique and protects replay/concurrent confirmation of the same source row.
- Semantic fingerprints remain duplicate candidates across different source batches. Confirmation MUST serialize the semantic check and roll back the whole batch if an equivalent transaction already exists in another source context.
- Exact file re-upload remains rejected by the existing content-hash uniqueness contract; remapping or retrying a confirmed batch remains idempotent.

### Phase 10 Evidence

- Focused import regressions: `cd backend && pytest tests/test_import_api.py -k "preserves_repeated_rows or cross_batch_duplicate or fingerprint or staged_batch"` -> passed; full import module -> `18 passed`.
- Compose storage contract: `cd backend && pytest tests/test_compose_port_contract.py -k storage` -> `1 passed`; Compose config includes `elite-intel_import_storage` mounted at `/tmp/elite-imports`.
- Frontend API configuration: `cd backend && pytest tests/test_frontend_api_config_contract.py` -> `2 passed`; runtime browser contract -> `1 passed`; container Playwright smoke observed `5` requests to `https://api.example.test/api/v1/` after runtime configuration injection.
- Calendar regressions: `cd backend && pytest tests/test_frontend_upload_step_contract.py -k "transaction_edit or new_transaction_form"` -> `3 passed`; `cd backend && pytest tests/test_dashboard_api.py -k timeseries` -> `1 passed`.
- Final gates: `cd backend && pytest` -> `48 passed`; `cd frontend && npm run build && npx tsc --noEmit` -> passed; `git diff --check` and `docker compose config --quiet` -> passed.
- Runtime acceptance: Postgres healthy, backend health returned `{"status":"ok"}`, Alembic `010_source_context_identity (head)`, pending and validated batches recovered after two backend restarts, and the named staging volume remained present.

## Phase 11: Authorized Scope Expansion - Three CRITICAL Blockers

- Incremental review forecast: 260-380 authored lines across three behavior work units plus cumulative evidence.
- 400-line budget risk: Medium.
- Delivery strategy: ask-on-risk with the already resolved `feature-branch-chain` boundary.
- Decision needed before apply: Resolved by the explicit remediation authorization in this apply session.
- Scope is limited to migration sequencing, date-only CSV business timezone parsing, and requested timeseries granularity.

- [x] 11.1 Make migrations 008 and 009 preserve semantic duplicates until migration 010 changes the identity model; handle only conflicting `(import_batch_id, source_row_number)` identities and cover fresh/existing upgrade paths deterministically.
- [x] 11.2 Parse date-only CSV values at local midnight in the configured business/IANA timezone and add negative-offset and positive-offset backend/API regressions.
- [x] 11.3 Implement `day`, `week`, and `month` timeseries granularity with requested IANA timezone bucket labels and add API/repository coverage for every granularity.
- [x] 11.4 Run strict TDD focused tests, `cd backend && pytest`, frontend build/typecheck, browser tests, migration and alternate-port Compose/API smoke, and append exact cumulative evidence without changing unrelated warning follow-ups.

### Phase 11 Critical Remediation Work Units

| Unit | Goal | Focused test command | Runtime harness | Rollback boundary |
|---|---|---|---|---|
| 31 | Preserve legitimate semantic repeats through migrations 008-010 while resolving only source-row conflicts | `cd backend && pytest tests/test_import_migration_upgrade.py` | Fresh and upgrade-from-009 Postgres migration smoke with repeated semantic fingerprints in distinct source contexts and a same-source-row conflict | Revert migrations 008, 009, 010 and migration upgrade regressions only |
| 32 | Apply the configured business timezone to date-only CSV values | `cd backend && pytest tests/test_import_api.py -k business_timezone` | Alternate-port Compose/API CSV mapping smoke under `America/New_York` and `Asia/Tokyo`, asserting persisted UTC instants map to the selected local date | Revert `IMPORT_DEFAULT_TIMEZONE` configuration, import date parsing, `.env.example`, and date-only API regressions only |
| 33 | Honor day/week/month timeseries requests and preserve IANA bucket labels | `cd backend && pytest tests/test_dashboard_api.py -k granularity tests/test_transaction_repository.py` | Alternate-port Compose/API smoke creates offset transactions and verifies day, ISO-week Monday, and month-first labels in the requested timezone | Revert dashboard API/service/repository granularity propagation and its API/repository tests only |

### Phase 11 Evidence

- Migration regressions: `cd backend && pytest tests/test_import_migration_upgrade.py` -> `5 passed`; temporary Postgres upgraded through `009_unique_import_fingerprints`, seeded two distinct source contexts with one semantic fingerprint, upgraded to `010_source_context_identity`, and returned `2 semantic_repeats, 2 source_fingerprints`.
- Date-only CSV regressions: `cd backend && pytest tests/test_import_api.py -k business_timezone` -> `2 passed`; `America/New_York` mapped `12/08/2026` to `2026-08-12T04:00:00Z`, and `Asia/Tokyo` mapped it to `2026-08-11T15:00:00Z`.
- Compose timezone contract: `cd backend && pytest tests/test_compose_port_contract.py` -> `4 passed`; `docker compose config --quiet` -> exit `0`.
- Timeseries regressions: `cd backend && pytest tests/test_dashboard_api.py -k granularity tests/test_transaction_repository.py` -> `6 passed, 5 deselected`; API and repository coverage asserted day labels, ISO-week Monday labels, month-first labels, and `America/New_York` local conversion.
- Complete backend gate: `cd backend && pytest` -> `60 passed in 17.11s`, exit `0`.
- Frontend gates: `cd frontend && npm run build && npx tsc --noEmit` -> exit `0`; Vite retained the existing approximately `705.04 kB` chunk warning.
- Browser gate: `cd backend && pytest tests/test_frontend_upload_step_contract.py` -> `12 passed in 17.58s`; alternate-port Compose Playwright smoke returned HTTP `200` and rendered `Import Transactions`, `Transaction History`, and `Add Transaction` for `/import`, `/transactions`, and `/transactions/new`.
- Alternate-port Compose/API smoke: `POSTGRES_PORT=55437 FRONTEND_PORT=43003 IMPORT_DEFAULT_TIMEZONE=America/New_York docker compose up -d --build`; Postgres healthy, backend health returned `{"status":"ok"}`, frontend `/import` returned `200`, Alembic reported `010_source_context_identity (head)`, CORS allowed `http://localhost:43003`, date-only mapping returned `2026-08-12T04:00:00Z`, and timeseries returned labels `2026-08-20`, `2026-08-17`, and `2026-08-01` for day/week/month.
- Diff validation: `git diff --check` -> exit `0`.

### Phase 11 Rollback Boundaries

- Migration sequencing: revert `backend/app/db/migrations/versions/008_protect_import_confirmation.py`, `009_unique_import_fingerprints.py`, `010_source_context_import_identity.py`, and `backend/tests/test_import_migration_upgrade.py`; this removes only migration identity-sequencing remediation.
- CSV business timezone: revert `backend/app/core/config.py`, `backend/app/services/import_service.py`, `.env.example`, `docker-compose.yml`, `backend/tests/test_import_api.py` business-timezone cases, and the Compose timezone contract; CSV validation and non-date import behavior remain independently revertible.
- Timeseries granularity: revert `backend/app/api/v1/dashboard.py`, `backend/app/services/dashboard_service.py`, `backend/app/repositories/transaction_repository.py`, `backend/tests/test_dashboard_api.py` granularity cases, and `backend/tests/test_transaction_repository.py`; existing day-only timezone bucketing and unrelated dashboard endpoints remain otherwise unchanged.

## Phase 12: Explicit Final Remediation - Amount Precision

- Incremental review scope: one remaining CRITICAL amount-precision defect under the existing `feature-branch-chain` boundary.
- Delivery strategy: `ask-on-risk` with the already resolved `feature-branch-chain` boundary.
- Decision needed before apply: Resolved by the explicit final remediation authorization in this apply session.
- Scope is limited to CSV monetary mapping precision, locale-grouped whole/cents values, and confirmation safety.

- [x] 12.1 Add RED/GREEN regression coverage proving that CSV amounts with more than two fractional digits, including `0,004` under `es_AR`, become row-level invalid data during mapping.
- [x] 12.2 Preserve valid locale-grouped whole/cents values for `es_AR` and `en_US` while rejecting excess precision before any storage quantization.
- [x] 12.3 Prove confirmation inserts only storage-safe valid rows and never inserts an amount rejected for excess precision.
- [x] 12.4 Re-run the complete backend suite, frontend build/typecheck, browser tests, and alternate-port Compose/API smoke with exact evidence while preserving unrelated warning follow-ups.

### Final Amount Precision Work Units

| Unit | Goal | Focused test command | Runtime harness | Rollback boundary |
|---|---|---|---|---|
| 35 | Reject excess-precision and sub-cent CSV values during mapping | `cd backend && pytest tests/test_import_api.py -k "fractional_digits or sub_cent or grouped_whole_and_cent"` -> 6 passed | Alternate-port Compose API maps `es_AR` values `1234,567` and `0,004` as `INVALID_AMOUNT`, while `1.234` and `1.234,56` map to `1234.00` and `1234.56`; `en_US` is covered by the focused API regression | Revert `AMOUNT_QUANTUM`, `MAX_AMOUNT_FRACTIONAL_DIGITS`, and the amount precision check in `backend/app/services/import_service.py`, plus the precision/grouping regressions in `backend/tests/test_import_api.py` |
| 36 | Keep confirmation safe after invalid precision mapping rows | `cd backend && pytest tests/test_import_api.py -k confirmation_only_inserts` -> 1 passed | The same Compose batch confirms with `records_inserted=2` from four rows, with only the two valid grouped values persisted and no excess-precision or sub-cent transaction inserted | Revert the confirmation safety regression in `backend/tests/test_import_api.py`; no unrelated confirmation hardening or storage behavior is removed |
| 37 | Re-run complete acceptance gates and preserve warning follow-ups | `cd backend && pytest` -> 67 passed; frontend build/typecheck and browser module passed | `POSTGRES_PORT=55439 FRONTEND_PORT=43004 IMPORT_DEFAULT_LOCALE=es_AR docker compose up -d --build`; Postgres healthy, backend health passed, frontend routes/browser passed, API/CORS smoke passed, and Alembic reached `010_source_context_identity (head)` | Revert only the Phase 12 evidence additions in this file and `apply-progress.md`; Units 35-36 remain independently revertible |

### Final Amount Precision Contract

- The parser MUST reject source monetary values with more than two fractional digits after locale normalization, rather than rounding them into the `Numeric(14,2)` storage scale.
- `es_AR` MUST continue accepting grouped whole values such as `1.234` and grouped cent values such as `1.234,56`.
- `en_US` MUST continue accepting grouped whole values such as `1,234` and grouped cent values such as `1,234.56`.
- Rejected excess-precision and sub-cent values MUST be represented as `INVALID_AMOUNT` row-level mapping errors before confirmation.
