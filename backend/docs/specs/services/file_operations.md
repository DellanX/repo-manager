# File Operations Service Specification

Source: `src/services/file_operations.py`

## Operations

| Function | Behavior | Error |
|----------|----------|-------|
| `read_file(path)` | Returns UTF-8 content | `File not found` |
| `write_file(path, content)` | Creates dirs, writes UTF-8 | `Path escapes workspace` |

## Path Resolution

Paths joined with workspace root, normalized. Traversal outside root raises `OperationError`.

## Invariants

- All operations emit completion events.
- All paths must pass isolation check per [security_baseline.md](../security/security_baseline.md).
- Writes are deterministic for same input.

## Planned

- Atomic write (temp file + replace)
- Diff/patch mode
