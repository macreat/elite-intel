# MVP Implementation Contract (FROZEN)

**Status:** Frozen — executors implement this, they do not redesign it.
**Repo:** `/home/lnxmacreat/wsp/projects/eliteSystem/repository/elite-intel`
**Branch:** `feat/mvp`
**Sources (read in order):** `SPEC.md` > `tasks/architecture.md` > `tasks/data-strategy.md` > `tasks/ui-design.md`

---

## 1. Locked stack

- Frontend: React + TypeScript + Vite + Tailwind
- Backend: FastAPI + Python + SQLAlchemy + Alembic + Pydantic
- DB: PostgreSQL 15 (docker-compose)
- No auth in MVP
- No ML models in MVP
- API base path: `/api/v1`
- CORS: allow frontend origin

## 2. Work partition (parallel-safe)

| Agent | May modify | Must NOT modify |
|---|---|---|
| Backend | `backend/**`, `docker-compose.yml` (only if required), root `.env.example` (backend vars), `data/**` only if seed fixtures needed | `frontend/**`, `tasks/**` (except own progress notes if any) |
| Frontend | `frontend/**` | `backend/**`, `tasks/**` |
| QA (later) | `backend/tests/**`, `frontend` tests only | redesign of schema/API |

Backend owns the contract; frontend consumes it. If a mock is needed before backend is up, frontend uses MSW or a thin fetch mock matching §5 of `tasks/architecture.md`.

## 3. Backend deliverables (must ship)

1. Project bootstrap: `pyproject.toml` or `requirements.txt`, `Dockerfile`, app entry `backend/app/main.py`
2. DB session + Alembic migrations creating tables in order:
   - enums
   - `categories` (+ seed default income/expense categories from SPEC FR-02)
   - `products` (table only)
   - `import_batches`
   - `import_rows`
   - `transactions` + indexes (incl. `pg_trgm` if used)
3. Models/schemas/repositories/services/api routers exactly as `tasks/architecture.md` §2 and §5
4. Endpoints (all under `/api/v1`):
   - Transactions: list (filter/paginate/search), get, create, update, delete
   - Categories: list, create, update, soft-delete
   - Dashboard: summary, categories breakdown, timeseries
   - Products: `GET /products` minimal list
   - Imports: upload, mapping, confirm, list, get
5. Business rules:
   - amount > 0, stored positive; type = INCOME|EXPENSE
   - category must match transaction type
   - savings = max(income - expenses, 0); savings_rate = savings/income or 0
   - import never mutates source file bytes; invalid rows reported; confirm is all-or-nothing
6. Tests (pytest): transaction CRUD, dashboard aggregation math, import validation/reject path, category type guard
7. Health: `GET /health` or `GET /api/v1/health`

## 4. Frontend deliverables (must ship)

1. Vite + React + TS + Tailwind + React Router bootstrap, `Dockerfile`
2. Routes (exact):
   - `/` Dashboard
   - `/transactions` History table
   - `/transactions/new` Create form
   - `/transactions/:id/edit` Edit form
   - `/import` Import wizard
3. Layout: sidebar (desktop) / compact nav (mobile), primary "Add Transaction" CTA
4. Dashboard: period filter, KPI cards (income, expenses, net, savings, savings rate, count), trend chart, category breakdown, recent transactions
5. Transactions: filterable table, edit/delete with confirm
6. Form: type, date, category (depends on type), amount, description, notes
7. Import wizard: upload → mapping → preview/errors → confirm → result
8. API client using `VITE_API_BASE_URL` (default `http://localhost:8000/api/v1`)
9. Loading + error states on all data views
10. `npm run build` succeeds

## 5. Acceptance criteria (SPEC §22 / orchestrator §13)

- [x] App starts (docker-compose or local)
- [x] DB starts
- [x] Create income / expense
- [x] Persist, edit, delete transactions
- [x] Filter transactions
- [x] Dashboard: income, expenses, net, savings
- [x] Category analysis
- [x] Period filtering
- [x] CSV import + invalid row report
- [x] Source file unchanged
- [x] Backend tests pass
- [x] Frontend builds
- [x] No critical runtime errors

## 6. Git

Small conventional commits, no Co-Authored-By. Examples:

- `feat(backend): bootstrap FastAPI app and db session`
- `feat(backend): add domain models and alembic migrations`
- `feat(backend): implement transaction and category APIs`
- `feat(backend): implement dashboard aggregations`
- `feat(backend): implement import pipeline`
- `test(backend): cover transaction and import flows`
- `feat(frontend): bootstrap Vite React app and layout`
- `feat(frontend): implement dashboard and transaction UI`
- `feat(frontend): implement import wizard`

## 7. Executor rules

- ROLE: EXECUTOR — implement yourself; do not spawn subagents; do not redesign architecture
- Prefer smallest change that satisfies the contract
- If blocked, write a short `tasks/blocker-<agent>.md` and stop that stream
- When done: summarize files changed + how to run tests/build

## 8. Runbook (target)

```bash
# from repo root
cp .env.example .env   # if needed
docker compose up -d postgres
# backend
cd backend && pip install -r requirements.txt && alembic upgrade head && uvicorn app.main:app --reload --port 8000
# frontend
cd frontend && npm install && npm run dev
```
