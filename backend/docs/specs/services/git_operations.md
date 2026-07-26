# Git Operations Service Specification

Source: `src/services/git_operations.py`

## Operations

| Function | Command | Required Args |
|----------|---------|---------------|
| `clone_repo(url, destination?)` | `git clone <url> [destination]` (cwd=`workspace`) | url |
| `checkout(branch, workspace_root)` | `git -C <workspace_root> checkout <branch>` | branch, workspace_root |
| `commit(message, workspace_root)` | `git -C <workspace_root> add .` + `git -C <workspace_root> commit -m` | message, workspace_root |
| `push(workspace_root, remote, branch)` | `git -C <workspace_root> push <remote> <branch>` | workspace_root, remote, branch |
| `exec_cmd(cmd, workspace_root)` | `shlex.split` + subprocess (cwd=`workspace_root`) | cmd, workspace_root |

## Error Contract

Non-zero exit raises `OperationError` with stderr (fallback: "Command failed").

## Invariants

- All operations emit `started`/`completed` events.
- `clone_repo` runs in global workspace root; all other operations run in the provided workspace root.
- No `shell=True`.
- `exec_cmd` subject to [security_baseline.md](../security/security_baseline.md) policy.

## Risks

- Concurrent git ops can race.
- `exec_cmd` needs policy guard.
