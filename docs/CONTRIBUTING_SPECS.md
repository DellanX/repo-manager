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

## Review Guidance

- Reject PRs that change behavior without spec updates.
- Reject PRs that add capability without traceability row.
- Reject PRs that weaken mandatory security controls.
- Reject PRs that introduce generic untyped API payload handling where a Pydantic schema can be defined.
- Reject PRs that add typed-boundary exceptions without a complete exception record in `docs/specs/core/config.md`.
