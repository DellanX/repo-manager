# Contributing Specification Changes

## Required with Code Changes

Update specs when changing:
- API route contracts.
- MCP tool contracts.
- Service behavior.
- Event payload structure.
- Schema defaults or required fields.
- Security controls.

## Pull Request Checklist

1. Updated matching module-aligned spec files.
2. Updated `implementation/traceability_matrix.md` rows.
3. Added or updated tests referenced by test IDs.
4. Confirmed security baseline impact.

## Review Guidance

- Reject PRs that change behavior without spec updates.
- Reject PRs that add capability without traceability row.
- Reject PRs that weaken mandatory security controls.
