"""Web UI API endpoints (JSON only).

Implements endpoints per docs/specs/ui/webui.md and docs/specs/ui/ux.md.
All HTML rendering is handled by the frontend SPA.
"""

from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException

from src.core import events
from src.models.schemas import (
    ActivityItem,
    DashboardResponse,
    InventoryCounts,
    InventoryRescanRequest,
    InventoryResponse,
    RepositoryInfo,
    RepositoryRenameRequest,
    WorkspaceCreateRequest,
    WorkspaceInfo,
    WorkspaceRenameRequest,
)
from src.services.workspace_inventory import InventoryError, inventory_service

router = APIRouter(prefix="/ui", tags=["ui"])


def _get_dashboard_data() -> DashboardResponse:
    """Get dashboard data."""
    inventory = inventory_service.get_inventory()

    # Calculate counts
    stale_count = sum(
        1
        for r in inventory.repositories
        if r.status in ("stale", "missing_path", "invalid_git_metadata")
    ) + sum(
        1
        for w in inventory.workspaces
        if w.status in ("stale", "missing_path", "invalid_git_metadata")
    )

    counts = InventoryCounts(
        repositories=len(inventory.repositories),
        workspaces=len(inventory.workspaces),
        stale_or_missing=stale_count,
    )

    # Determine health status
    health_status = "degraded" if stale_count > 0 else "healthy"

    # Get recent activity from event store
    recent_events = events.operation_events.list_since(0)[-20:]
    activity = [
        ActivityItem(
            id=e.id,
            timestamp=e.ts,
            operation=e.operation,
            status=e.status,
            summary=f"{e.operation} {e.status}",
        )
        for e in reversed(recent_events)
    ]

    return DashboardResponse(
        counts=counts,
        health_status=health_status,
        worktrees=inventory.workspaces,
        recent_activity=activity,
        generated_at=datetime.now(UTC).isoformat(),
    )


@router.get("/dashboard", response_model=DashboardResponse)
def get_dashboard() -> DashboardResponse:
    """Get dashboard data as JSON.

    Returns summary counts, worktree table, and recent activity
    per docs/specs/ui/ux.md section 3.1.

    Returns:
        DashboardResponse: Dashboard data including counts, worktrees, activity

    Raises:
        HTTPException: 500 if inventory backend unavailable
    """
    try:
        return _get_dashboard_data()
    except InventoryError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/inventory", response_model=InventoryResponse)
def get_inventory() -> InventoryResponse:
    """Get repository and workspace inventory.

    Returns the current inventory of managed repositories and workspaces.
    Response format follows docs/specs/ui/webui.md section 3.1.

    Returns:
        InventoryResponse: Current inventory state

    Raises:
        HTTPException: 500 if inventory backend unavailable
    """
    try:
        return inventory_service.get_inventory()
    except InventoryError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/inventory/rescan", response_model=InventoryResponse)
def rescan_inventory(request: InventoryRescanRequest) -> InventoryResponse:
    """Rescan filesystem roots and return refreshed inventory."""
    try:
        roots = request.roots or None
        return inventory_service.rescan(roots=roots)
    except InventoryError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/repositories/{repository_id}/fetch", response_model=RepositoryInfo)
def fetch_repository(repository_id: str) -> RepositoryInfo:
    """Fetch remote refs for a managed repository."""
    try:
        return inventory_service.fetch_repository(repository_id)
    except InventoryError as exc:
        detail = str(exc)
        if detail.startswith("Repository not found"):
            raise HTTPException(status_code=404, detail=detail) from exc
        raise HTTPException(status_code=400, detail=detail) from exc


@router.patch("/repositories/{repository_id}", response_model=RepositoryInfo)
def rename_repository(repository_id: str, request: RepositoryRenameRequest) -> RepositoryInfo:
    """Rename a repository display name."""
    try:
        return inventory_service.rename_repository(repository_id, request.name)
    except InventoryError as exc:
        detail = str(exc)
        if detail.startswith("Repository not found"):
            raise HTTPException(status_code=404, detail=detail) from exc
        raise HTTPException(status_code=400, detail=detail) from exc


@router.post("/workspaces", response_model=WorkspaceInfo)
def create_workspace(request: WorkspaceCreateRequest) -> WorkspaceInfo:
    """Create a new git worktree workspace for a repository."""
    try:
        return inventory_service.create_workspace(
            repository_id=request.repository_id,
            branch=request.branch,
            workspace_name=request.workspace_name,
        )
    except InventoryError as exc:
        detail = str(exc)
        if detail.startswith("Repository not found"):
            raise HTTPException(status_code=404, detail=detail) from exc
        raise HTTPException(status_code=400, detail=detail) from exc


@router.delete("/workspaces/{workspace_id}")
def remove_workspace(workspace_id: str) -> dict[str, bool]:
    """Remove a git worktree workspace."""
    try:
        inventory_service.remove_workspace(workspace_id)
        return {"ok": True}
    except InventoryError as exc:
        detail = str(exc)
        if detail.startswith("Workspace not found"):
            raise HTTPException(status_code=404, detail=detail) from exc
        raise HTTPException(status_code=400, detail=detail) from exc


@router.patch("/workspaces/{workspace_id}", response_model=WorkspaceInfo)
def rename_workspace(workspace_id: str, request: WorkspaceRenameRequest) -> WorkspaceInfo:
    """Rename a workspace display name."""
    try:
        return inventory_service.rename_workspace(workspace_id, request.workspace_name)
    except InventoryError as exc:
        detail = str(exc)
        if detail.startswith("Workspace not found"):
            raise HTTPException(status_code=404, detail=detail) from exc
        raise HTTPException(status_code=400, detail=detail) from exc
