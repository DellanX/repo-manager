# Testing Strategy Specification

## Scope

This document defines required tests for each module-level specification.

## Test Layers

1. Unit tests
- Validate pure service behavior and error mapping.
- Cover edge cases and invalid inputs.

2. Integration tests
- Cover end-to-end API behavior for REST and MCP call paths.
- Validate event emission side effects.

3. Contract tests
- Ensure request/response payloads match schema contracts.
- Ensure error payloads are stable.

4. Security tests
- Path traversal prevention.
- Command policy enforcement.
- Input size boundaries and error sanitization.

## Required Coverage by Area

- `src/api/rest.py`: route status codes, payload mapping, OperationError mapping.
- `src/api/mcp.py`: unknown tool behavior, missing args behavior, tool result envelope.
- `src/api/websocket.py`: welcome message, event stream envelope, sequential delivery.
- `src/services/git_operations.py`: clone/checkout/commit/push/exec success and failure paths.
- `src/services/file_operations.py`: path resolve, file not found, read/write success.
- `src/core/events.py`: ID monotonicity, list_since filtering, serialization shape.
- `src/core/config.py`: workspace default and startup creation behavior.
- Planned worktree service: create/list/remove/select behavior, branch isolation, and race safety.
- Planned webhook API/runtime: subscription CRUD, signature correctness, retries, dead-letter behavior, and observer loop resiliency.
- Planned credential management: encryption at rest, redaction, access control, rotation and revocation workflows, provider adapter contracts.

## Fixtures

- Temporary workspace directory per test module.
- Temporary git repo fixture for git operation tests.
- Event store reset fixture.

## CI Gate

- Security tests required for merge.
- Contract tests required for API changes.
- Traceability matrix row must reference at least one test ID.
