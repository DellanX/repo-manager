# Web UI UX Specification

Related feature spec: `docs/specs/ui/webui.md`

## 1. UX Goals

- Make repository and workspace management fast for common operations.
- Keep the interface simple and operational, not a full Git workstation.
- Provide explicit feedback for every mutation and integration action.

## 2. Information Architecture

Primary navigation:
- Dashboard (`/`)
- Repositories (`/repos`)
- Workspaces (`/workspaces`)
- Configuration
  - Credentials (`/config/credentials`)
  - Webhooks (`/config/webhooks`)

Global UI elements:
- Top navigation with active route indicator.
- Global status badge for inventory health (`healthy`, `degraded`).
- Toast region for success/error operation feedback.

## 3. Page Specifications

### 3.1 Dashboard (`/`)

Purpose:
- Quick operational summary and entry points.

Required widgets:
- Repository count card.
- Workspace count card.
- Stale/missing inventory count card.
- Worktree table (primary content) with:
  - Workspace ID
  - Repository Name
  - Path
  - Branch
  - Dirty State
  - Status
  - Last Seen
  - Actions (`Select`, `Remove`, `Open Repo`)
- Recent activity feed (clone, create/remove/select worktree, credential/webhook actions).

Primary actions:
- "Clone Repository"
- "Create Workspace"
- "Manage Credentials"
- "Manage Webhooks"

### 3.2 Repositories (`/repos`)

Table columns:
- Name
- Repository ID
- Root Path
- Origin URL
- Default Branch
- Status
- Last Seen
- Actions

Actions per row:
- "View Repository" (opens repository-specific view).
- "Clone New" (opens clone modal prefilled from selected context when possible).

Clone modal fields:
- Repository URL (required)
- Local path or workspace root (required)
- Default branch (optional)
- Credential binding (optional)

### 3.3 Repository Detail (`/repos/{repository_id}`)

Purpose:
- Focus management on a single repository.

Required sections:
- Repository summary panel (name, root path, origin, default branch, status, last seen).
- Repository-scoped worktree table (same columns as dashboard worktree table).
- Repository actions:
  - "Clone New"
  - "Create Workspace"
  - "Manage Credentials" (prefiltered to repository bindings)
  - "Manage Webhooks" (prefiltered to repository-related webhook usage where applicable)

### 3.4 Workspaces (`/workspaces`)

Table columns:
- Workspace ID
- Repository
- Path
- Branch
- HEAD
- Dirty State
- Status
- Last Seen
- Actions

Actions per row:
- "Select"
- "Remove"

Create workspace modal fields:
- Repository (required)
- Workspace ID (required)
- Branch or base ref (required)
- Target path (required)

Remove workspace flow:
- Confirmation dialog must show workspace ID, repo, and path.
- Confirmation text input required for destructive removal.

### 3.5 Credentials (`/config/credentials`)

Table columns:
- Name
- Provider
- Scope
- Bound Repositories
- Expiration
- Status
- Last Used
- Actions

Actions:
- Create
- Update metadata/bindings
- Rotate
- Revoke

Credential form fields:
- Provider (required)
- Credential type (required)
- Secret input (required on create/rotate)
- Scope/repository bindings (required)
- Optional expiration metadata

Rules:
- Never re-display full secret after create/update.
- Show masked token/key hint only (for example, last 4 characters where allowed).

### 3.6 Webhooks (`/config/webhooks`)

Table columns:
- Name
- Target URL
- Event Types
- Enabled
- Retry Policy
- Last Delivery
- Last Status
- Actions

Actions:
- Create
- Edit
- Enable/Disable
- Test
- Delete

Webhook form fields:
- Name (required)
- Target URL (required)
- Event types (required, multi-select)
- Secret reference (required)
- Retry policy (required)

## 4. Interaction Patterns

- All mutations are optimistic-disabled: action controls disable while request is in flight.
- Success toasts include operation + target (for example, "Workspace ws-abc removed").
- Error toasts include deterministic error code and user-actionable message.
- Long-running actions (clone, test webhook) must show progress state and final result.

## 5. Empty, Loading, And Error States

- Empty repositories: show CTA to clone first repository.
- Empty workspaces: show CTA to create first workspace.
- Empty credentials/webhooks: show CTA to create first item.
- Loading tables: show skeleton rows with fixed layout.
- Partial inventory failure: show degraded banner with retry action and timestamp.

## 6. Accessibility Requirements

- Full keyboard navigation for all tables, dialogs, and forms.
- Visible focus states on all interactive controls.
- Form fields must have labels and inline error association.
- Color cannot be the only status indicator; include icon/text labels.

## 7. Validation And Guardrails

- Client-side validation for required fields and obvious formatting errors.
- Server-side validation errors must map to field-level messages when possible.
- Destructive actions require explicit confirmation dialogs.
- Dangerous actions are not hidden behind ambiguous icons without labels/tooltips.

## 8. UX Test Requirements

- T-UI-UX-NAV-ROUTES: primary navigation reaches all required pages.
- T-UI-UX-REPO-CLONE-FLOW: clone modal validation and success/failure flows.
- T-UI-UX-REPO-DETAIL-FLOW: repository detail page filters and management actions.
- T-UI-UX-WORKSPACE-CRUD-FLOW: create/select/remove workspace flows.
- T-UI-UX-CRED-LIFECYCLE-FLOW: create/rotate/revoke credential flows with secret masking.
- T-UI-UX-WEBHOOK-LIFECYCLE-FLOW: create/test/enable-disable/delete webhook flows.
- T-UI-UX-ACCESSIBILITY-KEYBOARD: keyboard-only completion for critical flows.
