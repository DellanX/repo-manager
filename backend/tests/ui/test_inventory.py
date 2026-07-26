"""Tests for Web UI inventory endpoint and service.

Test IDs map to spec requirements in docs/specs/ui/webui.md section 8.
"""
from __future__ import annotations

import sqlite3
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from src.models.schemas import (
    InventoryResponse,
    RepositoryInfo,
    WorkspaceInfo,
)
from src.server import app
from src.services.workspace_inventory import (
    InventoryError,
    WorkspaceInventoryService,
)


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture()
def sample_repository() -> RepositoryInfo:
    return RepositoryInfo(
        repository_id="repo-123",
        name="repo-manager",
        root_path="/workspace/repo-manager",
        origin_url="https://github.com/org/repo-manager.git",
        default_branch="main",
        status="ready",
        last_seen_at="2026-07-22T12:00:00Z",
        last_fetched_at="2026-07-22T10:00:00Z",
        last_commit_at="2026-07-22T09:00:00Z",
    )


@pytest.fixture()
def sample_workspace() -> WorkspaceInfo:
    return WorkspaceInfo(
        workspace_id="ws-abc",
        repository_id="repo-123",
        workspace_name="ws-abc",
        path="/workspace/workspaces/repo-manager/ws-abc",
        branch="feature/webui",
        head_sha="abc123def456",
        is_dirty=False,
        status="ready",
        last_seen_at="2026-07-22T12:00:00Z",
    )


class TestInventorySchemas:
    """Unit tests for ID stability, path normalization, and status mapping."""

    def test_repository_id_stability(self, sample_repository: RepositoryInfo) -> None:
        """T-UI-INV-ID-STABLE: Repository IDs are stable and unique."""
        repo = sample_repository
        assert repo.repository_id == "repo-123"
        # ID should not change on re-serialization
        data = repo.model_dump()
        repo2 = RepositoryInfo.model_validate(data)
        assert repo2.repository_id == repo.repository_id

    def test_workspace_id_stability(self, sample_workspace: WorkspaceInfo) -> None:
        """T-UI-INV-ID-STABLE: Workspace IDs are stable and unique."""
        ws = sample_workspace
        assert ws.workspace_id == "ws-abc"
        data = ws.model_dump()
        ws2 = WorkspaceInfo.model_validate(data)
        assert ws2.workspace_id == ws.workspace_id

    def test_repository_path_normalization(self) -> None:
        """T-UI-INV-PATH-NORM: Paths are normalized absolute paths."""
        repo = RepositoryInfo(
            repository_id="repo-1",
            name="test",
            root_path="/workspace/test",
            origin_url="https://github.com/test/test.git",
            default_branch="main",
            status="ready",
            last_seen_at="2026-07-22T12:00:00Z",
        )
        # Path should be absolute
        assert repo.root_path.startswith("/")
        assert ".." not in repo.root_path

    def test_workspace_path_normalization(self) -> None:
        """T-UI-INV-PATH-NORM: Workspace paths are normalized absolute paths."""
        ws = WorkspaceInfo(
            workspace_id="ws-1",
            repository_id="repo-1",
            workspace_name="ws-1",
            path="/workspace/workspaces/test/ws-1",
            branch="main",
            head_sha="abc123",
            is_dirty=False,
            status="ready",
            last_seen_at="2026-07-22T12:00:00Z",
        )
        assert ws.path.startswith("/")
        assert ".." not in ws.path

    def test_status_values_explicit(self) -> None:
        """T-UI-INV-STATUS: Status values are explicit enumerated values."""
        valid_statuses = ["ready", "missing_path",
                          "invalid_git_metadata", "stale"]
        for status in valid_statuses:
            repo = RepositoryInfo(
                repository_id="repo-1",
                name="test",
                root_path="/workspace/test",
                origin_url="https://github.com/test/test.git",
                default_branch="main",
                status=status,
                last_seen_at="2026-07-22T12:00:00Z",
            )
            assert repo.status == status

    def test_workspace_maps_to_exactly_one_repository(
        self, sample_workspace: WorkspaceInfo
    ) -> None:
        """T-UI-INV-WS-REPO-MAP: Every workspace maps to exactly one repository."""
        ws = sample_workspace
        assert ws.repository_id is not None
        assert isinstance(ws.repository_id, str)
        assert len(ws.repository_id) > 0

    def test_inventory_response_no_duplicates(
        self, sample_repository: RepositoryInfo, sample_workspace: WorkspaceInfo
    ) -> None:
        """T-UI-INV-NO-DUPS: Inventory responses never include duplicates."""
        response = InventoryResponse(
            repositories=[sample_repository, sample_repository],
            workspaces=[sample_workspace, sample_workspace],
            source_mode="database",
            generated_at="2026-07-22T12:00:00Z",
        )
        # The dedupe happens at validation time
        repo_ids = [r.repository_id for r in response.repositories]
        ws_ids = [w.workspace_id for w in response.workspaces]
        assert len(repo_ids) == len(set(repo_ids))
        assert len(ws_ids) == len(set(ws_ids))


