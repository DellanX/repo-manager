# Git Operations Service Specification

Source: `src/services/git_operations.py`

## Operations

| Function | Command | Required Args |
|----------|---------|---------------|
| `clone_repo(url)` | `git clone <url> <workspace>` | url |
| `checkout(branch)` | `git checkout <branch>` | branch |
| `commit(message)` | `git add . && git commit -m` | message |
| `push(remote, branch)` | `git push <remote> <branch>` | remote, branch |
| `exec_cmd(cmd)` | `shlex.split` + subprocess | cmd |

## Error Contract

Non-zero exit raises `OperationError` with stderr (fallback: "Command failed").

## Invariants

- All operations emit `started`/`completed` events.
- Subprocess runs with workspace as cwd.
- No `shell=True`.
- `exec_cmd` subject to [security_baseline.md](../security/security_baseline.md) policy.

## Risks

- Concurrent git ops can race.
- `exec_cmd` needs policy guard.
