# Apply Progress: mvp-integration-hardening

## Batch

- Date: 2026-08-12
- Mode: Strict TDD
- Delivery: chained work unit (`feature-branch-chain`)
- Current work unit: Final autonomous closeout — live stack verification + acceptance evidence + final refactor slice

## Completed Tasks (cumulative)

- [x] 1.1 In `backend/tests/test_import_api.py`, add RED tests for non-CSV upload rejection (`400`) and CSV-only error wording.
- [x] 1.2 In `backend/tests/test_import_api.py`, add RED test proving valid `.csv` upload still follows the existing success path.
- [x] 1.3 In `.env.example`, align DB URL guidance with compose/psycopg runtime expectations if mismatch is found during baseline verification.
- [x] 2.1 Update `backend/app/services/import_service.py` to accept CSV only (extension/content-type checks) and reject non-CSV deterministically.
- [x] 2.2 Ensure backend validation messaging remains explicitly CSV-only across the import upload path in `backend/app/services/import_service.py`.
- [x] 2.3 Update `frontend/src/components/import/UploadStep.tsx` to enforce CSV-only UI contract (`accept` filter + user-facing copy).
- [x] 3.1 Run `cd backend && pytest tests/test_import_api.py -k "csv or import"` to turn RED→GREEN and capture command output as evidence.
- [x] 3.2 Run live stack verification (`docker compose up -d`, health/migrations, `/api/v1` smoke, CORS check) and capture dated evidence.
- [x] 3.3 Run frontend gates (`cd frontend && npm run build` and `cd frontend && npx tsc --noEmit`) plus manual `/import` smoke.
- [x] 4.1 Refactor import validation/test fixtures for clarity without broadening scope in `backend/app/services/import_service.py` and `backend/tests/test_import_api.py`.
- [x] 4.2 Update `tasks/mvp-implementation.md` §5: check only evidence-backed items from this run; keep unproven criteria unchecked.
- [x] 4.3 Ensure acceptance wording in `tasks/mvp-implementation.md` reflects CSV-only scope (remove Excel claims).
- [x] 4.4 Prepare conventional commit slices by work unit: backend contract+tests, frontend CSV UX, acceptance evidence/docs.

## TDD Cycle Evidence

| Task | Test File | Layer | Safety Net | RED | GREEN | TRIANGULATE | REFACTOR |
|---|---|---|---|---|---|---|---|
| 1.1 | `backend/tests/test_import_api.py` | Integration | ✅ `pytest tests/test_import_api.py` → `2 passed` | ✅ Added `test_import_rejects_non_csv_upload_with_csv_only_message` | ✅ `pytest tests/test_import_api.py -k "csv or import"` → `6 passed` | ✅ Added second rejection path (`.csv` + non-CSV MIME) | ➖ None needed in test layer |
| 1.2 | `backend/tests/test_import_api.py` | Integration | ✅ `pytest tests/test_import_api.py` → `2 passed` | ✅ Added `test_import_accepts_csv_upload_under_csv_only_contract` | ✅ `pytest tests/test_import_api.py -k "csv or import"` → `6 passed` | ✅ Added uppercase extension case (`SAMPLE.CSV`) | ➖ None needed in test layer |
| 2.1 | `backend/tests/test_import_api.py` | Integration | ✅ `pytest tests/test_import_api.py` → `2 passed` | ✅ Existing new tests failed before implementation (`1 failed, 1 passed`) | ✅ `pytest tests/test_import_api.py -k "csv or import"` → `6 passed` | ✅ Reject + accept scenarios enforce real logic | ✅ Extracted CSV constants and `_validate_csv_upload()` |
| 2.2 | `backend/tests/test_import_api.py` | Integration | ✅ `pytest tests/test_import_api.py` → `2 passed` | ✅ RED asserted CSV-only message content | ✅ `pytest tests/test_import_api.py -k "csv or import"` → `6 passed` | ✅ Message verified across multiple rejection paths | ✅ Reused single message constant (`CSV_ONLY_ERROR_MESSAGE`) |
| 1.3 | `.env.example` | Config | N/A (config update) | ✅ Mismatch identified vs compose driver scheme | ✅ File updated to `postgresql+psycopg://...` | ➖ Single structural output | ➖ None needed |
| 3.1 | `backend/tests/test_import_api.py` | Integration | N/A (execution evidence task) | ✅ Command selected from task plan | ✅ `pytest tests/test_import_api.py -k "csv or import"` → `6 passed` | ➖ Covered by prior test triangulation | ➖ None needed |
| 2.3 | `backend/tests/test_frontend_upload_step_contract.py` | Unit (contract) | ✅ `npm run build && npx tsc --noEmit` baseline green | ✅ Added contract tests for CSV-only `accept` and CSV-only copy; initial run failed (`2 failed`) | ✅ `pytest tests/test_frontend_upload_step_contract.py` → `2 passed` | ✅ Happy path (`accept=".csv"`) + edge guard (`Excel` claim absent) | ➖ None needed |
| 3.3 | `backend/tests/test_frontend_upload_step_contract.py` + frontend build/typecheck | Integration boundary evidence | N/A (execution evidence task) | ✅ Frontend verification command set from task plan | ✅ `npm run build` passed; `npx tsc --noEmit` passed; `/import` smoke captured | ➖ Covered by focused contract tests + runtime smoke | ➖ None needed |
| 4.1 | `backend/tests/test_import_api.py` + `backend/app/services/import_service.py` | Integration + unit helper refactor | ✅ `pytest tests/test_import_api.py` → `6 passed` baseline before refactor | ✅ Added parametrized coverage for supported CSV MIME aliases + helper fixture wrappers first | ✅ `pytest tests/test_import_api.py -k "csv or import"` → `8 passed` | ✅ Multiple accepted MIME cases (`text/csv`, `application/vnd.ms-excel`, `text/plain`) + reject branch retained | ✅ Extracted `_is_allowed_csv_extension`, `_normalize_upload_content_type`, `_is_allowed_csv_content_type` and reduced fixture duplication |
| 3.2 | `docker compose` runtime harness + API smoke script | Runtime integration | N/A (runtime evidence task) | ✅ Live-smoke command plan authored before execution | ✅ Compose stack launched (`postgres` healthy, `backend` up), Alembic head verified, all `/api/v1` endpoint families exercised successfully | ✅ Included both positive/negative import checks plus CORS preflight path | ➖ No code refactor required for runtime-only evidence task |
| 4.2 | `tasks/mvp-implementation.md` | Acceptance artifact | N/A (docs-only task) | ✅ Checklist update plan mapped to explicit evidence first | ✅ All §5 checks toggled based on captured command/runtime outputs | ➖ Single checklist artifact with one final evidence set | ✅ Removed stale unchecked state after proof-backed verification |
| 4.3 | `tasks/mvp-implementation.md` | Acceptance artifact | N/A (docs-only task) | ✅ CSV-only wording requirement identified before edit | ✅ Criterion changed to `CSV import + invalid row report` | ➖ Single wording branch | ✅ Removed Excel claim to match CSV-only contract |
| 4.4 | `openspec/changes/mvp-integration-hardening/tasks.md` + apply notes | Work-unit/commit planning | ✅ Existing work-unit split reviewed | ✅ Commit-slice plan captured before final status | ✅ Tasks and apply-progress now reflect all three slices complete | ➖ Planning cleanup only |

## Test Summary

- **Total tests written**: 8 (`backend/tests/test_import_api.py` 6 existing+new, `backend/tests/test_frontend_upload_step_contract.py` 2)
- **Total tests passing**: 16 (`cd backend && pytest`)
- **Layers used**: Unit (2 contract assertions), Integration (backend API/import tests), Runtime live smoke (`docker compose` + HTTP/CORS)
- **Approval tests** (refactoring): Existing API contract tests in `backend/tests/test_import_api.py` retained and expanded before helper refactor
- **Pure functions created**: 3 (`_is_allowed_csv_extension`, `_normalize_upload_content_type`, `_is_allowed_csv_content_type`)

## Work Unit Evidence

### Unit 1 — Backend CSV-only contract

| Evidence | Required value |
|---|---|
| Focused test command and exact result | `cd backend && pytest tests/test_import_api.py -k "csv or import"` → `collected 8 items`, `8 passed in 0.68s`, exit 0 |
| Runtime harness command/scenario and exact result | `POSTGRES_PORT=55432 docker compose up -d postgres backend` + `POSTGRES_PORT=55432 docker compose ps` + `curl -sf http://localhost:8000/api/v1/health` + `POSTGRES_PORT=55432 docker compose exec -T backend alembic current` → backend up on `:8000`, postgres healthy on `:55432`, health returned `{"status":"ok"}`, Alembic at `007_enable_pg_trgm (head)` |
| Rollback boundary | Revert only `.env.example`, `backend/app/services/import_service.py`, and CSV-only assertions/helpers in `backend/tests/test_import_api.py`; leaves frontend and acceptance-checklist artifacts untouched |

### Unit 2 — Frontend CSV-only UX

| Evidence | Required value |
|---|---|
| Focused test command and exact result | `cd backend && pytest tests/test_frontend_upload_step_contract.py` → `collected 2 items`, `2 passed in 0.04s`, exit 0 |
| Runtime harness command/scenario and exact result | `cd frontend && npm run dev -- --host 127.0.0.1 --port 4173` (background) + `npx playwright screenshot --wait-for-selector "input[type=file]" --wait-for-timeout 1500 http://127.0.0.1:4173/import /tmp/opencode/import-smoke-final.png` → screenshot captured showing `1) Upload CSV file` + CSV-only helper copy |
| Rollback boundary | Revert only `frontend/src/components/import/UploadStep.tsx` and `backend/tests/test_frontend_upload_step_contract.py`; backend CSV validation behavior remains intact |

### Unit 3 — Live verification + acceptance evidence

| Evidence | Required value |
|---|---|
| Focused test command and exact result | `cd backend && pytest` → `collected 16 items`, `16 passed in 2.28s`, exit 0 |
| Runtime harness command/scenario and exact result | `POSTGRES_PORT=55432 docker compose up -d postgres backend` followed by live `/api/v1` smoke script (categories create, transactions create/get/update/list/delete, dashboard summary/categories/timeseries, products list, imports upload/mapping/confirm/list/get, non-CSV reject, duplicate-file reject, invalid-row report, CORS `OPTIONS /api/v1/transactions`) → all assertions passed; summary output: `transactions 201 201 200 200 204`, `dashboard 200 200 200`, `imports 201 200 200 400 400 201 200`, `invalid_rows 1`, `products 200`, `cors 200 http://localhost:3000`; backend logs confirm request path success and container startup with Alembic Postgres migration context |
| Rollback boundary | Revert only acceptance evidence edits in `tasks/mvp-implementation.md`, `openspec/changes/mvp-integration-hardening/tasks.md`, and this `apply-progress.md`; keeps backend/frontend feature behavior untouched |

## Chained Commit Slice Readiness (Task 4.4)