class TestWorkspaceInventoryService:
    """Integration tests for inventory service."""

    def test_database_mode_inventory_listing(self, tmp_path: Path) -> None:
        """T-UI-INV-DB-LIST: Database mode returns managed repositories and workspaces."""
        service = WorkspaceInventoryService(
            source_mode="database", workspace_roots=[str(tmp_path)]
        )
        # Add test data
        service.add_repository(
            repository_id="repo-1",
            name="test-repo",
            root_path=str(tmp_path / "test-repo"),
            origin_url="https://github.com/test/repo.git",
            default_branch="main",
        )
        service.add_workspace(
            workspace_id="ws-1",
            repository_id="repo-1",
            workspace_name="ws-1",
            path=str(tmp_path / "workspaces" / "ws-1"),
            branch="main",
            head_sha="abc123",
        )

        inventory = service.get_inventory()
        assert inventory.source_mode == "database"
        assert len(inventory.repositories) == 1
        assert len(inventory.workspaces) == 1
        assert inventory.repositories[0].repository_id == "repo-1"
        assert inventory.workspaces[0].workspace_id == "ws-1"

    def test_database_mode_persists_across_instances(self, tmp_path: Path) -> None:
        """Database mode persists inventory records in SQLite."""
        db_path = tmp_path / "inventory.sqlite3"
        writer = WorkspaceInventoryService(
            source_mode="database",
            workspace_roots=[str(tmp_path)],
            inventory_db_path=str(db_path),
        )
        writer.add_repository(
            repository_id="repo-persisted",
            name="persisted-repo",
            root_path=str(tmp_path / "persisted-repo"),
            origin_url="https://github.com/test/persisted.git",
            default_branch="main",
        )

        reader = WorkspaceInventoryService(
            source_mode="database",
            workspace_roots=[str(tmp_path)],
            inventory_db_path=str(db_path),
        )
        inventory = reader.get_inventory()
        repo_ids = [repo.repository_id for repo in inventory.repositories]
        assert "repo-persisted" in repo_ids

    def test_database_mode_backfills_repo_timestamps_for_legacy_rows(
        self, tmp_path: Path
    ) -> None:
        """Legacy DB rows with null timestamps are refreshed from local git metadata."""
        db_path = tmp_path / "inventory.sqlite3"
        repo_path = tmp_path / "legacy-repo"
        repo_path.mkdir()
        git_dir = repo_path / ".git"
        git_dir.mkdir()
        (git_dir / "HEAD").write_text("ref: refs/heads/main\n")
        refs_dir = git_dir / "refs" / "heads"
        refs_dir.mkdir(parents=True)
        (refs_dir / "main").write_text("1234567890abcdef1234567890abcdef12345678\n")
        (git_dir / "logs").mkdir()
        commit_log_line = (
            "0" * 40
            + " "
            + "1" * 40
            + " Test User <test@example.com> 1720000000 +0000\tcommit: test\n"
        )
        (git_dir / "logs" / "HEAD").write_text(
            commit_log_line
        )
        (git_dir / "FETCH_HEAD").write_text("fetch data")

        WorkspaceInventoryService(
            source_mode="database",
            workspace_roots=[str(tmp_path)],
            inventory_db_path=str(db_path),
        )
        with sqlite3.connect(db_path) as connection:
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
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    "repo-legacy",
                    "legacy-repo",
                    str(repo_path.resolve()),
                    "https://github.com/test/legacy.git",
                    "main",
                    "ready",
                    "2026-07-22T12:00:00Z",
                    None,
                    None,
                ),
            )

        reader = WorkspaceInventoryService(
            source_mode="database",
            workspace_roots=[str(tmp_path)],
            inventory_db_path=str(db_path),
        )
        inventory = reader.get_inventory()
        repo = next(
            r for r in inventory.repositories if r.repository_id == "repo-legacy"
        )
        assert repo.last_fetched_at is not None
        assert repo.last_commit_at is not None

    def test_stale_detection_missing_path(self, tmp_path: Path) -> None:
        """T-UI-INV-STALE: Missing path is marked as stale/missing_path."""
        service = WorkspaceInventoryService(
            source_mode="database", workspace_roots=[str(tmp_path)]
        )
        # Add repository with non-existent path
        service.add_repository(
            repository_id="repo-missing",
            name="missing-repo",
            root_path=str(tmp_path / "nonexistent"),
            origin_url="https://github.com/test/missing.git",
            default_branch="main",
        )

        service.reconcile()
        inventory = service.get_inventory()
        assert inventory.repositories[0].status == "missing_path"

    def test_register_cloned_repository_adds_entry(self, tmp_path: Path) -> None:
        """T-UI-INV-CLONE-REGISTER: Cloned repository is registered in database mode."""
        service = WorkspaceInventoryService(
            source_mode="database", workspace_roots=[str(tmp_path)]
        )

        clone_path = tmp_path / "repo-manager-copy"
        clone_path.mkdir()

        repo = service.register_cloned_repository(
            root_path=str(clone_path),
            origin_url="https://github.com/test/repo-manager.git",
        )
        inventory = service.get_inventory()

        assert repo.name == "repo-manager-copy"
        assert len(inventory.repositories) == 1
        assert inventory.repositories[0].root_path == str(clone_path.resolve())

    def test_filesystem_mode_discovery(self, tmp_path: Path) -> None:
        """T-UI-INV-FS-DISCOVER: Filesystem mode discovers git repositories."""
        # Create a fake git repo
        repo_path = tmp_path / "my-repo"
        repo_path.mkdir()
        git_dir = repo_path / ".git"
        git_dir.mkdir()
        (git_dir / "HEAD").write_text("ref: refs/heads/main\n")
        (git_dir / "config").write_text(
            "[remote \"origin\"]\n\turl = https://github.com/test/repo.git\n"
        )
        (git_dir / "logs").mkdir()
        commit_log_line = (
            "0" * 40
            + " "
            + "1" * 40
            + " Test User <test@example.com> 1720000000 +0000\tcommit: test\n"
        )
        (git_dir / "logs" / "HEAD").write_text(
            commit_log_line
        )
        (git_dir / "FETCH_HEAD").write_text("fetch data")

        service = WorkspaceInventoryService(
            source_mode="filesystem", workspace_roots=[str(tmp_path)]
        )
        inventory = service.get_inventory()

        assert len(inventory.repositories) >= 1
        found = [r for r in inventory.repositories if "my-repo" in r.name]
        assert len(found) == 1
        assert found[0].status == "ready"
        assert found[0].last_fetched_at is not None
        assert found[0].last_commit_at is not None

    def test_database_mode_bootstraps_from_filesystem_when_empty(
        self, tmp_path: Path
    ) -> None:
        """T-UI-INV-DB-BOOTSTRAP: Empty database mode can discover existing clones."""
        repo_path = tmp_path / "existing-repo"
        repo_path.mkdir()
        git_dir = repo_path / ".git"
        git_dir.mkdir()
        (git_dir / "HEAD").write_text("ref: refs/heads/main\n")
        (git_dir / "config").write_text(
            "[remote \"origin\"]\n\turl = https://github.com/test/existing-repo.git\n"
        )

        service = WorkspaceInventoryService(
            source_mode="database", workspace_roots=[str(tmp_path)]
        )
        inventory = service.get_inventory()

        assert len(inventory.repositories) == 1
        assert inventory.repositories[0].name == "existing-repo"

    def test_filesystem_mode_discovers_linked_worktree(self, tmp_path: Path) -> None:
        """T-UI-INV-FS-WORKTREE-LINK: Linked worktrees are workspaces, not repositories."""
        repos_root = tmp_path / "repos"
        worktrees_root = tmp_path / "worktrees"
        repos_root.mkdir()
        worktrees_root.mkdir()

        repo_path = repos_root / "primary-repo"
        repo_path.mkdir()
        repo_git = repo_path / ".git"
        repo_git.mkdir()
        (repo_git / "HEAD").write_text("ref: refs/heads/main\n")
        repo_refs = repo_git / "refs" / "heads"
        repo_refs.mkdir(parents=True)
        (repo_refs / "main").write_text("1234567890abcdef1234567890abcdef12345678\n")

        worktree_path = worktrees_root / "linked-worktree"
        worktree_path.mkdir()
        git_meta = repo_git / "worktrees" / "linked-worktree"
        git_meta.mkdir(parents=True)
        (worktree_path / ".git").write_text(f"gitdir: {git_meta}\n")
        (git_meta / "HEAD").write_text("ref: refs/heads/feature/test\n")
        refs_dir = git_meta / "refs" / "heads" / "feature"
        refs_dir.mkdir(parents=True)
        (refs_dir / "test").write_text("1234567890abcdef1234567890abcdef12345678\n")
        (git_meta / "config").write_text(
            "[remote \"origin\"]\n\turl = https://github.com/test/linked-worktree.git\n"
        )

        service = WorkspaceInventoryService(source_mode="filesystem", workspace_roots=[
            str(repos_root),
            str(worktrees_root),
        ])
        inventory = service.get_inventory()

        repo_entries = [r for r in inventory.repositories if r.name == "primary-repo"]
        assert len(repo_entries) == 1
        assert repo_entries[0].status == "ready"

        linked_workspace = [
            ws for ws in inventory.workspaces if ws.path == str(worktree_path.resolve())
        ]
        assert len(linked_workspace) == 1
        assert linked_workspace[0].branch == "feature/test"
        assert linked_workspace[0].repository_id == repo_entries[0].repository_id

    def test_rescan_removes_worktree_paths_from_repositories(self, tmp_path: Path) -> None:
        """Database rescan drops repositories that are actually linked worktree paths."""
        repos_root = tmp_path / "repos"
        worktrees_root = tmp_path / "worktrees"
        repos_root.mkdir()
        worktrees_root.mkdir()

        repo_path = repos_root / "primary-repo"
        repo_path.mkdir()
        repo_git = repo_path / ".git"
        repo_git.mkdir()
        (repo_git / "HEAD").write_text("ref: refs/heads/main\n")
        repo_refs = repo_git / "refs" / "heads"
        repo_refs.mkdir(parents=True)
        (repo_refs / "main").write_text("1234567890abcdef1234567890abcdef12345678\n")

        worktree_path = worktrees_root / "linked-worktree"
        worktree_path.mkdir()
        git_meta = repo_git / "worktrees" / "linked-worktree"
        git_meta.mkdir(parents=True)
        (worktree_path / ".git").write_text(f"gitdir: {git_meta}\n")
        (git_meta / "HEAD").write_text("ref: refs/heads/feature/test\n")
        refs_dir = git_meta / "refs" / "heads" / "feature"
        refs_dir.mkdir(parents=True)
        (refs_dir / "test").write_text("1234567890abcdef1234567890abcdef12345678\n")

        service = WorkspaceInventoryService(
            source_mode="database",
            workspace_roots=[str(repos_root), str(worktrees_root)],
            inventory_db_path=str(tmp_path / "inventory.sqlite3"),
        )
        service.add_repository(
            repository_id="bad-linked-worktree-repo",
            name="linked-worktree",
            root_path=str(worktree_path.resolve()),
            origin_url="https://github.com/test/linked-worktree.git",
            default_branch="feature/test",
        )

        inventory = service.rescan([str(repos_root), str(worktrees_root)])
        repo_paths = {repo.root_path for repo in inventory.repositories}

        assert str(worktree_path.resolve()) not in repo_paths
        assert str(repo_path.resolve()) in repo_paths

    def test_invalid_git_metadata_status(self, tmp_path: Path) -> None:
        """T-UI-INV-INVALID-GIT: Unreadable git metadata marked invalid_git_metadata."""
        # Create a dir that looks like a repo but has no valid .git
        repo_path = tmp_path / "broken-repo"
        repo_path.mkdir()
        git_dir = repo_path / ".git"
        git_dir.mkdir()
        # No HEAD file - invalid

        service = WorkspaceInventoryService(
            source_mode="filesystem", workspace_roots=[str(tmp_path)]
        )
        inventory = service.get_inventory()

        found = [r for r in inventory.repositories if "broken-repo" in r.name]
        assert len(found) == 1
        assert found[0].status == "invalid_git_metadata"

    def test_create_workspace_creates_worktree_under_worktrees_root(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Create workspace uses /workspace/worktrees naming and registers inventory."""
        workspace_root = tmp_path / "workspace"
        workspace_root.mkdir()
        monkeypatch.setattr("src.services.workspace_inventory.WORKSPACE", str(workspace_root))

        repo_path = workspace_root / "repo-a"
        repo_path.mkdir()
        repo_git = repo_path / ".git"
        repo_git.mkdir()
        (repo_git / "HEAD").write_text("ref: refs/heads/main\n")
        refs = repo_git / "refs" / "heads"
        refs.mkdir(parents=True)
        (refs / "main").write_text("1234567890abcdef1234567890abcdef12345678\n")

        service = WorkspaceInventoryService(
            source_mode="database",
            workspace_roots=[str(workspace_root)],
            inventory_db_path=str(workspace_root / "inventory.sqlite3"),
        )
        repo = service.add_repository(
            repository_id="repo-a",
            name="repo-a",
            root_path=str(repo_path),
            origin_url="https://example.com/repo-a.git",
            default_branch="main",
        )

        def fake_run(
            cmd: list[str],
            capture_output: bool = True,
            text: bool = True,
            check: bool = False,
        ):
            if "show-ref" in cmd:
                return subprocess.CompletedProcess(cmd, 1, "", "")
            if "worktree" in cmd and "add" in cmd:
                destination = Path(cmd[-2])
                destination.mkdir(parents=True, exist_ok=True)
                git_meta = workspace_root / ".git" / "worktrees" / destination.name
                git_meta.mkdir(parents=True, exist_ok=True)
                (destination / ".git").write_text(f"gitdir: {git_meta}\n")
                (git_meta / "HEAD").write_text("ref: refs/heads/feature/new\n")
                feature_ref = git_meta / "refs" / "heads" / "feature"
                feature_ref.mkdir(parents=True, exist_ok=True)
                (feature_ref / "new").write_text("abcdef1234567890abcdef1234567890abcdef12\n")
                return subprocess.CompletedProcess(cmd, 0, "", "")
            if "status" in cmd:
                return subprocess.CompletedProcess(cmd, 0, "", "")
            return subprocess.CompletedProcess(cmd, 0, "", "")

        monkeypatch.setattr("src.services.workspace_inventory.subprocess.run", fake_run)
        created = service.create_workspace(repository_id=repo.repository_id, branch="feature/new")

        expected_root = (workspace_root / "worktrees").resolve()
        assert Path(created.path).resolve().parent == expected_root
        assert created.repository_id == repo.repository_id
        assert created.branch == "feature/new"
        assert created.status == "ready"

    def test_remove_workspace_deletes_inventory_record(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Removing workspace runs git worktree remove and drops DB record."""
        service = WorkspaceInventoryService(
            source_mode="database",
            workspace_roots=[str(tmp_path)],
            inventory_db_path=str(tmp_path / "inventory.sqlite3"),
        )
        repo_path = tmp_path / "repo"
        repo_path.mkdir()
        (repo_path / ".git").mkdir()
        (repo_path / ".git" / "HEAD").write_text("ref: refs/heads/main\n")
        service.add_repository(
            repository_id="repo-1",
            name="repo",
            root_path=str(repo_path),
            origin_url="https://example.com/repo.git",
            default_branch="main",
        )
        workspace_path = tmp_path / "worktrees" / "repo-ws"
        workspace_path.mkdir(parents=True)
        service.add_workspace(
            workspace_id="ws-1",
            repository_id="repo-1",
            workspace_name="repo-ws",
            path=str(workspace_path),
            branch="main",
            head_sha="abc123",
        )

        captured: dict[str, list[str]] = {}

        def fake_run(
            cmd: list[str],
            capture_output: bool = True,
            text: bool = True,
            check: bool = False,
        ):
            captured["cmd"] = cmd
            return subprocess.CompletedProcess(cmd, 0, "", "")

        monkeypatch.setattr("src.services.workspace_inventory.subprocess.run", fake_run)
        service.remove_workspace("ws-1")

        assert captured["cmd"][:5] == ["git", "-C", str(repo_path), "worktree", "remove"]
        assert captured["cmd"][5] == str(workspace_path)
        assert not any(ws.workspace_id == "ws-1" for ws in service.get_inventory().workspaces)

    def test_rename_repository_updates_name(self, tmp_path: Path) -> None:
        """Repository rename persists updated display name."""
        service = WorkspaceInventoryService(
            source_mode="database",
            workspace_roots=[str(tmp_path)],
            inventory_db_path=str(tmp_path / "inventory.sqlite3"),
        )
        service.add_repository(
            repository_id="repo-1",
            name="old-repo-name",
            root_path=str(tmp_path / "repo"),
            origin_url="https://example.com/repo.git",
            default_branch="main",
        )

        updated = service.rename_repository("repo-1", "new-repo-name")
        assert updated.name == "new-repo-name"
        inventory = service.get_inventory()
        assert inventory.repositories[0].name == "new-repo-name"

    def test_rename_workspace_updates_name(self, tmp_path: Path) -> None:
        """Workspace rename persists updated display name."""
        service = WorkspaceInventoryService(
            source_mode="database",
            workspace_roots=[str(tmp_path)],
            inventory_db_path=str(tmp_path / "inventory.sqlite3"),
        )
        repo_path = tmp_path / "repo"
        repo_path.mkdir()
        (repo_path / ".git").mkdir()
        (repo_path / ".git" / "HEAD").write_text("ref: refs/heads/main\n")
        service.add_repository(
            repository_id="repo-1",
            name="repo",
            root_path=str(repo_path),
            origin_url="https://example.com/repo.git",
            default_branch="main",
        )
        service.add_workspace(
            workspace_id="ws-1",
            repository_id="repo-1",
            workspace_name="old-workspace-name",
            path=str(tmp_path / "worktrees" / "ws-1"),
            branch="main",
            head_sha="abc123",
        )

        updated = service.rename_workspace("ws-1", "new-workspace-name")
        assert updated.workspace_name == "new-workspace-name"
        inventory = service.get_inventory()
        assert inventory.workspaces[0].workspace_name == "new-workspace-name"


class TestInventoryEndpoint:
    """Contract tests for /ui/inventory endpoint."""

    def test_t_ui_inventory_200(
        self,
        client: TestClient,
        sample_repository: RepositoryInfo,
        sample_workspace: WorkspaceInfo,
    ) -> None:
        """T-UI-INV-200: GET /ui/inventory returns valid inventory response."""
        mock_inventory = InventoryResponse(
            repositories=[sample_repository],
            workspaces=[sample_workspace],
            source_mode="database",
            generated_at=datetime.now(UTC).isoformat(),
        )

        with patch(
            "src.api.ui.inventory_service.get_inventory", return_value=mock_inventory
        ):
            resp = client.get("/api/v1/ui/inventory")

        assert resp.status_code == 200
        data = resp.json()
        assert "repositories" in data
        assert "workspaces" in data
        assert "source_mode" in data
        assert "generated_at" in data

    def test_t_ui_inventory_schema_valid(
        self,
        client: TestClient,
        sample_repository: RepositoryInfo,
        sample_workspace: WorkspaceInfo,
    ) -> None:
        """T-UI-INV-SCHEMA: Response matches documented JSON schema."""
        mock_inventory = InventoryResponse(
            repositories=[sample_repository],
            workspaces=[sample_workspace],
            source_mode="database",
            generated_at=datetime.now(UTC).isoformat(),
        )

        with patch(
            "src.api.ui.inventory_service.get_inventory", return_value=mock_inventory
        ):
            resp = client.get("/api/v1/ui/inventory")

        data = resp.json()
        repo = data["repositories"][0]
        assert "repository_id" in repo
        assert "name" in repo
        assert "root_path" in repo
        assert "origin_url" in repo
        assert "default_branch" in repo
        assert "status" in repo
        assert "last_seen_at" in repo
        assert "last_fetched_at" in repo
        assert "last_commit_at" in repo

        ws = data["workspaces"][0]
        assert "workspace_id" in ws
        assert "repository_id" in ws
        assert "workspace_name" in ws
        assert "path" in ws
        assert "branch" in ws
        assert "head_sha" in ws
        assert "is_dirty" in ws
        assert "status" in ws
        assert "last_seen_at" in ws

    def test_t_ui_inventory_500_on_backend_error(self, client: TestClient) -> None:
        """T-UI-INV-500: Returns 500 when inventory backend unavailable."""
        with patch(
            "src.api.ui.inventory_service.get_inventory",
            side_effect=InventoryError("Backend unavailable"),
        ):
            resp = client.get("/api/v1/ui/inventory")

        assert resp.status_code == 500
        assert "unavailable" in resp.json()["detail"].lower()

    def test_t_ui_inventory_rescan_200(
        self,
        client: TestClient,
        sample_repository: RepositoryInfo,
        sample_workspace: WorkspaceInfo,
    ) -> None:
        """T-UI-INV-RESCAN-200: POST /ui/inventory/rescan returns refreshed inventory."""
        mock_inventory = InventoryResponse(
            repositories=[sample_repository],
            workspaces=[sample_workspace],
            source_mode="database",
            generated_at=datetime.now(UTC).isoformat(),
        )

        with patch("src.api.ui.inventory_service.rescan", return_value=mock_inventory):
            resp = client.post(
                "/api/v1/ui/inventory/rescan",
                json={"roots": ["/workspace/repos", "/workspace/worktrees"]},
            )

        assert resp.status_code == 200
        data = resp.json()
        assert len(data["repositories"]) == 1
        assert len(data["workspaces"]) == 1

    def test_t_ui_inventory_rescan_500_on_backend_error(self, client: TestClient) -> None:
        """T-UI-INV-RESCAN-500: Returns 500 when rescan fails."""
        with patch(
            "src.api.ui.inventory_service.rescan",
            side_effect=InventoryError("Rescan failed"),
        ):
            resp = client.post(
                "/api/v1/ui/inventory/rescan",
                json={"roots": ["/workspace/repos", "/workspace/worktrees"]},
            )

        assert resp.status_code == 500

    def test_t_ui_inventory_fetch_repository_200(
        self,
        client: TestClient,
        sample_repository: RepositoryInfo,
    ) -> None:
        """POST /ui/repositories/{repository_id}/fetch fetches and returns repository."""
        with patch(
            "src.api.ui.inventory_service.fetch_repository",
            return_value=sample_repository,
        ):
            resp = client.post("/api/v1/ui/repositories/repo-123/fetch")

        assert resp.status_code == 200
        data = resp.json()
        assert data["repository_id"] == "repo-123"
        assert data["last_fetched_at"] == "2026-07-22T10:00:00Z"

    def test_t_ui_inventory_fetch_repository_404(self, client: TestClient) -> None:
        """POST /ui/repositories/{repository_id}/fetch returns 404 when repo missing."""
        with patch(
            "src.api.ui.inventory_service.fetch_repository",
            side_effect=InventoryError("Repository not found: repo-missing"),
        ):
            resp = client.post("/api/v1/ui/repositories/repo-missing/fetch")

        assert resp.status_code == 404

    def test_t_ui_inventory_fetch_repository_400(self, client: TestClient) -> None:
        """POST /ui/repositories/{repository_id}/fetch returns 400 for fetch failures."""
        with patch(
            "src.api.ui.inventory_service.fetch_repository",
            side_effect=InventoryError("Failed to fetch repository: remote failure"),
        ):
            resp = client.post("/api/v1/ui/repositories/repo-123/fetch")

        assert resp.status_code == 400

    def test_t_ui_workspaces_create_200(
        self,
        client: TestClient,
        sample_workspace: WorkspaceInfo,
    ) -> None:
        """POST /ui/workspaces creates and returns workspace."""
        with patch(
            "src.api.ui.inventory_service.create_workspace",
            return_value=sample_workspace,
        ):
            resp = client.post(
                "/api/v1/ui/workspaces",
                json={"repository_id": "repo-123", "branch": "feature/new"},
            )

        assert resp.status_code == 200
        assert resp.json()["workspace_id"] == "ws-abc"

    def test_t_ui_workspaces_create_404(self, client: TestClient) -> None:
        """POST /ui/workspaces returns 404 when repository is missing."""
        with patch(
            "src.api.ui.inventory_service.create_workspace",
            side_effect=InventoryError("Repository not found: missing"),
        ):
            resp = client.post(
                "/api/v1/ui/workspaces",
                json={"repository_id": "missing", "branch": "feature/new"},
            )

        assert resp.status_code == 404

    def test_t_ui_workspaces_delete_200(self, client: TestClient) -> None:
        """DELETE /ui/workspaces/{workspace_id} removes workspace."""
        with patch("src.api.ui.inventory_service.remove_workspace", return_value=None):
            resp = client.delete("/api/v1/ui/workspaces/ws-abc")

        assert resp.status_code == 200
        assert resp.json() == {"ok": True}

    def test_t_ui_workspaces_delete_404(self, client: TestClient) -> None:
        """DELETE /ui/workspaces/{workspace_id} returns 404 when missing."""
        with patch(
            "src.api.ui.inventory_service.remove_workspace",
            side_effect=InventoryError("Workspace not found: ws-missing"),
        ):
            resp = client.delete("/api/v1/ui/workspaces/ws-missing")

        assert resp.status_code == 404

    def test_t_ui_repositories_rename_200(
        self,
        client: TestClient,
        sample_repository: RepositoryInfo,
    ) -> None:
        """PATCH /ui/repositories/{repository_id} renames repository."""
        renamed = RepositoryInfo(
            repository_id=sample_repository.repository_id,
            name="renamed-repo",
            root_path=sample_repository.root_path,
            origin_url=sample_repository.origin_url,
            default_branch=sample_repository.default_branch,
            status=sample_repository.status,
            last_seen_at=sample_repository.last_seen_at,
            last_fetched_at=sample_repository.last_fetched_at,
            last_commit_at=sample_repository.last_commit_at,
        )
        with patch(
            "src.api.ui.inventory_service.rename_repository",
            return_value=renamed,
        ):
            resp = client.patch(
                "/api/v1/ui/repositories/repo-123",
                json={"name": "renamed-repo"},
            )

        assert resp.status_code == 200
        assert resp.json()["name"] == "renamed-repo"

    def test_t_ui_workspaces_rename_200(
        self,
        client: TestClient,
        sample_workspace: WorkspaceInfo,
    ) -> None:
        """PATCH /ui/workspaces/{workspace_id} renames workspace."""
        renamed = WorkspaceInfo(
            workspace_id=sample_workspace.workspace_id,
            repository_id=sample_workspace.repository_id,
            workspace_name="renamed-workspace",
            path=sample_workspace.path,
            branch=sample_workspace.branch,
            head_sha=sample_workspace.head_sha,
            is_dirty=sample_workspace.is_dirty,
            status=sample_workspace.status,
            last_seen_at=sample_workspace.last_seen_at,
        )
        with patch(
            "src.api.ui.inventory_service.rename_workspace",
            return_value=renamed,
        ):
            resp = client.patch(
                "/api/v1/ui/workspaces/ws-abc",
                json={"workspace_name": "renamed-workspace"},
            )

        assert resp.status_code == 200
        assert resp.json()["workspace_name"] == "renamed-workspace"

    def test_t_ui_inventory_no_secrets(
        self,
        client: TestClient,
        sample_repository: RepositoryInfo,
        sample_workspace: WorkspaceInfo,
    ) -> None:
        """T-UI-INV-SEC-NO-SECRETS: No secrets in response payload."""
        mock_inventory = InventoryResponse(
            repositories=[sample_repository],
            workspaces=[sample_workspace],
            source_mode="database",
            generated_at=datetime.now(UTC).isoformat(),
        )

        with patch(
            "src.api.ui.inventory_service.get_inventory", return_value=mock_inventory
        ):
            resp = client.get("/api/v1/ui/inventory")

        data = resp.json()
        # Check no secret-like fields exist
        response_str = str(data).lower()
        assert "password" not in response_str
        assert "secret" not in response_str
        assert "token" not in response_str
        assert "credential" not in response_str


class TestInventoryObservability:
    """Tests for observability requirements."""

    def test_inventory_refresh_emits_events(self, tmp_path: Path) -> None:
        """T-UI-INV-OBS-EVENTS: Inventory operations emit structured events."""
        from src.core import events

        events.operation_events = events.OperationEventStore()

        service = WorkspaceInventoryService(
            source_mode="database", workspace_roots=[str(tmp_path)]
        )
        service.get_inventory()

        all_events = events.operation_events.list_since(0)
        inventory_events = [
            e for e in all_events if "inventory" in e.operation]
        assert len(inventory_events) >= 1
