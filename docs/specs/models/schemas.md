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
