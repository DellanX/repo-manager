<script setup lang="ts">
import { onMounted } from 'vue'
import { useInventoryStore } from '@/stores/inventory'
import WorktreeTable from '@/components/WorktreeTable.vue'
import { PageHeader, AppButton } from '@/components/ui'

const store = useInventoryStore()

onMounted(() => {
  store.fetchInventory()
})
</script>

<template>
  <div>
    <PageHeader title="Workspaces">
      <template #actions>
        <AppButton>Create Workspace</AppButton>
      </template>
    </PageHeader>

    <WorktreeTable :workspaces="store.workspaces" show-repository />
  </div>
</template>
