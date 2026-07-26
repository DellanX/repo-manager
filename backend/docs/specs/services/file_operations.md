# File Operations Service Specification

Source: `src/services/file_operations.py`

## Operations

| Function | Behavior | Error |
|----------|----------|-------|
| `read_file(path, workspace_root)` | Returns UTF-8 content from workspace | `File not found` |
| `write_file(path, content, workspace_root)` | Creates dirs, writes UTF-8 in workspace | `Path escapes workspace` |

## Path Resolution

Paths are joined with the provided workspace root, normalized, and checked. Traversal outside root raises `OperationError`.

## Invariants

- All operations emit completion events.
- All paths must pass isolation check per [security_baseline.md](../security/security_baseline.md).
- Writes are deterministic for same input.

## Planned

- Atomic write (temp file + replace)
- Diff/patch mode
