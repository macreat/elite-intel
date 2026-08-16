# Archive Report: MVP Integration Hardening

## Archive Result

- Schema: `gentle-ai.archive-result/v1`
- Change: `mvp-integration-hardening`
- Artifact store: OpenSpec
- Archive date: `2026-08-13`
- Status: `success-with-warnings`
- Application code modified by archive: No
- Commit created by archive: No

## Review Gate

- Review lineage: `review-d81b0eb10c2ba7ae`
- Review state: approved and validated, as supplied for this archive execution.
- Review gate result: `allow`.
- No review or lifecycle command was started by this archive phase.

The final verification report records the approved post-apply review lineage and a final PASS WITH WARNINGS verdict.
The caller supplied the approved and validated review state required to proceed.

## Verification Closure

- Final verdict: PASS WITH WARNINGS
- Blockers: `0`
- Critical findings: `0`
- Requirements: `3/3`
- Scenarios: `6/6`
- Tasks total: `49`
- Tasks complete: `49`
- Tasks incomplete: `0`
- Task checkbox reconciliation: None required.

The final evidence includes 67 passing backend tests, a passing frontend build, a passing TypeScript typecheck, passing Compose/API/browser smoke, and passing diff validation.
The live stack reached Alembic head `010_source_context_identity` with healthy Postgres, backend health, frontend routes, CSV-only import behavior, amount-precision rejection, confirmation safety, and CORS evidence.

## Spec Synchronization

No main spec existed at `openspec/specs/mvp-integration-hardening/spec.md` before archiving.
The delta spec was copied as the complete main specification without destructive merging.

- Main spec created: `openspec/specs/mvp-integration-hardening/spec.md`
- Requirements added: `3`
- Requirements modified: `0`
- Requirements removed: `0`
- Requirements renamed: `0`

## Archived Evidence Trail

The complete active change directory was moved to:

`openspec/changes/archive/2026-08-13-mvp-integration-hardening/`

Archived artifacts:

- `proposal.md`
- `exploration.md`
- `specs/mvp-integration-hardening/spec.md`
- `design.md`
- `tasks.md`
- `apply-progress.md`
- `verify-report.md`
- `archive-report.md`

No `state.yaml` was present in the active change directory and none was synthesized.
The cumulative `apply-progress.md` and final `verify-report.md` remain in the archive as the implementation and verification evidence trail.

## Preserved Warnings

- The frontend production bundle remains approximately 705.04 kB and triggers the existing Vite chunk warning.
- The standard backend pytest fixture remains SQLite-backed rather than a generalized Postgres fixture.
- Compose emits the existing non-blocking warning that the `version` attribute is obsolete.
- Historical TDD evidence has inconsistent RED marker wording in some cumulative rows.
- The repository has no standalone frontend JavaScript test runner.

These warnings are non-blocking follow-up items recorded by the final verification report.

## Archive Checks

- Main spec updated: PASS
- Change folder moved to archive: PASS
- Requested evidence artifacts preserved: PASS
- Archived tasks contain no unchecked implementation tasks: PASS
- Active changes directory no longer contains this change: verified after move
