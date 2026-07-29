from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator


class CloneRequest(BaseModel):
    url: str
    destination: str | None = None
    credential_id: str | None = None
    ssh_identity_id: str | None = None


class CheckoutRequest(BaseModel):
    workspace_id: str
    branch: str


class CommitRequest(BaseModel):
    workspace_id: str
    message: str


class PushRequest(BaseModel):
    workspace_id: str
    remote: str = "origin"
    branch: str = "main"


class ReadFileRequest(BaseModel):
    workspace_id: str
    path: str


class WriteFileRequest(BaseModel):
    workspace_id: str
    path: str
    content: str


class ExecRequest(BaseModel):
    workspace_id: str
    cmd: str


class MCPCallRequest(BaseModel):
    tool: str = Field(..., description="MCP tool name")
    args: dict[str, Any] = Field(default_factory=dict)


CredentialProvider = Literal["github", "gitlab", "azure_devops", "generic"]


class CredentialCreateRequest(BaseModel):
    name: str
    provider: CredentialProvider
    host: str
    username: str = "oauth2"
    secret: str


class CredentialUpdateRequest(BaseModel):
    name: str | None = None
    host: str | None = None
    username: str | None = None
    secret: str | None = None


class CredentialResponse(BaseModel):
    credential_id: str
    name: str
    provider: CredentialProvider
    host: str
    username: str
    created_at: str
    updated_at: str
    revoked_at: str | None
    is_active: bool


class SecretDriverResponse(BaseModel):
    name: str
    is_secure: bool


class SSHIdentityCreateRequest(BaseModel):
    name: str
    host: str
    username: str = "git"


class SSHIdentityResponse(BaseModel):
    identity_id: str
    name: str
    host: str
    username: str
    identity_file: str
    public_key: str
    created_at: str
    updated_at: str
    revoked_at: str | None
    is_active: bool


class InventoryRescanRequest(BaseModel):
    roots: list[str] = Field(default_factory=list)


class WorkspaceCreateRequest(BaseModel):
    repository_id: str
    branch: str
    workspace_name: str | None = None


class RepositoryRenameRequest(BaseModel):
    name: str


class WorkspaceRenameRequest(BaseModel):
    workspace_name: str


# Web UI Inventory Schemas (per docs/specs/ui/webui.md)

InventoryStatus = Literal["ready", "missing_path", "invalid_git_metadata", "stale"]
SourceMode = Literal["database", "filesystem"]


class RepositoryInfo(BaseModel):
    """Repository information for inventory display."""

    repository_id: str = Field(..., description="Stable unique repository identifier")
    name: str = Field(..., description="Repository name")
    root_path: str = Field(..., description="Normalized absolute path to repository root")
    origin_url: str = Field(..., description="Git origin remote URL")
    default_branch: str = Field(..., description="Default branch name")
    status: InventoryStatus = Field(..., description="Current repository status")
    last_seen_at: str = Field(..., description="ISO8601 timestamp of last inventory check")
    last_fetched_at: str | None = Field(
        default=None,
        description="ISO8601 timestamp of most recent fetch/pull metadata update",
    )
    last_commit_at: str | None = Field(
        default=None,
        description="ISO8601 timestamp of most recent commit in the repository",
    )


class WorkspaceInfo(BaseModel):
    """Workspace/worktree information for inventory display."""

    workspace_id: str = Field(..., description="Stable unique workspace identifier")
    repository_id: str = Field(..., description="Parent repository ID")
    workspace_name: str = Field(..., description="Workspace display name")
    path: str = Field(..., description="Normalized absolute path to workspace")
    branch: str = Field(..., description="Current branch name")
    head_sha: str = Field(..., description="Current HEAD commit SHA")
    is_dirty: bool = Field(..., description="Whether workspace has uncommitted changes")
    status: InventoryStatus = Field(..., description="Current workspace status")
    last_seen_at: str = Field(..., description="ISO8601 timestamp of last inventory check")


class InventoryResponse(BaseModel):
    """Response schema for GET /ui/inventory endpoint."""

    repositories: list[RepositoryInfo] = Field(
        default_factory=list, description="List of managed repositories"
    )
    workspaces: list[WorkspaceInfo] = Field(
        default_factory=list, description="List of managed workspaces"
    )
    source_mode: SourceMode = Field(..., description="Inventory source mode")
    generated_at: str = Field(..., description="ISO8601 timestamp when inventory was generated")

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
    stale_or_missing: int = Field(..., description="Stale or missing inventory items")


class DashboardResponse(BaseModel):
    """Response schema for GET /ui/dashboard endpoint (per docs/specs/ui/ux.md)."""

    counts: InventoryCounts = Field(..., description="Summary count widgets")
    health_status: Literal["healthy", "degraded"] = Field(
        ..., description="Global inventory health status"
    )
    worktrees: list[WorkspaceInfo] = Field(default_factory=list, description="Worktree table data")
    recent_activity: list[ActivityItem] = Field(
        default_factory=list, description="Recent activity feed"
    )
    generated_at: str = Field(..., description="ISO8601 timestamp when dashboard was generated")
