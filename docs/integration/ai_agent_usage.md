# AI Agent Integration

See [specs/agents/](../specs/agents/) for machine-readable contracts.

## Quick Reference

| Resource | Purpose |
|----------|----------|
| [tools.yaml](../specs/agents/tools.yaml) | Tool args, returns, errors |
| [sequences.md](../specs/agents/sequences.md) | Canonical operation flows |
| [constraints.md](../specs/agents/constraints.md) | Safety rules, retry policy |

## Error Recovery Tips

- Write failure → re-read file, check path.
- Commit failure → check `git status`.
- Push failure → verify remote/branch.
