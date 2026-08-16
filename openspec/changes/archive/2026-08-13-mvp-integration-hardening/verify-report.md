schema: gentle-ai.verify-result/v1
evidence_revision: sha256:055212850bb6f9f90f67de88b55f5c3c402ec06da3ba3f432d5e641552ca3496
verdict: pass
blockers: 0
critical_findings: 0
requirements: 3/3
scenarios: 6/6
test_command: cd backend && pytest
test_exit_code: 0
test_output_hash: sha256:0bfb7de1fc96a136ef97afdb3d16f5ee51ef86f84f1cc730007051a311f9f02
build_command: cd frontend && npm run build
build_exit_code: 0
build_output_hash: sha256:98c7ac9932e8125d723bad7ab00f0f676ed102a8eaa5ef1cb7f423dae07709f8

## Verification Report

**Change**: mvp-integration-hardening
**Version**: N/A
**Mode**: Strict TDD
**Review context**: The approved post-apply review lineage supplied for this retry is `review-d81b0eb10c2ba7ae`.
No new review or lifecycle transaction was started.

### Completeness

| Metric | Value |
|--------|-------|
| Tasks total | 49 |
| Tasks complete | 49 |
| Tasks incomplete | 0 |
| TDD evidence rows | 49 |

All 49 task checkboxes in `openspec/changes/mvp-integration-hardening/tasks.md` are checked.
The cumulative `apply-progress.md` contains TDD Cycle Evidence for every task row across the initial batch and remediation batches 5 through 12.

### Build & Tests Execution

**Backend tests**: ✅ 67 passed, 0 failed, 0 skipped.

Command: `cd backend && pytest`

Exit code: `0`

Output hash: `sha256:0bfb7de1fc96a136ef97afdb3d16f5ee51ef86f84f1cc730007051a311f9f02`

The run collected all 67 tests and completed in 27.03 seconds.

**Frontend build**: ✅ Passed.

Command: `cd frontend && npm run build`

Exit code: `0`

Output hash: `sha256:98c7ac9932e8125d723bad7ab00f0f676ed102a8eaa5ef1cb7f423dae07709f8`

The build completed in 15.87 seconds.
It emitted the existing Vite warning for a 705.04 kB JavaScript chunk exceeding the 500 kB warning threshold.

**Frontend typecheck**: ✅ Passed.

Command: `cd frontend && npx tsc --noEmit`

Exit code: `0`

Output hash: `sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`

**Diff validation**: ✅ Passed.

Command: `git diff --check`

Exit code: `0`

Output hash: `sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`

**Coverage**: ➖ Coverage analysis skipped because `pytest-cov` was not detected.

### Compose, API, and Browser Smoke

The available Compose stack was already running from the approved apply evidence and was inspected without restarting or changing application code.

`docker compose ps` showed all three services running:

| Service | Runtime evidence |
|---------|------------------|
| `elite_postgres` | Healthy, host `55439` to container `5432` |
| `elite_backend` | Up, host `8000` to container `8000` |
| `elite_frontend` | Up, host `43004` to container `80` |

`docker compose config --quiet` exited `0`.
The command emitted the existing non-blocking warning that the Compose `version` attribute is obsolete.
The backend environment reported `IMPORT_DEFAULT_LOCALE=es_AR` and `IMPORT_DEFAULT_TIMEZONE=UTC`.
`docker compose exec -T backend alembic current` reported `010_source_context_identity (head)`.

**Compose/API smoke**: ✅ Passed.

The smoke exercised health, category create/list, transaction create/list, dashboard summary/categories/timeseries for day/week/month, products, CORS preflight, CSV upload/detail/mapping/confirmation, valid grouped amounts, excess-precision and sub-cent rejection, confirmed-row persistence, and non-CSV rejection.

Command harness output hash: `sha256:fb5ddb531332d9117e17060c67d10788c82d49c7c383061b660609ccb99b368c`

The live import mapping classified four rows as two valid and two `INVALID_AMOUNT` rows.
Confirmation inserted exactly the two valid rows and did not insert excess-precision or sub-cent values.
The non-CSV upload returned HTTP 400 with CSV-only wording.
CORS preflight returned HTTP 200 with `Access-Control-Allow-Origin: http://localhost:43004`.

**Compose/browser smoke**: ✅ Passed.

Headless Chromium opened `/import`, `/transactions`, and `/transactions/new` directly through nginx.
Each route returned HTTP 200 and rendered `Import Transactions`, `Transaction History`, and `Add Transaction` respectively.
The `/import` route rendered the CSV-only picker and copy, rejected no runtime precondition, and enabled upload after selecting a CSV file.

Command harness output hash: `sha256:d2eabdaf52c3100427bbff5ffaadccdb0d602ef078abd3e65cd5aa17b306a6f7`

### Spec Compliance Matrix

