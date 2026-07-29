<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useInventoryStore } from '@/stores/inventory'
import WorktreeTable from '@/components/WorktreeTable.vue'
import { PageHeader, AppButton } from '@/components/ui'

const store = useInventoryStore()
const showCreateForm = ref(false)
const selectedRepositoryId = ref('')
const branch = ref('main')
const workspaceName = ref('')
const createError = ref<string | null>(null)
const createSuccess = ref<string | null>(null)

const canCreateWorkspace = computed(
  () => selectedRepositoryId.value.trim().length > 0 && branch.value.trim().length > 0 && !store.loading
)

onMounted(() => {
  store.fetchInventory()
})

function openCreateForm() {
  showCreateForm.value = true
  createError.value = null
  createSuccess.value = null
  if (!selectedRepositoryId.value && store.repositories.length > 0) {
    selectedRepositoryId.value = store.repositories[0].repository_id
  }
}

async function submitCreateWorkspace() {
  createError.value = null
  createSuccess.value = null
  try {
    const created = await store.createWorkspace(
      selectedRepositoryId.value.trim(),
      branch.value.trim(),
      workspaceName.value.trim() || undefined
    )
    createSuccess.value = `Created workspace ${created.workspace_id}.`
    branch.value = 'main'
    workspaceName.value = ''
    showCreateForm.value = false
  } catch (error) {
    createError.value = error instanceof Error ? error.message : 'Failed to create workspace.'
  }
}
</script>

<template>
  <div>
    <PageHeader title="Workspaces">
      <template #actions>
        <AppButton :disabled="store.loading || store.repositories.length === 0" @click="openCreateForm()">
          Create Workspace
        </AppButton>
      </template>
    </PageHeader>

    <form
      v-if="showCreateForm"
      class="bg-white dark:bg-neutral-800 border border-gray-200 dark:border-neutral-700 rounded-lg p-4 mb-6 space-y-4"
      @submit.prevent="submitCreateWorkspace"
    >
      <h2 class="text-lg font-medium">Create Workspace</h2>
      <div>
        <label for="workspace-repository" class="block text-sm font-medium mb-1">Repository</label>
        <select
          id="workspace-repository"
          v-model="selectedRepositoryId"
          class="w-full rounded border border-gray-300 dark:border-neutral-600 bg-white dark:bg-neutral-900 px-3 py-2"
        >
          <option disabled value="">Select a repository</option>
          <option v-for="repo in store.repositories" :key="repo.repository_id" :value="repo.repository_id">
            {{ repo.name }} ({{ repo.repository_id }})
          </option>
        </select>
      </div>
      <div>
        <label for="workspace-branch" class="block text-sm font-medium mb-1">Branch</label>
        <input
          id="workspace-branch"
          v-model="branch"
          type="text"
          class="w-full rounded border border-gray-300 dark:border-neutral-600 bg-white dark:bg-neutral-900 px-3 py-2"
          placeholder="feature/my-branch"
        >
      </div>
      <div>
        <label for="workspace-name" class="block text-sm font-medium mb-1">Workspace Name (optional)</label>
        <input
          id="workspace-name"
          v-model="workspaceName"
          type="text"
          class="w-full rounded border border-gray-300 dark:border-neutral-600 bg-white dark:bg-neutral-900 px-3 py-2"
          placeholder="my-worktree"
        >
      </div>
      <div class="flex flex-wrap gap-2">
        <AppButton type="submit" :disabled="!canCreateWorkspace">Create</AppButton>
        <AppButton type="button" variant="secondary" :disabled="store.loading" @click="showCreateForm = false">
          Cancel
        </AppButton>
      </div>
      <p v-if="createError" class="text-sm text-red-600 dark:text-red-400">{{ createError }}</p>
    </form>

    <p v-if="createSuccess" class="mb-4 text-sm text-green-600 dark:text-green-400">{{ createSuccess }}</p>
    <WorktreeTable :workspaces="store.workspaces" show-repository />
  </div>
</template>
