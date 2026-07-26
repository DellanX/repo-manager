"""Tests for Web UI dashboard endpoint.

Test IDs map to spec requirements in docs/specs/ui/ux.md section 3.1.
All tests use /api/v1 prefix per API versioning.
"""
from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from src.models.schemas import (
    InventoryResponse,
    RepositoryInfo,
    WorkspaceInfo,
)
from src.server import app
from src.services.workspace_inventory import InventoryError


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


class TestDashboardEndpoint:
    """Contract tests for /api/v1/ui/dashboard endpoint (per docs/specs/ui/ux.md)."""

    def test_t_ui_dashboard_json_200(
        self,
        client: TestClient,
        sample_repository: RepositoryInfo,
        sample_workspace: WorkspaceInfo,
    ) -> None:
        """T-UI-DASH-JSON-200: GET /api/v1/ui/dashboard returns valid JSON response."""
        mock_inventory = InventoryResponse(
            repositories=[sample_repository],
            workspaces=[sample_workspace],
            source_mode="database",
            generated_at=datetime.now(UTC).isoformat(),
        )

        with patch(
            "src.api.ui.inventory_service.get_inventory", return_value=mock_inventory
        ):
            resp = client.get("/api/v1/ui/dashboard")

        assert resp.status_code == 200
        data = resp.json()
        assert "counts" in data
        assert "health_status" in data
        assert "worktrees" in data
        assert "recent_activity" in data
        assert "generated_at" in data

    def test_t_ui_dashboard_counts(
        self,
        client: TestClient,
        sample_repository: RepositoryInfo,
        sample_workspace: WorkspaceInfo,
    ) -> None:
        """T-UI-DASH-COUNTS: Dashboard shows correct counts."""
        mock_inventory = InventoryResponse(
            repositories=[sample_repository],
            workspaces=[sample_workspace],
            source_mode="database",
            generated_at=datetime.now(UTC).isoformat(),
        )

        with patch(
            "src.api.ui.inventory_service.get_inventory", return_value=mock_inventory
        ):
            resp = client.get("/api/v1/ui/dashboard")

        data = resp.json()
        assert data["counts"]["repositories"] == 1
        assert data["counts"]["workspaces"] == 1
        assert data["counts"]["stale_or_missing"] == 0

    def test_t_ui_dashboard_health_degraded(
        self,
        client: TestClient,
    ) -> None:
        """T-UI-DASH-HEALTH: Dashboard shows degraded when stale items exist."""
        stale_repo = RepositoryInfo(
            repository_id="repo-stale",
            name="stale-repo",
            root_path="/workspace/stale",
            origin_url="https://github.com/test/stale.git",
            default_branch="main",
            status="stale",
            last_seen_at="2026-07-22T12:00:00Z",
            last_fetched_at=None,
            last_commit_at=None,
        )
        mock_inventory = InventoryResponse(
            repositories=[stale_repo],
            workspaces=[],
            source_mode="database",
            generated_at=datetime.now(UTC).isoformat(),
        )

        with patch(
            "src.api.ui.inventory_service.get_inventory", return_value=mock_inventory
        ):
            resp = client.get("/api/v1/ui/dashboard")

        data = resp.json()
        assert data["health_status"] == "degraded"
        assert data["counts"]["stale_or_missing"] == 1

    def test_t_ui_dashboard_500_on_backend_error(self, client: TestClient) -> None:
        """T-UI-DASH-500: Returns 500 when inventory backend unavailable."""
        with patch(
            "src.api.ui.inventory_service.get_inventory",
            side_effect=InventoryError("Backend unavailable"),
        ):
            resp = client.get("/api/v1/ui/dashboard")

        assert resp.status_code == 500
        assert "unavailable" in resp.json()["detail"].lower()

    def test_t_ui_dashboard_worktrees_included(
        self,
        client: TestClient,
        sample_repository: RepositoryInfo,
        sample_workspace: WorkspaceInfo,
    ) -> None:
        """T-UI-DASH-WORKTREES: Dashboard includes worktree data."""
        mock_inventory = InventoryResponse(
            repositories=[sample_repository],
            workspaces=[sample_workspace],
            source_mode="database",
            generated_at=datetime.now(UTC).isoformat(),
        )

        with patch(
            "src.api.ui.inventory_service.get_inventory", return_value=mock_inventory
        ):
            resp = client.get("/api/v1/ui/dashboard")

        data = resp.json()
        assert len(data["worktrees"]) == 1
        worktree = data["worktrees"][0]
        assert worktree["workspace_id"] == "ws-abc"
        assert worktree["repository_id"] == "repo-123"
        assert worktree["branch"] == "feature/webui"
        assert worktree["is_dirty"] is False
        assert worktree["status"] == "ready"


class TestInventoryEndpoint:
    """Contract tests for /api/v1/ui/inventory endpoint."""

    def test_t_ui_inventory_200(
        self,
        client: TestClient,
        sample_repository: RepositoryInfo,
        sample_workspace: WorkspaceInfo,
    ) -> None:
        """T-UI-INV-200: GET /api/v1/ui/inventory returns inventory."""
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
        assert len(data["repositories"]) == 1
        assert len(data["workspaces"]) == 1

    def test_t_ui_inventory_500_on_error(self, client: TestClient) -> None:
        """T-UI-INV-500: Returns 500 when inventory backend unavailable."""
        with patch(
            "src.api.ui.inventory_service.get_inventory",
            side_effect=InventoryError("Backend unavailable"),
        ):
            resp = client.get("/api/v1/ui/inventory")

        assert resp.status_code == 500
