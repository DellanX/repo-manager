# Git Operations Service Specification

Source module: `src/services/git_operations.py`

## Operations

1. `clone_repo(url)`
- Runs `git clone <url> <workspace>`.
- Records `started` and `completed` events.

2. `checkout(branch)`
- Runs `git checkout <branch>` in workspace.
- Records `started` and `completed` events.

3. `commit(message)`
- Runs `git add .` then `git commit -m <message>`.
- Records `started` and `completed` events.

4. `push(remote, branch)`
- Runs `git push <remote> <branch>` in workspace.
- Records `started` and `completed` events.

5. `exec_cmd(cmd)`
- Parses with `shlex.split` and executes command in workspace.
- Records `started` and `completed` events.
- Must comply with security policy for command restrictions.

## Error Contract

- Non-zero subprocess exit raises `OperationError`.
- Error message uses stderr, fallback `Command failed`.

## Invariants

- All subprocess calls execute with workspace context where relevant.
- Shell execution must not use shell=True.
- Event emission occurs for each operation.

## Risks to Track

- Concurrent git operations can race.
- `exec_cmd` can enable risky commands without policy guard.
