# MVP Integration Hardening Specification

## Purpose

Define MVP acceptance behavior for integration hardening, CSV-only import scope, and verification evidence boundaries.

## Requirements

### Requirement: Live Integration Verification

The MVP verification process MUST validate the running stack against the containerized Postgres-backed environment before acceptance.

#### Scenario: End-to-end smoke verification succeeds

- GIVEN the MVP change candidate is ready for verification
- WHEN the team runs the live integration smoke flow against the containerized stack
- THEN Postgres health, migration application, API smoke checks, frontend smoke checks, and CORS behavior MUST be verified as successful
- AND the verification outcome MUST be recorded as acceptance evidence

#### Scenario: Live stack cannot be executed in the current environment

- GIVEN the verification environment cannot run the containerized stack
- WHEN integration verification is attempted
- THEN acceptance MUST remain incomplete for live integration checks
- AND a manual runbook MAY be recorded as a temporary fallback artifact

### Requirement: CSV-Only Import Contract

The MVP import contract SHALL accept CSV inputs only and MUST NOT claim Excel support.

#### Scenario: CSV import path is validated

- GIVEN a valid CSV file is provided for import
- WHEN import validation and processing are executed
- THEN the flow MUST proceed under the MVP import contract
- AND user-facing and acceptance-facing language SHALL refer to CSV only

#### Scenario: Non-CSV input is submitted

- GIVEN a non-CSV file is provided for import
- WHEN import validation is executed
- THEN the request MUST be rejected as out of MVP format scope
- AND the reported scope MUST remain CSV-only

### Requirement: Acceptance Evidence Boundaries

Acceptance reporting MUST include only directly observed verification evidence and SHALL keep unchecked any criterion lacking proof.

#### Scenario: Evidence-backed checklist completion

- GIVEN the MVP acceptance checklist is being finalized
- WHEN each criterion is reviewed
- THEN every checked criterion MUST map to direct evidence from this change execution
- AND the evidence reference MUST be explicit enough for independent review

#### Scenario: Missing evidence for a criterion

- GIVEN a criterion has no direct execution evidence
- WHEN acceptance evidence is reviewed
- THEN that criterion MUST remain unchecked
- AND no inferred or assumed pass state SHALL be recorded
