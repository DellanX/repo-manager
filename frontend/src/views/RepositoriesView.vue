<script setup lang="ts">
import { onMounted } from 'vue'
import { useInventoryStore } from '@/stores/inventory'
import { PageHeader, AppButton, DataTable, EmptyState } from '@/components/ui'

const store = useInventoryStore()

onMounted(() => {
  store.fetchInventory()
})

const columns = ['Name', 'Repository ID', 'Root Path', 'Origin URL', 'Default Branch', 'Status', 'Last Seen', 'Actions']
</script>

<template>
  <div>
    <PageHeader title="Repositories">
      <template #actions>
        <AppButton>Clone New</AppButton>
      </template>
    </PageHeader>

    <DataTable :columns="columns">
      <EmptyState v-if="store.repositories.length === 0" :colspan="8" message="No repositories found.">
        <AppButton class="ml-2">Clone your first repository</AppButton>
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
          <AppButton size="sm">Clone New</AppButton>
        </td>
      </tr>
    </DataTable>
  </div>
</template>
