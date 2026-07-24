<script setup lang="ts">
import { useInventoryStore } from '@/stores/inventory'
import type { WorkspaceInfo } from '@/api/client'
import { DataTable, EmptyState, AppButton } from '@/components/ui'

defineProps<{
  workspaces: WorkspaceInfo[]
  showRepository?: boolean
}>()

const store = useInventoryStore()

async function handleSelect(workspaceId: string) {
  await store.selectWorkspace(workspaceId)
}

async function handleRemove(workspaceId: string) {
  if (confirm('Are you sure you want to remove this workspace?')) {
    await store.removeWorkspace(workspaceId)
  }
}
</script>

<template>
  <DataTable
    :columns="showRepository
      ? ['Workspace ID', 'Repository', 'Path', 'Branch', 'Dirty', 'Status', 'Last Seen', 'Actions']
      : ['Workspace ID', 'Path', 'Branch', 'Dirty', 'Status', 'Last Seen', 'Actions']"
  >
    <EmptyState v-if="workspaces.length === 0" :colspan="showRepository ? 8 : 7" message="No workspaces found.">
      <RouterLink to="/workspaces">
        <AppButton class="ml-2">Create your first workspace</AppButton>
      </RouterLink>
    </EmptyState>
    <tr
      v-for="ws in workspaces"
      :key="ws.workspace_id"
      class="hover:bg-gray-50 dark:hover:bg-neutral-700"
    >
      <td class="px-4 py-3">{{ ws.workspace_id }}</td>
      <td v-if="showRepository" class="px-4 py-3">
        <RouterLink :to="`/repos/${ws.repository_id}`" class="text-blue-600 dark:text-blue-400 hover:underline">
          {{ ws.repository_id }}
        </RouterLink>
      </td>
      <td class="px-4 py-3 font-mono text-sm max-w-xs truncate">{{ ws.path }}</td>
      <td class="px-4 py-3">{{ ws.branch }}</td>
      <td class="px-4 py-3">{{ ws.is_dirty ? 'Yes' : 'No' }}</td>
      <td
        :class="[
          'px-4 py-3',
          ws.status === 'ready' ? 'text-green-600 dark:text-green-400' : 'text-yellow-500 dark:text-yellow-400'
        ]"
      >
        {{ ws.status }}
      </td>
      <td class="px-4 py-3">{{ ws.last_seen_at.slice(0, 19) }}</td>
      <td class="px-4 py-3 space-x-1">
        <AppButton size="sm" @click="handleSelect(ws.workspace_id)">Select</AppButton>
        <AppButton size="sm" variant="danger" @click="handleRemove(ws.workspace_id)">Remove</AppButton>
      </td>
    </tr>
  </DataTable>
</template>
