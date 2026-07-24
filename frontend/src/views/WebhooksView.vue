<script setup lang="ts">
import { PageHeader, AppButton, DataTable, EmptyState } from '@/components/ui'

const columns = ['Name', 'URL', 'Events', 'Status', 'Last Delivery', 'Actions']
</script>

<template>
  <div>
    <PageHeader title="Webhooks">
      <template #actions>
        <AppButton>Create Webhook</AppButton>
      </template>
    </PageHeader>

    <DataTable :columns="columns">
      <EmptyState :colspan="6" message="No webhooks configured.">
        <AppButton class="ml-2">Create your first webhook</AppButton>
      </EmptyState>
    </DataTable>

    <p class="mt-8 text-gray-500 dark:text-gray-400 text-sm">
      Webhooks notify external services when repository or workspace events occur.
    </p>
  </div>
</template>
