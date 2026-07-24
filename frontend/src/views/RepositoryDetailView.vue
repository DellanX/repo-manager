<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useInventoryStore } from '@/stores/inventory'
import WorktreeTable from '@/components/WorktreeTable.vue'
import { PageHeader, AppButton } from '@/components/ui'

const props = defineProps<{
  repositoryId: string
}>()

const store = useInventoryStore()

const repository = computed(() => store.getRepositoryById(props.repositoryId))
const workspaces = computed(() => store.getWorkspacesByRepository(props.repositoryId))

onMounted(() => {
  if (store.repositories.length === 0) {
    store.fetchInventory()
  }
})
</script>

<template>
  <div v-if="repository">
    <PageHeader :title="repository.name">
      <template #actions>
        <AppButton>Clone New</AppButton>
        <AppButton>Create Workspace</AppButton>
        <RouterLink to="/config/credentials">
          <AppButton>Manage Credentials</AppButton>
        </RouterLink>
        <RouterLink to="/config/webhooks">
          <AppButton>Manage Webhooks</AppButton>
        </RouterLink>
      </template>
    </PageHeader>

    <div class="bg-white dark:bg-neutral-800 border border-gray-200 dark:border-neutral-700 rounded-lg p-6 mb-8">
      <dl class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        <div>
          <dt class="text-gray-500 dark:text-gray-400 text-sm mb-1">Repository ID</dt>
          <dd class="font-medium">{{ repository.repository_id }}</dd>
        </div>
        <div>
          <dt class="text-gray-500 dark:text-gray-400 text-sm mb-1">Root Path</dt>
          <dd class="font-mono text-sm">{{ repository.root_path }}</dd>
        </div>
        <div>
          <dt class="text-gray-500 dark:text-gray-400 text-sm mb-1">Origin URL</dt>
          <dd class="font-mono text-sm">{{ repository.origin_url }}</dd>
        </div>
        <div>
          <dt class="text-gray-500 dark:text-gray-400 text-sm mb-1">Default Branch</dt>
          <dd class="font-medium">{{ repository.default_branch }}</dd>
        </div>
        <div>
          <dt class="text-gray-500 dark:text-gray-400 text-sm mb-1">Status</dt>
          <dd
            :class="[
              'font-medium',
              repository.status === 'ready' ? 'text-green-600 dark:text-green-400' : 'text-yellow-500 dark:text-yellow-400'
            ]"
          >
            {{ repository.status }}
          </dd>
        </div>
        <div>
          <dt class="text-gray-500 dark:text-gray-400 text-sm mb-1">Last Seen</dt>
          <dd class="font-medium">{{ repository.last_seen_at.slice(0, 19) }}</dd>
        </div>
      </dl>
    </div>

    <section class="mb-8">
      <h2 class="text-xl font-medium mb-4">Workspaces</h2>
      <WorktreeTable :workspaces="workspaces" />
    </section>
  </div>

  <div v-else class="text-center text-gray-500 dark:text-gray-400 p-8">
    <p class="mb-4">Repository not found.</p>
    <RouterLink to="/repos">
      <AppButton>Back to Repositories</AppButton>
    </RouterLink>
  </div>
</template>