- Slice A (backend contract + tests): `backend/app/services/import_service.py`, `backend/tests/test_import_api.py`, `.env.example`
- Slice B (frontend CSV UX): `frontend/src/components/import/UploadStep.tsx`, `backend/tests/test_frontend_upload_step_contract.py`
- Slice C (acceptance evidence/docs): `tasks/mvp-implementation.md`, `openspec/changes/mvp-integration-hardening/tasks.md`, `openspec/changes/mvp-integration-hardening/apply-progress.md`

## Remaining Tasks

- None. All tasks in `openspec/changes/mvp-integration-hardening/tasks.md` are checked `[x]`.

## Final Status

- Apply phase is complete for `mvp-integration-hardening`.
- Strict-TDD evidence is cumulative and merged from prior batches plus this final batch.
- State is ready for `sdd-verify`.

## Notes

- Default `docker compose up -d` on this host still conflicts on ports `5432` and `3000`; verification was completed with `POSTGRES_PORT=55432` while keeping backend on `:8000` for API smoke and CORS checks.
- Frontend container could not be started due to host `:3000` collision, but required frontend acceptance evidence was completed via local Vite runtime smoke (`:4173`) plus build/typecheck gates.

## Remediation Batch: Approved Verification Blockers

- Date: 2026-08-12
- Mode: Strict TDD
- Delivery: focused remediation slice within the resolved `feature-branch-chain`
- Scope: runtime frontend contract coverage and configurable Compose host bindings only
- Prior apply-progress sections are preserved above and remain cumulative context.

### Completed Remediation Tasks

- [x] 5.1 Replaced source-string-only frontend contract assertions with Playwright runtime coverage that executes the Vite-served production `UploadStep` path.
- [x] 5.2 Parameterized and documented the Compose frontend host binding with `FRONTEND_PORT`, preserved `POSTGRES_PORT`, mapped frontend host ports to nginx container port `80`, and derived the default frontend CORS origin from `FRONTEND_PORT` without changing default values.
- [x] 5.3 Re-ran the complete backend suite, frontend build/typecheck, runtime frontend test, and full alternate-port Compose smoke with direct evidence.

### TDD Cycle Evidence - Remediation

| Task | Test File | Layer | Safety Net | RED | GREEN | TRIANGULATE | REFACTOR |
|---|---|---|---|---|---|---|---|
| 5.1 | `backend/tests/test_frontend_upload_step_contract.py` | Browser runtime | ✅ Existing static contract tests -> `2 passed` before replacement | ✅ Written; runtime assertions replaced source inspection before implementation changes | ✅ `cd backend && pytest tests/test_frontend_upload_step_contract.py` -> `2 passed in 3.89s` | ✅ Rendered copy/picker plus selected-file state and enabled upload state | ✅ Removed all source-string assertions and exercised the production route with Chromium |
| 5.2 | `backend/tests/test_compose_port_contract.py` | Compose configuration | N/A (new test file) | ✅ Written; `2 failed` against the hardcoded frontend binding | ✅ `cd backend && pytest tests/test_compose_port_contract.py` -> `2 passed in 0.21s` | ✅ Default ports and alternate ports both verify unchanged container targets | ✅ Added nested default origin interpolation so alternate frontend ports keep CORS aligned |
| 5.3 | `tasks.md` and `apply-progress.md` | Runtime/evidence | ✅ Prior full suite and frontend gates were green | ✅ Written; remediation command plan recorded before execution | ✅ Full gates and alternate-port Compose smoke passed | ✅ Same stack verified through container status, HTTP, Alembic, CORS, and browser checks | ✅ Evidence is additive and does not rewrite prior apply history |

### Remediation Test Summary

- **New runtime tests**: 4 total (`2` browser tests and `2` Compose configuration tests).
- **Full backend suite**: `cd backend && pytest` -> `18 passed in 8.42s`, exit `0`.
- **Frontend build**: `cd frontend && npm run build` -> passed, exit `0`; existing Vite chunk warning remains (`704.51 kB`).
- **Frontend typecheck**: `cd frontend && npx tsc --noEmit` -> passed with no output, exit `0`.
- **Runtime frontend test**: `cd backend && pytest tests/test_frontend_upload_step_contract.py` -> `2 passed`, with Vite and headless Chromium executing the route and file-selection behavior.
- **Static assertion status**: `backend/tests/test_frontend_upload_step_contract.py` no longer reads `UploadStep.tsx` source text.

### Remediation Work Unit Evidence

#### Unit 4 - Runtime frontend CSV contract

| Evidence | Required value |
|---|---|
| Focused test command and exact result | `cd backend && pytest tests/test_frontend_upload_step_contract.py` -> `collected 2 items`, `2 passed in 3.89s`, exit `0` |
| Runtime harness command/scenario and exact result | The same pytest module starts Vite on a free loopback port, launches headless Chromium, opens `/import`, verifies rendered `Upload CSV file` and CSV-only helper copy, asserts `accept=".csv"`, selects `transactions.csv`, and observes the production selected-file state and enabled upload button -> passed |
| Rollback boundary | Revert only `backend/tests/test_frontend_upload_step_contract.py`; this removes remediation proof without changing frontend production behavior |

#### Unit 5 - Alternate-port Compose bindings

| Evidence | Required value |
|---|---|
| Focused test command and exact result | `cd backend && pytest tests/test_compose_port_contract.py` -> `collected 2 items`, `2 passed in 0.21s`, exit `0` |
| Runtime harness command/scenario and exact result | `docker compose down && POSTGRES_PORT=55433 FRONTEND_PORT=43000 docker compose up -d --build`; `docker compose ps` showed `elite_postgres` healthy on `55433->5432`, `elite_backend` up on `8000->8000`, and `elite_frontend` up on `43000->80`; `docker inspect -f '{{.State.Health.Status}}' elite_postgres` -> `healthy`; backend health -> `{"status":"ok"}`; frontend HTTP -> `200`; `docker compose exec -T backend alembic current` -> `007_enable_pg_trgm (head)`; CORS preflight allowed `http://localhost:43000`; compose frontend browser smoke reached `/import` and passed CSV assertions |
| Rollback boundary | Revert only `docker-compose.yml`, `.env.example`, and `backend/tests/test_compose_port_contract.py`; the Postgres container target `5432`, frontend nginx target `80`, backend API port `8000`, and application API behavior remain otherwise unchanged |

#### Unit 6 - Complete gates and evidence

| Evidence | Required value |
|---|---|
| Focused test command and exact result | `cd backend && pytest` -> `18 passed in 8.42s`; `cd frontend && npm run build` -> pass; `cd frontend && npx tsc --noEmit` -> pass |
| Runtime harness command/scenario and exact result | Full alternate-port Compose stack was built and started together, then checked with Compose status, Postgres health, backend health, frontend HTTP, Alembic head, CORS preflight, and a headless browser route smoke -> all passed |
| Rollback boundary | Revert only the remediation evidence additions in `openspec/changes/mvp-integration-hardening/tasks.md` and this `apply-progress.md`; implementation and tests remain independently revertible by Units 4 and 5 boundaries |

### Current Remediation Status

- All remediation tasks in `openspec/changes/mvp-integration-hardening/tasks.md` are checked `[x]`.
- The two verification blockers are addressed without changing the API surface, container ports, data model, or CSV-only scope.
- The alternate-port Compose stack remains running for independent inspection at frontend `http://localhost:43000`, backend `http://localhost:8000`, and Postgres host port `55433`.

## Remediation Batch: Authorized Scope Expansion - Confirmed Critical Findings

- Date: 2026-08-12
- Mode: Strict TDD
- Delivery: focused remediation slice within the resolved `feature-branch-chain`
- Scope: four confirmed CRITICAL blockers only; review warnings remain follow-ups unless directly required by a blocker fix.
- Prior apply-progress sections are preserved above and remain cumulative context.

### Completed Remediation Tasks

- [x] 6.1 Made import confirmation atomic and idempotent for concurrent duplicate requests with a database row lock, a database uniqueness constraint, and a concurrent regression test.
- [x] 6.2 Configured the nginx frontend image with SPA fallback for direct client-route navigation and refresh.
- [x] 6.3 Corrected the import mapping UI to submit backend-required `occurred_at`, including absent/custom date detection coverage.
- [x] 6.4 Made date-only/timestamp formatting, date input payloads, and edit initialization timezone-safe.
- [x] 6.5 Re-ran backend, frontend, runtime frontend, migration, and Compose/browser acceptance gates.

### TDD Cycle Evidence - Authorized Scope Expansion

| Task | Test File | Layer | Safety Net | RED | GREEN | TRIANGULATE | REFACTOR |
|---|---|---|---|---|---|---|---|
| 6.1 | `backend/tests/test_import_confirmation_concurrency.py` | Integration/runtime API | N/A (new file) | ✅ Written; pre-fix run produced two committed transactions | ✅ `pytest tests/test_import_confirmation_concurrency.py` -> `1 passed` | ✅ Two simultaneous requests, both successful and one persisted transaction | ✅ Added `FOR UPDATE` batch retrieval, confirmed-state replay, unique constraint, and integrity recovery |
| 6.2 | `backend/tests/test_frontend_spa_fallback_contract.py` | Configuration/runtime | N/A (new file) | ✅ Written; config file was absent | ✅ `pytest tests/test_frontend_spa_fallback_contract.py` -> `1 passed` | ➖ Structural-only configuration with one required fallback directive; runtime route smoke supplies behavior proof | ✅ Isolated nginx config and copied it in the image without changing app routing |
| 6.3 | `backend/tests/test_import_api.py` + `backend/tests/test_frontend_upload_step_contract.py` | API/browser E2E | ✅ Existing import API -> `8 passed`; existing browser contract -> `2 passed` | ✅ UI test written first and failed with submitted key `date`; backend contract test remained green because the backend already required `occurred_at` | ✅ `pytest tests/test_import_api.py tests/test_frontend_upload_step_contract.py` -> `13 passed` | ✅ Backend custom-header mapping plus browser custom-date mapping request | ➖ Replaced the UI field key only; no backend contract broadening |
| 6.4 | `backend/tests/test_frontend_upload_step_contract.py` | Browser runtime | ✅ Existing browser contract -> `3 passed` before the new date test | ✅ Test written before timezone implementation; old local-midnight payload was the targeted failure condition | ✅ `pytest tests/test_frontend_upload_step_contract.py` -> `4 passed` | ✅ Negative-offset edit initialization and UTC-midnight submit behavior | ✅ Centralized date-prefix preservation and UTC input conversion in `frontend/src/utils/format.ts` |
| 6.5 | Full gate and runtime evidence | Integration/runtime | ✅ Prior cumulative gates preserved above | ✅ Command set recorded before final execution | ✅ All listed gates passed | ✅ Postgres migration, Compose health, HTTP routes, browser routes, API concurrency, and UI mapping smoke | ✅ Evidence appended without rewriting prior batches |