| Requirement | Scenario | Test or evidence | Result |
|-------------|----------|------------------|--------|
| Live Integration Verification | End-to-end smoke verification succeeds | Current Compose service inspection, Alembic head, `Compose/API smoke`, and `Compose/browser smoke` | ✅ COMPLIANT |
| Live Integration Verification | Live stack cannot be executed in the current environment | Conditional fallback branch was not applicable because the complete three-service stack executed successfully | ➖ N/A |
| CSV-Only Import Contract | CSV import path is validated | `backend/tests/test_import_api.py` CSV upload/mapping/confirmation tests and current Compose/API CSV smoke | ✅ COMPLIANT |
| CSV-Only Import Contract | Non-CSV input is submitted | `backend/tests/test_import_api.py` rejection tests and current Compose/API `.xlsx` rejection smoke | ✅ COMPLIANT |
| Acceptance Evidence Boundaries | Evidence-backed checklist completion | `tasks/mvp-implementation.md` §5, current command hashes, current Compose evidence, and current browser evidence | ✅ COMPLIANT |
| Acceptance Evidence Boundaries | Missing evidence for a criterion | No criterion was marked from an unobserved pass; the report keeps the conditional fallback branch explicitly N/A | ✅ COMPLIANT |

**Compliance summary**: 5/5 applicable scenarios compliant; 1/6 conditional scenarios N/A because its failure precondition did not occur.

All three requirements are evidenced.
The live integration success branch is directly verified against Postgres, Alembic, the backend API, nginx, browser routes, and CORS.

### Correctness (Static Evidence)

| Requirement | Status | Notes |
|------------|--------|-------|
| Live Compose boot and migration path | ✅ Implemented | Compose uses `postgresql+psycopg`, Postgres health gating, backend Alembic-on-boot, configurable host ports, and the current migration head is `010_source_context_identity`. |
| CSV-only import contract | ✅ Implemented | Backend accepts only `.csv` extensions and approved CSV content types, emits CSV-only rejection wording, and the frontend exposes `accept=".csv"` with CSV-only copy. |
| Source-context import identity | ✅ Implemented | Semantic fingerprints remain non-unique across source contexts, exact source rows use `source_fingerprint`, and migration 010 installs the source-row uniqueness constraint. |
| Staged-file persistence | ✅ Implemented | Compose mounts the named `import_storage` volume at `IMPORT_STORAGE_DIR`; apply regressions cover pending and validated recovery after backend recreation. |
| Frontend API configuration | ✅ Implemented | Compose supplies build-time and runtime `VITE_API_BASE_URL`; the browser resolves runtime configuration before build configuration. |
| Calendar and timeseries behavior | ✅ Implemented | Date-only values use the configured IANA business timezone, filters convert local calendar boundaries to UTC, and day/week/month buckets use the requested timezone. |
| Amount precision and confirmation safety | ✅ Implemented | More than two fractional digits are rejected before quantization, grouped `es_AR` and `en_US` whole/cents values remain valid, and confirmation inserts only storage-safe rows. |
| Acceptance evidence boundaries | ✅ Implemented | The acceptance checklist is checked only alongside direct test, build, API, Compose, browser, and typecheck evidence recorded here and in cumulative apply progress. |

### Coherence (Design)

| Decision | Followed? | Notes |
|----------|-----------|-------|
| Require live Compose smoke on Postgres | ✅ Yes | The complete alternate-port Compose stack was exercised with healthy Postgres, Alembic head, API smoke, browser smoke, and CORS. Default host-port preservation is covered by Compose contract tests. |
| Restrict MVP import behavior to CSV | ✅ Yes | Backend and frontend enforce the CSV-only contract while legacy unreachable Excel schema support remains as allowed by the compatibility decision. |
| Link checked acceptance criteria to direct evidence | ✅ Yes | Every checked §5 criterion is covered by current runtime, API, browser, test, build, or typecheck evidence in this report. |
| Keep the existing data model compatible | ⚠️ Authorized deviation documented | Later authorized remediation added migrations 008 through 010 for source-row identity, duplicate safety, and upgrade sequencing. `apply-progress.md` records the deviation and its rollback boundary; runtime migration and regression evidence pass. |
| Preserve user-selected local calendar dates | ✅ Yes | Frontend calendar strings remain date-only, API requests include the browser IANA timezone, and backend boundaries are normalized to UTC. |

### TDD Compliance

