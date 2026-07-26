"""Workspace inventory service for Web UI.

Implements inventory management per docs/specs/ui/webui.md.
Supports both database and filesystem discovery modes.
"""
from __future__ import annotations

import hashlib
import os
import re
import sqlite3
import subprocess
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
    - database: Persist managed repo/workspace metadata in SQLite
    - filesystem: Derive inventory from workspace roots using git metadata
    """

    def __init__(
        self,
        source_mode: SourceMode = "database",
        workspace_roots: list[str] | None = None,
        inventory_db_path: str | None = None,
    ) -> None:
        self.source_mode = source_mode
        self.workspace_roots = workspace_roots or [WORKSPACE]
        db_root = Path(self.workspace_roots[0]) if self.workspace_roots else Path(WORKSPACE)
        default_db_path = db_root / ".repo-manager" / "inventory.sqlite3"
        db_path_value = inventory_db_path or os.getenv(
            "REPO_MANAGER_INVENTORY_DB_PATH", str(default_db_path)
        )
        self.inventory_db_path = Path(db_path_value)
        self._repositories: dict[str, RepositoryInfo] = {}
        self._workspaces: dict[str, WorkspaceInfo] = {}

        if self.source_mode == "database":
            self._init_db()

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
        repo_path = Path(normalized_path)
        git_dir = self._resolve_git_dir(repo_path) if repo_path.exists() else None
        last_fetched_at, last_commit_at = self._get_repository_timestamps(
            repo_path, git_dir
        )
        repo = RepositoryInfo(
            repository_id=repository_id,
            name=name,
            root_path=normalized_path,
            origin_url=origin_url,
            default_branch=default_branch,
            status="ready",
            last_seen_at=datetime.now(UTC).isoformat(),
            last_fetched_at=last_fetched_at,
            last_commit_at=last_commit_at,
        )
        if self.source_mode == "database":
            self._upsert_repository(repo)
        else:
            self._repositories[repository_id] = repo
        events.operation_events.record(
            "inventory", "add_repository", "completed", {
                "repository_id": repository_id}
        )
        return repo

    def register_cloned_repository(
        self,
        root_path: str,
        origin_url: str,
    ) -> RepositoryInfo:
        """Register a cloned repository in inventory so it appears in UI listings."""
        normalized_path = os.path.normpath(os.path.abspath(root_path))
        repo_path = Path(normalized_path)
        repository_id = self._generate_id(normalized_path)
        name = repo_path.name
        default_branch = "main"

        git_dir = self._resolve_git_dir(repo_path) if repo_path.exists() else None
        if git_dir is not None and self._is_valid_git_repo(repo_path):
            parsed_origin = self._parse_origin_url(git_dir / "config")
            parsed_branch = self._parse_head_branch(git_dir / "HEAD")
            if parsed_origin:
                origin_url = parsed_origin
            default_branch = parsed_branch

        return self.add_repository(
            repository_id=repository_id,
            name=name,
            root_path=normalized_path,
            origin_url=origin_url,
            default_branch=default_branch,
        )

    def add_workspace(
        self,
        workspace_id: str,
        repository_id: str,
        workspace_name: str,
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
            workspace_name=workspace_name,
            path=normalized_path,
            branch=branch,
            head_sha=head_sha,
            is_dirty=is_dirty,
            status="ready",
            last_seen_at=datetime.now(UTC).isoformat(),
        )
        if self.source_mode == "database":
            self._upsert_workspace(ws)
        else:
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

        if self.source_mode == "database":
            repositories = self._list_repositories_from_db()
            for repo in repositories:
                path = Path(repo.root_path)
                if not path.exists():
                    self._upsert_repository(
                        RepositoryInfo(
                            repository_id=repo.repository_id,
                            name=repo.name,
                            root_path=repo.root_path,
                            origin_url=repo.origin_url,
                            default_branch=repo.default_branch,
                            status="missing_path",
                            last_seen_at=datetime.now(UTC).isoformat(),
                            last_fetched_at=repo.last_fetched_at,
                            last_commit_at=repo.last_commit_at,
                        )
                    )
                elif not self._is_valid_git_repo(path):
                    self._upsert_repository(
                        RepositoryInfo(
                            repository_id=repo.repository_id,
                            name=repo.name,
                            root_path=repo.root_path,
                            origin_url=repo.origin_url,
                            default_branch=repo.default_branch,
                            status="invalid_git_metadata",
                            last_seen_at=datetime.now(UTC).isoformat(),
                            last_fetched_at=repo.last_fetched_at,
                            last_commit_at=repo.last_commit_at,
                        )
                    )
                else:
                    refreshed_repo = self._with_refreshed_repository_timestamps(repo)
                    self._upsert_repository(refreshed_repo)

            workspaces = self._list_workspaces_from_db()
            for ws in workspaces:
                path = Path(ws.path)
                if not path.exists():
                    self._upsert_workspace(
                        WorkspaceInfo(
                            workspace_id=ws.workspace_id,
                            repository_id=ws.repository_id,
                            workspace_name=ws.workspace_name,
                            path=ws.path,
                            branch=ws.branch,
                            head_sha=ws.head_sha,
                            is_dirty=ws.is_dirty,
                            status="missing_path",
                            last_seen_at=datetime.now(UTC).isoformat(),
                        )
                    )
        else:
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
                        last_fetched_at=repo.last_fetched_at,
                        last_commit_at=repo.last_commit_at,
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
                        last_fetched_at=repo.last_fetched_at,
                        last_commit_at=repo.last_commit_at,
                    )

            for ws_id, ws in self._workspaces.items():
                path = Path(ws.path)
                if not path.exists():
                    self._workspaces[ws_id] = WorkspaceInfo(
                        workspace_id=ws.workspace_id,
                        repository_id=ws.repository_id,
                        workspace_name=ws.workspace_name,
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
                repositories = list(self._repositories.values())
                workspaces = list(self._workspaces.values())
            elif self.source_mode == "database" and not self._list_repositories_from_db():
                # Bootstrap from local clones so pre-existing repositories appear in UI.
                self._repositories.clear()
                self._workspaces.clear()
                self._scan_filesystem()
                for repo in self._repositories.values():
                    self._upsert_repository(repo)
                for ws in self._workspaces.values():
                    self._upsert_workspace(ws)
                repositories = list(self._repositories.values())
                workspaces = list(self._workspaces.values())
            else:
                repositories = self._list_repositories_from_db()
                workspaces = self._list_workspaces_from_db()
                refreshed_repositories: list[RepositoryInfo] = []
                for repo in repositories:
                    refreshed_repo = self._with_refreshed_repository_timestamps(repo)
                    refreshed_repositories.append(refreshed_repo)
                    if (
                        refreshed_repo.last_fetched_at != repo.last_fetched_at
                        or refreshed_repo.last_commit_at != repo.last_commit_at
                    ):
                        self._upsert_repository(refreshed_repo)
                repositories = refreshed_repositories

            response = InventoryResponse(
                repositories=repositories,
                workspaces=workspaces,
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

    def fetch_repository(self, repository_id: str, remote: str = "origin") -> RepositoryInfo:
        """Fetch latest refs for a managed repository and refresh inventory metadata."""
        events.operation_events.record(
            "inventory",
            "fetch_repository",
            "started",
            {"repository_id": repository_id, "remote": remote},
        )

        repo = self._get_repository_by_id(repository_id)
        if repo is None:
            raise InventoryError(f"Repository not found: {repository_id}")

        repo_path = Path(repo.root_path)
        if not repo_path.exists():
            raise InventoryError(f"Repository path missing: {repo.root_path}")
        if not self._is_valid_git_repo(repo_path):
            raise InventoryError(f"Invalid git metadata for repository: {repository_id}")

        try:
            subprocess.run(
                ["git", "-C", str(repo_path), "fetch", "--prune", remote],
                capture_output=True,
                text=True,
                check=True,
            )
        except FileNotFoundError as exc:
            raise InventoryError("Git executable not found") from exc
        except subprocess.CalledProcessError as exc:
            message = exc.stderr.strip() or exc.stdout.strip() or "git fetch failed"
            raise InventoryError(f"Failed to fetch repository: {message}") from exc

        refreshed = self._with_refreshed_repository_timestamps(repo)
        updated_repo = RepositoryInfo(
            repository_id=refreshed.repository_id,
            name=refreshed.name,
            root_path=refreshed.root_path,
            origin_url=refreshed.origin_url,
            default_branch=refreshed.default_branch,
            status=refreshed.status,
            last_seen_at=datetime.now(UTC).isoformat(),
            last_fetched_at=refreshed.last_fetched_at,
            last_commit_at=refreshed.last_commit_at,
        )

        if self.source_mode == "database":
            self._upsert_repository(updated_repo)
        else:
            self._repositories[repository_id] = updated_repo

        events.operation_events.record(
            "inventory",
            "fetch_repository",
            "completed",
            {"repository_id": repository_id, "remote": remote},
        )
        return updated_repo

    def create_workspace(
        self,
        repository_id: str,
        branch: str,
        workspace_name: str | None = None,
    ) -> WorkspaceInfo:
        """Create a git worktree workspace for a managed repository."""
        normalized_branch = branch.strip()
        if not normalized_branch:
            raise InventoryError("Branch cannot be empty")

        repo = self._get_repository_by_id(repository_id)
        if repo is None:
            raise InventoryError(f"Repository not found: {repository_id}")

        repo_path = Path(repo.root_path)
        if not repo_path.exists():
            raise InventoryError(f"Repository path missing: {repo.root_path}")
        if not self._is_valid_git_repo(repo_path):
            raise InventoryError(f"Invalid git metadata for repository: {repository_id}")

        worktrees_root = Path(WORKSPACE) / "worktrees"
        worktrees_root.mkdir(parents=True, exist_ok=True)
        destination = self._build_workspace_path(
            worktrees_root=worktrees_root,
            repository=repo,
            branch=normalized_branch,
            workspace_name=workspace_name,
        )

        events.operation_events.record(
            "inventory",
            "create_workspace",
            "started",
            {
                "repository_id": repository_id,
                "branch": normalized_branch,
                "path": str(destination),
            },
        )

        command = self._build_worktree_create_command(
            repo_path=repo_path,
            destination=destination,
            branch=normalized_branch,
            default_branch=repo.default_branch,
        )
        try:
            subprocess.run(command, capture_output=True, text=True, check=True)
        except FileNotFoundError as exc:
            raise InventoryError("Git executable not found") from exc
        except subprocess.CalledProcessError as exc:
            message = exc.stderr.strip() or exc.stdout.strip() or "git worktree add failed"
            events.operation_events.record(
                "inventory",
                "create_workspace",
                "failed",
                {"repository_id": repository_id, "error": message},
            )
            raise InventoryError(f"Failed to create workspace: {message}") from exc

        git_dir = self._resolve_git_dir(destination)
        if git_dir is None:
            raise InventoryError("Workspace created but git metadata was not found")
        workspace = self.add_workspace(
            workspace_id=self._generate_id(str(destination.resolve())),
            repository_id=repository_id,
            workspace_name=self._workspace_name_from_path(destination),
            path=str(destination.resolve()),
            branch=self._parse_head_branch(git_dir / "HEAD"),
            head_sha=self._parse_head_sha(git_dir),
            is_dirty=self._is_worktree_dirty(destination),
        )
        events.operation_events.record(
            "inventory",
            "create_workspace",
            "completed",
            {"workspace_id": workspace.workspace_id, "repository_id": repository_id},
        )
        return workspace

    def remove_workspace(self, workspace_id: str) -> None:
        """Remove a managed git worktree workspace."""
        workspace = self._get_workspace_by_id(workspace_id)
        if workspace is None:
            raise InventoryError(f"Workspace not found: {workspace_id}")

        repo = self._get_repository_by_id(workspace.repository_id)
        if repo is None:
            raise InventoryError(
                f"Repository not found for workspace: {workspace.repository_id}"
            )

        events.operation_events.record(
            "inventory",
            "remove_workspace",
            "started",
            {"workspace_id": workspace_id},
        )

        try:
            subprocess.run(
                [
                    "git",
                    "-C",
                    repo.root_path,
                    "worktree",
                    "remove",
                    workspace.path,
                ],
                capture_output=True,
                text=True,
                check=True,
            )
        except FileNotFoundError as exc:
            raise InventoryError("Git executable not found") from exc
        except subprocess.CalledProcessError as exc:
            message = exc.stderr.strip() or exc.stdout.strip() or "git worktree remove failed"
            events.operation_events.record(
                "inventory",
                "remove_workspace",
                "failed",
                {"workspace_id": workspace_id, "error": message},
            )
            raise InventoryError(f"Failed to remove workspace: {message}") from exc

        self._delete_workspace(workspace_id)
        events.operation_events.record(
            "inventory",
            "remove_workspace",
            "completed",
            {"workspace_id": workspace_id},
        )

    def rename_repository(self, repository_id: str, name: str) -> RepositoryInfo:
        """Rename a managed repository display name."""
        normalized_name = name.strip()
        if not normalized_name:
            raise InventoryError("Repository name cannot be empty")
        repo = self._get_repository_by_id(repository_id)
        if repo is None:
            raise InventoryError(f"Repository not found: {repository_id}")
        updated = RepositoryInfo(
            repository_id=repo.repository_id,
            name=normalized_name,
            root_path=repo.root_path,
            origin_url=repo.origin_url,
            default_branch=repo.default_branch,
            status=repo.status,
            last_seen_at=repo.last_seen_at,
            last_fetched_at=repo.last_fetched_at,
            last_commit_at=repo.last_commit_at,
        )
        if self.source_mode == "database":
            self._upsert_repository(updated)
        else:
            self._repositories[repository_id] = updated
        events.operation_events.record(
            "inventory",
            "rename_repository",
            "completed",
            {"repository_id": repository_id},
        )
        return updated

    def rename_workspace(self, workspace_id: str, workspace_name: str) -> WorkspaceInfo:
        """Rename a managed workspace display name."""
        normalized_name = workspace_name.strip()
        if not normalized_name:
            raise InventoryError("Workspace name cannot be empty")
        workspace = self._get_workspace_by_id(workspace_id)
        if workspace is None:
            raise InventoryError(f"Workspace not found: {workspace_id}")
        updated = WorkspaceInfo(
            workspace_id=workspace.workspace_id,
            repository_id=workspace.repository_id,
            workspace_name=normalized_name,
            path=workspace.path,
            branch=workspace.branch,
            head_sha=workspace.head_sha,
            is_dirty=workspace.is_dirty,
            status=workspace.status,
            last_seen_at=workspace.last_seen_at,
        )
        if self.source_mode == "database":
            self._upsert_workspace(updated)
        else:
            self._workspaces[workspace_id] = updated
        events.operation_events.record(
            "inventory",
            "rename_workspace",
            "completed",
            {"workspace_id": workspace_id},
        )
        return updated

    def rescan(self, roots: list[str] | None = None) -> InventoryResponse:
        """Rescan filesystem roots and refresh inventory entries."""
        scan_roots = roots or self.workspace_roots
        events.operation_events.record(
            "inventory", "rescan", "started", {"roots": scan_roots}
        )

        try:
            discovered_repositories: dict[str, RepositoryInfo] = {}
            discovered_workspaces: dict[str, WorkspaceInfo] = {}
            original_repositories = self._repositories
            original_workspaces = self._workspaces
            try:
                self._repositories = discovered_repositories
                self._workspaces = discovered_workspaces
                self._scan_filesystem(scan_roots)
            finally:
                self._repositories = original_repositories
                self._workspaces = original_workspaces

            if self.source_mode == "database":
                self._preserve_custom_names(discovered_repositories, discovered_workspaces)
                discovered_workspace_paths = {
                    os.path.normpath(os.path.abspath(workspace.path))
                    for workspace in discovered_workspaces.values()
                }
                discovered_repository_paths = {
                    os.path.normpath(os.path.abspath(repository.root_path))
                    for repository in discovered_repositories.values()
                }
                misclassified_repository_paths = (
                    discovered_workspace_paths - discovered_repository_paths
                )
                if misclassified_repository_paths:
                    self._delete_repositories_by_paths(misclassified_repository_paths)

                for repo in discovered_repositories.values():
                    self._upsert_repository(repo)
                for ws in discovered_workspaces.values():
                    self._upsert_workspace(ws)
            else:
                self._repositories = discovered_repositories
                self._workspaces = discovered_workspaces

            inventory = self.get_inventory()
            events.operation_events.record(
                "inventory",
                "rescan",
                "completed",
                {
                    "repository_count": len(inventory.repositories),
                    "workspace_count": len(inventory.workspaces),
                },
            )
            return inventory
        except Exception as exc:
            events.operation_events.record(
                "inventory", "rescan", "failed", {"error": str(exc)}
            )
            raise InventoryError(f"Failed to rescan inventory: {exc}") from exc

    def _scan_filesystem(self, roots: list[str] | None = None) -> None:
        """Scan workspace roots for git repositories."""
        scan_roots = roots or self.workspace_roots
        for root in scan_roots:
            root_path = Path(root)
            if not root_path.exists():
                continue

            for path in root_path.iterdir():
                if path.is_dir() and (path / ".git").exists():
                    if self._is_linked_worktree(path):
                        self._discover_workspace(path)
                    else:
                        self._discover_repository(path)

    def _discover_repository(self, repo_path: Path) -> None:
        """Discover and register a repository from filesystem."""
        repo_id = self._generate_id(str(repo_path))
        git_dir = self._resolve_git_dir(repo_path)
        last_fetched_at, last_commit_at = self._get_repository_timestamps(
            repo_path, git_dir
        )

        if git_dir is None or not self._is_valid_git_repo(repo_path):
            self._repositories[repo_id] = RepositoryInfo(
                repository_id=repo_id,
                name=repo_path.name,
                root_path=str(repo_path.resolve()),
                origin_url="",
                default_branch="main",
                status="invalid_git_metadata",
                last_seen_at=datetime.now(UTC).isoformat(),
                last_fetched_at=last_fetched_at,
                last_commit_at=last_commit_at,
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
            last_fetched_at=last_fetched_at,
            last_commit_at=last_commit_at,
        )

        # Also register as a workspace
        ws_id = f"ws-{repo_id}"
        self._workspaces[ws_id] = WorkspaceInfo(
            workspace_id=ws_id,
            repository_id=repo_id,
            workspace_name=repo_path.name,
            path=str(repo_path.resolve()),
            branch=default_branch,
            head_sha=head_sha,
            is_dirty=False,  # Would need git status check for accurate value
            status="ready",
            last_seen_at=datetime.now(UTC).isoformat(),
        )

    def _discover_workspace(self, workspace_path: Path) -> None:
        """Discover and register a linked git worktree as a workspace only."""
        git_dir = self._resolve_git_dir(workspace_path)
        if git_dir is None:
            return

        repository_root = self._resolve_worktree_repository_root(git_dir)
        if repository_root is None:
            return

        repository_id = self._generate_id(str(repository_root))
        if repository_id not in self._repositories:
            self._discover_repository(repository_root)

        if repository_id not in self._repositories:
            return

        ws_id = self._generate_id(str(workspace_path.resolve()))
        self._workspaces[ws_id] = WorkspaceInfo(
            workspace_id=ws_id,
            repository_id=repository_id,
            workspace_name=workspace_path.name,
            path=str(workspace_path.resolve()),
            branch=self._parse_head_branch(git_dir / "HEAD"),
            head_sha=self._parse_head_sha(git_dir),
            is_dirty=self._is_worktree_dirty(workspace_path),
            status="ready",
            last_seen_at=datetime.now(UTC).isoformat(),
        )

    def _is_valid_git_repo(self, path: Path) -> bool:
        """Check if path contains valid git metadata."""
        git_dir = self._resolve_git_dir(path)
        if git_dir is None:
            return False
        head_file = git_dir / "HEAD"
        return head_file.exists()

    def _resolve_git_dir(self, repo_path: Path) -> Path | None:
        """Resolve a repository's git dir for normal repos and linked worktrees."""
        git_entry = repo_path / ".git"
        if git_entry.is_dir():
            return git_entry
        if git_entry.is_file():
            try:
                content = git_entry.read_text().strip()
            except OSError:
                return None
            if not content.startswith("gitdir:"):
                return None
            raw_git_dir = content.split("gitdir:", 1)[1].strip()
            candidate = Path(raw_git_dir)
            if not candidate.is_absolute():
                candidate = (repo_path / candidate).resolve()
            return candidate
        return None

    def _is_linked_worktree(self, path: Path) -> bool:
        git_entry = path / ".git"
        if not git_entry.is_file():
            return False
        git_dir = self._resolve_git_dir(path)
        if git_dir is None:
            return False
        return git_dir.parent.name == "worktrees"

    def _resolve_worktree_repository_root(self, git_dir: Path) -> Path | None:
        if git_dir.parent.name != "worktrees":
            return None
        common_git_dir = git_dir.parent.parent
        repository_root = common_git_dir.parent
        if not repository_root.exists():
            return None
        return repository_root.resolve()

    def _workspace_name_from_path(self, workspace_path: Path) -> str:
        resolved = workspace_path.resolve()
        return resolved.name or self._generate_id(str(resolved))

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

    def _get_repository_timestamps(
        self, repo_path: Path, git_dir: Path | None
    ) -> tuple[str | None, str | None]:
        if git_dir is None:
            return None, None
        return self._parse_last_fetched_at(git_dir), self._parse_last_commit_at(
            repo_path, git_dir
        )

    def _parse_last_fetched_at(self, git_dir: Path) -> str | None:
        fetch_head = git_dir / "FETCH_HEAD"
        if not fetch_head.exists():
            return None
        try:
            fetched_at = datetime.fromtimestamp(fetch_head.stat().st_mtime, UTC)
        except OSError:
            return None
        return fetched_at.isoformat()

    def _parse_last_commit_at(self, repo_path: Path, git_dir: Path) -> str | None:
        try:
            result = subprocess.run(
                ["git", "-C", str(repo_path), "log", "-1", "--format=%cI"],
                capture_output=True,
                text=True,
                check=True,
            )
            commit_timestamp = result.stdout.strip()
            if commit_timestamp:
                return commit_timestamp
        except (FileNotFoundError, subprocess.CalledProcessError):
            pass

        head_log = git_dir / "logs" / "HEAD"
        if not head_log.exists():
            return None
        try:
            lines = [line for line in head_log.read_text().splitlines() if line.strip()]
        except OSError:
            return None
        if not lines:
            return None

        match = re.search(r"\s(\d{10,})\s[+-]\d{4}\t", lines[-1])
        if match is None:
            return self._parse_last_commit_at_from_ref_metadata(git_dir)
        commit_epoch = int(match.group(1))
        return datetime.fromtimestamp(commit_epoch, UTC).isoformat()

    def _parse_last_commit_at_from_ref_metadata(self, git_dir: Path) -> str | None:
        head_ref = self._parse_head_branch(git_dir / "HEAD")
        if head_ref:
            ref_path = git_dir / "refs" / "heads" / head_ref
            if ref_path.exists():
                try:
                    ref_updated_at = datetime.fromtimestamp(ref_path.stat().st_mtime, UTC)
                    return ref_updated_at.isoformat()
                except OSError:
                    pass

        head_path = git_dir / "HEAD"
        if not head_path.exists():
            return None
        try:
            head_updated_at = datetime.fromtimestamp(head_path.stat().st_mtime, UTC)
        except OSError:
            return None
        return head_updated_at.isoformat()

    def _with_refreshed_repository_timestamps(
        self, repo: RepositoryInfo
    ) -> RepositoryInfo:
        repo_path = Path(repo.root_path)
        if not repo_path.exists():
            return repo
        git_dir = self._resolve_git_dir(repo_path)
        last_fetched_at, last_commit_at = self._get_repository_timestamps(
            repo_path, git_dir
        )
        return RepositoryInfo(
            repository_id=repo.repository_id,
            name=repo.name,
            root_path=repo.root_path,
            origin_url=repo.origin_url,
            default_branch=repo.default_branch,
            status=repo.status,
            last_seen_at=repo.last_seen_at,
            last_fetched_at=last_fetched_at,
            last_commit_at=last_commit_at,
        )

    def _preserve_custom_names(
        self,
        discovered_repositories: dict[str, RepositoryInfo],
        discovered_workspaces: dict[str, WorkspaceInfo],
    ) -> None:
        existing_repositories = {
            repo.repository_id: repo for repo in self._list_repositories_from_db()
        }
        existing_workspaces = {
            workspace.workspace_id: workspace for workspace in self._list_workspaces_from_db()
        }

        for repo_id, repo in list(discovered_repositories.items()):
            existing_repo = existing_repositories.get(repo_id)
            if existing_repo is None:
                continue
            discovered_repositories[repo_id] = RepositoryInfo(
                repository_id=repo.repository_id,
                name=existing_repo.name,
                root_path=repo.root_path,
                origin_url=repo.origin_url,
                default_branch=repo.default_branch,
                status=repo.status,
                last_seen_at=repo.last_seen_at,
                last_fetched_at=repo.last_fetched_at,
                last_commit_at=repo.last_commit_at,
            )

        for workspace_id, workspace in list(discovered_workspaces.items()):
            existing_workspace = existing_workspaces.get(workspace_id)
            if existing_workspace is None:
                continue
            discovered_workspaces[workspace_id] = WorkspaceInfo(
                workspace_id=workspace.workspace_id,
                repository_id=workspace.repository_id,
                workspace_name=existing_workspace.workspace_name,
                path=workspace.path,
                branch=workspace.branch,
                head_sha=workspace.head_sha,
                is_dirty=workspace.is_dirty,
                status=workspace.status,
                last_seen_at=workspace.last_seen_at,
            )

    def _get_repository_by_id(self, repository_id: str) -> RepositoryInfo | None:
        if self.source_mode == "database":
            for repo in self._list_repositories_from_db():
                if repo.repository_id == repository_id:
                    return repo
            return None
        return self._repositories.get(repository_id)

    def _get_workspace_by_id(self, workspace_id: str) -> WorkspaceInfo | None:
        if self.source_mode == "database":
            for workspace in self._list_workspaces_from_db():
                if workspace.workspace_id == workspace_id:
                    return workspace
            return None
        return self._workspaces.get(workspace_id)

    def _delete_workspace(self, workspace_id: str) -> None:
        if self.source_mode == "database":
            with self._connect() as connection:
                connection.execute(
                    "DELETE FROM workspaces WHERE workspace_id = ?",
                    (workspace_id,),
                )
            return
        self._workspaces.pop(workspace_id, None)

    def _build_workspace_path(
        self,
        worktrees_root: Path,
        repository: RepositoryInfo,
        branch: str,
        workspace_name: str | None,
    ) -> Path:
        if workspace_name:
            candidate_name = self._slugify(workspace_name)
            if not candidate_name:
                raise InventoryError("Workspace name cannot be empty")
        else:
            timestamp = datetime.now(UTC).strftime("%Y%m%d%H%M%S")
            candidate_name = (
                f"{self._slugify(repository.name)}-{self._slugify(branch)}-{timestamp}"
            )

        destination = (worktrees_root / candidate_name).resolve()
        root_resolved = worktrees_root.resolve()
        if destination == root_resolved or root_resolved not in destination.parents:
            raise InventoryError("Workspace path escapes worktrees root")
        if destination.exists():
            raise InventoryError(f"Workspace path already exists: {destination}")
        return destination

    def _build_worktree_create_command(
        self,
        repo_path: Path,
        destination: Path,
        branch: str,
        default_branch: str,
    ) -> list[str]:
        branch_exists = self._branch_exists(repo_path, branch)
        if branch_exists:
            return [
                "git",
                "-C",
                str(repo_path),
                "worktree",
                "add",
                str(destination),
                branch,
            ]
        return [
            "git",
            "-C",
            str(repo_path),
            "worktree",
            "add",
            "-b",
            branch,
            str(destination),
            default_branch,
        ]

    def _branch_exists(self, repo_path: Path, branch: str) -> bool:
        result = subprocess.run(
            ["git", "-C", str(repo_path), "show-ref", "--verify", f"refs/heads/{branch}"],
            capture_output=True,
            text=True,
        )
        return result.returncode == 0

    def _is_worktree_dirty(self, worktree_path: Path) -> bool:
        result = subprocess.run(
            ["git", "-C", str(worktree_path), "status", "--porcelain"],
            capture_output=True,
            text=True,
        )
        return bool(result.stdout.strip())

    def _slugify(self, value: str) -> str:
        normalized = re.sub(r"[^a-zA-Z0-9._-]+", "-", value.strip().lower())
        normalized = normalized.strip("._-")
        return normalized

    def _generate_id(self, value: str) -> str:
        """Generate a stable ID from a value."""
        return hashlib.sha256(value.encode()).hexdigest()[:12]

    def _connect(self) -> sqlite3.Connection:
        if str(self.inventory_db_path) != ":memory:":
            self.inventory_db_path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.inventory_db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _init_db(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS repositories (
                    repository_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    root_path TEXT NOT NULL,
                    origin_url TEXT NOT NULL,
                    default_branch TEXT NOT NULL,
                    status TEXT NOT NULL,
                    last_seen_at TEXT NOT NULL,
                    last_fetched_at TEXT,
                    last_commit_at TEXT
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS workspaces (
                    workspace_id TEXT PRIMARY KEY,
                    repository_id TEXT NOT NULL,
                    workspace_name TEXT NOT NULL,
                    path TEXT NOT NULL,
                    branch TEXT NOT NULL,
                    head_sha TEXT NOT NULL,
                    is_dirty INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    last_seen_at TEXT NOT NULL
                )
                """
            )
            repo_columns = {
                row["name"]
                for row in connection.execute("PRAGMA table_info(repositories)").fetchall()
            }
            if "last_fetched_at" not in repo_columns:
                connection.execute(
                    "ALTER TABLE repositories ADD COLUMN last_fetched_at TEXT"
                )
            if "last_commit_at" not in repo_columns:
                connection.execute("ALTER TABLE repositories ADD COLUMN last_commit_at TEXT")
            workspace_columns = {
                row["name"]
                for row in connection.execute("PRAGMA table_info(workspaces)").fetchall()
            }
            if "workspace_name" not in workspace_columns:
                connection.execute(
                    "ALTER TABLE workspaces ADD COLUMN workspace_name TEXT NOT NULL DEFAULT ''"
                )
                connection.execute(
                    "UPDATE workspaces SET workspace_name = '' WHERE workspace_name IS NULL"
                )

    def _upsert_repository(self, repo: RepositoryInfo) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO repositories (
                    repository_id,
                    name,
                    root_path,
                    origin_url,
                    default_branch,
                    status,
                    last_seen_at,
                    last_fetched_at,
                    last_commit_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(repository_id) DO UPDATE SET
                    name=excluded.name,
                    root_path=excluded.root_path,
                    origin_url=excluded.origin_url,
                    default_branch=excluded.default_branch,
                    status=excluded.status,
                    last_seen_at=excluded.last_seen_at,
                    last_fetched_at=excluded.last_fetched_at,
                    last_commit_at=excluded.last_commit_at
                """,
                (
                    repo.repository_id,
                    repo.name,
                    repo.root_path,
                    repo.origin_url,
                    repo.default_branch,
                    repo.status,
                    repo.last_seen_at,
                    repo.last_fetched_at,
                    repo.last_commit_at,
                ),
            )

    def _delete_repositories_by_paths(self, paths: set[str]) -> None:
        with self._connect() as connection:
            for path in paths:
                connection.execute(
                    "DELETE FROM repositories WHERE root_path = ?",
                    (path,),
                )

    def _upsert_workspace(self, workspace: WorkspaceInfo) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO workspaces (
                    workspace_id,
                    repository_id,
                    workspace_name,
                    path,
                    branch,
                    head_sha,
                    is_dirty,
                    status,
                    last_seen_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(workspace_id) DO UPDATE SET
                    repository_id=excluded.repository_id,
                    workspace_name=excluded.workspace_name,
                    path=excluded.path,
                    branch=excluded.branch,
                    head_sha=excluded.head_sha,
                    is_dirty=excluded.is_dirty,
                    status=excluded.status,
                    last_seen_at=excluded.last_seen_at
                """,
                (
                    workspace.workspace_id,
                    workspace.repository_id,
                    workspace.workspace_name,
                    workspace.path,
                    workspace.branch,
                    workspace.head_sha,
                    int(workspace.is_dirty),
                    workspace.status,
                    workspace.last_seen_at,
                ),
            )

    def _list_repositories_from_db(self) -> list[RepositoryInfo]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT
                    repository_id,
                    name,
                    root_path,
                    origin_url,
                    default_branch,
                    status,
                    last_seen_at,
                    last_fetched_at,
                    last_commit_at
                FROM repositories
                """
            ).fetchall()
        return [
            RepositoryInfo(
                repository_id=row["repository_id"],
                name=row["name"],
                root_path=row["root_path"],
                origin_url=row["origin_url"],
                default_branch=row["default_branch"],
                status=row["status"],
                last_seen_at=row["last_seen_at"],
                last_fetched_at=row["last_fetched_at"],
                last_commit_at=row["last_commit_at"],
            )
            for row in rows
        ]

    def _list_workspaces_from_db(self) -> list[WorkspaceInfo]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT
                    workspace_id,
                    repository_id,
                    workspace_name,
                    path,
                    branch,
                    head_sha,
                    is_dirty,
                    status,
                    last_seen_at
                FROM workspaces
                """
            ).fetchall()
        return [
            WorkspaceInfo(
                workspace_id=row["workspace_id"],
                repository_id=row["repository_id"],
                workspace_name=(
                    row["workspace_name"] or Path(row["path"]).name or row["workspace_id"]
                ),
                path=row["path"],
                branch=row["branch"],
                head_sha=row["head_sha"],
                is_dirty=bool(row["is_dirty"]),
                status=row["status"],
                last_seen_at=row["last_seen_at"],
            )
            for row in rows
        ]


# Default service instance
inventory_service = WorkspaceInventoryService(source_mode="database")
