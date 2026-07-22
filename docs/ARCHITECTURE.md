# Architecture Specification

## Purpose

Repo Manager is a focused microservice that exposes repository operations for AI clients.

## Non-goals

- No orchestration of multi-service workflows.
- No planner logic for agent task decomposition.
- No server-rendered UI implementation inside the microservice runtime.

## Layered Model

1. API Layer

- REST endpoints in `src/api/rest.py`
- MCP tool interface in `src/api/mcp.py`
- WebSocket feed in `src/api/websocket.py`
- Planned webhook lifecycle endpoints and management surface

2. Service Layer

- Git operations in `src/services/git_operations.py`
- File operations in `src/services/file_operations.py`
- Planned worktree and multi-workspace operations

3. Core Layer

- Runtime configuration in `src/core/config.py`
- Operation event store in `src/core/events.py`
- Planned webhook observer loop runtime and delivery workers

4. Schema Layer

- Request payload contracts in `src/models/schemas.py`

## Operation Lifecycle

1. Client sends request through REST, MCP, or WebSocket observer connection.
2. API validates payload shape and required arguments.
3. API calls service functions.
4. Service executes operation within configured workspace root.
5. Service records operation events.
6. API returns structured response or mapped error.

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
