# Architecture Specification

## Purpose

Repo Manager is a monorepo containing:
- A **backend** FastAPI microservice that exposes repository operations for AI clients
- A **frontend** Vue.js SPA for human operators to manage repositories and workspaces

## Monorepo Structure

```
/
├── backend/           # FastAPI backend service
│   ├── src/           # Python source code
│   ├── tests/         # Backend tests
│   └── docs/specs/    # Backend-specific specifications
├── frontend/          # Vue.js 3 SPA
│   ├── src/           # TypeScript/Vue source code
│   ├── docs/specs/    # UI/UX specifications
│   └── tests/         # Frontend tests
└── docs/              # Shared documentation
    └── specs/api/     # API contracts (consumed by both)
```

## Non-goals

- No orchestration of multi-service workflows.
- No planner logic for agent task decomposition.
- No server-rendered UI in the backend (frontend is a separate SPA).

## Backend Layered Model

1. API Layer (`backend/src/api/`)

- REST endpoints in `rest.py`
- MCP tool interface in `mcp.py`
- WebSocket feed in `websocket.py`
- UI data endpoints in `ui.py` (JSON-only)
- All endpoints prefixed with `/api/v1/`

2. Service Layer (`backend/src/services/`)

- Git operations in `git_operations.py`
- File operations in `file_operations.py`
- Workspace inventory in `workspace_inventory.py`

3. Core Layer (`backend/src/core/`)

- Runtime configuration in `config.py`
- Operation event store in `events.py`

4. Schema Layer (`backend/src/models/`)

- Request/response contracts in `schemas.py`

## Frontend Architecture

- **Router**: Vue Router with routes matching UX spec (`/`, `/repos`, `/workspaces`, `/config/*`)
- **State**: Pinia stores for inventory and UI state
- **API Client**: Typed client for `/api/v1/*` endpoints
- **Dev Server**: Vite with HMR, proxies API calls to backend

## Operation Lifecycle

1. Client sends request through REST, MCP, WebSocket, or Frontend SPA.
2. API validates payload shape and required arguments.
3. API calls service functions.
4. Service executes operation within configured workspace root.
5. Service records operation events.
6. API returns structured JSON response or mapped error.
7. Frontend updates UI state via Pinia stores.

## Cross-Cutting Invariants

- Workspace isolation must be enforced on all file paths.
- Git and command execution must run with workspace as working directory.
- All externally visible failures must return deterministic error shapes.
- Security controls in `specs/security/security_baseline.md` are mandatory.

## Current Constraints

- Event store is in-memory.
- Authentication and authorization are not implemented yet.
- Command execution is exposed by design and requires strict guardrails.

## Planned Capability Additions

- Multi-workspace support via git worktrees for concurrent developer and AI sandboxes.
- Webhook subscriptions with observer-loop dispatch and retry/dead-letter semantics.
- Credential management for secure provider authentication without interactive prompts.
- Simple Web UI surface for repository/workspace management and integration configuration.
