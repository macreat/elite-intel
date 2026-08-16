## Exploration: MVP integration hardening (post-implementation gaps)

### Current State

Backend (`backend/app`) is committed on `feat/mvp` (3 commits: bootstrap, models/API, tests) and implements all `tasks/mvp-implementation.md` §3 deliverables: models, repositories, services, `/api/v1` routers for transactions/categories/dashboard/products/imports, Alembic migrations 001-006, and 8 passing pytest tests (`cd backend && pytest` → `8 passed`).

Frontend (`frontend/src`) is fully implemented (routes, layout, dashboard, transactions table/form, import wizard, API client) but is **entirely uncommitted** — `git status` shows all `frontend/**` files as untracked (`??`), plus `openspec/`, `tasks/`, `opencode.json` untracked too. No frontend commit exists in history despite the code being present and working (`npx tsc --noEmit` clean, `npm run build` succeeds, single JS bundle 704 KB / 206 KB gzip with a Vite "chunk >500KB" warning).

Small QA-driven fixes are already applied but also uncommitted: `backend/Dockerfile` CMD now runs `alembic upgrade head` before `uvicorn` (previously migrations never ran in the container), and `docker-compose.yml` `DATABASE_URL` now uses the `postgresql+psycopg://` driver scheme instead of bare `postgresql://` (the app depends on `psycopg` v3 per `requirements.txt`, so the untouched compose file would have failed to connect). `.gitignore` and 3 migration files also show as modified (`002`, `004`, `005`, `006` — likely whitespace/import cleanups from the same pass; not yet diffed against baseline commit `c284bb4`... they ARE part of the commit history changes, confirm before archiving).

Critically: **no integration/end-to-end pass has actually run**. All 8 backend tests run against an **in-memory SQLite** engine (`backend/tests/conftest.py`), not the Postgres 15 target in `docker-compose.yml`. `docker compose up` has not been executed in this session — Postgres connectivity, Alembic migration execution order, CORS between the two containers, and the frontend↔backend contract have never been exercised together. The MVP acceptance checklist in `tasks/mvp-implementation.md` §5 is entirely unchecked (`- [ ]` on every line), including "App starts (docker-compose)", "DB starts", "CSV/Excel import + invalid row report", "Backend tests pass", "Frontend builds".

### Affected Areas