### Remediation Test Summary

- **New regression tests**: 5 tests across 4 new/modified test paths (`1` concurrent confirmation test, `1` SPA config test, `1` backend custom mapping test, and `2` browser mapping/date tests; existing browser coverage was retained).
- **Focused critical remediation tests**: `cd backend && pytest tests/test_import_confirmation_concurrency.py` -> `1 passed`; `cd backend && pytest tests/test_frontend_spa_fallback_contract.py` -> `1 passed`; `cd backend && pytest tests/test_frontend_upload_step_contract.py` -> `4 passed`; import API suite -> `9 passed`.
- **Full backend suite**: `cd backend && pytest` -> `23 passed in 7.40s`, exit `0`.
- **Frontend build**: `cd frontend && npm run build` -> passed, exit `0`; existing Vite chunk warning remains (`704.59 kB`).
- **Frontend typecheck**: `cd frontend && npx tsc --noEmit` -> passed with no output, exit `0`.
- **Migration**: `DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:55433/elite_db alembic upgrade head` -> passed; Compose backend reports `008_protect_import_confirmation (head)`.
- **Runtime frontend browser test**: `cd backend && pytest tests/test_frontend_upload_step_contract.py` -> `4 passed`; Vite and Chromium exercised CSV upload, custom `occurred_at` mapping submission, and `America/Los_Angeles` date editing.

### Remediation Work Unit Evidence

#### Unit 7 - Concurrent import confirmation protection

| Evidence | Required value |
|---|---|
| Focused test command and exact result | `cd backend && pytest tests/test_import_confirmation_concurrency.py` -> `1 passed in 1.15s`, exit `0`; test used two concurrent HTTP requests against independent SQLite sessions and asserted both idempotent responses plus one persisted transaction |
| Runtime harness command/scenario and exact result | Live Postgres Compose API harness uploaded a unique CSV, mapped it, submitted two concurrent `POST /api/v1/imports/{batch_id}/confirm` requests, and queried the unique transaction; output was two `200/CONFIRMED/1` responses and `matching_transactions: 1` |
| Rollback boundary | Revert `backend/app/services/import_service.py`, `backend/app/repositories/import_repository.py`, `backend/app/models/transaction.py`, `backend/app/db/migrations/versions/008_protect_import_confirmation.py`, and the concurrency regression test; this removes only confirmation hardening |

#### Unit 8 - nginx SPA fallback

| Evidence | Required value |
|---|---|
| Focused test command and exact result | `cd backend && pytest tests/test_frontend_spa_fallback_contract.py` -> `1 passed`, exit `0`; config contains `try_files $uri $uri/ /index.html;` |
| Runtime harness command/scenario and exact result | `POSTGRES_PORT=55433 FRONTEND_PORT=43000 docker compose up -d --build`; direct HTTP requests to `/`, `/import`, `/transactions`, and `/transactions/new` returned `200`; headless Chromium loaded `/import`, `/transactions`, and `/transactions/new` directly and rendered `Import Transactions`, `Transaction History`, and `Add Transaction` |
| Rollback boundary | Revert `frontend/nginx.conf`, the nginx `Dockerfile` copy line, and `backend/tests/test_frontend_spa_fallback_contract.py`; React route definitions and API behavior remain untouched |

#### Unit 9 - `occurred_at` import mapping contract

| Evidence | Required value |
|---|---|
| Focused test command and exact result | `cd backend && pytest tests/test_import_api.py tests/test_frontend_upload_step_contract.py` -> `13 passed`, exit `0` across backend mapping and browser contract coverage |
| Runtime harness command/scenario and exact result | Compose frontend browser smoke uploaded a unique CSV with an unrecognized `When occurred` header, selected it in the mapping UI, submitted validation, and rendered `3) Validation report` through the live backend; exit `0` |
| Rollback boundary | Revert `frontend/src/components/import/MappingStep.tsx`, the added backend custom-header regression, and the browser mapping regression; upload and backend-required mapping behavior outside this UI key alignment remain unchanged |

#### Unit 10 - Timezone-safe calendar dates

| Evidence | Required value |
|---|---|
| Focused test command and exact result | `cd backend && pytest tests/test_frontend_upload_step_contract.py` -> `4 passed in 7.24s`, exit `0`; browser test asserts edit value `2026-06-15` and submitted `2026-06-15T00:00:00.000Z` in `America/Los_Angeles` |
| Runtime harness command/scenario and exact result | Headless Chromium negative-offset runtime test loaded a timestamped edit form, preserved the calendar date, and submitted UTC midnight; passed |
| Rollback boundary | Revert `frontend/src/utils/format.ts`, `frontend/src/components/transactions/TransactionFormFields.tsx`, and the timezone regression test; transaction edit fields return to the previous local-midnight conversion only |

#### Unit 11 - Complete gates and evidence

| Evidence | Required value |
|---|---|
| Focused test command and exact result | `cd backend && pytest` -> `23 passed in 7.40s`; `cd frontend && npm run build` -> pass; `cd frontend && npx tsc --noEmit` -> pass; `git diff --check` -> pass |
| Runtime harness command/scenario and exact result | Alternate-port Compose stack built and ran with Postgres healthy, backend health `{"status":"ok"}`, migration head `008_protect_import_confirmation`, frontend HTTP/browser route smoke, live concurrent-confirmation smoke, and live custom-date mapping browser smoke -> all passed |
| Rollback boundary | Revert only the added Phase 6 evidence sections in `openspec/changes/mvp-integration-hardening/tasks.md` and `apply-progress.md`; implementation/test files remain independently revertible under Units 7-10 |

### Warnings Preserved as Follow-ups

- Vite production bundle warning remains at approximately `704.59 kB`; no code-splitting work was added to this blocker remediation.
- The ordinary backend pytest fixture remains in-memory SQLite; the critical confirmation contract was additionally exercised against the live Postgres Compose service, but no generalized Postgres pytest fixture was introduced.
- The Compose file emits the existing non-blocking warning that the `version` attribute is obsolete; no unrelated Compose cleanup was included.

### Current Remediation Status

- All Phase 6 remediation tasks in `openspec/changes/mvp-integration-hardening/tasks.md` are checked `[x]`.
- The four confirmed CRITICAL findings are addressed with cumulative TDD and runtime evidence.
- No commit was created.
- Apply phase is ready for `sdd-verify`.

## Remediation Batch: Authorized Scope Expansion - Five Critical Findings

- Date: 2026-08-13
- Mode: Strict TDD
- Delivery: focused remediation slice within the resolved `feature-branch-chain`
- Scope: the five critical findings explicitly authorized in this apply session.
- Prior apply-progress sections are preserved above and remain cumulative context.

### Completed Remediation Tasks

- [x] 7.1 Made migration `008_protect_import_confirmation.py` upgrade-safe for historical duplicate import transactions.
- [x] 7.2 Fixed DashboardPage transaction requests to use backend-compatible inclusive UTC datetime boundaries.
- [x] 7.3 Made inclusive period boundaries calendar-date stable in UTC-negative browser timezones.
- [x] 7.4 Added configured `es_AR` thousands parsing while preserving decimal amount values.
- [x] 7.5 Made absent or null mapped descriptions invalid without producing the literal `None`.
- [x] 7.6 Re-ran backend, frontend, browser, migration, and alternate-port Compose/API acceptance gates.

### TDD Cycle Evidence - Five Critical Findings

| Task | Test File | Layer | Safety Net | RED | GREEN | TRIANGULATE | REFACTOR |
|---|---|---|---|---|---|---|---|
| 7.1 | `backend/tests/test_import_migration_upgrade.py` | Migration integration | N/A (new) | ✅ Written; `pytest tests/test_import_migration_upgrade.py` -> `2 failed` before the cleanup helper existed | ✅ `pytest tests/test_import_migration_upgrade.py` -> `2 passed` | ✅ Duplicate group keeps the lowest id, rewires `import_rows`, preserves nullable/manual rows, and a clean history is idempotent | ✅ Isolated deterministic cleanup helper and documented earliest-committed-row data decision in migration |
| 7.2 | `backend/tests/test_frontend_upload_step_contract.py` | Browser runtime | ✅ Existing browser contract -> `4 passed` before this test | ✅ Written; date-only transaction query assertion failed before implementation | ✅ `pytest tests/test_frontend_upload_step_contract.py -k dashboard_transaction` -> `1 passed` | ✅ Both start-of-day and end-of-day boundaries are asserted for every DashboardPage transaction request | ✅ Centralized conversion in the transaction API client and preserved already-datetime values |
| 7.3 | `backend/tests/test_frontend_upload_step_contract.py` | Browser runtime | ✅ Existing browser contract -> `5 passed` before this test | ✅ Written; `1 failed` with `2026-08-21` returned for requested inclusive `2026-08-20` in `America/Los_Angeles` | ✅ `pytest tests/test_frontend_upload_step_contract.py -k custom_period` -> `1 passed` | ✅ Distinct custom start and end dates verify both inclusive boundaries | ✅ Added local calendar formatter and removed UTC serialization from date-only period output |
| 7.4 | `backend/tests/test_import_api.py` | Integration | ✅ Existing import API -> `9 passed` before these tests | ✅ Written; `pytest tests/test_import_api.py -k "argentine or absent_mapped_description"` -> `2 failed, 1 passed` before implementation | ✅ Same command -> `3 passed` | ✅ Thousands grouping (`1.234`) and decimal (`1234.56`) paths are both covered | ✅ Locale grouping decision is isolated to configured `es_AR`; existing mixed-separator behavior remains |
| 7.5 | `backend/tests/test_import_api.py` | Integration | ✅ Existing import API -> `9 passed` before these tests | ✅ Written; absent trailing CSV description produced a valid row before implementation | ✅ Same focused command -> `3 passed` after the shared null-value normalization | ✅ Missing mapped column and null trailing CSV value both normalize to empty validation input | ✅ Reused one `_clean_import_value` helper for required and optional mapped fields |
| 7.6 | Full gate and runtime evidence | Integration/runtime | ✅ Prior cumulative gates preserved above | ✅ Command set recorded before final execution | ✅ All listed gates passed | ✅ Postgres migration cleanup, Compose API, CORS, browser routes, and frontend runtime requests were exercised | ✅ Evidence appended without rewriting prior batches or follow-up warnings |

### Remediation Test Summary

- **New regression tests**: 7 tests across migration, browser, and import API paths.
- **Focused migration test**: `cd backend && pytest tests/test_import_migration_upgrade.py` -> `2 passed`, exit `0`.
- **Focused browser tests**: `cd backend && pytest tests/test_frontend_upload_step_contract.py -k "dashboard_transaction or custom_period"` -> `2 passed`, exit `0`.
- **Focused import tests**: `cd backend && pytest tests/test_import_api.py -k "argentine or absent_mapped_description"` -> `3 passed`, exit `0`.
- **Full backend suite**: `cd backend && pytest` -> `30 passed in 15.80s`, exit `0`.
- **Frontend build**: `cd frontend && npm run build` -> passed, exit `0`; existing Vite chunk warning remains at `704.71 kB`.
- **Frontend typecheck**: `cd frontend && npx tsc --noEmit` -> passed with no output, exit `0`.
- **Diff validation**: `git diff --check` -> passed, exit `0`.

