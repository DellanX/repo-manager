<script setup lang="ts">
import { RouterView } from 'vue-router'
import { useInventoryStore } from '@/stores/inventory'
import { onMounted } from 'vue'
import { useDark, useToggle } from '@vueuse/core'
import { NavLink, StatusBadge } from '@/components/ui'

const inventoryStore = useInventoryStore()
const isDark = useDark()
const toggleDark = useToggle(isDark)

onMounted(() => {
  inventoryStore.fetchDashboard()
})
</script>

<template>
  <nav class="bg-white dark:bg-neutral-800 border-b border-gray-200 dark:border-neutral-700 px-8 py-4 flex items-center gap-4">
    <span class="font-semibold text-xl text-blue-600 dark:text-blue-400 mr-4">Repo Manager</span>
    <NavLink to="/">Dashboard</NavLink>
    <NavLink to="/repos">Repositories</NavLink>
    <NavLink to="/workspaces">Workspaces</NavLink>
    <NavLink to="/config/credentials">Credentials</NavLink>
    <NavLink to="/config/webhooks">Webhooks</NavLink>
    <div class="ml-auto">
      <StatusBadge :status="inventoryStore.healthStatus">
        {{ inventoryStore.healthStatus === 'healthy' ? 'Healthy' : 'Degraded' }}
      </StatusBadge>
    </div>
    <button
      class="bg-transparent text-gray-500 dark:text-gray-400 p-2 text-xl leading-none rounded cursor-pointer hover:text-gray-900 dark:hover:text-white border-none"
      @click="toggleDark()"
      title="Toggle dark mode"
      aria-label="Toggle dark mode"
    >
      <span>{{ isDark ? '☀️' : '🌙' }}</span>
    </button>
  </nav>
  <main class="p-8 max-w-7xl mx-auto">
    <RouterView />
  </main>
  <footer class="text-center p-4 text-gray-500 dark:text-gray-400 text-sm">
    <span v-if="inventoryStore.generatedAt">
      Generated at {{ inventoryStore.generatedAt.slice(0, 19) }} UTC
    </span>
  </footer>
</template>
