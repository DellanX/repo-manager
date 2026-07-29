<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useInventoryStore } from '@/stores/inventory'
import { PageHeader, AppButton } from '@/components/ui'

const props = defineProps<{
  workspaceId: string
}>()

const store = useInventoryStore()

const workspace = computed(() =>
  store.workspaces.find((item) => item.workspace_id === props.workspaceId)
)
const repository = computed(() =>
  workspace.value ? store.getRepositoryById(workspace.value.repository_id) : undefined
)
const renameError = ref<string | null>(null)
const renameSuccess = ref<string | null>(null)
const showRenameForm = ref(false)
const workspaceNameInput = ref('')

function getWorkspaceName(path: string, fallback: string): string {
  const parts = path.split(/[\\/]/).filter((part) => part.length > 0)
  return parts.length > 0 ? parts[parts.length - 1] : fallback
}

function openRenameForm() {
  if (!workspace.value) {
    return
  }
  renameError.value = null
  renameSuccess.value = null
  showRenameForm.value = true
  workspaceNameInput.value = workspace.value.workspace_name
}

async function submitRenameWorkspace() {
  const current = workspace.value
  if (!current) {
    renameError.value = 'Workspace not found.'
    return
  }
  renameError.value = null
  renameSuccess.value = null
  try {
    const updated = await store.renameWorkspace(current.workspace_id, workspaceNameInput.value.trim())
    renameSuccess.value = `Workspace renamed to ${updated.workspace_name}.`
    showRenameForm.value = false
  } catch (error) {
    renameError.value = error instanceof Error ? error.message : 'Failed to rename workspace.'
  }
}

onMounted(() => {
  if (store.workspaces.length === 0 || store.repositories.length === 0) {
    store.fetchInventory()
  }
})
</script>

<template>
  <div v-if="workspace">
    <PageHeader :title="workspace.workspace_name">
      <template #actions>
        <RouterLink to="/workspaces">
          <AppButton variant="secondary">Back to Workspaces</AppButton>
        </RouterLink>
        <RouterLink :to="`/repos/${workspace.repository_id}`">
          <AppButton>View Repository</AppButton>
        </RouterLink>
        <AppButton :disabled="store.loading" @click="openRenameForm()">Rename Workspace</AppButton>
      </template>
    </PageHeader>
    <p v-if="renameSuccess" class="mb-4 text-sm text-green-600 dark:text-green-400">{{ renameSuccess }}</p>
    <p v-if="renameError" class="mb-4 text-sm text-red-600 dark:text-red-400">{{ renameError }}</p>
    <form
      v-if="showRenameForm"
      class="bg-white dark:bg-neutral-800 border border-gray-200 dark:border-neutral-700 rounded-lg p-4 mb-6 space-y-4"
      @submit.prevent="submitRenameWorkspace"
    >
      <h2 class="text-lg font-medium">Rename Workspace</h2>
      <div>
        <label for="rename-workspace-name" class="block text-sm font-medium mb-1">Workspace Name</label>
        <input
          id="rename-workspace-name"
          v-model="workspaceNameInput"
          type="text"
          class="w-full rounded border border-gray-300 dark:border-neutral-600 bg-white dark:bg-neutral-900 px-3 py-2"
          placeholder="my-workspace"
        >
      </div>
      <div class="flex flex-wrap gap-2">
        <AppButton type="submit" :disabled="store.loading || workspaceNameInput.trim().length === 0">
          Save
        </AppButton>
        <AppButton type="button" variant="secondary" :disabled="store.loading" @click="showRenameForm = false">
          Cancel
        </AppButton>
      </div>
    </form>

    <div class="bg-white dark:bg-neutral-800 border border-gray-200 dark:border-neutral-700 rounded-lg p-6">
      <dl class="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div>
          <dt class="text-gray-500 dark:text-gray-400 text-sm mb-1">Workspace Name</dt>
          <dd class="font-medium">
            {{ workspace.workspace_name || getWorkspaceName(workspace.path, workspace.workspace_id) }}
          </dd>
        </div>
        <div>
          <dt class="text-gray-500 dark:text-gray-400 text-sm mb-1">Workspace ID</dt>
          <dd class="font-mono text-sm">{{ workspace.workspace_id }}</dd>
        </div>
        <div>
          <dt class="text-gray-500 dark:text-gray-400 text-sm mb-1">Repository</dt>
          <dd>
            <RouterLink
              :to="`/repos/${workspace.repository_id}`"
              class="text-blue-600 dark:text-blue-400 hover:underline"
            >
              {{ repository?.name || workspace.repository_id }}
            </RouterLink>
          </dd>
        </div>
        <div>
          <dt class="text-gray-500 dark:text-gray-400 text-sm mb-1">Branch</dt>
          <dd class="font-medium">{{ workspace.branch }}</dd>
        </div>
        <div>
          <dt class="text-gray-500 dark:text-gray-400 text-sm mb-1">Path</dt>
          <dd class="font-mono text-sm break-all">{{ workspace.path }}</dd>
        </div>
        <div>
          <dt class="text-gray-500 dark:text-gray-400 text-sm mb-1">Dirty</dt>
          <dd class="font-medium">{{ workspace.is_dirty ? 'Yes' : 'No' }}</dd>
        </div>
        <div>
          <dt class="text-gray-500 dark:text-gray-400 text-sm mb-1">Status</dt>
          <dd
            :class="[
              'font-medium',
              workspace.status === 'ready' ? 'text-green-600 dark:text-green-400' : 'text-yellow-500 dark:text-yellow-400'
            ]"
          >
            {{ workspace.status }}
          </dd>
        </div>
        <div>
          <dt class="text-gray-500 dark:text-gray-400 text-sm mb-1">Last Seen</dt>
          <dd class="font-medium">{{ workspace.last_seen_at.slice(0, 19) }}</dd>
        </div>
      </dl>
    </div>
  </div>

  <div v-else class="text-center text-gray-500 dark:text-gray-400 p-8">
    <p class="mb-4">Workspace not found.</p>
    <RouterLink to="/workspaces">
      <AppButton>Back to Workspaces</AppButton>
    </RouterLink>
  </div>
</template>
