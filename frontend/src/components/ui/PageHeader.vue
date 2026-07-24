<script setup lang="ts">
defineProps<{
  title: string
}>()
</script>

<template>
  <div class="mb-6">
    <h1 class="text-2xl font-semibold mb-4">{{ title }}</h1>
    <div v-if="$slots.actions" class="flex flex-wrap gap-4">
      <slot name="actions" />
    </div>
  </div>
</template>
