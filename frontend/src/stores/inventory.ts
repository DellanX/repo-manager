import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import {
  apiClient,
  type DashboardResponse,
  type InventoryResponse,
  type RepositoryInfo,
  type WorkspaceInfo,
  type ActivityItem
} from '@/api/client'

export const useInventoryStore = defineStore('inventory', () => {
  // State
  const repositories = ref<RepositoryInfo[]>([])
  const workspaces = ref<WorkspaceInfo[]>([])
  const recentActivity = ref<ActivityItem[]>([])
  const healthStatus = ref<'healthy' | 'degraded'>('healthy')
  const generatedAt = ref<string>('')
  const loading = ref(false)
  const error = ref<string | null>(null)

  // Computed
  const counts = computed(() => ({
    repositories: repositories.value.length,
    workspaces: workspaces.value.length,
    staleOrMissing:
      repositories.value.filter((r) =>
        ['stale', 'missing_path', 'invalid_git_metadata'].includes(r.status)
      ).length +
      workspaces.value.filter((w) =>
        ['stale', 'missing_path', 'invalid_git_metadata'].includes(w.status)
      ).length
  }))

  const getRepositoryById = computed(() => (id: string) =>
    repositories.value.find((r) => r.repository_id === id)
  )

  const getWorkspacesByRepository = computed(() => (repoId: string) =>
    workspaces.value.filter((w) => w.repository_id === repoId)
  )

  // Actions
  async function fetchDashboard() {
    loading.value = true
    error.value = null
    try {
      const data: DashboardResponse = await apiClient.getDashboard()
      workspaces.value = data.worktrees
      recentActivity.value = data.recent_activity
      healthStatus.value = data.health_status
      generatedAt.value = data.generated_at
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to fetch dashboard'
    } finally {
      loading.value = false
    }
  }

  async function fetchInventory() {
    loading.value = true
    error.value = null
    try {
      const data: InventoryResponse = await apiClient.getInventory()
      repositories.value = data.repositories
      workspaces.value = data.workspaces
      generatedAt.value = data.generated_at
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to fetch inventory'
    } finally {
      loading.value = false
    }
  }

  async function rescanInventory(roots: string[]) {
    loading.value = true
    error.value = null
    try {
      const data: InventoryResponse = await apiClient.rescanInventory(roots)
      repositories.value = data.repositories
      workspaces.value = data.workspaces
      generatedAt.value = data.generated_at
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to rescan inventory'
      throw e
    } finally {
      loading.value = false
    }
  }

  async function fetchRepository(repositoryId: string) {
    loading.value = true
    error.value = null
    try {
      await apiClient.fetchRepository(repositoryId)
      await fetchInventory()
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to fetch repository'
      throw e
    } finally {
      loading.value = false
    }
  }

  async function cloneRepository(url: string, destination?: string) {
    loading.value = true
    error.value = null
    try {
      await apiClient.cloneRepository(url, destination)
      await fetchInventory()
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to clone repository'
      throw e
    } finally {
      loading.value = false
    }
  }

  async function createWorkspace(repositoryId: string, branch: string, path: string) {
    loading.value = true
    error.value = null
    try {
      const workspace = await apiClient.createWorkspace(repositoryId, branch, path)
      workspaces.value.push(workspace)
      return workspace
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to create workspace'
      throw e
    } finally {
      loading.value = false
    }
  }

  async function removeWorkspace(workspaceId: string) {
    loading.value = true
    error.value = null
    try {
      await apiClient.removeWorkspace(workspaceId)
      workspaces.value = workspaces.value.filter((w) => w.workspace_id !== workspaceId)
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to remove workspace'
      throw e
    } finally {
      loading.value = false
    }
  }

  async function selectWorkspace(workspaceId: string) {
    loading.value = true
    error.value = null
    try {
      await apiClient.selectWorkspace(workspaceId)
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to select workspace'
      throw e
    } finally {
      loading.value = false
    }
  }

  return {
    // State
    repositories,
    workspaces,
    recentActivity,
    healthStatus,
    generatedAt,
    loading,
    error,
    // Computed
    counts,
    getRepositoryById,
    getWorkspacesByRepository,
    // Actions
    fetchDashboard,
    fetchInventory,
    rescanInventory,
    fetchRepository,
    cloneRepository,
    createWorkspace,
    removeWorkspace,
    selectWorkspace
  }
})
