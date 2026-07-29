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
  last_fetched_at: string | null
  last_commit_at: string | null
}

export interface WorkspaceInfo {
  workspace_id: string
  repository_id: string
  workspace_name: string
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

export type CredentialProvider = 'github' | 'gitlab' | 'azure_devops' | 'generic'

export interface CredentialInfo {
  credential_id: string
  name: string
  provider: CredentialProvider
  host: string
  username: string
  created_at: string
  updated_at: string
  revoked_at: string | null
  is_active: boolean
}

export interface CredentialCreatePayload {
  name: string
  provider: CredentialProvider
  host: string
  username: string
  secret: string
}

export interface SecretDriverInfo {
  name: string
  is_secure: boolean
}

export interface CredentialDriversResponse {
  active_driver: string
  drivers: SecretDriverInfo[]
}

export interface SSHIdentityInfo {
  identity_id: string
  name: string
  host: string
  username: string
  identity_file: string
  public_key: string
  created_at: string
  updated_at: string
  revoked_at: string | null
  is_active: boolean
}

export interface SSHIdentityCreatePayload {
  name: string
  host: string
  username: string
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

  async rescanInventory(roots: string[]): Promise<InventoryResponse> {
    return this.request<InventoryResponse>('/ui/inventory/rescan', {
      method: 'POST',
      body: JSON.stringify({ roots })
    })
  }

  async fetchRepository(repositoryId: string): Promise<RepositoryInfo> {
    return this.request<RepositoryInfo>(`/ui/repositories/${repositoryId}/fetch`, {
      method: 'POST'
    })
  }

  async renameRepository(repositoryId: string, name: string): Promise<RepositoryInfo> {
    return this.request<RepositoryInfo>(`/ui/repositories/${repositoryId}`, {
      method: 'PATCH',
      body: JSON.stringify({ name })
    })
  }

  // Repositories
  async cloneRepository(
    url: string,
    destination?: string,
    credentialId?: string,
    sshIdentityId?: string
  ): Promise<void> {
    const payload: { url: string; destination?: string; credential_id?: string; ssh_identity_id?: string } = { url }
    if (destination) {
      payload.destination = destination
    }
    if (credentialId) {
      payload.credential_id = credentialId
    }
    if (sshIdentityId) {
      payload.ssh_identity_id = sshIdentityId
    }

    await this.request<{ output: string }>('/clone', {
      method: 'POST',
      body: JSON.stringify(payload)
    })
  }

  // Credentials
  async listCredentials(): Promise<CredentialInfo[]> {
    const payload = await this.request<{ credentials: CredentialInfo[] }>('/credentials')
    return payload.credentials
  }

  async createCredential(input: CredentialCreatePayload): Promise<CredentialInfo> {
    return this.request<CredentialInfo>('/credentials', {
      method: 'POST',
      body: JSON.stringify(input)
    })
  }

  async revokeCredential(credentialId: string): Promise<CredentialInfo> {
    return this.request<CredentialInfo>(`/credentials/${credentialId}`, {
      method: 'DELETE'
    })
  }

  async getCredentialDrivers(): Promise<CredentialDriversResponse> {
    return this.request<CredentialDriversResponse>('/credentials/drivers')
  }

  // SSH identities
  async listSshIdentities(): Promise<SSHIdentityInfo[]> {
    const payload = await this.request<{ ssh_identities: SSHIdentityInfo[] }>('/ssh-identities')
    return payload.ssh_identities
  }

  async createSshIdentity(input: SSHIdentityCreatePayload): Promise<SSHIdentityInfo> {
    return this.request<SSHIdentityInfo>('/ssh-identities', {
      method: 'POST',
      body: JSON.stringify(input)
    })
  }

  async revokeSshIdentity(identityId: string): Promise<SSHIdentityInfo> {
    return this.request<SSHIdentityInfo>(`/ssh-identities/${identityId}`, {
      method: 'DELETE'
    })
  }

  // Workspaces
  async createWorkspace(
    repositoryId: string,
    branch: string,
    workspaceName?: string
  ): Promise<WorkspaceInfo> {
    return this.request<WorkspaceInfo>('/ui/workspaces', {
      method: 'POST',
      body: JSON.stringify({
        repository_id: repositoryId,
        branch,
        workspace_name: workspaceName
      })
    })
  }

  async removeWorkspace(workspaceId: string): Promise<void> {
    await this.request(`/ui/workspaces/${workspaceId}`, {
      method: 'DELETE'
    })
  }

  async renameWorkspace(workspaceId: string, workspaceName: string): Promise<WorkspaceInfo> {
    return this.request<WorkspaceInfo>(`/ui/workspaces/${workspaceId}`, {
      method: 'PATCH',
      body: JSON.stringify({ workspace_name: workspaceName })
    })
  }
}

export const apiClient = new ApiClient()
