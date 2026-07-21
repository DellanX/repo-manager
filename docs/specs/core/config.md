# Configuration Specification

Source module: `src/core/config.py`

## Environment Variables

- `REPO_MANAGER_WORKSPACE`
  - Default: `/workspace`
  - Meaning: root directory for git and file operations.

## Startup Behavior

- Workspace directory is created at import/startup if missing.

## Requirements

- Runtime must have read/write access to workspace path.
- Production deployment must override workspace path to host-specific location.

## Validation Rules (target)

- Reject empty or whitespace-only workspace values.
- Reject paths that cannot be created or accessed.
- Emit startup failure with clear operator-facing message.
