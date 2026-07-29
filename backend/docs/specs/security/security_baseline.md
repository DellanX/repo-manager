# Security Baseline Specification

**Status**: Mandatory. New features must satisfy these controls.

## Required Controls

| Control | Requirement |
|---------|-------------|
| Workspace isolation | Paths resolve under workspace root; `../` rejected |
| Command execution | Policy allowlist or sandbox; no free-form shell |
| Input limits | Max sizes for cmd/file; exceed → 4xx |
| Error hygiene | No secrets/paths/usernames in errors |
| Event auditability | Redact sensitive fields; include op/status/ts |
| Auth readiness | Declared "not implemented"; prod requires decision record |
| Credential handling | Encrypted at rest; referenced by ID; redacted from logs |
| Webhook safety | SSRF protections; signed payloads; TLS required |
| Typed boundaries | Pydantic at API boundary; see [typed_boundaries.md](../linting/typed_boundaries.md) |

## Test Requirements

- Traversal rejection for read/write
- Injection rejection for exec
- Input-size boundary tests
- Redaction checks
- Unauthorized access (when auth added)

## Exceptions

Document in [config.md](../core/config.md) under Type Linting Exceptions.
