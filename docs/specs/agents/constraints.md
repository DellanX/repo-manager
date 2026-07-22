# Agent Constraints

Rules agents must follow. Violations return 400.

## Path Safety

See [security_baseline.md](../security/security_baseline.md) for full policy.

| Rule | Example |
|------|----------|
| Relative paths only | `src/file.py` not `/workspace/src/file.py` |
| No traversal | `../secret` rejected |

## Command Execution

| Rule | Note |
|------|------|
| `policy_allowlist` | Server policy restricts allowed commands |
| `shlex_parsed` | Commands tokenized, not shell-interpolated |

## Retry Policy

| Error | Action |
|-------|--------|
| 400 (bad arg/path/conflict) | Do not retry; fix input |
| 404 (unknown tool) | Do not retry; check name |
| Network timeout | Retry with backoff, max 3 |

## Prohibited

- Absolute paths outside workspace
- Credentials in args or commit messages
- Retry loops without backoff

## Invariants

1. `write_file` should follow `read_file` to confirm path.
2. `commit` should follow successful validation when required.
3. `push` should specify explicit branch.