| Check | Result | Details |
|-------|--------|---------|
| TDD Evidence reported | ✅ | All 49 task rows have entries in cumulative `TDD Cycle Evidence` tables. |
| All tasks have tests | ✅ | All 36 rows that name a test file or runtime harness resolve to current test or runtime artifacts; the remaining 13 rows are explicitly configuration, documentation, planning, or evidence-only tasks. |
| RED confirmed (tests exist) | ⚠️ | All referenced test files exist and all current tests pass. 21/36 test-bearing rows use the exact `✅ Written` marker; 15 earlier rows use equivalent explicit pre-fix RED wording rather than the strict marker. |
| GREEN confirmed (tests pass) | ✅ | The complete backend suite passed 67/67 tests, including all change-related API, migration, configuration, repository, concurrency, and browser tests. |
| Triangulation adequate | ✅ | The cumulative evidence records rejection/acceptance, locale, timezone, migration, replay, route, and confirmation variants; structural single-case checks are supplemented by runtime smoke. |
| Safety Net for modified files | ✅ | Existing modified implementation/test paths record baseline runs, and new/configuration/evidence paths explicitly record `N/A (new)` or equivalent applicability. |

**TDD Compliance**: 5/6 strict checks passed without qualification.

The only qualification is historical RED marker wording in cumulative apply evidence, not missing tests or failing runtime behavior.

### Test Layer Distribution

| Layer | Tests | Files | Tools |
|-------|-------|-------|-------|
| Unit | 0 | 0 | No isolated unit-only test file identified |
| Integration | 44 | 5 | pytest, FastAPI TestClient, SQLAlchemy, migration and Compose subprocess checks |
| E2E | 12 | 1 | pytest with Playwright and Chromium |
| Configuration/static contracts | 7 | 3 | pytest and Compose config inspection |
| **Change-related total** | **63** | **9** | |

The four baseline tests in `test_health_and_categories.py` and `test_transactions_api.py` are included in the 67-test full-suite result but are not counted as change-related files.

### Changed File Coverage

Coverage analysis skipped - no coverage tool was detected.

### Assertion Quality

No tautologies, ghost loops, orphan empty-result assertions, or smoke-only assertions were found in the behavior tests.
The replacement frontend contract tests execute Vite and Chromium and assert rendered copy, file-picker behavior, selected-file state, mapping requests, calendar payloads, and runtime API origin.

| File | Lines | Assertion type | Issue | Severity |
|------|-------|----------------|-------|----------|
| `backend/tests/test_frontend_api_config_contract.py` | 24-39 | Compose/Dockerfile/runtime-bootstrap structure | Structural configuration assertions are supplemental; runtime configured-origin browser coverage also passed. | WARNING |
| `backend/tests/test_frontend_spa_fallback_contract.py` | 7-10 | nginx directive presence | Structural fallback assertion is supplemental; direct Compose route/browser smoke also passed. | WARNING |
| `backend/tests/test_compose_port_contract.py` | 29-64 | Rendered Compose configuration | Configuration-shape assertions are supplemental; the running alternate-port stack passed the same route, health, and CORS contracts. | WARNING |

**Assertion quality**: 0 CRITICAL, 3 WARNING.

### Quality Metrics

**Linter**: ➖ No project linter configuration or dependency was detected.

**Type Checker**: ✅ `cd frontend && npx tsc --noEmit` passed with zero errors.

### Issues Found

**CRITICAL**: None.

**WARNING**:

1. The frontend production bundle is 705.04 kB and triggers Vite's over-500 kB chunk warning.

2. The standard backend pytest fixture remains SQLite-backed rather than a generalized Postgres fixture.
The critical migration and runtime API paths were separately exercised against the live Postgres Compose service.

3. Compose emits the existing non-blocking warning that the `version` attribute is obsolete.

4. The cumulative apply artifact has inconsistent historical RED marker wording.
The current test files exist and all 67 current tests pass, but 15 of 36 test-bearing evidence rows do not use the exact strict `✅ Written` marker.

5. The repository has no standalone frontend JavaScript test runner.
Browser coverage is available through the pytest/Playwright contract module and the direct Compose browser smoke.

**SUGGESTION**:

1. Split the frontend production bundle with code-splitting in a follow-up change.

2. Add a generalized Postgres pytest fixture in a follow-up change.

3. Normalize historical RED evidence wording if the cumulative apply artifact is regenerated.

### Canonical Evidence Manifest

The `evidence_revision` is the SHA-256 digest of the following exact manifest bytes:

```text
backend=0bfb7de1fc96a136ef97afdb3d16f5ee51ef86f84f1cc730007051a311f9f02|build=98c7ac9932e8125d723bad7ab00f0f676ed102a8eaa5ef1cb7f423dae07709f8|typecheck=e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855|api=fb5ddb531332d9117e17060c67d10788c82d49c7c383061b660609ccb99b368c|browser=d2eabdaf52c3100427bbff5ffaadccdb0d602ef078abd3e65cd5aa17b306a6f7|compose_ps=945bc14c5faf69df204a6f85936e1e7069fe94c1fe7dc58334876684524b3cbc|diff=e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
```

### Verdict

**PASS WITH WARNINGS**

The complete final implementation passes the strict backend suite, frontend build, frontend typecheck, current three-service Compose/API/browser smoke, and all applicable specification scenarios.
No critical findings or blockers remain.
The warnings are non-blocking follow-ups and the historical RED marker wording qualification.
