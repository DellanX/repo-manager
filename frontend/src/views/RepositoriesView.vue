<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useInventoryStore } from '@/stores/inventory'
import { PageHeader, AppButton, DataTable, EmptyState } from '@/components/ui'
import { apiClient, type CredentialInfo, type SSHIdentityInfo } from '@/api/client'

const store = useInventoryStore()
const cloneUrl = ref('')
const cloneDestination = ref('')
const cloneCredentialId = ref('')
const cloneSshIdentityId = ref('')
const cloneError = ref<string | null>(null)
const cloneSuccess = ref<string | null>(null)
const scanSuccess = ref<string | null>(null)
const showCloneForm = ref(false)
const credentials = ref<CredentialInfo[]>([])
const sshIdentities = ref<SSHIdentityInfo[]>([])

const isCloneDisabled = computed(() => store.loading || cloneUrl.value.trim().length === 0)

onMounted(() => {
  store.fetchInventory()
  loadCredentials().catch(() => {
    cloneError.value = 'Unable to load credentials.'
  })
  loadSshIdentities().catch(() => {
    cloneError.value = 'Unable to load SSH identities.'
  })
})

const columns = ['Name', 'Repository ID', 'Root Path', 'Origin URL', 'Default Branch', 'Status', 'Last Seen', 'Actions']

function openCloneForm(originUrl?: string) {
  showCloneForm.value = true
  cloneError.value = null
  cloneSuccess.value = null
  cloneUrl.value = originUrl || ''
  cloneDestination.value = ''
  cloneCredentialId.value = ''
  cloneSshIdentityId.value = ''
}

async function loadCredentials() {
  credentials.value = await apiClient.listCredentials()
}

async function loadSshIdentities() {
  sshIdentities.value = await apiClient.listSshIdentities()
}

function onCredentialChange() {
  if (cloneCredentialId.value) {
    cloneSshIdentityId.value = ''
  }
}

function onSshIdentityChange() {
  if (cloneSshIdentityId.value) {
    cloneCredentialId.value = ''
  }
}

async function submitClone() {
  const url = cloneUrl.value.trim()
  if (!url) {
    cloneError.value = 'Repository URL is required.'
    return
  }

  cloneError.value = null
  cloneSuccess.value = null

  try {
    await store.cloneRepository(
      url,
      cloneDestination.value.trim() || undefined,
      cloneCredentialId.value || undefined,
      cloneSshIdentityId.value || undefined
    )
    cloneSuccess.value = `Clone started for ${url}`
    cloneUrl.value = ''
    cloneDestination.value = ''
    cloneCredentialId.value = ''
    cloneSshIdentityId.value = ''
    showCloneForm.value = false
  } catch (error) {
    cloneError.value = error instanceof Error ? error.message : 'Failed to clone repository.'
  }
}

async function rescanRepositories() {
  cloneError.value = null
  cloneSuccess.value = null
  scanSuccess.value = null

  try {
    await store.rescanInventory(['/workspace/repos', '/workspace/worktrees'])
    scanSuccess.value = 'Inventory scan completed.'
  } catch (error) {
    cloneError.value = error instanceof Error ? error.message : 'Failed to rescan inventory.'
  }
}
</script>

