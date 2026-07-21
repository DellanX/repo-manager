# Schema Contracts Specification

Source module: `src/models/schemas.py`

## Request Models

- `CloneRequest { url: string }`
- `CheckoutRequest { branch: string }`
- `CommitRequest { message: string }`
- `PushRequest { remote: string='origin', branch: string='main' }`
- `ReadFileRequest { path: string }` (defined, currently not used by GET route)
- `WriteFileRequest { path: string, content: string }`
- `ExecRequest { cmd: string }`
- `MCPCallRequest { tool: string, args: object={} }`

## Compatibility Policy

- Additive fields allowed when backward compatible.
- Renames/removals require a compatibility note and migration plan.
- Defaults must be explicit in spec and tests.

## Validation Policy

- Required fields must fail fast with 422 (framework behavior).
- Optional fields must define deterministic defaults.
- Future strict mode should add field constraints and length limits.

## Type Safety Convention

- Avoid generic catch-all types for domain data and request payloads (for example `Any`, unbounded `dict`, `object`, or "unknown"-style placeholders).
- Every externally ingested payload (REST body, MCP args, webhook payload, websocket message) must be parsed through a Pydantic model before service-layer use.
- Use explicit nested Pydantic models instead of free-form JSON blobs whenever a structure is known.
- If a truly dynamic map is required, constrain it with typed keys/values and document the exception in the owning API spec.
- New or changed API contracts must include a matching Pydantic model update and satisfy the lint/type policy in `docs/specs/linting/typed_boundaries.md`.
