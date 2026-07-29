<script setup lang="ts">
defineProps<{
  status: 'healthy' | 'degraded' | 'success' | 'warning' | 'error'
}>()
</script>

<template>
  <span
    :class="[
      'px-3 py-1 rounded-full text-sm font-medium',
      status === 'healthy' || status === 'success'
        ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300'
        : status === 'error'
          ? 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300'
          : 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300'
    ]"
  >
    <slot />
  </span>
</template>
