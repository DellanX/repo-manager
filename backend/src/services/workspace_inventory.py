"""Workspace inventory service for Web UI.

Implements inventory management per docs/specs/ui/webui.md.
Supports both database and filesystem discovery modes.
"""
from __future__ import annotations

import hashlib
import os
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING

from src.core import events
from src.core.config import WORKSPACE
from src.models.schemas import (
    InventoryResponse,
    RepositoryInfo,
    SourceMode,
    WorkspaceInfo,
)

if TYPE_CHECKING:
    pass


class InventoryError(Exception):
    """Raised when inventory backend is unavailable or fails."""

    pass


class WorkspaceInventoryService:
    """Service for managing repository and workspace inventory.

    Supports two modes:
    - database: Persist managed repo/workspace metadata in memory (simulating DB)
    - filesystem: Derive inventory from workspace roots using git metadata
    """

    def __init__(
        self,
        source_mode: SourceMode = "database",
        workspace_roots: list[str] | None = None,
    ) -> None:
        self.source_mode = source_mode
        self.workspace_roots = workspace_roots or [WORKSPACE]
        self._repositories: dict[str, RepositoryInfo] = {}
        self._workspaces: dict[str, WorkspaceInfo] = {}

    def add_repository(
        self,
        repository_id: str,
        name: str,
        root_path: str,
        origin_url: str,
        default_branch: str,
    ) -> RepositoryInfo:
        """Add a repository to the inventory (database mode)."""
        normalized_path = os.path.normpath(os.path.abspath(root_path))
        repo = RepositoryInfo(
            repository_id=repository_id,
            name=name,
            root_path=normalized_path,
            origin_url=origin_url,
            default_branch=default_branch,
            status="ready",
            last_seen_at=datetime.now(UTC).isoformat(),
        )
        self._repositories[repository_id] = repo
        events.operation_events.record(
            "inventory", "add_repository", "completed", {
                "repository_id": repository_id}
        )
        return repo

    def add_workspace(
        self,
        workspace_id: str,
        repository_id: str,
        path: str,
        branch: str,
        head_sha: str,
        is_dirty: bool = False,
    ) -> WorkspaceInfo:
        """Add a workspace to the inventory (database mode)."""
        normalized_path = os.path.normpath(os.path.abspath(path))
        ws = WorkspaceInfo(
            workspace_id=workspace_id,
            repository_id=repository_id,
            path=normalized_path,
            branch=branch,
            head_sha=head_sha,
            is_dirty=is_dirty,
            status="ready",
            last_seen_at=datetime.now(UTC).isoformat(),
        )
        self._workspaces[workspace_id] = ws
        events.operation_events.record(
            "inventory", "add_workspace", "completed", {
                "workspace_id": workspace_id}
        )
        return ws

    def reconcile(self) -> None:
        """Reconcile database records against filesystem reality.

        Marks stale records according to spec:
        - missing_path: directory doesn't exist
        - invalid_git_metadata: .git exists but unreadable
        - stale: DB record with no filesystem match
        """
        events.operation_events.record("inventory", "reconcile", "started", {})

        for repo_id, repo in self._repositories.items():
            path = Path(repo.root_path)
            if not path.exists():
                self._repositories[repo_id] = RepositoryInfo(
                    repository_id=repo.repository_id,
                    name=repo.name,
                    root_path=repo.root_path,
                    origin_url=repo.origin_url,
                    default_branch=repo.default_branch,
                    status="missing_path",
                    last_seen_at=datetime.now(UTC).isoformat(),
                )
            elif not self._is_valid_git_repo(path):
                self._repositories[repo_id] = RepositoryInfo(
                    repository_id=repo.repository_id,
                    name=repo.name,
                    root_path=repo.root_path,
                    origin_url=repo.origin_url,
                    default_branch=repo.default_branch,
                    status="invalid_git_metadata",
                    last_seen_at=datetime.now(UTC).isoformat(),
                )

        for ws_id, ws in self._workspaces.items():
            path = Path(ws.path)
            if not path.exists():
                self._workspaces[ws_id] = WorkspaceInfo(
                    workspace_id=ws.workspace_id,
                    repository_id=ws.repository_id,
                    path=ws.path,
                    branch=ws.branch,
                    head_sha=ws.head_sha,
                    is_dirty=ws.is_dirty,
                    status="missing_path",
                    last_seen_at=datetime.now(UTC).isoformat(),
                )

        events.operation_events.record(
            "inventory", "reconcile", "completed", {})

    def get_inventory(self) -> InventoryResponse:
        """Get current inventory state.

        In database mode, returns stored records.
        In filesystem mode, scans workspace roots for git repositories.
        """
        events.operation_events.record(
            "inventory", "get_inventory", "started", {})

        try:
            if self.source_mode == "filesystem":
                self._scan_filesystem()

            response = InventoryResponse(
                repositories=list(self._repositories.values()),
                workspaces=list(self._workspaces.values()),
                source_mode=self.source_mode,
                generated_at=datetime.now(UTC).isoformat(),
            )

            events.operation_events.record(
                "inventory",
                "get_inventory",
                "completed",
                {
                    "repository_count": len(response.repositories),
                    "workspace_count": len(response.workspaces),
                },
            )

            return response
        except Exception as e:
            events.operation_events.record(
                "inventory", "get_inventory", "failed", {"error": str(e)}
            )
            raise InventoryError(f"Failed to get inventory: {e}") from e

    def _scan_filesystem(self) -> None:
        """Scan workspace roots for git repositories."""
        for root in self.workspace_roots:
            root_path = Path(root)
            if not root_path.exists():
                continue

            # Look for .git directories
            for path in root_path.iterdir():
                if path.is_dir():
                    git_dir = path / ".git"
                    if git_dir.exists():
                        self._discover_repository(path)

    def _discover_repository(self, repo_path: Path) -> None:
        """Discover and register a repository from filesystem."""
        repo_id = self._generate_id(str(repo_path))
        git_dir = repo_path / ".git"

        if not self._is_valid_git_repo(repo_path):
            self._repositories[repo_id] = RepositoryInfo(
                repository_id=repo_id,
                name=repo_path.name,
                root_path=str(repo_path.resolve()),
                origin_url="",
                default_branch="main",
                status="invalid_git_metadata",
                last_seen_at=datetime.now(UTC).isoformat(),
            )
            return

        # Parse git config for origin URL
        origin_url = self._parse_origin_url(git_dir / "config")

        # Parse HEAD for default branch
        default_branch = self._parse_head_branch(git_dir / "HEAD")
        head_sha = self._parse_head_sha(git_dir)

        self._repositories[repo_id] = RepositoryInfo(
            repository_id=repo_id,
            name=repo_path.name,
            root_path=str(repo_path.resolve()),
            origin_url=origin_url,
            default_branch=default_branch,
            status="ready",
            last_seen_at=datetime.now(UTC).isoformat(),
        )

        # Also register as a workspace
        ws_id = f"ws-{repo_id}"
        self._workspaces[ws_id] = WorkspaceInfo(
            workspace_id=ws_id,
            repository_id=repo_id,
            path=str(repo_path.resolve()),
            branch=default_branch,
            head_sha=head_sha,
            is_dirty=False,  # Would need git status check for accurate value
            status="ready",
            last_seen_at=datetime.now(UTC).isoformat(),
        )

    def _is_valid_git_repo(self, path: Path) -> bool:
        """Check if path contains valid git metadata."""
        git_dir = path / ".git"
        if not git_dir.is_dir():
            return False
        head_file = git_dir / "HEAD"
        return head_file.exists()

    def _parse_origin_url(self, config_path: Path) -> str:
        """Parse origin URL from git config file."""
        if not config_path.exists():
            return ""
        try:
            content = config_path.read_text()
            # Simple regex to find origin URL
            match = re.search(
                r'\[remote "origin"\][^\[]*url\s*=\s*(.+)', content)
            if match:
                return match.group(1).strip()
        except OSError:
            pass
        return ""

    def _parse_head_branch(self, head_path: Path) -> str:
        """Parse current branch from HEAD file."""
        if not head_path.exists():
            return "main"
        try:
            content = head_path.read_text().strip()
            if content.startswith("ref: refs/heads/"):
                return content.replace("ref: refs/heads/", "")
        except OSError:
            pass
        return "main"

    def _parse_head_sha(self, git_dir: Path) -> str:
        """Parse HEAD commit SHA."""
        head_path = git_dir / "HEAD"
        if not head_path.exists():
            return ""
        try:
            content = head_path.read_text().strip()
            if content.startswith("ref: "):
                # Symbolic ref - need to read the ref file
                ref = content.replace("ref: ", "")
                ref_path = git_dir / ref
                if ref_path.exists():
                    return ref_path.read_text().strip()[:12]
            else:
                # Detached HEAD - direct SHA
                return content[:12]
        except OSError:
            pass
        return ""

    def _generate_id(self, value: str) -> str:
        """Generate a stable ID from a value."""
        return hashlib.sha256(value.encode()).hexdigest()[:12]


# Default service instance
inventory_service = WorkspaceInventoryService(source_mode="database")
