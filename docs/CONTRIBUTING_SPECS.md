# Contributing Specification Changes

## Required with Code Changes

Update specs when changing:
- API route contracts.
- MCP tool contracts.
- Service behavior.
- Event payload structure.
- Schema defaults or required fields.
- Security controls.
- Validation models and type constraints for externally ingested data.
- Linting policy baselines or exception workflows under `docs/specs/linting/`.

## Pull Request Checklist

1. Updated matching module-aligned spec files.
2. Updated `implementation/traceability_matrix.md` rows.
3. Updated lint/type policy references and documented any required exceptions.
4. Confirmed security baseline impact.
5. Confirmed 100% line coverage for in-scope source files, or documented approved exceptions for every uncovered line.

## CI And Branch Rules

- GitHub Actions workflow `CI - Tests` runs on every push and pull request for `main` and `develop`.
- `main` must be branch-protected with required status checks enabled for `CI - Tests / tests`.
- `develop` should keep the workflow enabled but should not require this check to merge, so failures are visible early without blocking integration.
- Recommended GitHub setting for `main`: enable "Require status checks to pass before merging" and select `CI - Tests / tests`.

## Review Guidance

- Reject PRs that change behavior without spec updates.
- Reject PRs that add capability without traceability row.
- Reject PRs that weaken mandatory security controls.
- Reject PRs that introduce generic untyped API payload handling where a Pydantic schema can be defined.
- Reject PRs that add typed-boundary exceptions without a complete exception record in `docs/specs/core/config.md`.
- Reject PRs with uncovered lines that do not include explicit justification/exception records.
