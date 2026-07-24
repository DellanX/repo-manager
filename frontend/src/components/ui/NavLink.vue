<script setup lang="ts">
import { RouterLink } from 'vue-router'

defineProps<{
  to: string
}>()
</script>

<template>
  <RouterLink
    :to="to"
    class="text-gray-500 dark:text-gray-400 no-underline px-4 py-2 rounded transition-colors hover:bg-gray-100 dark:hover:bg-neutral-700 hover:text-gray-900 dark:hover:text-white [&.router-link-active]:bg-gray-100 dark:[&.router-link-active]:bg-neutral-700 [&.router-link-active]:text-gray-900 dark:[&.router-link-active]:text-white [&.router-link-active]:font-medium"
  >
    <slot />
  </RouterLink>
</template>