### Remediation Work Unit Evidence

#### Unit 12 - Upgrade-safe migration cleanup

| Evidence | Required value |
|---|---|
| Focused test command and exact result | `cd backend && pytest tests/test_import_migration_upgrade.py` -> `2 passed`, exit `0` |
| Runtime harness command/scenario and exact result | Temporary Postgres on host port `55434`: `DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:55434/elite_db alembic upgrade 007_enable_pg_trgm`, seed duplicate ids `100/101` for batch `1`, then `DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:55434/elite_db alembic upgrade head`; final query returned `1|100|1` for one transaction, canonical `import_rows.transaction_id=100`, and the unique constraint present |
| Rollback boundary | Revert only `backend/app/db/migrations/versions/008_protect_import_confirmation.py` and `backend/tests/test_import_migration_upgrade.py`; the cleanup removes only duplicate-history migration hardening |

#### Unit 13 - Dashboard transaction datetime contract

| Evidence | Required value |
|---|---|
| Focused test command and exact result | `cd backend && pytest tests/test_frontend_upload_step_contract.py -k dashboard_transaction` -> `1 passed`, exit `0` |
| Runtime harness command/scenario and exact result | Alternate-port Compose browser opened `http://localhost:43000/`; every `/api/v1/transactions` response was non-422 and used `start_date=...T00:00:00.000Z` plus `end_date=...T23:59:59.999Z` |
| Rollback boundary | Revert `frontend/src/services/apiClient.ts` and the DashboardPage transaction-query regression test; other dashboard endpoints remain unchanged |

#### Unit 14 - UTC-negative calendar-date stability

| Evidence | Required value |
|---|---|
| Focused test command and exact result | `cd backend && pytest tests/test_frontend_upload_step_contract.py -k custom_period` -> `1 passed`, exit `0` |
| Runtime harness command/scenario and exact result | Headless Chromium with `timezone_id="America/Los_Angeles"` selected `2026-08-15` through `2026-08-20`; dashboard summary requests preserved exactly those inclusive query dates |
| Rollback boundary | Revert `frontend/src/utils/period.ts` and the custom-period timezone regression test; preset and custom period formatting return to the prior UTC serialization behavior |

#### Unit 15 - Locale-aware amounts and missing descriptions

| Evidence | Required value |
|---|---|
| Focused test command and exact result | `cd backend && pytest tests/test_import_api.py -k "argentine or absent_mapped_description"` -> `3 passed`, exit `0` |
| Runtime harness command/scenario and exact result | Alternate-port Compose API smoke returned `200` for the datetime transaction filter, preview amount `1234.00` for configured `es_AR` input `1.234`, and `MISSING_DESCRIPTION` for a null mapped description; health returned `{"status":"ok"}` |
| Rollback boundary | Revert `_clean_import_value`, `DOT_GROUPING_LOCALES`, and the `es_AR` branch in `backend/app/services/import_service.py` plus its three regression tests; CSV-only validation and unrelated import flows remain |

#### Unit 16 - Complete gates and alternate-port runtime evidence

| Evidence | Required value |
|---|---|
| Focused test command and exact result | `cd backend && pytest` -> `30 passed in 15.80s`; `cd frontend && npm run build` -> pass; `cd frontend && npx tsc --noEmit` -> pass; `git diff --check` -> pass |
| Runtime harness command/scenario and exact result | `POSTGRES_PORT=55433 FRONTEND_PORT=43000 docker compose up -d --build`; Postgres healthy, backend health `{"status":"ok"}`, Alembic `008_protect_import_confirmation (head)`, frontend routes `/`, `/import`, `/transactions`, `/transactions/new` returned `200`, CORS allowed `http://localhost:43000`, Compose browser smoke passed Dashboard datetime requests and direct SPA routes |
| Rollback boundary | Revert only the Phase 7 evidence sections in `openspec/changes/mvp-integration-hardening/tasks.md` and this `apply-progress.md`; implementation and regression tests remain independently revertible under Units 12-15 |

### Warnings Preserved as Follow-ups

- Vite production bundle warning remains at approximately `704.71 kB`; no code-splitting work was added.
- The ordinary backend pytest fixture remains in-memory SQLite; migration cleanup also passed against temporary Postgres, but no generalized Postgres pytest fixture was introduced.
- The Compose file emits the existing non-blocking warning that the `version` attribute is obsolete; no unrelated Compose cleanup was included.
- Empty CSV handling, missing frontend test dependencies, staged-file persistence, and concurrent upload deduplication remain follow-up items.

### Current Remediation Status

- All Phase 7 remediation tasks in `openspec/changes/mvp-integration-hardening/tasks.md` are checked `[x]`.
- All five newly authorized critical findings are addressed with cumulative RED/GREEN/triangulation evidence and runtime proof.
- No commit was created.
- Apply phase is ready for `sdd-verify`.

## Remediation Batch: Authorized Scope Expansion - Latest Critical Findings

- Date: 2026-08-13
- Mode: Strict TDD
- Delivery: focused remediation slice within the resolved `feature-branch-chain`
- Scope: the four newly confirmed critical findings explicitly authorized in this apply session.
- Prior apply-progress sections are preserved above and remain cumulative context.

### Completed Remediation Tasks

- [x] 8.1 Rejected malformed monetary text without stripping arbitrary characters; preserved configured `es_AR` and `en_US` grouping behavior.
- [x] 8.2 Added database-backed uniqueness for non-null `record_fingerprint` values and preserved all-or-nothing confirmation rollback across distinct import batches.
- [x] 8.3 Made migration 008 canonical selection use persisted `created_at ASC, id ASC` ordering, rewired references, and preserved import counters; added migration 009 for databases already at 008.
- [x] 8.4 Aligned frontend local calendar defaults/periods, Dashboard transaction UTC boundaries, backend UTC comparisons, and UTC-negative/positive-offset regression coverage.
- [x] 8.5 Re-ran complete backend/frontend/runtime acceptance gates and kept unrelated warning follow-ups unchanged.

### TDD Cycle Evidence - Latest Critical Findings

| Task | Test File | Layer | Safety Net | RED | GREEN | TRIANGULATE | REFACTOR |
|---|---|---|---|---|---|---|---|
| 8.1 | `backend/tests/test_import_api.py` | Integration | ✅ `pytest tests/test_import_api.py tests/test_import_confirmation_concurrency.py tests/test_import_migration_upgrade.py tests/test_frontend_upload_step_contract.py` -> 21 passed | ✅ Written; malformed amount and `en_US` grouping run -> `3 failed` before parser change | ✅ `pytest tests/test_import_api.py -k "malformed_amount or us_thousands or cross_batch_duplicate or argentine"` -> `5 passed` | ✅ `es_AR 1.234`, `es_AR 1234.56`, `en_US 1,234`, and `12abc34` invalid path | ✅ Full-match numeric grammar and locale-specific separator normalization replace arbitrary stripping |
| 8.2 | `backend/tests/test_import_api.py` | Integration/database contract | ✅ Same 21-test baseline before test edits | ✅ Written; cross-batch confirmation -> `200` with two inserted rows before uniqueness | ✅ Focused import command -> `5 passed`; live Postgres smoke returned confirmations `[200, 400]` and one transaction | ✅ Unique row is inserted before the duplicate in the second batch, proving rollback of prior work in that batch | ✅ Model uniqueness plus migration 009 upgrade path handle both fresh and already-008 databases |
| 8.3 | `backend/tests/test_import_migration_upgrade.py` | Migration integration | ✅ Baseline migration coverage included in 21 passed | ✅ Written; inverted ids/timestamps -> `1 failed, 1 passed` before migration ordering change | ✅ `pytest tests/test_import_migration_upgrade.py` -> `2 passed` | ✅ Earliest timestamp wins even with larger id; equal timestamp ties resolve to lower id; source/fingerprint groups and nullable/manual rows are covered | ✅ Shared deterministic `_deduplicate_by_key` helper rewires `import_rows` before deletion |
| 8.4 | `backend/tests/test_frontend_upload_step_contract.py` + `backend/tests/test_dashboard_api.py` | Browser/API integration | ✅ Existing browser contract and frontend build/typecheck passed before source changes | ✅ Written; negative-offset mocked form date -> `1 failed`; offset API comparison -> `1 failed` before UTC normalization | ✅ `pytest tests/test_frontend_upload_step_contract.py -k "transaction_form_default or custom_period"` -> `4 passed`; dashboard API regression -> `1 passed` | ✅ `America/Los_Angeles` and `Asia/Tokyo` form defaults, negative/positive custom periods, and UTC transaction list/dashboard ranges | ✅ Shared `formatCalendarDate`, local form default, UTC-aware dashboard ranges, and service-level UTC normalization remove date drift |
| 8.5 | `apply-progress.md` and runtime harnesses | Acceptance/runtime | ✅ Prior cumulative gates preserved above | ✅ Command set and runtime scenarios recorded before final execution | ✅ Full gates and alternate-port Compose/API/browser smoke passed | ✅ Local Vite browser, Compose nginx routes, Postgres migration head, API rollback, and timezone paths all exercised | ✅ Evidence appended without rewriting prior batches or warning follow-ups |

### Remediation Test Summary

- **New regression tests**: 10 behavior cases: 3 import API cases, 2 migration scenarios expanded with persisted timestamps/tie-breaking, 1 dashboard API scenario, and 4 browser timezone cases.
- **Focused import command**: `cd backend && pytest tests/test_import_api.py -k "malformed_amount or us_thousands or cross_batch_duplicate or argentine"` -> `5 passed, 10 deselected`, exit `0`.
- **Focused migration command**: `cd backend && pytest tests/test_import_migration_upgrade.py` -> `2 passed`, exit `0`.
- **Focused calendar command**: `cd backend && pytest tests/test_frontend_upload_step_contract.py -k "transaction_form_default or custom_period"` -> `4 passed, 5 deselected`, exit `0`; `cd backend && pytest tests/test_dashboard_api.py::test_dashboard_uses_utc_calendar_boundaries_for_offset_transactions` -> `1 passed`, exit `0`.
- **Full backend suite**: `cd backend && pytest` -> `37 passed in 17.13s`, exit `0`.
- **Frontend build/typecheck**: `cd frontend && npm run build && npx tsc --noEmit` -> build and typecheck passed, exit `0`; existing Vite chunk warning remains at approximately `704.71 kB`.
- **Diff validation**: `git diff --check` -> passed, exit `0`.

### Remediation Work Unit Evidence

#### Unit 17 - Strict monetary parsing and locale grouping

