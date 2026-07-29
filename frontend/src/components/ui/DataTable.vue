<script setup lang="ts">
defineProps<{
  columns: string[]
}>()
</script>

<template>
  <div class="overflow-x-auto">
    <table
      class="w-full bg-white dark:bg-neutral-800 border border-gray-200 dark:border-neutral-700 rounded-lg"
    >
      <thead>
        <tr>
          <th
            v-for="col in columns"
            :key="col"
            class="px-4 py-3 text-left bg-gray-100 dark:bg-neutral-700 font-medium text-gray-500 dark:text-gray-400 border-b border-gray-200 dark:border-neutral-700 first:rounded-tl-lg last:rounded-tr-lg"
          >
            {{ col }}
          </th>
        </tr>
      </thead>
      <tbody class="divide-y divide-gray-200 dark:divide-neutral-700">
        <slot />
      </tbody>
    </table>
  </div>
</template>
