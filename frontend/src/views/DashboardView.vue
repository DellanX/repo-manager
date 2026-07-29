<script setup lang="ts">
import { useInventoryStore } from '@/stores/inventory'
import WorktreeTable from '@/components/WorktreeTable.vue'
import ActivityTable from '@/components/ActivityTable.vue'
import { PageHeader, AppButton, StatCard } from '@/components/ui'

const store = useInventoryStore()
</script>

<template>
  <div>
    <PageHeader title="Dashboard">
      <template #actions>
        <RouterLink to="/repos">
          <AppButton>Clone Repository</AppButton>
        </RouterLink>
        <RouterLink to="/workspaces">
          <AppButton>Create Workspace</AppButton>
        </RouterLink>
        <AppButton as="a" href="/config/credentials">Manage Credentials</AppButton>
        <AppButton as="a" href="/config/webhooks">Manage Webhooks</AppButton>
      </template>
    </PageHeader>

    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 mb-8">
      <StatCard label="Repositories" :value="store.counts.repositories" />
      <StatCard label="Workspaces" :value="store.counts.workspaces" />
      <StatCard
        label="Stale/Missing"
        :value="store.counts.staleOrMissing"
        :warning="store.counts.staleOrMissing > 0"
      />
    </div>

    <section class="mb-8">
      <h2 class="text-xl font-medium mb-4">Worktrees</h2>
      <WorktreeTable :workspaces="store.workspaces" />
    </section>

    <section class="mb-8">
      <h2 class="text-xl font-medium mb-4">Recent Activity</h2>
      <ActivityTable :activity="store.recentActivity" />
    </section>
  </div>
</template>
