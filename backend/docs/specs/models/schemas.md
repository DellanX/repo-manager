# Schema Contracts Specification

Source: `src/models/schemas.py`

## Request Models

| Model | Fields | Defaults |
|-------|--------|----------|
| CloneRequest | url | — |
| CheckoutRequest | workspace_id, branch | — |
| CommitRequest | workspace_id, message | — |
| PushRequest | workspace_id, remote, branch | origin, main |
| WriteFileRequest | workspace_id, path, content | — |
| ExecRequest | workspace_id, cmd | — |
| MCPCallRequest | tool, args | args={} |

For full tool contracts see [agents/tools.yaml](../agents/tools.yaml).

## Compatibility

- Additive fields OK when backward compatible.
- Renames/removals require migration plan.

## Validation

- Required fields fail fast (422).
- Optional fields have explicit defaults.
- Type safety per [linting/typed_boundaries.md](../linting/typed_boundaries.md).
