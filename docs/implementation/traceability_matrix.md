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
| RM-WEBUI-INVENTORY | View and manage repositories/workspaces in simple Web UI | `specs/ui/webui.md`, `specs/ui/ux.md` | `specs/ui/webui.md` | `specs/ui/webui.md` | T-UI-INVENTORY-200, T-UI-INVENTORY-STALE-200, T-UI-INVENTORY-SCHEMA, T-UI-WORKSPACE-CREATE-200, T-UI-WORKSPACE-REMOVE-200, T-UI-UX-REPO-DETAIL-FLOW, T-UI-UX-WORKSPACE-CRUD-FLOW |
| RM-WEBUI-CONFIG | Configure credentials and webhook integrations in Web UI | `specs/ui/webui.md`, `specs/ui/ux.md`, `specs/api/webhooks.md` | `specs/security/credential_management.md`, `specs/core/webhook_runtime.md` | `specs/models/schemas.md` | T-UI-CRED-CREATE-200, T-UI-CRED-REVOKE-200, T-UI-WEBHOOK-CREATE-200, T-UI-WEBHOOK-TEST-200, T-UI-UX-CRED-LIFECYCLE-FLOW, T-UI-UX-WEBHOOK-LIFECYCLE-FLOW |
| RM-WEBHOOK-SUBSCRIPTIONS | Manage webhook subscriptions | `specs/api/webhooks.md` | `specs/core/webhook_runtime.md` | `specs/models/schemas.md` | T-WH-CREATE-200, T-WH-SIGNATURE-200, T-WH-RETRY-DLQ |
| RM-CREDENTIAL-LIFECYCLE | Manage provider credentials securely | `specs/api/mcp.md` | `specs/security/credential_management.md` | `specs/models/schemas.md` | T-CRED-REDACTION, T-CRED-ROTATE-200, T-CRED-ACCESS-403 |
| RM-AGENT-TOOLS | Tool contract definitions for agents | `specs/agents/tools.yaml` | N/A | N/A | T-AGENT-TOOLS-PARSE |
| RM-AGENT-SEQUENCES | Operation flow patterns | `specs/agents/sequences.md` | N/A | N/A | T-AGENT-SEQ-VALID |
| RM-AGENT-CONSTRAINTS | Safety constraint rules | `specs/agents/constraints.md` | N/A | N/A | T-AGENT-CONSTRAINT-400 |

## Completion Rule

A capability row is complete when all columns are populated and all listed tests exist.
