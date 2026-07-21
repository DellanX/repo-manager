# Agent Task Flows

## Flow A: Feature Edit

1. `git.clone`
2. `git.checkout`
3. `workspace.read_file`
4. `workspace.write_file`
5. `workspace.exec` for tests/lint per policy
6. `git.commit`
7. `git.push`

Traceability IDs:
- RM-GIT-CLONE
- RM-GIT-CHECKOUT
- RM-FILE-READ
- RM-FILE-WRITE
- RM-EXEC-CMD
- RM-GIT-COMMIT
- RM-GIT-PUSH

## Flow B: Hotfix

1. Checkout hotfix branch.
2. Read and patch minimal files.
3. Run targeted validation.
4. Commit and push.

## Flow C: Failure Handling

1. If command fails, capture output and classify root cause.
2. If file path rejected, normalize to workspace-relative path.
3. If push fails, verify upstream branch and permissions.