| Evidence | Required value |
|---|---|
| Focused test command and exact result | `cd backend && pytest tests/test_import_api.py -k "malformed_amount or us_thousands or cross_batch_duplicate or argentine"` -> `5 passed, 10 deselected`, exit `0` |
| Runtime harness command/scenario and exact result | `python - <<'PY' ... requests ... PY` against `http://localhost:8000/api/v1` on alternate Compose stack -> preview `es_AR 1.234` returned `1234.00`; `12abc34` returned `INVALID_AMOUNT`; local `en_US 1,234` regression returned `1234.00` |
| Rollback boundary | Revert `backend/app/services/import_service.py` amount parser/constants and the amount-related cases in `backend/tests/test_import_api.py`; CSV-only validation and unrelated import behavior remain |

#### Unit 18 - Cross-batch fingerprint uniqueness and atomic rollback

| Evidence | Required value |
|---|---|
| Focused test command and exact result | `cd backend && pytest tests/test_import_api.py -k cross_batch_duplicate` -> `1 passed`, exit `0` (included in the 5-case focused run) |
| Runtime harness command/scenario and exact result | Alternate Compose Postgres API harness uploaded two distinct CSV batches, mapped both before confirmation, confirmed the first (`200`), confirmed the second with one new row before the duplicate (`400`), and observed one transaction after rollback; Postgres constraint `uq_transactions_record_fingerprint` present |
| Rollback boundary | Revert `backend/app/models/transaction.py`, `backend/app/db/migrations/versions/008_protect_import_confirmation.py`, `backend/app/db/migrations/versions/009_unique_import_fingerprints.py`, and the cross-batch test; existing per-batch confirmation locking remains independently removable |

#### Unit 19 - Earliest persisted migration canonicalization

| Evidence | Required value |
|---|---|
| Focused test command and exact result | `cd backend && pytest tests/test_import_migration_upgrade.py` -> `2 passed`, exit `0` |
| Runtime harness command/scenario and exact result | `POSTGRES_PORT=55435 FRONTEND_PORT=43001 docker compose up -d --build`; `docker compose exec -T backend alembic current` -> `009_unique_import_fingerprints (head)`; migration cleanup tests proved timestamps beat ids, equal timestamps use lower id, `import_rows` references are rewired, and `records_inserted` counters remain unchanged |
| Rollback boundary | Revert migration 008 canonical ordering and migration 009 incremental fingerprint cleanup plus `backend/tests/test_import_migration_upgrade.py`; no application API code is removed |

#### Unit 20 - Browser/business timezone calendar boundaries

| Evidence | Required value |
|---|---|
| Focused test command and exact result | `cd backend && pytest tests/test_frontend_upload_step_contract.py -k "transaction_form_default or custom_period"` -> `4 passed, 5 deselected`, exit `0`; dashboard API boundary test -> `1 passed` |
| Runtime harness command/scenario and exact result | Native Playwright against Compose frontend `http://localhost:43001` in `America/Los_Angeles` and `Asia/Tokyo` opened `/transactions/new`, `/import`, and `/transactions`; all route and local-date assertions passed. Local Vite browser tests additionally asserted UTC-negative and positive-offset custom period requests preserve `2026-08-15` through `2026-08-20` |
| Rollback boundary | Revert `frontend/src/utils/format.ts`, `frontend/src/utils/period.ts`, `frontend/src/pages/TransactionFormPage.tsx`, `backend/app/services/transaction_service.py`, `backend/app/api/v1/dashboard.py`, and their timezone regressions; import and uniqueness hardening remain |

#### Unit 21 - Complete gates and alternate-port runtime evidence

| Evidence | Required value |
|---|---|
| Focused test command and exact result | `cd backend && pytest` -> `37 passed in 17.13s`; `cd frontend && npm run build && npx tsc --noEmit` -> passed; `git diff --check` -> passed |
| Runtime harness command/scenario and exact result | `POSTGRES_PORT=55435 FRONTEND_PORT=43001 docker compose up -d --build`; Postgres healthy, backend `{"status":"ok"}`, frontend `/` and `/import` HTTP `200`, Alembic `009_unique_import_fingerprints (head)`, fingerprint unique constraint present, API amount/malformed/cross-batch/UTC smoke passed, and Compose browser routes passed |
| Rollback boundary | Revert only this Phase 8 evidence section in `openspec/changes/mvp-integration-hardening/tasks.md` and `apply-progress.md`; implementation and regression tests remain independently revertible under Units 17-20 |

### Deviations from Existing Design

- The original design described verification without a schema migration. The authorized critical data-integrity finding required the additive fingerprint uniqueness constraint and upgrade-safe migration 009; this is limited to deduplication and uniqueness and does not redesign the domain model.
- The original design did not specify timezone normalization. The fix makes persisted transaction timestamps and dashboard comparisons explicitly UTC while preserving user-selected local calendar dates.

### Warnings Preserved as Follow-ups

- Vite production bundle warning remains at approximately `704.71 kB`; no code-splitting work was added.
- The ordinary backend pytest fixture remains in-memory SQLite; the critical uniqueness and migration paths were additionally exercised against live Postgres.
- The Compose file emits the existing non-blocking warning that the `version` attribute is obsolete; no unrelated Compose cleanup was included.
- Empty CSV handling, missing frontend test dependencies, staged-file persistence, and concurrent upload deduplication remain follow-up items.

### Current Remediation Status

- All Phase 8 remediation tasks in `openspec/changes/mvp-integration-hardening/tasks.md` are checked `[x]`.
- All four newly authorized critical findings are addressed with cumulative RED/GREEN/triangulation evidence and runtime proof.
- Migration 009 is required because the live database had already recorded revision 008 before the newly authorized fingerprint uniqueness change; the incremental migration keeps upgrades safe without rewriting migration history.
- No commit was created.
- Apply phase is ready for `sdd-verify`.

## Remediation Batch: Authorized Scope Expansion - Final Two Critical Blockers

- Date: 2026-08-13
- Mode: Strict TDD
- Delivery: focused remediation slice within the resolved `feature-branch-chain`
- Scope: the two remaining CRITICAL blockers explicitly authorized in this apply session.
- Prior apply-progress sections are preserved above and remain cumulative context.

### Calendar-Boundary Contract Implemented

- Persisted transaction timestamps and repository comparison bounds are UTC instants.
- Date-only `start_date` and `end_date` filters represent local calendar dates in the IANA timezone supplied through the `timezone` query parameter.
- Backend endpoints convert local start-of-day and end-of-day boundaries to UTC before repository filtering.
- The `timezone` parameter defaults to `UTC` for direct API consumers that omit a local timezone.
- Frontend period utilities emit date-only local calendar strings, and the API client supplies the browser timezone without converting date-only values to UTC midnight.
- Full timestamp transaction filters remain supported as exact instants and are normalized to UTC.

### Completed Remediation Tasks

- [x] 9.1 Canonicalized imported transaction timestamps to UTC before fingerprint hashing and rejected equivalent offset representations across import batches.
- [x] 9.2 Applied one explicit local calendar-boundary contract across frontend period utilities, API clients, backend endpoints, repositories, and regression coverage.
- [x] 9.3 Re-ran focused RED/GREEN tests, the complete backend suite, frontend build/typecheck, runtime browser tests, and alternate-port Compose/API smoke.

### TDD Cycle Evidence - Final Two Critical Blockers

| Task | Test File | Layer | Safety Net | RED | GREEN | TRIANGULATE | REFACTOR |
|---|---|---|---|---|---|---|---|
| 9.1 | `backend/tests/test_import_api.py` | Integration/database contract | ✅ Existing import API baseline -> 15 passed before the new test | ✅ Written; equivalent-offset scenario failed with `records_valid == 1` before canonicalization | ✅ `pytest tests/test_import_api.py::test_import_fingerprint_normalizes_equivalent_timezone_offsets` -> 1 passed | ✅ `pytest tests/test_import_api.py -k "fingerprint or cross_batch_duplicate"` -> 2 passed across equivalent timestamp and existing cross-batch rollback cases | ✅ Extracted deterministic `_canonical_utc_timestamp`; payload and hash use the same canonical value |
| 9.2 | `backend/tests/test_dashboard_api.py` + `backend/tests/test_frontend_upload_step_contract.py` | API integration + browser runtime | ✅ Existing dashboard/browser baseline -> 12 passed before the new contract assertions | ✅ Written; backend local-date scenario returned zero and browser requests still used UTC-midnight timestamps | ✅ Dashboard offset filter -> 2 passed; browser local-period/API contract -> 3 passed; full browser module -> 9 passed | ✅ Covered UTC-negative `America/New_York`, UTC-positive `Asia/Tokyo`, default browser timezone, and both dashboard/list API paths | ✅ Centralized timezone conversion in `calendar.py`, API-client timezone injection, and repository UTC normalization |
| 9.3 | Cumulative gate and runtime harness artifacts | Integration/runtime | ✅ Prior cumulative gates preserved above | ➖ Evidence-only task; command plan recorded before final execution | ✅ `cd backend && pytest` -> 39 passed; frontend build/typecheck and diff checks passed | ✅ Alternate Compose API smoke, direct Compose browser smoke, health, routes, migration head, and new blocker scenarios all passed | ✅ Evidence appended without rewriting prior batches or warning follow-ups |

### Test Summary - Final Two Critical Blockers

- **New regression tests**: 2 behavior cases: one equivalent-offset import fingerprint case and one local-calendar API case covering both dashboard and transaction list filtering.
- **Focused fingerprint command**: `cd backend && pytest tests/test_import_api.py -k "fingerprint or cross_batch_duplicate"` -> 2 passed, 14 deselected, exit `0`.
- **Focused calendar API command**: `cd backend && pytest tests/test_dashboard_api.py -k "calendar or offset"` -> 2 passed, 2 deselected, exit `0`.
- **Focused calendar browser command**: `cd backend && pytest tests/test_frontend_upload_step_contract.py -k "dashboard_transaction or custom_period"` -> 3 passed, 6 deselected, exit `0`.
- **Full backend suite**: `cd backend && pytest` -> 39 passed in 18.40s, exit `0`.
- **Frontend build**: `cd frontend && npm run build` -> passed, exit `0`; existing Vite chunk warning remains at approximately `704.71 kB`.
- **Frontend typecheck**: `cd frontend && npx tsc --noEmit` -> passed with no output, exit `0`.
- **Diff validation**: `git diff --check` -> passed, exit `0`.

### Remediation Work Unit Evidence - Final Two Critical Blockers

#### Unit 22 - Canonical UTC transaction fingerprints

| Evidence | Required value |
|---|---|
| Focused test command and exact result | `cd backend && pytest tests/test_import_api.py -k "fingerprint or cross_batch_duplicate"` -> 2 passed, 14 deselected, exit `0` |
| Runtime harness command/scenario and exact result | `POSTGRES_PORT=55435 FRONTEND_PORT=43001 docker compose up -d --build`; runtime API uploaded two distinct CSV batches with `2099-08-20T23:30:00-04:00` and equivalent `2099-08-21T03:30:00+00:00`, confirmed the first, then observed the second mapping as one duplicate and confirmation as `records_inserted=0`; output `canonical_fingerprint=duplicate_rejected_without_second_insert` |
| Rollback boundary | Revert `_canonical_utc_timestamp` and canonical fingerprint payload use in `backend/app/services/import_service.py` plus `test_import_fingerprint_normalizes_equivalent_timezone_offsets`; existing uniqueness migration and per-batch confirmation locking remain |

