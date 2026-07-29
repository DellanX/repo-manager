# Agent Specifications

Machine-readable contracts for AI agents consuming Repo Manager.

## Files

| File | Purpose |
|------|---------|
| [tools.yaml](tools.yaml) | Tool registry with argument schemas |
| [sequences.md](sequences.md) | Canonical operation flows |
| [constraints.md](constraints.md) | Safety rules and limits |

## Usage

1. Parse `tools.yaml` to discover available tools and their contracts.
2. Follow sequences in `sequences.md` for common workflows.
3. Enforce rules in `constraints.md` before and after each call.

## Endpoint

All tools are invoked via `POST /mcp/call`:

```json
{"tool": "<tool_name>", "args": {<tool_args>}}
```

Response: `{"tool": "<tool_name>", "ok": true, "result": {<output>}}`

## Traceability

| ID | Description |
|----|-------------|
| RM-AGENT-TOOLS | Tool contract definitions |
| RM-AGENT-SEQUENCES | Operation flow patterns |
| RM-AGENT-CONSTRAINTS | Safety constraint rules |
