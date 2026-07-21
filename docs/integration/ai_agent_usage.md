# AI Agent Integration Guidance

## Objective

Define safe and deterministic usage patterns for AI clients interacting with Repo Manager.

## Recommended Operation Sequence

1. Clone repository.
2. Checkout target branch.
3. Read relevant files.
4. Write file updates.
5. Run safe validation commands.
6. Commit changes.
7. Push branch.

## Retry Guidance

- Do not blindly retry validation failures.
- Retry network-like git failures only after bounded backoff.
- Do not retry argument validation errors without changing input.

## Error Recovery

- On write failure: re-read target file and reassess path validity.
- On commit failure: inspect git status output before retrying.
- On push failure: verify remote and branch assumptions.

## Safety Rules for Agents

- Never send absolute paths outside workspace.
- Prefer tool-native operations over raw exec.
- Avoid destructive commands unless explicitly requested by user policy.
