<script setup lang="ts">
import { PageHeader, AppButton, DataTable, EmptyState } from '@/components/ui'

const columns = ['Name', 'Provider', 'Repository Bindings', 'Created', 'Actions']
</script>

<template>
  <div>
    <PageHeader title="Credentials">
      <template #actions>
        <AppButton>Add Credential</AppButton>
      </template>
    </PageHeader>

    <div
      class="bg-yellow-100 dark:bg-yellow-900/30 border border-yellow-400 dark:border-yellow-600 rounded px-4 py-3 mb-6 text-yellow-800 dark:text-yellow-200"
    >
      <strong>⚠️ Development Notice:</strong> This service is still in development and has not
      undergone security validation. Do not store production credentials.
    </div>

    <DataTable :columns="columns">
      <EmptyState :colspan="5" message="No credentials configured.">
        <AppButton class="ml-2">Add your first credential</AppButton>
      </EmptyState>
    </DataTable>

    <p class="mt-8 text-gray-500 dark:text-gray-400 text-sm">
      Credentials are used for authenticated Git operations and webhook delivery. Secret values are
      never displayed after creation.
    </p>
  </div>
</template>