#### Unit 23 - Local calendar filtering contract

| Evidence | Required value |
|---|---|
| Focused test command and exact result | `cd backend && pytest tests/test_dashboard_api.py -k "calendar or offset"` -> 2 passed, 2 deselected, exit `0`; browser contract filter -> 3 passed, 6 deselected, exit `0` |
| Runtime harness command/scenario and exact result | Runtime API created `2099-08-20T23:30:00-04:00` and `2099-08-20T00:30:00+09:00`; selected local date `2099-08-20` returned exactly one transaction and the matching income for `America/New_York` and `Asia/Tokyo`; output `calendar_filters=America/New_York:1,Asia/Tokyo:1`; direct Compose browser routes `/import`, `/transactions`, and `/transactions/new` returned HTTP 200 and rendered their expected headings |
| Rollback boundary | Revert `backend/app/services/calendar.py`, timezone parsing in `backend/app/api/v1/dashboard.py` and `backend/app/api/v1/transactions.py`, repository UTC normalization, `frontend/src/types/api.ts`, `frontend/src/utils/period.ts`, `frontend/src/services/apiClient.ts`, and their Phase 9 regression assertions; persisted UTC storage and unrelated API filters remain |

#### Unit 24 - Complete gates and alternate-port runtime evidence

| Evidence | Required value |
|---|---|
| Focused test command and exact result | `cd backend && pytest` -> 39 passed in 18.40s; `cd frontend && npm run build` -> pass; `cd frontend && npx tsc --noEmit` -> pass; `git diff --check` -> pass |
| Runtime harness command/scenario and exact result | `POSTGRES_PORT=55435 FRONTEND_PORT=43001 docker compose up -d --build`; Postgres healthy, backend health `{"status":"ok"}`, frontend host `43001` routes passed, Alembic `009_unique_import_fingerprints (head)`, API fingerprint/calendar smoke passed, and native Playwright Compose browser smoke passed |
| Rollback boundary | Revert only this Phase 9 evidence section in `openspec/changes/mvp-integration-hardening/tasks.md` and `apply-progress.md`; implementation and regression tests remain independently revertible under Units 22-23 |

### Deviations from Existing Design

- The original design did not define a timezone-bearing calendar filter contract.
- The authorized remediation adds an optional IANA `timezone` query parameter with a `UTC` default while retaining exact timestamp filters for direct API consumers.
- No schema migration was required because transaction timestamps were already normalized for persistence and the existing fingerprint uniqueness constraint remains sufficient.

### Warnings Preserved as Follow-ups

- Vite production bundle warning remains at approximately `704.71 kB`; no code-splitting work was added.
- The ordinary backend pytest fixture remains in-memory SQLite; the runtime blocker paths were additionally exercised against live Postgres Compose.
- The Compose file emits the existing non-blocking warning that the `version` attribute is obsolete; no unrelated Compose cleanup was included.
- Empty CSV handling, missing frontend test dependencies, staged-file persistence, and concurrent upload deduplication remain follow-up items.

### Current Remediation Status

- All Phase 9 remediation tasks in `openspec/changes/mvp-integration-hardening/tasks.md` are checked `[x]`.
- Both remaining CRITICAL blockers are addressed with cumulative RED/GREEN/triangulation evidence and runtime proof.
- No commit was created.
- Apply phase is ready for `sdd-verify`.

## Remediation Batch: Authorized Scope Expansion - Five Confirmed CRITICAL Findings

- Date: 2026-08-13
- Mode: Strict TDD
- Delivery: focused remediation slice within the resolved `feature-branch-chain`
- Scope: source-context import identity, staged-file persistence, containerized frontend API configuration, date-only form calendar semantics, and timezone-aware dashboard timeseries aggregation.
- Prior apply-progress sections are preserved above and remain cumulative context.

### Completed Remediation Tasks

- [x] 10.1 Preserved legitimate repeated source rows, added deterministic source-row identity, retained cross-source semantic duplicate protection, and documented the two-key identity contract.
- [x] 10.2 Mounted a named Compose `import_storage` volume at `IMPORT_STORAGE_DIR` and verified pending and validated batch recovery after backend restarts.
- [x] 10.3 Added build-time and runtime frontend API-base configuration through Docker/Compose and verified browser requests use a configured non-local origin.
- [x] 10.4 Made date-only transaction form values serialize as local midnight in the browser IANA timezone and verified save/edit calendar-date stability.
- [x] 10.5 Propagated the requested IANA timezone into timeseries aggregation and bucketed persisted UTC instants by local calendar date.
- [x] 10.6 Re-ran focused tests, the complete backend suite, frontend build/typecheck, browser tests, migration/Compose smoke, and relevant API checks.

### Identity Contract Implemented

- `record_fingerprint` is the semantic fingerprint of normalized transaction content: canonical UTC instant, transaction type, category, description, amount, currency, and product.
- Same-source repeated rows are retained because mapping no longer collapses same-batch semantic fingerprints.
- `source_fingerprint` is a unique SHA-256 identity of the immutable upload content hash plus source row number.
- Exact file re-upload remains rejected by `ImportBatch.content_hash` uniqueness, and confirmed-batch replay remains idempotent through the locked batch state.
- Cross-source semantic duplicates are checked under a PostgreSQL transaction advisory lock. An equivalent transaction in another source context rolls back the entire confirmation batch.
- Migration `010_source_context_identity` drops global semantic-fingerprint uniqueness and adds the unique source-row constraint, with deterministic legacy source fingerprints during upgrade.

### TDD Cycle Evidence - Five Confirmed CRITICAL Findings

| Task | Test File | Layer | Safety Net | RED | GREEN | TRIANGULATE | REFACTOR |
|---|---|---|---|---|---|---|---|
| 10.1 | `backend/tests/test_import_api.py` | Integration/database | ✅ Baseline `pytest` -> `39 passed` | ✅ Temporary pre-fix same-batch deduplication -> `1 failed` | ✅ `-k preserves_repeated_rows` -> `1 passed`; import module -> `18 passed` | ✅ Repeated rows insert `2`, replay returns `2`, cross-source equivalent inserts `0` | ✅ Added `_source_fingerprint`, removed in-batch collapse, added locked cross-source check and migration 010 |
| 10.2 | `backend/tests/test_compose_port_contract.py` + import recovery | Configuration/runtime | ✅ Existing Compose/import tests green | ✅ Storage contract -> `1 failed` without volume | ✅ Storage contract -> `1 passed`; restart recovery passed | ✅ Pending mapped and validated confirmed after separate backend restarts | ✅ Reused `IMPORT_STORAGE_DIR` with named-volume interpolation |
| 10.3 | API config contract + browser contract | Configuration/browser | ✅ Existing browser module -> `12 passed` | ✅ Compose contract -> `2 failed`; runtime test had no configured-origin requests | ✅ Config contract -> `2 passed`; runtime browser -> `1 passed` | ✅ Build arg, runtime env, local Vite injection, and container config paths | ✅ Runtime-first `resolveApiBaseUrl` plus nginx bootstrap |
| 10.4 | `backend/tests/test_frontend_upload_step_contract.py` | Browser runtime | ✅ Browser baseline -> `12 passed` | ✅ Negative-offset edit test failed with UTC midnight | ✅ Edit/new form filter -> `3 passed` | ✅ `America/Los_Angeles` and `Asia/Tokyo` local-midnight instants | ✅ Separated date-only input conversion from display formatting |
| 10.5 | `backend/tests/test_dashboard_api.py` | API integration | ✅ Dashboard baseline -> `5 passed` | ✅ Timeseries test failed with UTC/database-date bucket | ✅ Timeseries filter -> `1 passed` | ✅ New York and Tokyo offset transactions bucket on requested local date | ✅ Propagated IANA timezone and normalized two-decimal buckets |
| 10.6 | Cumulative gates and runtime harnesses | Integration/runtime | ✅ Prior evidence preserved | ➖ Evidence-only task | ✅ Full gates and runtime checks passed | ✅ Postgres, volume, API, browser, migration, and restart paths | ✅ Evidence appended after all prior batches |

### Test Summary - Phase 10

- `cd backend && pytest` -> `48 passed in 20.53s`, exit `0`.
- `cd frontend && npm run build && npx tsc --noEmit` -> passed, exit `0`; Vite warning remains approximately `705.04 kB`.
- `cd backend && pytest tests/test_frontend_upload_step_contract.py` -> `12 passed`.
- `cd backend && pytest tests/test_compose_port_contract.py -k storage` -> `1 passed`; `pytest tests/test_frontend_api_config_contract.py` -> `2 passed`.
- `git diff --check` and `docker compose config --quiet` -> passed.

### Remediation Work Unit Evidence - Phase 10

#### Unit 25 - Source-context import identity

| Evidence | Required value |
|---|---|
| Focused test command and exact result | `cd backend && pytest tests/test_import_api.py -k preserves_repeated_rows` -> `1 passed`, exit `0`; full import module -> `18 passed` |
| Runtime harness command/scenario and exact result | Compose Postgres retained two identical rows from one source with `records_inserted=2`; an equivalent normalized row from another source mapped `records_duplicate=1` and confirmed with `records_inserted=0`; SQL showed `uq_transactions_source_fingerprint` and no semantic unique constraint |
| Rollback boundary | Revert transaction identity model/repository/service changes, migration 010, identity docs, and related import regressions only |

#### Unit 26 - Persistent staged-file recovery

| Evidence | Required value |
|---|---|
| Focused test command and exact result | `cd backend && pytest tests/test_compose_port_contract.py -k storage` -> `1 passed`, exit `0`; staged service recovery regression passed |
| Runtime harness command/scenario and exact result | On Compose ports `55436/43002`, pending batch `20` mapped as `VALIDATED` after backend restart; validated batch `21` confirmed with `records_inserted=1` after another restart; `docker volume inspect elite-intel_import_storage` succeeded |
| Rollback boundary | Revert backend `import_storage` mapping, named volume, storage contract test, and recovery regression only |

#### Unit 27 - Build/runtime frontend API configuration

| Evidence | Required value |
|---|---|
| Focused test command and exact result | `cd backend && pytest tests/test_frontend_api_config_contract.py` -> `2 passed`; runtime browser config -> `1 passed` |
| Runtime harness command/scenario and exact result | `VITE_API_BASE_URL=https://api.example.test/api/v1 ... docker compose up -d --build frontend`; runtime config returned that URL; native Playwright rendered dashboard/import and observed `5` configured-origin requests |
| Rollback boundary | Revert frontend Docker/runtime-config/API-client files, Compose wiring, and config tests only |