- `docker-compose.yml`, `backend/Dockerfile`, `.env.example` — need a real `docker compose up` verification pass; the psycopg driver fix and alembic-on-boot fix are uncommitted and unverified end-to-end.
- `backend/app/db/migrations/versions/*` — migrations have only ever run against SQLite via `Base.metadata.create_all` in tests, never via `alembic upgrade head` against Postgres. Alembic revision chain integrity (`down_revision` links, enum creation order) is unverified.
- `backend/tests/conftest.py` — SQLite-only test harness means Postgres-specific behavior (native enums, `ON DELETE` behavior, trigram/text-search if used, connection pooling) is unverified.
- `frontend/src/services/apiClient.ts`, `frontend/.env*` — `VITE_API_BASE_URL` default and `FRONTEND_ORIGIN` CORS default (`http://localhost:3000`) must match whatever host/port combination is actually used (compose serves frontend prod build on 3000, but local dev via `npm run dev` typically defaults to Vite's 5173 — mismatch risk for local (non-docker) dev flow).
- Git history / working tree — frontend code, openspec scaffolding, and Docker/env QA fixes are all uncommitted; nothing is at risk of being lost only because this is a single working tree, but there is no commit boundary to review, bisect, or roll back independently, and `tasks/mvp-implementation.md` §6 (small conventional commits per deliverable) has not been followed for the frontend stream at all.
- `tasks/mvp-implementation.md` §5 acceptance checklist — unchecked; no artifact records that anyone walked through the criteria against a running stack.
- Frontend bundle size warning (704 KB single chunk) — not a blocker for MVP but worth a follow-up task if perf becomes a concern later.

### Approaches

1. **Full docker-compose integration pass + commit hardening** — Run `docker compose up -d`, confirm Postgres healthcheck, confirm `alembic upgrade head` applies cleanly against real Postgres, smoke-test each API endpoint and the frontend against the live backend, walk the §5 acceptance checklist, then commit the frontend and QA fixes as properly scoped conventional commits (one for frontend bootstrap, one for the Docker/env fixes, one for openspec scaffolding).
   - Pros: closes the actual verification gap (nothing has run against Postgres yet); produces a clean, reviewable git history; directly satisfies the frozen contract's own acceptance criteria.
   - Cons: requires Docker available in the execution environment; real e2e run takes longer than unit tests.
   - Effort: Medium.

2. **Postgres-backed test fixture only (skip live docker-compose smoke test)** — Add a `pytest` fixture/marker that runs the same test suite against a real Postgres instance (e.g., via `testcontainers` or a CI Postgres service), keeping the SQLite fixture for fast unit runs, without manually running `docker compose up`.
   - Pros: catches Postgres-specific and Alembic-specific regressions automatically and repeatably (CI-friendly); no manual verification step to forget.
   - Cons: does not verify the frontend↔backend integration or CORS in a real browser-like environment; adds a new test dependency; still leaves the acceptance checklist and commit hygiene gaps unaddressed on its own.
   - Effort: Medium-High (new dependency, CI wiring).

3. **Commit-only pass, defer integration verification** — Commit frontend + QA fixes as-is with conventional commits, leave the Postgres/Docker verification and acceptance checklist for a later change.
   - Pros: fastest; unblocks review of the code that already exists.
   - Cons: leaves the core unresolved risk (nobody has proven the stack works end-to-end against its target database) completely open; contradicts the frozen contract's own acceptance criteria being a gating deliverable.
   - Effort: Low.

### Recommendation

Approach 1 (full docker-compose integration pass + commit hardening), because the frozen contract's acceptance criteria explicitly require "App starts (docker-compose)" and "DB starts" as gating items, and the two already-applied fixes (`psycopg` driver scheme, alembic-on-boot) are themselves unverified guesses until a real `docker compose up` proves the container boots and migrates against Postgres. Approach 2's automated Postgres test coverage is valuable as a **follow-up**, not a substitute, because it does not touch the frontend/CORS/browser integration surface at all. Approach 3 defers the one gap that actually matters for MVP sign-off.

Recommended proposal scope: (a) run and document a live `docker compose up` verification, capturing Alembic + Postgres + CORS + frontend-build results; (b) fix any real defects found in that pass (do not assume the two existing uncommitted fixes are sufficient — verify them); (c) walk and check off `tasks/mvp-implementation.md` §5 acceptance criteria with evidence; (d) split the uncommitted work into scoped conventional commits (frontend bootstrap, Docker/env QA fixes, SDD scaffolding) per §6/§7 of the frozen contract; (e) file a follow-up (not in this change) for an automated Postgres-backed test fixture and frontend bundle code-splitting.

### Risks

- Docker may not be available/runnable in the execution sandbox for this change — verification could be blocked; needs an explicit fallback (e.g., local Postgres binary, or scoping the change to what CAN be verified plus a documented manual runbook for the rest).
- The already-uncommitted migration file changes (`002`, `004`, `005`, `006`) have not been diffed against the last commit in this exploration — must confirm they are QA/bugfix related and not silent schema drift before committing.
- Splitting uncommitted work into multiple commits risks bundling unrelated changes if not done carefully (frontend code + Docker fixes + openspec scaffolding are currently all mixed in one dirty working tree).
- CORS/API-base-URL mismatch between local `npm run dev` (Vite default port) and the compose `FRONTEND_ORIGIN` default could cause a false-negative "it doesn't work" during local (non-docker) verification if not clarified in the proposal.
- No frontend automated test runner exists (`testing.frontend.runner: none` in `openspec/config.yaml`); verification of frontend behavior will be manual/build-only, which limits regression protection this change can add without a larger test-tooling investment (out of scope here).

### Ready for Proposal

Yes. The gap is well-defined (live docker-compose/Postgres/CORS verification + acceptance checklist + commit hygiene), the current state and affected files are confirmed by direct inspection, and the recommended approach is scoped to fit the existing frozen contract without redesigning architecture. The orchestrator should tell the user: proceed to `sdd-propose` for `mvp-integration-hardening` covering the live verification pass, checklist walkthrough, and commit-splitting; treat automated Postgres test fixtures and frontend bundle optimization as separate follow-up changes.
