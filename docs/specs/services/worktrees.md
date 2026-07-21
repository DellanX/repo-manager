# Worktrees and Workspaces Specification

Source modules (planned): `src/services/git_operations.py` and a new worktree service module.

## Purpose

Support multiple isolated sandboxes for the same repository using git worktrees, so multiple users or AI agents can work concurrently without cloning the repository repeatedly.

## Core Concepts

- Primary repository: the canonical git directory for a project.
- Worktree workspace: a filesystem path attached to the primary repository at a branch or commit.
- Workspace identifier: stable logical name used by API and MCP calls.

## Required Operations

1. Create workspace worktree
- Input: repository ID, workspace ID, branch name or base ref, target path.
- Behavior: creates a git worktree and records metadata.

2. List workspace worktrees
- Input: repository ID.
- Behavior: returns all registered workspaces and branch bindings.

3. Remove workspace worktree
- Input: repository ID and workspace ID.
- Behavior: removes worktree safely, with force flag policy.

4. Switch active workspace context
- Input: repository ID and workspace ID.
- Behavior: updates operation context for file and git commands.

## MCP Requirements

MCP must expose first-class tools:

- `workspace.create_worktree`
- `workspace.list_worktrees`
- `workspace.remove_worktree`
- `workspace.select_worktree`

All existing git and file tools must accept optional `workspace_id` for explicit routing.

## Invariants

- Workspace IDs are unique per repository.
- All workspace paths remain under allowed workspace root policy.
- A workspace must map to exactly one checked-out branch/ref at a time.
- Removing a workspace must not corrupt primary repository metadata.

## Failure Cases

- Workspace ID conflict.
- Invalid branch/ref.
- Path outside allowed root.
- Unmerged or dirty workspace removal without force policy.

## Validation Requirements

- Concurrent create/remove race tests.
- Branch isolation tests across multiple worktrees.
- Path traversal rejection tests for workspace paths.
- MCP routing tests for `workspace_id` support.
