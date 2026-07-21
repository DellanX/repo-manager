# MCP API Specification

Source module: `src/api/mcp.py`

## Tool Registry

Exposed tools:

- `git.clone`
- `git.checkout`
- `git.commit`
- `git.push`
- `workspace.read_file`
- `workspace.write_file`
- `workspace.exec`

`GET /mcp/tools` returns `{ tools: [{ name, description }] }`.

## Tool Call Contract

`POST /mcp/call`

Request:
- `tool: string`
- `args: object` (default `{}`)

Success response:
- `{ tool, ok: true, result: object }`

Error behavior:
- 404 for unknown tool.
- 400 for missing required argument.
- 400 for operation errors.

## Validation Rules

- Required args per tool are mandatory.
- Optional args for push default to `remote='origin'` and `branch='main'`.
- Values are currently cast to string in handlers.

## Agent Usage Notes

- Tools are thin wrappers over service functions.
- Agent clients should treat tool names as stable identifiers.
- Argument mismatch should be treated as non-retryable unless corrected.
