import { createRouter, createWebHistory } from 'vue-router'
import DashboardView from '@/views/DashboardView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'dashboard',
      component: DashboardView
    },
    {
      path: '/repos',
      name: 'repositories',
      component: () => import('@/views/RepositoriesView.vue')
    },
    {
      path: '/repos/:repositoryId',
      name: 'repository-detail',
      component: () => import('@/views/RepositoryDetailView.vue'),
      props: true
    },
    {
      path: '/workspaces',
      name: 'workspaces',
      component: () => import('@/views/WorkspacesView.vue')
    },
    {
      path: '/config/credentials',
      name: 'credentials',
      component: () => import('@/views/CredentialsView.vue')
    },
    {
      path: '/config/webhooks',
      name: 'webhooks',
      component: () => import('@/views/WebhooksView.vue')
    }
  ]
})

export default router
