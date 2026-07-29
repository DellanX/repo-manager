# Configuration Specification

Source: `src/core/config.py`

## Environment Variables

| Var | Default | Purpose |
|-----|---------|----------|
| `REPO_MANAGER_WORKSPACE` | `/workspace` | Root for git/file ops |

## Startup

Workspace dir created if missing. Runtime needs read/write access.

## Validation (target)

- Reject empty/whitespace workspace.
- Reject inaccessible paths.
- Fail with clear operator message.

## Type Linting Exceptions

Record exceptions to [typed_boundaries.md](../linting/typed_boundaries.md) here:

| Location | Rationale | Risk/Mitigation | Owner | Review |
|----------|-----------|-----------------|-------|--------|
| — | — | — | — | — |
