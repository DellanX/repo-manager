<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { PageHeader, AppButton, DataTable, EmptyState } from '@/components/ui'
import {
  apiClient,
  type CredentialInfo,
  type CredentialProvider,
  type SecretDriverInfo,
  type SSHIdentityInfo
} from '@/api/client'

const credentialColumns = ['Name', 'Provider', 'Host', 'Username', 'Created', 'Status', 'Actions']
const sshColumns = ['Name', 'Host', 'Username', 'Identity File', 'Created', 'Status', 'Actions']

const credentials = ref<CredentialInfo[]>([])
const sshIdentities = ref<SSHIdentityInfo[]>([])
const drivers = ref<SecretDriverInfo[]>([])
const activeDriver = ref('')

const loading = ref(false)
const error = ref<string | null>(null)
const success = ref<string | null>(null)

const name = ref('')
const provider = ref<CredentialProvider>('gitlab')
const host = ref('gitlab.com')
const username = ref('oauth2')
const secret = ref('')

const sshName = ref('')
const sshHost = ref('gitlab.com')
const sshUsername = ref('git')

const canSubmitCredential = computed(() =>
  !loading.value &&
  name.value.trim().length > 0 &&
  host.value.trim().length > 0 &&
  username.value.trim().length > 0 &&
  secret.value.trim().length > 0
)

const canSubmitSshIdentity = computed(() =>
  !loading.value &&
  sshName.value.trim().length > 0 &&
  sshHost.value.trim().length > 0 &&
  sshUsername.value.trim().length > 0
)

function applyProviderDefaults(nextProvider: CredentialProvider) {
  if (nextProvider === 'gitlab') {
    host.value = 'gitlab.com'
    username.value = 'oauth2'
    return
  }
  if (nextProvider === 'azure_devops') {
    host.value = 'dev.azure.com'
    username.value = 'pat'
    return
  }
  if (nextProvider === 'github') {
    host.value = 'github.com'
    username.value = 'x-access-token'
  }
}

async function loadData() {
  loading.value = true
  error.value = null
  try {
    const [credentialItems, identityItems, driverData] = await Promise.all([
      apiClient.listCredentials(),
      apiClient.listSshIdentities(),
      apiClient.getCredentialDrivers()
    ])
    credentials.value = credentialItems
    sshIdentities.value = identityItems
    drivers.value = driverData.drivers
    activeDriver.value = driverData.active_driver
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'Failed to load credential data.'
  } finally {
    loading.value = false
  }
}

async function submitCredential() {
  if (!canSubmitCredential.value) {
    return
  }
  loading.value = true
  error.value = null
  success.value = null
  try {
    const created = await apiClient.createCredential({
      name: name.value.trim(),
      provider: provider.value,
      host: host.value.trim().toLowerCase(),
      username: username.value.trim(),
      secret: secret.value
    })
    credentials.value = [created, ...credentials.value]
    success.value = `Credential ${created.name} created.`
    name.value = ''
    secret.value = ''
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'Failed to create credential.'
  } finally {
    loading.value = false
  }
}

async function revokeCredential(credentialId: string) {
  loading.value = true
  error.value = null
  success.value = null
  try {
    const revoked = await apiClient.revokeCredential(credentialId)
    credentials.value = credentials.value.map((item) =>
      item.credential_id === credentialId ? revoked : item
    )
    success.value = `Credential ${revoked.name} revoked.`
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'Failed to revoke credential.'
  } finally {
    loading.value = false
  }
}

async function submitSshIdentity() {
  if (!canSubmitSshIdentity.value) {
    return
  }
  loading.value = true
  error.value = null
  success.value = null
  try {
    const created = await apiClient.createSshIdentity({
      name: sshName.value.trim(),
      host: sshHost.value.trim().toLowerCase(),
      username: sshUsername.value.trim()
    })
    sshIdentities.value = [created, ...sshIdentities.value]
    success.value = `SSH identity ${created.name} created.`
    sshName.value = ''
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'Failed to create SSH identity.'
  } finally {
    loading.value = false
  }
}

async function revokeSshIdentity(identityId: string) {
  loading.value = true
  error.value = null
  success.value = null
  try {
    const revoked = await apiClient.revokeSshIdentity(identityId)
    sshIdentities.value = sshIdentities.value.map((item) =>
      item.identity_id === identityId ? revoked : item
    )
    success.value = `SSH identity ${revoked.name} revoked.`
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'Failed to revoke SSH identity.'
  } finally {
    loading.value = false
  }
}

