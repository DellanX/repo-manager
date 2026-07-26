from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator


class CloneRequest(BaseModel):
    url: str
    destination: str | None = None


class CheckoutRequest(BaseModel):
    branch: str


class CommitRequest(BaseModel):
    message: str


class PushRequest(BaseModel):
    remote: str = "origin"
    branch: str = "main"


class ReadFileRequest(BaseModel):
    path: str


class WriteFileRequest(BaseModel):
    path: str
    content: str


class ExecRequest(BaseModel):
    cmd: str


class MCPCallRequest(BaseModel):
    tool: str = Field(..., description="MCP tool name")
    args: dict[str, Any] = Field(default_factory=dict)


# Web UI Inventory Schemas (per docs/specs/ui/webui.md)

InventoryStatus = Literal["ready", "missing_path",
                          "invalid_git_metadata", "stale"]
SourceMode = Literal["database", "filesystem"]


class RepositoryInfo(BaseModel):
    """Repository information for inventory display."""

    repository_id: str = Field(...,
                               description="Stable unique repository identifier")
    name: str = Field(..., description="Repository name")
    root_path: str = Field(...,
                           description="Normalized absolute path to repository root")
    origin_url: str = Field(..., description="Git origin remote URL")
    default_branch: str = Field(..., description="Default branch name")
    status: InventoryStatus = Field(...,
                                    description="Current repository status")
    last_seen_at: str = Field(...,
                              description="ISO8601 timestamp of last inventory check")


class WorkspaceInfo(BaseModel):
    """Workspace/worktree information for inventory display."""

    workspace_id: str = Field(...,
                              description="Stable unique workspace identifier")
    repository_id: str = Field(..., description="Parent repository ID")
    path: str = Field(..., description="Normalized absolute path to workspace")
    branch: str = Field(..., description="Current branch name")
    head_sha: str = Field(..., description="Current HEAD commit SHA")
    is_dirty: bool = Field(...,
                           description="Whether workspace has uncommitted changes")
    status: InventoryStatus = Field(...,
                                    description="Current workspace status")
    last_seen_at: str = Field(...,
                              description="ISO8601 timestamp of last inventory check")


class InventoryResponse(BaseModel):
    """Response schema for GET /ui/inventory endpoint."""

    repositories: list[RepositoryInfo] = Field(
        default_factory=list, description="List of managed repositories"
    )
    workspaces: list[WorkspaceInfo] = Field(
        default_factory=list, description="List of managed workspaces"
    )
    source_mode: SourceMode = Field(..., description="Inventory source mode")
    generated_at: str = Field(...,
                              description="ISO8601 timestamp when inventory was generated")

    @model_validator(mode="after")
    def deduplicate_entries(self) -> "InventoryResponse":
        """Ensure no duplicate repository or workspace IDs per spec invariant."""
        seen_repos: set[str] = set()
        unique_repos: list[RepositoryInfo] = []
        for repo in self.repositories:
            if repo.repository_id not in seen_repos:
                seen_repos.add(repo.repository_id)
                unique_repos.append(repo)
        self.repositories = unique_repos

        seen_ws: set[str] = set()
        unique_ws: list[WorkspaceInfo] = []
        for ws in self.workspaces:
            if ws.workspace_id not in seen_ws:
                seen_ws.add(ws.workspace_id)
                unique_ws.append(ws)
        self.workspaces = unique_ws

        return self


class ActivityItem(BaseModel):
    """Recent activity feed item."""

    id: int = Field(..., description="Activity event ID")
    timestamp: str = Field(..., description="ISO8601 timestamp")
    operation: str = Field(..., description="Operation type")
    status: str = Field(..., description="Operation status")
    summary: str = Field(..., description="Human-readable summary")


class InventoryCounts(BaseModel):
    """Summary counts for dashboard widgets."""

    repositories: int = Field(..., description="Total managed repositories")
    workspaces: int = Field(..., description="Total managed workspaces")
    stale_or_missing: int = Field(...,
                                  description="Stale or missing inventory items")


class DashboardResponse(BaseModel):
    """Response schema for GET /ui/dashboard endpoint (per docs/specs/ui/ux.md)."""

    counts: InventoryCounts = Field(..., description="Summary count widgets")
    health_status: Literal["healthy", "degraded"] = Field(
        ..., description="Global inventory health status"
    )
    worktrees: list[WorkspaceInfo] = Field(
        default_factory=list, description="Worktree table data"
    )
    recent_activity: list[ActivityItem] = Field(
        default_factory=list, description="Recent activity feed"
    )
    generated_at: str = Field(
        ..., description="ISO8601 timestamp when dashboard was generated"
    )
