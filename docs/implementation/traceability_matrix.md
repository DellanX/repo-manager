# Traceability Matrix

Each capability must map to API contracts, service contracts, schema contracts, and tests.

| Capability ID | Capability | API Contract | Service Contract | Schema Contract | Test IDs |
| --- | --- | --- | --- | --- | --- |
| RM-GIT-CLONE | Clone repository | `specs/api/rest.md`, `specs/api/mcp.md` | `specs/services/git_operations.md` | `specs/models/schemas.md` | T-REST-CLONE-200, T-MCP-GIT-CLONE-200 |
| RM-GIT-CHECKOUT | Checkout branch | `specs/api/rest.md`, `specs/api/mcp.md` | `specs/services/git_operations.md` | `specs/models/schemas.md` | T-REST-CHECKOUT-200, T-MCP-GIT-CHECKOUT-200 |
| RM-GIT-COMMIT | Commit changes | `specs/api/rest.md`, `specs/api/mcp.md` | `specs/services/git_operations.md` | `specs/models/schemas.md` | T-REST-COMMIT-200, T-MCP-GIT-COMMIT-200 |
| RM-GIT-PUSH | Push branch | `specs/api/rest.md`, `specs/api/mcp.md` | `specs/services/git_operations.md` | `specs/models/schemas.md` | T-REST-PUSH-200, T-MCP-GIT-PUSH-200 |
| RM-FILE-READ | Read file | `specs/api/rest.md`, `specs/api/mcp.md` | `specs/services/file_operations.md` | `specs/models/schemas.md` | T-REST-FILE-GET-200, T-FILE-READ-TRAVERSAL-400 |
| RM-FILE-WRITE | Write file | `specs/api/rest.md`, `specs/api/mcp.md` | `specs/services/file_operations.md` | `specs/models/schemas.md` | T-REST-FILE-POST-200, T-FILE-WRITE-TRAVERSAL-400 |
| RM-EXEC-CMD | Execute command | `specs/api/rest.md`, `specs/api/mcp.md` | `specs/services/git_operations.md` | `specs/models/schemas.md` | T-REST-EXEC-200, T-EXEC-POLICY-REJECT-400 |
| RM-EVENT-FEED | Stream operation events | `specs/api/websocket.md` | `specs/core/events.md` | `specs/models/schemas.md` | T-WS-WELCOME-200, T-WS-EVENTS-ORDER |
| RM-HEALTH | Health probe | `specs/api/rest.md` | N/A | N/A | T-REST-HEALTH-200 |
| RM-WORKTREE-MULTI-WS | Manage multi-workspace worktrees | `specs/api/mcp.md` | `specs/services/worktrees.md` | `specs/models/schemas.md` | T-WT-CREATE-200, T-WT-ISOLATION-200, T-WT-REMOVE-PROTECT-400 |
| RM-WEBHOOK-SUBSCRIPTIONS | Manage webhook subscriptions | `specs/api/webhooks.md` | `specs/core/webhook_runtime.md` | `specs/models/schemas.md` | T-WH-CREATE-200, T-WH-SIGNATURE-200, T-WH-RETRY-DLQ |
| RM-CREDENTIAL-LIFECYCLE | Manage provider credentials securely | `specs/api/mcp.md` | `specs/security/credential_management.md` | `specs/models/schemas.md` | T-CRED-REDACTION, T-CRED-ROTATE-200, T-CRED-ACCESS-403 |

## Completion Rule

A capability row is complete when all columns are populated and all listed tests exist.
