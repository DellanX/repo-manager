<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useInventoryStore } from '@/stores/inventory'
import WorktreeTable from '@/components/WorktreeTable.vue'
import { PageHeader, AppButton } from '@/components/ui'

const props = defineProps<{
  repositoryId: string
}>()

const store = useInventoryStore()
const fetchError = ref<string | null>(null)
const fetchSuccess = ref<string | null>(null)
const now = ref(Date.now())
let nowTimer: ReturnType<typeof setInterval> | null = null

const repository = computed(() => store.getRepositoryById(props.repositoryId))
const workspaces = computed(() => store.getWorkspacesByRepository(props.repositoryId))

function formatTimestamp(timestamp: string | null | undefined, emptyLabel: string): string {
  if (!timestamp) {
    return emptyLabel
  }
  const parsed = Date.parse(timestamp)
  if (Number.isNaN(parsed)) {
    return emptyLabel
  }
  const deltaSeconds = Math.max(0, Math.floor((now.value - parsed) / 1000))
  if (deltaSeconds < 60) {
    return `${deltaSeconds} second${deltaSeconds === 1 ? '' : 's'} ago`
  }
  const deltaMinutes = Math.floor(deltaSeconds / 60)
  if (deltaMinutes < 60) {
    return `${deltaMinutes} minute${deltaMinutes === 1 ? '' : 's'} ago`
  }
  const deltaHours = Math.floor(deltaMinutes / 60)
  if (deltaHours < 24) {
    return `${deltaHours} hour${deltaHours === 1 ? '' : 's'} ago`
  }
  const deltaDays = Math.floor(deltaHours / 24)
  if (deltaDays < 30) {
    return `${deltaDays} day${deltaDays === 1 ? '' : 's'} ago`
  }
  const deltaMonths = Math.floor(deltaDays / 30)
  if (deltaMonths < 12) {
    return `${deltaMonths} month${deltaMonths === 1 ? '' : 's'} ago`
  }
  const deltaYears = Math.floor(deltaDays / 365)
  return `${deltaYears} year${deltaYears === 1 ? '' : 's'} ago`
}

onMounted(() => {
  if (store.repositories.length === 0) {
    store.fetchInventory()
  }
  nowTimer = setInterval(() => {
    now.value = Date.now()
  }, 1000)
})

onUnmounted(() => {
  if (nowTimer) {
    clearInterval(nowTimer)
    nowTimer = null
  }
})

async function fetchLatest() {
  const repo = repository.value
  fetchError.value = null
  fetchSuccess.value = null
  if (!repo) {
    fetchError.value = 'Repository not found.'
    return
  }
  try {
    await store.fetchRepository(repo.repository_id)
    fetchSuccess.value = 'Repository fetch completed.'
  } catch (error) {
    fetchError.value = error instanceof Error ? error.message : 'Failed to fetch repository.'
  }
}
</script>

<template>
  <div v-if="repository">
    <PageHeader :title="repository.name">
      <template #actions>
        <RouterLink to="/repos">
          <AppButton>Clone New</AppButton>
        </RouterLink>
        <AppButton :disabled="store.loading" @click="fetchLatest()">Fetch</AppButton>
        <AppButton>Create Workspace</AppButton>
        <RouterLink to="/config/credentials">
          <AppButton>Manage Credentials</AppButton>
        </RouterLink>
        <RouterLink to="/config/webhooks">
          <AppButton>Manage Webhooks</AppButton>
        </RouterLink>
      </template>
    </PageHeader>

    <p v-if="fetchSuccess" class="mb-4 text-sm text-green-600 dark:text-green-400">{{ fetchSuccess }}</p>
    <p v-if="fetchError" class="mb-4 text-sm text-red-600 dark:text-red-400">{{ fetchError }}</p>

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
          <dd class="font-medium">
            <time :datetime="repository.last_seen_at" :title="repository.last_seen_at">
              {{ formatTimestamp(repository.last_seen_at, 'Unknown') }}
            </time>
          </dd>
        </div>
        <div>
          <dt class="text-gray-500 dark:text-gray-400 text-sm mb-1">Last Fetched</dt>
          <dd class="font-medium">
            <time
              v-if="repository.last_fetched_at"
              :datetime="repository.last_fetched_at"
              :title="repository.last_fetched_at"
            >
              {{ formatTimestamp(repository.last_fetched_at, 'Never') }}
            </time>
            <span v-else>Never</span>
          </dd>
        </div>
        <div>
          <dt class="text-gray-500 dark:text-gray-400 text-sm mb-1">Last Commit</dt>
          <dd class="font-medium">
            <time
              v-if="repository.last_commit_at"
              :datetime="repository.last_commit_at"
              :title="repository.last_commit_at"
            >
              {{ formatTimestamp(repository.last_commit_at, 'Unknown') }}
            </time>
            <span v-else>Unknown</span>
          </dd>
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
