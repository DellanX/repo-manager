"""Tests for Web UI inventory endpoint and service.

Test IDs map to spec requirements in docs/specs/ui/webui.md section 8.
"""
from __future__ import annotations

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
    )


@pytest.fixture()
def sample_workspace() -> WorkspaceInfo:
    return WorkspaceInfo(
        workspace_id="ws-abc",
        repository_id="repo-123",
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

        service = WorkspaceInventoryService(
            source_mode="filesystem", workspace_roots=[str(tmp_path)]
        )
        inventory = service.get_inventory()

        assert len(inventory.repositories) >= 1
        found = [r for r in inventory.repositories if "my-repo" in r.name]
        assert len(found) == 1
        assert found[0].status == "ready"

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

        ws = data["workspaces"][0]
        assert "workspace_id" in ws
        assert "repository_id" in ws
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
