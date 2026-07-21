# Python Linting Specification

## Scope

Applies to:
- `src/**/*.py`
- `tests/**/*.py`

## Baseline Tooling Profile

Tooling is implementation-defined, but must provide equivalent coverage to:
- A fast linter (for example Ruff) for correctness, import hygiene, and anti-pattern detection.
- A static type checker (for example mypy or pyright) for boundary typing and contract checks.

## Required Rule Outcomes

1. Correctness
- Detect undefined names and unreachable/unused code patterns.
- Detect dangerous broad exception handling unless explicitly justified.

2. Type Discipline
- Discourage `Any` in domain and API boundary code.
- Discourage unbounded `dict`/`object` for inbound payloads.
- Require explicit models (Pydantic) at API ingestion boundaries where structure is known.

3. Suppression Hygiene
- Disallow file-level blanket ignores except with approved exception records.
- Require suppression comments to include a short reason.

4. CI Gate
- Lint and type checks must run in CI for changed Python modules.
- Blocking behavior must be documented per rule category.

## Domain Cross-Reference

- Typed API boundary policy is defined in `docs/specs/linting/typed_boundaries.md`.
- Exception records are tracked via `docs/specs/core/config.md` under `Type Linting Exceptions`.
