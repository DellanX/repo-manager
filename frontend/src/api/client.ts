/**
 * API client for backend communication.
 * All endpoints use /api/v1 prefix per API versioning decision.
 */

const API_BASE = '/api/v1'

export interface RepositoryInfo {
  repository_id: string
  name: string
  root_path: string
  origin_url: string
  default_branch: string
  status: 'ready' | 'missing_path' | 'invalid_git_metadata' | 'stale'
  last_seen_at: string
}

export interface WorkspaceInfo {
  workspace_id: string
  repository_id: string
  path: string
  branch: string
  head_sha: string
  is_dirty: boolean
  status: 'ready' | 'missing_path' | 'invalid_git_metadata' | 'stale'
  last_seen_at: string
}

export interface ActivityItem {
  id: string
  timestamp: string
  operation: string
  status: string
  summary: string
}

export interface InventoryCounts {
  repositories: number
  workspaces: number
  stale_or_missing: number
}

export interface DashboardResponse {
  counts: InventoryCounts
  health_status: 'healthy' | 'degraded'
  worktrees: WorkspaceInfo[]
  recent_activity: ActivityItem[]
  generated_at: string
}

export interface InventoryResponse {
  repositories: RepositoryInfo[]
  workspaces: WorkspaceInfo[]
  source_mode: 'database' | 'filesystem'
  generated_at: string
}

class ApiClient {
  private async request<T>(endpoint: string, options?: RequestInit): Promise<T> {
    const response = await fetch(`${API_BASE}${endpoint}`, {
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers
      },
      ...options
    })

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Request failed' })) as { detail?: string }
      throw new Error(error.detail || `HTTP ${response.status}`)
    }

    return response.json() as Promise<T>
  }

  // Dashboard
  async getDashboard(): Promise<DashboardResponse> {
    return this.request<DashboardResponse>('/ui/dashboard')
  }

  // Inventory
  async getInventory(): Promise<InventoryResponse> {
    return this.request<InventoryResponse>('/ui/inventory')
  }

  // Repositories
  async cloneRepository(url: string, path: string, defaultBranch?: string): Promise<void> {
    await this.request('/ui/repos/clone', {
      method: 'POST',
      body: JSON.stringify({ url, path, default_branch: defaultBranch })
    })
  }

  // Workspaces
  async createWorkspace(
    repositoryId: string,
    branch: string,
    path: string
  ): Promise<WorkspaceInfo> {
    return this.request<WorkspaceInfo>('/ui/workspaces', {
      method: 'POST',
      body: JSON.stringify({ repository_id: repositoryId, branch, path })
    })
  }

  async removeWorkspace(workspaceId: string): Promise<void> {
    await this.request(`/ui/workspaces/${workspaceId}`, {
      method: 'DELETE'
    })
  }

  async selectWorkspace(workspaceId: string): Promise<void> {
    await this.request(`/ui/workspaces/${workspaceId}/select`, {
      method: 'POST'
    })
  }
}

export const apiClient = new ApiClient()
