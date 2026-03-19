import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue')
  },
  {
    path: '/',
    component: () => import('@/layouts/Default.vue'),
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        name: 'Dashboard',
        component: () => import('@/views/Dashboard.vue')
      },
      {
        path: 'vms',
        name: 'VmList',
        component: () => import('@/views/VmList.vue')
      },
      {
        path: 'vms/create',
        name: 'VmCreate',
        component: () => import('@/views/VmCreate.vue')
      },
      {
        path: 'vms/:id',
        name: 'VmDetail',
        component: () => import('@/views/VmDetail.vue')
      },
      {
        path: 'vms/:id/snapshots',
        name: 'VmSnapshots',
        component: () => import('@/views/VmSnapshots.vue')
      },
      {
        path: 'hosts',
        name: 'Hosts',
        component: () => import('@/views/Hosts.vue')
      },
      {
        path: 'datastores',
        name: 'Datastores',
        component: () => import('@/views/Datastores.vue')
      },
      {
        path: 'networks',
        name: 'Networks',
        component: () => import('@/views/Networks.vue')
      },
      {
        path: 'tasks',
        name: 'Tasks',
        component: () => import('@/views/Tasks.vue')
      },
      {
        path: 'logs',
        name: 'Logs',
        component: () => import('@/views/Logs.vue')
      },
      {
        path: 'users',
        name: 'Users',
        component: () => import('@/views/Users.vue')
      },
      {
        path: 'settings',
        name: 'Settings',
        component: () => import('@/views/Settings.vue')
      },
      {
        path: 'topology',
        name: 'Topology',
        component: () => import('@/views/Topology.vue')
      },
      {
        path: 'portal',
        name: 'TenantPortal',
        component: () => import('@/views/TenantPortal.vue')
      }
    ]
  },
  {
    path: '/console/:vmId',
    name: 'Console',
    component: () => import('@/views/Console.vue'),
    meta: { requiresAuth: true }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()
  
  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    next('/login')
  } else if (to.path === '/login' && authStore.isAuthenticated) {
    next('/')
  } else {
    next()
  }
})

export default router