<template>
  <div>
    <PageHeader title="Repositories">
      <template #actions>
        <AppButton variant="secondary" :disabled="store.loading" @click="rescanRepositories()">
          Scan Repos/Worktrees
        </AppButton>
        <AppButton :disabled="store.loading" @click="openCloneForm()">Clone New</AppButton>
      </template>
    </PageHeader>

    <form
      v-if="showCloneForm"
      class="bg-white dark:bg-neutral-800 border border-gray-200 dark:border-neutral-700 rounded-lg p-4 mb-6 space-y-4"
      @submit.prevent="submitClone"
    >
      <h2 class="text-lg font-medium">Clone Repository</h2>
      <div>
        <label for="clone-url" class="block text-sm font-medium mb-1">Repository URL</label>
        <input
          id="clone-url"
          v-model="cloneUrl"
          type="text"
          class="w-full rounded border border-gray-300 dark:border-neutral-600 bg-white dark:bg-neutral-900 px-3 py-2"
          placeholder="https://github.com/org/repo.git"
        >
      </div>
      <div>
        <label for="clone-credential" class="block text-sm font-medium mb-1">Credential (optional)</label>
        <select
          id="clone-credential"
          v-model="cloneCredentialId"
          class="w-full rounded border border-gray-300 dark:border-neutral-600 bg-white dark:bg-neutral-900 px-3 py-2"
          @change="onCredentialChange"
        >
          <option value="">None</option>
          <option
            v-for="credential in credentials.filter((item) => item.is_active)"
            :key="credential.credential_id"
            :value="credential.credential_id"
          >
            {{ credential.name }} ({{ credential.provider }} @ {{ credential.host }})
          </option>
        </select>
      </div>
      <div>
        <label for="clone-ssh-identity" class="block text-sm font-medium mb-1">SSH Identity (optional)</label>
        <select
          id="clone-ssh-identity"
          v-model="cloneSshIdentityId"
          class="w-full rounded border border-gray-300 dark:border-neutral-600 bg-white dark:bg-neutral-900 px-3 py-2"
          @change="onSshIdentityChange"
        >
          <option value="">None</option>
          <option
            v-for="identity in sshIdentities.filter((item) => item.is_active)"
            :key="identity.identity_id"
            :value="identity.identity_id"
          >
            {{ identity.name }} ({{ identity.username }}@{{ identity.host }})
          </option>
        </select>
      </div>
      <div>
        <label for="clone-destination" class="block text-sm font-medium mb-1">Destination (optional)</label>
        <input
          id="clone-destination"
          v-model="cloneDestination"
          type="text"
          class="w-full rounded border border-gray-300 dark:border-neutral-600 bg-white dark:bg-neutral-900 px-3 py-2"
          placeholder="repos/my-repo-copy"
        >
      </div>
      <div class="flex flex-wrap gap-2">
        <AppButton type="submit" :disabled="isCloneDisabled">Clone</AppButton>
        <AppButton
          type="button"
          variant="secondary"
          :disabled="store.loading"
          @click="showCloneForm = false"
        >
          Cancel
        </AppButton>
      </div>
      <p v-if="cloneError" class="text-sm text-red-600 dark:text-red-400">{{ cloneError }}</p>
    </form>

    <p v-if="cloneSuccess" class="mb-4 text-sm text-green-600 dark:text-green-400">{{ cloneSuccess }}</p>
    <p v-if="scanSuccess" class="mb-4 text-sm text-green-600 dark:text-green-400">{{ scanSuccess }}</p>

    <DataTable :columns="columns">
      <EmptyState v-if="store.repositories.length === 0" :colspan="8" message="No repositories found.">
        <AppButton class="ml-2" :disabled="store.loading" @click="openCloneForm()">
          Clone your first repository
        </AppButton>
      </EmptyState>
      <tr
        v-for="repo in store.repositories"
        :key="repo.repository_id"
        class="hover:bg-gray-50 dark:hover:bg-neutral-700"
      >
        <td class="px-4 py-3">{{ repo.name }}</td>
        <td class="px-4 py-3">{{ repo.repository_id }}</td>
        <td class="px-4 py-3 font-mono text-sm max-w-xs truncate">{{ repo.root_path }}</td>
        <td class="px-4 py-3 font-mono text-sm max-w-xs truncate">{{ repo.origin_url }}</td>
        <td class="px-4 py-3">{{ repo.default_branch }}</td>
        <td
          :class="[
            'px-4 py-3',
            repo.status === 'ready' ? 'text-green-600 dark:text-green-400' : 'text-yellow-500 dark:text-yellow-400'
          ]"
        >
          {{ repo.status }}
        </td>
        <td class="px-4 py-3">{{ repo.last_seen_at.slice(0, 19) }}</td>
        <td class="px-4 py-3 space-x-1">
          <RouterLink :to="`/repos/${repo.repository_id}`">
            <AppButton size="sm">View</AppButton>
          </RouterLink>
          <AppButton
            size="sm"
            :disabled="store.loading"
            @click="openCloneForm(repo.origin_url)"
          >
            Clone New
          </AppButton>
        </td>
      </tr>
    </DataTable>
  </div>
</template>