#### Unit 28 - Local calendar transaction form contract

| Evidence | Required value |
|---|---|
| Focused test command and exact result | `cd backend && pytest tests/test_frontend_upload_step_contract.py -k "transaction_edit or new_transaction_form"` -> `3 passed`, exit `0` |
| Runtime harness command/scenario and exact result | `America/Los_Angeles` emitted `2026-08-15T07:00:00.000Z`; `Asia/Tokyo` emitted `2026-08-14T15:00:00.000Z`; live API retrieval with the LA timezone matched the selected calendar date |
| Rollback boundary | Revert `frontend/src/utils/format.ts` and calendar regressions only |

#### Unit 29 - Timezone-aware dashboard timeseries

| Evidence | Required value |
|---|---|
| Focused test command and exact result | `cd backend && pytest tests/test_dashboard_api.py -k timeseries` -> `1 passed`, exit `0` |
| Runtime harness command/scenario and exact result | Compose API delta smoke observed `America/New_York_delta=75.0` and `Asia/Tokyo_delta=125.0` in bucket `2099-08-20` |
| Rollback boundary | Revert dashboard API/service/repository timezone propagation and timeseries regression only |

#### Unit 30 - Complete Phase 10 acceptance gates

| Evidence | Required value |
|---|---|
| Focused test command and exact result | Full backend `48 passed`; frontend build/typecheck passed; `git diff --check` passed |
| Runtime harness command/scenario and exact result | Postgres healthy on `55436`, backend `8000`, frontend `43002`, Alembic `010_source_context_identity (head)`, health `{"status":"ok"}`, named-volume recovery, configured-origin browser, identity, date, and timeseries API smoke all passed |
| Rollback boundary | Revert only the Phase 10 evidence additions in `tasks.md` and `apply-progress.md`; behavior units remain independently revertible |

### Deviations and Issues Resolved

- The first migration boot attempt used `010_source_context_import_identity`, exceeding Alembic's `version_num` length and causing a real `StringDataRightTruncation` startup failure.
- The revision was shortened to `010_source_context_identity`; the successful rerun reached that head.
- No other design deviation was introduced.

### Warnings Preserved as Follow-ups

- Vite chunk warning, in-memory SQLite fixture, obsolete Compose `version` warning, empty CSV handling, missing frontend test dependencies, and concurrent upload deduplication remain follow-ups.
- `npm install` reports existing dependency audit findings during the frontend image build; dependency remediation remains out of scope.

### Current Remediation Status

- All Phase 10 tasks in `tasks.md` are checked `[x]`.
- All five newly authorized CRITICAL findings have cumulative RED/GREEN/triangulation evidence and direct runtime proof.
- No commit was created.
- Apply phase is ready for `sdd-verify`.

## Remediation Batch: Authorized Scope Expansion - Three CRITICAL Blockers

- Date: 2026-08-13
- Mode: Strict TDD
- Delivery: focused remediation slice within the resolved `feature-branch-chain`
- Scope: migration identity sequencing, configured business timezone for date-only CSV values, and requested dashboard timeseries granularity.
- Prior apply-progress sections are preserved above and remain cumulative context.

### Completed Remediation Tasks

- [x] 11.1 Made migrations 008 and 009 preserve semantic fingerprints until migration 010 changes the identity model; only conflicting `(import_batch_id, source_row_number)` identities are canonically rewired.
- [x] 11.2 Parsed date-only CSV values at local midnight under the configured business/IANA timezone and covered negative and positive offset APIs.
- [x] 11.3 Implemented `day`, `week`, and `month` timeseries granularity with requested IANA timezone bucket labels and API/repository tests.
- [x] 11.4 Re-ran strict TDD focused tests, the complete backend suite, frontend build/typecheck, browser tests, migration smoke, and alternate-port Compose/API smoke.

### Migration Identity Contract Corrected

- Migration 008 now deduplicates only conflicting transaction rows with the same non-null `(import_batch_id, source_row_number)` source identity.
- Migration 008 no longer deletes rows solely because `record_fingerprint` matches.
- Migration 009 is a compatibility no-op and does not create a semantic-fingerprint uniqueness constraint before the identity-model change.
- Migration 010 conditionally removes the legacy `uq_transactions_record_fingerprint` constraint when it exists, adds deterministic legacy source fingerprints, and creates the source-context uniqueness constraint.
- Fresh upgrades preserve semantic repeats from distinct source contexts through 008 and 009, then retain them with distinct source fingerprints at 010.
- Existing databases that recorded the previous 009 constraint are handled by the conditional 010 drop path; no semantic cleanup is run by the compatibility revisions.

### TDD Cycle Evidence - Three CRITICAL Blockers

| Task | Test File | Layer | Safety Net | RED | GREEN | TRIANGULATE | REFACTOR |
|---|---|---|---|---|---|---|---|
| 11.1 | `backend/tests/test_import_migration_upgrade.py` | Migration integration | ✅ Existing migration tests -> `2 passed` before new assertions | ✅ Written; first run -> `3 failed, 1 passed` against semantic cleanup in 008/009 | ✅ `pytest tests/test_import_migration_upgrade.py` -> `5 passed` | ✅ Same-source-row conflict, distinct-source semantic repeats, fresh 008→009→010 path, clean idempotence, and existing-009 constraint removal | ✅ Removed semantic cleanup from 008/009 and made 010 legacy-constraint removal conditional |
| 11.2 | `backend/tests/test_import_api.py` + `backend/tests/test_compose_port_contract.py` | API integration/configuration | ✅ Existing import API -> `18 passed` before date-only tests | ✅ Written; date-only cases -> `2 failed` before `IMPORT_DEFAULT_TIMEZONE`; Compose env contract -> `1 failed` before wiring | ✅ `pytest tests/test_import_api.py -k business_timezone` -> `2 passed`; Compose contract -> `4 passed` | ✅ Negative offset `America/New_York`, positive offset `Asia/Tokyo`, and configured Compose environment propagation | ✅ Centralized naive import datetime localization before canonical UTC serialization |
| 11.3 | `backend/tests/test_dashboard_api.py` + `backend/tests/test_transaction_repository.py` | API/repository integration | ✅ Existing dashboard API -> `5 passed`; repository path was new | ✅ Written; initial granularity run -> `5 failed, 1 passed` because the parameter was discarded/not accepted | ✅ Combined focused run -> `6 passed, 5 deselected` across day, week, and month | ✅ Extracted deterministic local bucket-label helper with ISO-week Monday and month-first semantics |
| 11.4 | Cumulative gates and runtime harnesses | Integration/runtime | ✅ Prior cumulative evidence preserved above | ➖ Evidence-only task; command plan recorded before final execution | ✅ Full and runtime gates passed | ✅ Browser, Postgres migration, Compose health, CORS, date-only API, and all granularity paths exercised | ✅ Evidence appended without rewriting prior batches or warning follow-ups |

### Test Summary - Three CRITICAL Blockers

- **Focused migration command**: `cd backend && pytest tests/test_import_migration_upgrade.py` -> `5 passed`, exit `0`.
- **Focused date-only command**: `cd backend && pytest tests/test_import_api.py -k business_timezone` -> `2 passed`, exit `0`.
- **Focused Compose configuration command**: `cd backend && pytest tests/test_compose_port_contract.py` -> `4 passed`, exit `0`.
- **Focused granularity command**: `cd backend && pytest tests/test_dashboard_api.py -k granularity tests/test_transaction_repository.py` -> `6 passed, 5 deselected`, exit `0`.
- **Browser command**: `cd backend && pytest tests/test_frontend_upload_step_contract.py` -> `12 passed in 17.58s`, exit `0`.
- **Full backend suite**: `cd backend && pytest` -> `60 passed in 17.11s`, exit `0`.
- **Frontend build/typecheck**: `cd frontend && npm run build && npx tsc --noEmit` -> exit `0`; existing Vite chunk warning remains at approximately `705.04 kB`.
- **Compose configuration/diff checks**: `docker compose config --quiet` and `git diff --check` -> exit `0`.

### Remediation Work Unit Evidence - Three CRITICAL Blockers

#### Unit 31 - Upgrade-safe migration identity sequencing

| Evidence | Required value |
|---|---|
| Focused test command and exact result | `cd backend && pytest tests/test_import_migration_upgrade.py` -> `5 passed`, exit `0`; tests retain distinct semantic fingerprints across different source contexts and collapse only same-source-row conflicts. |
| Runtime harness command/scenario and exact result | Temporary Postgres on host port `55438`: `alembic upgrade 009_unique_import_fingerprints`, seed two transactions in distinct batches with one semantic fingerprint, `alembic upgrade head`; SQL returned `2 semantic_repeats, 2 source_fingerprints` and `010_source_context_identity`. |
| Rollback boundary | Revert only `backend/app/db/migrations/versions/008_protect_import_confirmation.py`, `009_unique_import_fingerprints.py`, `010_source_context_import_identity.py`, and `backend/tests/test_import_migration_upgrade.py`; this removes migration identity sequencing only. |

#### Unit 32 - Configured business timezone for date-only CSV values

| Evidence | Required value |
|---|---|
| Focused test command and exact result | `cd backend && pytest tests/test_import_api.py -k business_timezone` -> `2 passed`, exit `0`; `America/New_York` yielded `2026-08-12T04:00:00Z`, and `Asia/Tokyo` yielded `2026-08-11T15:00:00Z` for the same `12/08/2026` value. |
| Runtime harness command/scenario and exact result | `POSTGRES_PORT=55437 FRONTEND_PORT=43003 IMPORT_DEFAULT_TIMEZONE=America/New_York docker compose up -d --build`; backend `printenv IMPORT_DEFAULT_TIMEZONE` returned `America/New_York`, live CSV mapping returned `2026-08-12T04:00:00Z`, Postgres was healthy, and backend health returned `{"status":"ok"}`. |
| Rollback boundary | Revert `backend/app/core/config.py`, `backend/app/services/import_service.py`, `.env.example`, `docker-compose.yml`, the date-only regressions, and the Compose timezone contract; non-date import behavior remains independently revertible. |

#### Unit 33 - Requested timeseries granularity and IANA labels

| Evidence | Required value |
|---|---|
| Focused test command and exact result | `cd backend && pytest tests/test_dashboard_api.py -k granularity tests/test_transaction_repository.py` -> `6 passed, 5 deselected`, exit `0`; API and repository tests cover day, ISO-week Monday, and month-first labels. |
| Runtime harness command/scenario and exact result | Against the alternate-port Compose stack, API requests with `timezone=America/New_York` returned labels `2026-08-20` for `day`, `2026-08-17` for `week`, and `2026-08-01` for `month`; CORS preflight from `http://localhost:43003` returned `200` and the matching allow-origin header. |
| Rollback boundary | Revert `backend/app/api/v1/dashboard.py`, `backend/app/services/dashboard_service.py`, `backend/app/repositories/transaction_repository.py`, and their granularity regressions; existing dashboard summary/categories and unrelated filters remain. |

