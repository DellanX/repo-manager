<script setup lang="ts">
import type { ActivityItem } from '@/api/client'
import { DataTable, EmptyState } from '@/components/ui'

defineProps<{
  activity: ActivityItem[]
}>()
</script>

<template>
  <DataTable :columns="['Time', 'Operation', 'Status']">
    <EmptyState v-if="activity.length === 0" :colspan="3" message="No recent activity" />
    <tr
      v-for="item in activity.slice(0, 10)"
      :key="item.id"
      class="hover:bg-gray-50 dark:hover:bg-neutral-700"
    >
      <td class="px-4 py-3">{{ item.timestamp.slice(0, 19) }}</td>
      <td class="px-4 py-3">{{ item.operation }}</td>
      <td
        :class="[
          'px-4 py-3',
          item.status === 'completed' ? 'text-green-600 dark:text-green-400' : 'text-blue-600 dark:text-blue-400'
        ]"
      >
        {{ item.status }}
      </td>
    </tr>
  </DataTable>
</template>
