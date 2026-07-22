# MCP API Specification

Source: `src/api/mcp.py`

## Endpoints

| Method | Path | Response |
|--------|------|----------|
| GET | `/mcp/tools` | `{ tools: [{ name, description }] }` |
| POST | `/mcp/call` | `{ tool, ok: true, result }` or error |

## Tool Contracts

See [agents/tools.yaml](../agents/tools.yaml) for complete tool definitions including args, returns, and constraints.

## Error Codes

| Code | Cause |
|------|-------|
| 400 | Missing arg, validation failure, operation error |
| 404 | Unknown tool |

## Invariants

- Tools wrap service functions; treat names as stable.
- Typed boundaries required per [linting/typed_boundaries.md](../linting/typed_boundaries.md).
