<script setup lang="ts">
defineProps<{
  label: string
  value: string | number
  warning?: boolean
}>()
</script>

<template>
  <div
    class="bg-white dark:bg-neutral-800 border border-gray-200 dark:border-neutral-700 rounded-lg p-6"
  >
    <h3 class="text-gray-500 dark:text-gray-400 text-sm font-medium mb-2">{{ label }}</h3>
    <div :class="['text-4xl font-semibold', warning ? 'text-yellow-500 dark:text-yellow-400' : '']">
      {{ value }}
    </div>
  </div>
</template>