async function copyPublicKey(publicKey: string) {
  try {
    await navigator.clipboard.writeText(publicKey)
    success.value = 'Public key copied to clipboard.'
  } catch {
    error.value = 'Failed to copy public key.'
  }
}

onMounted(() => {
  loadData()
})
</script>

<template>
  <div>
    <PageHeader title="Credentials" />

    <div
      class="bg-yellow-100 dark:bg-yellow-900/30 border border-yellow-400 dark:border-yellow-600 rounded px-4 py-3 mb-6 text-yellow-800 dark:text-yellow-200"
    >
      <strong>⚠️ Development Notice:</strong> This service is still in development and has not
      undergone security validation. Do not store production credentials.
    </div>

    <div class="bg-white dark:bg-neutral-800 border border-gray-200 dark:border-neutral-700 rounded-lg p-4 mb-6">
      <h2 class="text-lg font-medium mb-2">Secret Driver</h2>
      <p class="text-sm mb-2">
        Active: <span class="font-mono">{{ activeDriver || 'unknown' }}</span>
      </p>
      <p class="text-sm text-gray-500 dark:text-gray-400">
        Available:
        <span v-for="driver in drivers" :key="driver.name" class="mr-2">
          {{ driver.name }}{{ driver.is_secure ? '' : ' (non-secure)' }}
        </span>
      </p>
    </div>

    <form
      class="bg-white dark:bg-neutral-800 border border-gray-200 dark:border-neutral-700 rounded-lg p-4 mb-6 space-y-4"
      @submit.prevent="submitCredential"
    >
      <h2 class="text-lg font-medium">Add Token Credential</h2>
      <div>
        <label for="credential-name" class="block text-sm font-medium mb-1">Name</label>
        <input
          id="credential-name"
          v-model="name"
          type="text"
          class="w-full rounded border border-gray-300 dark:border-neutral-600 bg-white dark:bg-neutral-900 px-3 py-2"
          placeholder="GitLab PAT for team repos"
        >
      </div>
      <div>
        <label for="credential-provider" class="block text-sm font-medium mb-1">Provider</label>
        <select
          id="credential-provider"
          v-model="provider"
          class="w-full rounded border border-gray-300 dark:border-neutral-600 bg-white dark:bg-neutral-900 px-3 py-2"
          @change="applyProviderDefaults(provider)"
        >
          <option value="gitlab">GitLab</option>
          <option value="azure_devops">Azure DevOps</option>
          <option value="github">GitHub</option>
          <option value="generic">Generic HTTPS Git</option>
        </select>
      </div>
      <div>
        <label for="credential-host" class="block text-sm font-medium mb-1">Host</label>
        <input
          id="credential-host"
          v-model="host"
          type="text"
          class="w-full rounded border border-gray-300 dark:border-neutral-600 bg-white dark:bg-neutral-900 px-3 py-2"
          placeholder="gitlab.com"
        >
      </div>
      <div>
        <label for="credential-username" class="block text-sm font-medium mb-1">Username</label>
        <input
          id="credential-username"
          v-model="username"
          type="text"
          class="w-full rounded border border-gray-300 dark:border-neutral-600 bg-white dark:bg-neutral-900 px-3 py-2"
          placeholder="oauth2"
        >
      </div>
      <div>
        <label for="credential-secret" class="block text-sm font-medium mb-1">Secret / Token</label>
        <input
          id="credential-secret"
          v-model="secret"
          type="password"
          class="w-full rounded border border-gray-300 dark:border-neutral-600 bg-white dark:bg-neutral-900 px-3 py-2"
          placeholder="Paste PAT or token"
          autocomplete="new-password"
        >
      </div>
      <AppButton type="submit" :disabled="!canSubmitCredential">Save Credential</AppButton>
    </form>

    <form
      class="bg-white dark:bg-neutral-800 border border-gray-200 dark:border-neutral-700 rounded-lg p-4 mb-6 space-y-4"
      @submit.prevent="submitSshIdentity"
    >
      <h2 class="text-lg font-medium">Generate SSH Identity</h2>
      <div>
        <label for="ssh-name" class="block text-sm font-medium mb-1">Name</label>
        <input
          id="ssh-name"
          v-model="sshName"
          type="text"
          class="w-full rounded border border-gray-300 dark:border-neutral-600 bg-white dark:bg-neutral-900 px-3 py-2"
          placeholder="GitLab Deploy Key"
        >
      </div>
      <div>
        <label for="ssh-host" class="block text-sm font-medium mb-1">Host</label>
        <input
          id="ssh-host"
          v-model="sshHost"
          type="text"
          class="w-full rounded border border-gray-300 dark:border-neutral-600 bg-white dark:bg-neutral-900 px-3 py-2"
          placeholder="gitlab.com"
        >
      </div>
      <div>
        <label for="ssh-username" class="block text-sm font-medium mb-1">SSH User</label>
        <input
          id="ssh-username"
          v-model="sshUsername"
          type="text"
          class="w-full rounded border border-gray-300 dark:border-neutral-600 bg-white dark:bg-neutral-900 px-3 py-2"
          placeholder="git"
        >
      </div>
      <AppButton type="submit" :disabled="!canSubmitSshIdentity">Generate SSH Keypair</AppButton>
    </form>

    <p v-if="error" class="mb-4 text-sm text-red-600 dark:text-red-400">{{ error }}</p>
    <p v-if="success" class="mb-4 text-sm text-green-600 dark:text-green-400">{{ success }}</p>

    <h2 class="text-lg font-medium mb-2">Token Credentials</h2>
    <DataTable :columns="credentialColumns">
      <EmptyState v-if="credentials.length === 0" :colspan="7" message="No credentials configured." />
      <tr
        v-for="credential in credentials"
        :key="credential.credential_id"
        class="hover:bg-gray-50 dark:hover:bg-neutral-700"
      >
        <td class="px-4 py-3">{{ credential.name }}</td>
        <td class="px-4 py-3">{{ credential.provider }}</td>
        <td class="px-4 py-3 font-mono text-sm">{{ credential.host }}</td>
        <td class="px-4 py-3 font-mono text-sm">{{ credential.username }}</td>
        <td class="px-4 py-3">{{ credential.created_at.slice(0, 19) }}</td>
        <td class="px-4 py-3">
          <span :class="credential.is_active ? 'text-green-600 dark:text-green-400' : 'text-gray-500 dark:text-gray-400'">
            {{ credential.is_active ? 'active' : 'revoked' }}
          </span>
        </td>
        <td class="px-4 py-3">
          <AppButton
            size="sm"
            variant="secondary"
            :disabled="loading || !credential.is_active"
            @click="revokeCredential(credential.credential_id)"
          >
            Revoke
          </AppButton>
        </td>
      </tr>
    </DataTable>

    <h2 class="text-lg font-medium mt-8 mb-2">SSH Identities</h2>
    <DataTable :columns="sshColumns">
      <EmptyState v-if="sshIdentities.length === 0" :colspan="7" message="No SSH identities configured." />
      <tr
        v-for="identity in sshIdentities"
        :key="identity.identity_id"
        class="hover:bg-gray-50 dark:hover:bg-neutral-700"
      >
        <td class="px-4 py-3">{{ identity.name }}</td>
        <td class="px-4 py-3 font-mono text-sm">{{ identity.host }}</td>
        <td class="px-4 py-3 font-mono text-sm">{{ identity.username }}</td>
        <td class="px-4 py-3 font-mono text-xs max-w-xs truncate">{{ identity.identity_file }}</td>
        <td class="px-4 py-3">{{ identity.created_at.slice(0, 19) }}</td>
        <td class="px-4 py-3">
          <span :class="identity.is_active ? 'text-green-600 dark:text-green-400' : 'text-gray-500 dark:text-gray-400'">
            {{ identity.is_active ? 'active' : 'revoked' }}
          </span>
        </td>
        <td class="px-4 py-3 space-x-2">
          <AppButton size="sm" variant="secondary" :disabled="!identity.is_active" @click="copyPublicKey(identity.public_key)">
            Copy Public Key
          </AppButton>
          <AppButton
            size="sm"
            variant="secondary"
            :disabled="loading || !identity.is_active"
            @click="revokeSshIdentity(identity.identity_id)"
          >
            Revoke
          </AppButton>
        </td>
      </tr>
    </DataTable>

    <p class="mt-8 text-gray-500 dark:text-gray-400 text-sm">
      Token secrets are stored through the configured secret driver; SSH private keys are stored as managed identity files under the service workspace.
    </p>
  </div>
</template>
