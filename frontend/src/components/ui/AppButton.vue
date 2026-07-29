<script setup lang="ts">
defineProps<{
  variant?: 'primary' | 'danger' | 'secondary'
  size?: 'sm' | 'md'
  as?: 'button' | 'a'
}>()
</script>

<template>
  <component
    :is="as || 'button'"
    :class="[
      'inline-flex items-center justify-center rounded text-sm font-medium transition-colors cursor-pointer no-underline',
      size === 'sm' ? 'px-2 py-1' : 'px-3 py-1.5',
      variant === 'danger'
        ? 'bg-red-600 text-white hover:bg-red-700 dark:bg-red-500 dark:hover:bg-red-600'
        : variant === 'secondary'
          ? 'bg-gray-200 text-gray-900 hover:bg-gray-300 dark:bg-neutral-700 dark:text-white dark:hover:bg-neutral-600'
          : 'bg-blue-600 text-white hover:bg-blue-700 dark:bg-blue-500 dark:hover:bg-blue-600'
    ]"
  >
    <slot />
  </component>
</template>
