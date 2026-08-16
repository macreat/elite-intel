# Proposal: MVP Integration Hardening

## Intent

Backend/frontend are implemented but never verified end-to-end. Backend tests only run against SQLite, never Postgres; frontend is built but uncommitted; two QA fixes (psycopg driver, alembic-on-boot) are unverified. Close this gap per §5 of `tasks/mvp-implementation.md`.

## Scope

### In Scope
- Live `docker compose up`: Postgres healthcheck, migrations, boot order
- CSV-only import hardening: scope validation/docs to CSV, drop Excel claims
- Frontend gates: build + typecheck, plus manual smoke checks (no test runner)
- Walk and check off §5 acceptance criteria with evidence
- Split uncommitted work into conventional commits (frontend, Docker, scaffolding)

### Out of Scope
- Automated Postgres pytest fixture/CI (follow-up)
- Frontend bundle code-splitting (follow-up)
- Excel import (never implemented; CSV only)
- Auth, ML models (excluded by frozen contract)

## Capabilities

### New Capabilities
None.

### Modified Capabilities
None — verification and commit hygiene, not a requirements change.

## Approach

Run `docker compose up -d`, confirm Postgres health and migrations, smoke-test each `/api/v1` endpoint and frontend against the live backend, verify CORS. Restrict import validation/messaging to CSV. Walk §5 checklist with evidence. Split dirty tree into conventional commits.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `docker-compose.yml`, `backend/Dockerfile` | Verified | Confirm psycopg + alembic-on-boot fixes work live |
| `backend/app/db/migrations/versions/*` | Verified | Revision chain applies cleanly on Postgres |
| `backend/app/api/v1/imports.py` | Clarified | Scope validation/messaging to CSV only |
| `frontend/src/services/apiClient.ts`, `.env*` | Verified | URL/CORS match dev + compose |
| Git history | New commits | Frontend, Docker/env, scaffolding split |
| `tasks/mvp-implementation.md` §5 | Updated | Checklist marked with evidence |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Docker unavailable in sandbox | Med | Fallback: local Postgres or manual runbook |
| Uncommitted migration diffs hide drift | Low | Diff against last commit before committing |
| CORS/URL mismatch (Vite 5173 vs compose 3000) | Med | Document both flows |
| Commit splitting bundles unrelated changes | Low | Stage per group before commit |

## Rollback Plan

Additive verification + commit organization only; no schema/API redesign. If a live defect is found, revert the isolated commit and file a blocker; SQLite tests unaffected.

## Dependencies

- Docker/docker-compose available for the smoke test

## Success Criteria

- [ ] `docker compose up -d` succeeds; Postgres healthy; migrations apply cleanly
- [ ] All `/api/v1` endpoints smoke-tested against live Postgres backend
- [ ] Import pipeline validated/documented as CSV-only
- [ ] Build + typecheck pass; manual smoke checks done
- [ ] §5 checklist fully checked with evidence
- [ ] Frontend, Docker/env, SDD scaffolding committed as separate conventional commits
