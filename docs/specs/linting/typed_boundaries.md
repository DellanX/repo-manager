# Type Linting and Exception Policy

## Purpose

Enforce typed API boundaries; discourage generic catch-all types for inbound data.

## Scope

`src/api/*`, `src/models/*`, service entry points receiving API payloads.

## Rules

| Rule | Requirement |
|------|-------------|
| No catch-all types | No `Any`, bare `object`, unbounded `dict` for payloads |
| Pydantic at boundary | REST, MCP, webhook, websocket payloads use explicit models |
| Unknown fields | Reject by default; permissive parsing = documented exception |

## Tooling

Ruff + mypy/pyright (or equivalent). Must flag generic types and broad suppressions.

## Exception Process

Allowed only when payload is genuinely dynamic.

**Required fields**:
- Location (file, symbol)
- Reason schema not viable
- Risk + mitigation
- Owner, review date
- Tracking issue/ADR

**Document in**: [config.md](../core/config.md) under Type Linting Exceptions.

## Review Gate

PRs adding generic payload types blocked without approved exception.
