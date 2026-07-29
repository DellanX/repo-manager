<script setup lang="ts">
defineProps<{
  message: string
  colspan?: number
}>()
</script>

<template>
  <tr>
    <td :colspan="colspan" class="text-center text-gray-500 dark:text-gray-400 p-8">
      {{ message }}
      <slot />
    </td>
  </tr>
</template>