#### Unit 34 - Complete gates and alternate-port runtime evidence

| Evidence | Required value |
|---|---|
| Focused test command and exact result | `cd backend && pytest` -> `60 passed in 17.11s`; `cd frontend && npm run build && npx tsc --noEmit` -> exit `0`; `git diff --check` -> exit `0`. |
| Runtime harness command/scenario and exact result | `POSTGRES_PORT=55437 FRONTEND_PORT=43003 IMPORT_DEFAULT_TIMEZONE=America/New_York docker compose up -d --build`; `elite_postgres` healthy, `elite_backend` up on `8000`, `elite_frontend` up on `43003->80`, Alembic at `010_source_context_identity (head)`, frontend routes `/import`, `/transactions`, `/transactions/new` returned `200` and rendered expected headings, API date-only and day/week/month smoke passed, and CORS passed. |
| Rollback boundary | Revert only the Phase 11 evidence additions in `openspec/changes/mvp-integration-hardening/tasks.md` and this `apply-progress.md`; behavior units remain independently revertible under Units 31-33. |

### Warnings Preserved as Follow-ups

- Vite production bundle warning remains at approximately `705.04 kB`; no code-splitting work was added.
- The ordinary backend pytest fixture remains in-memory SQLite; migration behavior was additionally exercised against temporary Postgres.
- The Compose file emits the existing non-blocking warning that the `version` attribute is obsolete; no unrelated Compose cleanup was included.
- Empty CSV handling, missing frontend test dependencies, staged-file persistence, concurrent upload deduplication, and dependency audit findings remain follow-ups.

### Current Remediation Status

- All Phase 11 remediation tasks in `openspec/changes/mvp-integration-hardening/tasks.md` are checked `[x]`.
- The three newly authorized CRITICAL blockers are addressed with cumulative RED/GREEN/triangulation evidence and direct runtime proof.
- No commit was created.
- Apply phase is ready for `sdd-verify`.

## Remediation Batch: Explicit Final Remediation - Amount Precision

- Date: 2026-08-13
- Mode: Strict TDD
- Delivery: focused remediation slice within the resolved `feature-branch-chain`
- Scope: the explicitly authorized final CRITICAL amount-precision defect only.
- Prior apply-progress sections are preserved above and remain cumulative context.

### Completed Remediation Tasks

- [x] 12.1 Added RED/GREEN regression coverage for excess fractional precision, the `es_AR` sub-cent value `0,004`, and valid grouped whole/cents values for `es_AR` and `en_US`.
- [x] 12.2 Rejected more than two fractional digits before storage quantization while preserving valid locale-grouped whole/cents parsing.
- [x] 12.3 Proved confirmation inserts only valid storage-safe rows and never inserts rows rejected for excess precision.
- [x] 12.4 Re-ran the complete backend suite, frontend build/typecheck, browser tests, and alternate-port Compose/API smoke with exact evidence.

### Amount Precision Contract Implemented

- CSV monetary mapping now treats values with more than two fractional digits after locale normalization as row-level `INVALID_AMOUNT` data.
- The parser performs the precision check before `Decimal("0.01")` quantization, so excess precision is rejected instead of silently rounded.
- `es_AR` grouped whole values such as `1.234` and grouped cent values such as `1.234,56` remain accepted.
- `en_US` grouped whole values such as `1,234` and grouped cent values such as `1,234.56` remain accepted.
- Invalid precision rows remain excluded from `valid_rows`; confirmation inserts only the validated storage-safe rows.

### TDD Cycle Evidence - Final Amount Precision

| Task | Test File | Layer | Safety Net | RED | GREEN | TRIANGULATE | REFACTOR |
|---|---|---|---|---|---|---|---|
| 12.1 | `backend/tests/test_import_api.py` | Integration | ✅ `pytest tests/test_import_api.py` -> `20 passed` before adding the regressions | ✅ Written first; pre-fix focused run -> `3 failed, 4 passed, 20 deselected` | ✅ `pytest tests/test_import_api.py -k "fractional_digits or sub_cent or grouped_whole_and_cent or confirmation_only_inserts"` -> `7 passed, 20 deselected` | ✅ Excess precision `1234,567`, sub-cent `0,004`, es_AR grouped whole/cents, and en_US grouped whole/cents | ✅ Added explicit amount quantum and fractional-digit constants; no parser redesign |
| 12.2 | `backend/tests/test_import_api.py` | Integration | ✅ Same `20 passed` import-module baseline | ✅ Written first; excess precision was accepted/rounded before the implementation | ✅ Focused precision/grouping run -> `6 passed, 21 deselected` | ✅ Both locale grouping separators and both grouped whole/cents branches remain covered | ✅ Precision validation is isolated before the existing storage quantization |
| 12.3 | `backend/tests/test_import_api.py` | Integration/API confirmation | ✅ Same `20 passed` import-module baseline | ✅ Written first; mixed confirmation run accepted both rows before the implementation | ✅ `pytest tests/test_import_api.py -k confirmation_only_inserts` -> `1 passed, 26 deselected` | ✅ A mixed batch confirms one valid cent row while excluding one excess-precision row; the sub-cent-only test confirms zero inserts | ✅ Reused the existing mapping/confirmation path without changing confirmation transaction semantics |
| 12.4 | Cumulative gates and Compose/API/browser harnesses | Integration/runtime | ✅ All prior cumulative evidence preserved | ➖ Evidence-only task; command plan recorded before execution | ✅ Full gates and runtime checks passed | ✅ Local browser module plus Compose frontend routes, API mapping/confirmation, Postgres, Alembic, and CORS | ✅ Evidence appended without rewriting prior batches or warning follow-ups |

### Test Summary - Final Amount Precision

- **Focused amount precision regressions**: `cd backend && pytest tests/test_import_api.py -k "fractional_digits or sub_cent or grouped_whole_and_cent or confirmation_only_inserts"` -> `7 passed, 20 deselected`, exit `0`.
- **Focused import module**: `cd backend && pytest tests/test_import_api.py` -> `27 passed in 1.07s`, exit `0`.
- **Full backend gate**: `cd backend && pytest` -> `67 passed in 40.33s`, exit `0`.
- **Frontend build**: `cd frontend && npm run build` -> passed, exit `0`; existing Vite chunk warning remains at `705.04 kB`.
- **Frontend typecheck**: `cd frontend && npx tsc --noEmit` -> passed with no output, exit `0`.
- **Browser gate**: `cd backend && pytest tests/test_frontend_upload_step_contract.py` -> `12 passed in 37.90s`, exit `0`.
- **Diff validation**: `git diff --check` -> passed, exit `0`.

### Remediation Work Unit Evidence - Final Amount Precision

#### Unit 35 - Excess precision and locale grouping

| Evidence | Required value |
|---|---|
| Focused test command and exact result | `cd backend && pytest tests/test_import_api.py -k "fractional_digits or sub_cent or grouped_whole_and_cent"` -> `6 passed, 21 deselected`, exit `0` |
| Runtime harness command/scenario and exact result | `POSTGRES_PORT=55439 FRONTEND_PORT=43004 IMPORT_DEFAULT_LOCALE=es_AR docker compose up -d --build` exited `0`; the first composite precision harness classified `1234,567` and `0,004` as `INVALID_AMOUNT`, retained `1.234` as `1234.00` and `1.234,56` as `1234.56`, and confirmed the batch before its later default-page assertion exited `1` because existing transactions exceeded `page_size=20`; the corrected `search` plus `page_size=100` rerun exited `0`, and the en_US grouped variants passed in the focused API regression |
| Rollback boundary | Revert `AMOUNT_QUANTUM`, `MAX_AMOUNT_FRACTIONAL_DIGITS`, and the precision guard in `backend/app/services/import_service.py` plus the amount precision/grouping cases in `backend/tests/test_import_api.py`; existing CSV validation, locale behavior outside excess precision, and confirmation hardening remain |

#### Unit 36 - Confirmation safety for invalid precision rows

| Evidence | Required value |
|---|---|
| Focused test command and exact result | `cd backend && pytest tests/test_import_api.py -k confirmation_only_inserts` -> `1 passed, 26 deselected`, exit `0`; the sub-cent-only regression also passed in the 7-case focused run |
| Runtime harness command/scenario and exact result | On the alternate-port Compose stack, batch `31` mapped four rows as `2 valid, 2 invalid`, confirmed with `records_inserted=2`, and the transaction search returned exactly `1234.00` and `1234.56`; no invalid amount was inserted |
| Rollback boundary | Revert only the confirmation safety regression in `backend/tests/test_import_api.py`; no production confirmation, migration, or unrelated import behavior is removed |

#### Unit 37 - Complete gates and alternate-port runtime evidence

| Evidence | Required value |
|---|---|
| Focused test command and exact result | `cd backend && pytest` -> `67 passed in 40.33s`; `cd frontend && npm run build` -> pass with the existing `705.04 kB` warning; `cd frontend && npx tsc --noEmit` -> pass; browser module -> `12 passed`; `git diff --check` -> pass |
| Runtime harness command/scenario and exact result | `POSTGRES_PORT=55439 FRONTEND_PORT=43004 IMPORT_DEFAULT_LOCALE=es_AR docker compose up -d --build`; `elite_postgres` healthy, backend health `{"status":"ok"}`, frontend `/, /import, /transactions, /transactions/new` returned `200`, Playwright `/import` asserted CSV picker behavior, CORS returned `200` with `http://localhost:43004`, and Alembic reported `010_source_context_identity (head)` |
| Rollback boundary | Revert only the Phase 12 evidence additions in `openspec/changes/mvp-integration-hardening/tasks.md` and `apply-progress.md`; Units 35-36 implementation and regression files remain independently revertible |

### Harness Note

- The first runtime assertion queried the default transactions page and did not find the newly inserted rows because the endpoint defaulted to `page_size=20` over an existing database.
- The product flow had already mapped and confirmed the expected batch; the corrected rerun queried the unique description with `search` and `page_size=100` and passed without changing application code.

### Warnings Preserved as Follow-ups

- Vite production bundle warning remains at approximately `705.04 kB`; no code-splitting work was added.
- The ordinary backend pytest fixture remains in-memory SQLite; no generalized Postgres pytest fixture was introduced.
- The Compose file emits the existing non-blocking warning that the `version` attribute is obsolete; no unrelated Compose cleanup was included.
- Empty CSV handling, missing frontend test dependencies, staged-file persistence, concurrent upload deduplication, and dependency audit findings remain follow-ups.

### Current Remediation Status

- All Phase 12 remediation tasks in `openspec/changes/mvp-integration-hardening/tasks.md` are checked `[x]`.
- The final amount-precision CRITICAL defect is addressed with cumulative RED/GREEN/triangulation evidence and direct runtime proof.
- No commit was created.
- Apply phase is ready for `sdd-verify`.
