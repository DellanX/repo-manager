# Repo Manager Specifications

This directory is the source of truth for architecture, feature contracts, security requirements, and validation guidance for the Repo Manager microservice.

## Goals

- Keep specs aligned to code layout under `src/`.
- Make feature behavior testable before implementation changes.
- Give AI agents deterministic contracts for repo-management tasks.

## Navigation

- `ARCHITECTURE.md`: service boundaries, operation lifecycle, and non-goals.
- `specs/`: module-aligned behavior contracts.
- `implementation/`: testing strategy and full traceability matrix.
- `integration/`: guidance for AI-agent usage patterns.
- `examples/`: canonical task flows.
- `templates/`: reusable spec template.

## Module Mapping

- `src/api/*` -> `specs/api/*`
- `src/services/*` -> `specs/services/*`
- `src/core/*` -> `specs/core/*`
- `src/models/*` -> `specs/models/*`
- `src/ui/*` -> `specs/ui/*` (planned)

## Change Policy

Any pull request that changes API routes, service behavior, schemas, security posture, or event semantics must update matching spec files and `implementation/traceability_matrix.md`.
