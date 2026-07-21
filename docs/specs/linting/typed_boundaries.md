# Type Linting and Exception Policy

## Purpose

Define static analysis rules that enforce typed API boundaries and discourage generic catch-all types for inbound data.

This document defines typed-boundary requirements and should be read with the linting framework in:
- `docs/specs/linting/baseline.md`
- `docs/specs/linting/python.md`
- `docs/specs/linting/exceptions.md`

## Scope

Applies to:
- `src/api/*`
- `src/models/*`
- Service entry points that receive API-parsed payloads

## Baseline Rules

1. No generic catch-all types for inbound domain payloads
- Do not use `Any`, bare `object`, or unbounded `dict` for request payloads and API-ingested structures.
- Use explicit typed fields and nested models.

2. API boundary validation must use Pydantic models
- REST request bodies, MCP tool args, webhook payloads, and websocket inbound messages must be represented by explicit Pydantic models.
- Route and handler code must not pass raw payload maps to service logic.

3. Unknown/extra field handling must be explicit
- Default behavior should reject unknown fields.
- Permissive parsing must be documented as an exception.

## Recommended Lint and Type Checks

- Enable a lint rule set that flags generic payload types and broad type suppressions.
- Enable type checking strict enough to detect untyped boundary arguments.
- Equivalent tools are acceptable; common choices are Ruff plus mypy or pyright.
- Apply repository-wide lint policy structure from `docs/specs/linting/README.md`.

## Exception Process

Exceptions are allowed only when payload shape is genuinely dynamic and cannot be modeled safely.

Required for each exception:
- Exact location (file and symbol).
- Reason explicit schema modeling is not viable.
- Risk and mitigation notes.
- Owner and review date.
- Tracking issue or ADR reference.

Exception documentation location:
- Add an entry to `docs/specs/core/config.md` under a section named `Type Linting Exceptions`.

## Review Gate

- PRs introducing new generic inbound payload types must be blocked unless they include an approved exception record.
- PRs that relax type/lint checks must include a spec update and rationale.
