# File Operations Service Specification

Source module: `src/services/file_operations.py`

## Path Resolution

- Paths are resolved by joining with workspace root and normalizing absolute path.
- Any path outside workspace root is rejected with `OperationError('Path escapes workspace')`.

## Read

`read_file(path)`

- Requires resolved path to exist.
- Returns UTF-8 text content.
- Raises `OperationError('File not found')` if missing.
- Records completion event with logical path.

## Write

`write_file(path, content)`

- Creates parent directories if needed.
- Writes UTF-8 text in overwrite mode.
- Returns `{ status: 'ok' }`.
- Records completion event with logical path.

## Invariants

- All operations must pass path-isolation checks.
- No direct file access bypassing resolver.
- Writes are deterministic for same path/content input.

## Planned Enhancements

- Add atomic write semantics using temporary file + replace.
- Add optional diff/patch write mode with conflict behavior.
