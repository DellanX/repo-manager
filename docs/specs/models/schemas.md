# Schema Contracts Specification

Source: `src/models/schemas.py`

## Request Models

| Model | Fields | Defaults |
|-------|--------|----------|
| CloneRequest | url | — |
| CheckoutRequest | branch | — |
| CommitRequest | message | — |
| PushRequest | remote, branch | origin, main |
| WriteFileRequest | path, content | — |
| ExecRequest | cmd | — |
| MCPCallRequest | tool, args | args={} |

For full tool contracts see [agents/tools.yaml](../agents/tools.yaml).

## Compatibility

- Additive fields OK when backward compatible.
- Renames/removals require migration plan.

## Validation

- Required fields fail fast (422).
- Optional fields have explicit defaults.
- Type safety per [linting/typed_boundaries.md](../linting/typed_boundaries.md).
