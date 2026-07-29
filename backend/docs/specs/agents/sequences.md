# Operation Sequences

Canonical flows for common agent tasks. Follow these exactly.

## Feature Edit

```
1. git.clone       {url: "<repo_url>"}
2. git.checkout    {branch: "<feature_branch>"}
3. workspace.read_file   {path: "<target_file>"}
4. workspace.write_file  {path: "<target_file>", content: "<new_content>"}
5. workspace.exec        {cmd: "<test_or_lint_cmd>"}  # optional, per policy
6. git.commit      {message: "<commit_message>"}
7. git.push        {remote: "origin", branch: "<feature_branch>"}
```

## Hotfix

```
1. git.checkout    {branch: "hotfix/<name>"}
2. workspace.read_file   {path: "<file>"}
3. workspace.write_file  {path: "<file>", content: "<patched>"}
4. git.commit      {message: "fix: <description>"}
5. git.push        {}
```

## Read-Only Inspection

```
1. git.clone       {url: "<repo_url>"}
2. workspace.read_file   {path: "<file1>"}
3. workspace.read_file   {path: "<file2>"}
# No commit/push
```

## Validation Run

```
1. workspace.exec  {cmd: "pytest tests/"}
2. workspace.exec  {cmd: "ruff check src/"}
```

## Traceability

| Sequence | Capability IDs |
|----------|----------------|
| Feature Edit | RM-GIT-CLONE, RM-GIT-CHECKOUT, RM-FILE-READ, RM-FILE-WRITE, RM-EXEC-CMD, RM-GIT-COMMIT, RM-GIT-PUSH |
| Hotfix | RM-GIT-CHECKOUT, RM-FILE-READ, RM-FILE-WRITE, RM-GIT-COMMIT, RM-GIT-PUSH |
| Read-Only | RM-GIT-CLONE, RM-FILE-READ |
| Validation | RM-EXEC-CMD |
