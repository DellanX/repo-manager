# Web UI Repository, Workspace, And Configuration Specification

Source modules (planned): `src/ui/*`, `src/services/workspace_inventory.py`, `src/core/config.py`
Detailed UX specification: `docs/specs/ui/ux.md`

## 1. Purpose

Define a simple Web UI that lets users:
- View all managed repositories and managed workspaces.
- Run core management mutations (clone repository, create/remove/select worktree).
- Configure integrations through dedicated pages for credentials and webhooks.
- Open repository-specific views to filter and manage a single repository's workspaces quickly.

This UI is an operator convenience surface, not a full Git client replacement.

## 2. Scope

In scope:
- Inventory views for repositories and workspaces.
- Lightweight mutation actions for repository/workspace management.
- Configuration pages for credentials and webhook subscriptions.
- Discovery and tracking rules for which repositories/workspaces are "managed."
- Backend contracts the Web UI consumes for rendering and actions.

Out of scope:
- Full Git porcelain and history workflows (interactive rebase, cherry-pick UI, conflict resolution UI, commit graph browsing).
- Rich IDE features (inline diff editor, merge tooling, blame explorer).
- Authentication and authorization design details beyond baseline requirements.
- Real-time collaborative editing.

## 3. Contracts

### 3.1 Inventory Endpoint

`GET /ui/inventory`

Response:
```json
{
  "repositories": [
    {
      "repository_id": "repo-123",
      "name": "repo-manager",
      "root_path": "D:\\repo-manager",
      "origin_url": "https://github.com/org/repo-manager.git",
      "default_branch": "main",
      "status": "ready",
      "last_seen_at": "2026-07-22T12:00:00Z",
      "last_fetched_at": "2026-07-22T11:45:00Z",
      "last_commit_at": "2026-07-22T11:30:00Z"
    }
  ],
  "workspaces": [
    {
      "workspace_id": "ws-abc",
      "repository_id": "repo-123",
      "path": "D:\\workspaces\\repo-manager\\ws-abc",
      "branch": "feature/webui",
      "head_sha": "abc123...",
      "is_dirty": false,
      "status": "ready",
      "last_seen_at": "2026-07-22T12:00:00Z"
    }
  ],
  "source_mode": "database",
  "generated_at": "2026-07-22T12:00:00Z"
}
```

Errors:
- `400` invalid query filters.
- `500` inventory backend unavailable.

### 3.2 UI Mutation Surface

The UI may call existing API/MCP-backed operations directly or through a UI adapter, but behavior must match existing service specs.

Minimum actions:
1. Clone repository
   - `POST /clone` with `{ "url": ..., "destination"?: ... }` -> delegates to clone capability.
2. Create worktree workspace
   - `POST /ui/workspaces` -> delegates to worktree create capability.
3. Remove worktree workspace
   - `DELETE /ui/workspaces/{workspace_id}` -> delegates to worktree remove capability.
4. Select active workspace
   - `POST /ui/workspaces/{workspace_id}/select` -> delegates to worktree select capability.
5. Rescan inventory roots
   - `POST /ui/inventory/rescan` with `{ "roots": ["/workspace/repos", "/workspace/worktrees"] }`.
6. Fetch repository remotes
   - `POST /ui/repositories/{repository_id}/fetch` -> runs `git fetch --prune origin` for that repository and refreshes repository metadata timestamps.

All mutation responses must return deterministic status and error payloads aligned with API standards.

### 3.3 Configuration Pages

The Web UI must expose:
- `/config/credentials` for credential registration, update, revoke, and repository binding.
- `/config/webhooks` for webhook create/list/update/delete/test and enable/disable.

Credential and webhook behavior must align with:
- `docs/specs/security/credential_management.md`
- `docs/specs/api/webhooks.md`

### 3.4 Required Page Routing And Views

- Dashboard route must be `/`.
- Dashboard must include a worktree table that includes repository name as a first-class column.
- Repository list route: `/repos`.
- Repository detail route: `/repos/{repository_id}` with repository-scoped worktree filtering and management actions.

### 3.5 Discovery Modes

Inventory must be provided by one configured mode:
1. `database` (default): persist managed repository/workspace metadata in a local store (SQLite is acceptable).
2. `filesystem`: derive inventory from configured workspace roots using git metadata and directory scanning.

If `database` mode is used, implementations must include a reconciliation job that verifies DB records against filesystem reality and marks stale records.

## 4. Invariants

- Every workspace maps to exactly one managed repository.
- Repository and workspace IDs are stable and unique.
- All paths are normalized absolute paths under allowed workspace roots.
- Inventory responses never include duplicate repository/workspace records.
- `status` values are explicit (`ready`, `missing_path`, `invalid_git_metadata`, `stale`).
- UI mutations are limited to repository/workspace management and must not expose arbitrary command execution.
- UI configuration pages never return plaintext secret material after creation/update.

## 5. Failure Cases

- Workspace directory missing on disk -> mark `missing_path`; do not drop silently.
- Git metadata unreadable -> mark `invalid_git_metadata`.
- DB record exists but no filesystem match during reconciliation -> mark `stale`.
- Filesystem scan timeout -> return partial data with explicit degraded status and error telemetry.
- Clone/create/remove/select operation failure -> return explicit error message and code; do not mask failure as success.
- Credential validation failure -> reject and present provider-scoped error details without secret leakage.
- Webhook test or delivery check failure -> return explicit transport/signature failure status.

## 6. Observability

Required:
- Structured logs for inventory refresh start/end and failure reason.
- Metric counters for discovered repositories/workspaces and stale records.
- Duration metric for inventory scan/reconciliation.
- Event emission when inventory status for any repository/workspace changes.
- Audit logs for UI-triggered clone/worktree mutations, credential lifecycle actions, and webhook lifecycle actions.

## 7. Security

- Web UI endpoints must not execute shell commands from raw user input.
- Do not expose secrets or credential material in repository/workspace payloads.
- Enforce workspace-root boundary checks before returning filesystem-derived paths.
- Require CSRF protection for browser mutation endpoints.
- Require explicit confirmation on destructive actions (for example, remove workspace, revoke credential, delete webhook).
- Follow baseline controls in `docs/specs/security/security_baseline.md`.

## 8. Validation

- Unit tests for ID stability, path normalization, and status mapping.
- Integration tests for `database` mode inventory listing and stale detection.
- Integration tests for `filesystem` mode discovery and git metadata parsing.
- Contract tests for `/ui/inventory` response schema and error shape.
- Contract tests for mutation endpoints and delegated failure mapping.
- UI flow tests for credential and webhook config pages.
- Security tests proving no secret fields are serialized.
- CSRF and boundary-enforcement tests for all browser-triggered mutations.

## 9. Traceability

Capability ID: `RM-WEBUI-INVENTORY`, `RM-WEBUI-CONFIG`  
Traceability row: `docs/implementation/traceability_matrix.md`
