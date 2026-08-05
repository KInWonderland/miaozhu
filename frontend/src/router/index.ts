import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'
import { authApi } from '@/api'

const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/LoginView.vue'),
    meta: { public: true, title: '登录' },
  },
  {
    path: '/',
    redirect: '/copyright',
  },
  {
    path: '/',
    component: () => import('@/layouts/MainLayout.vue'),
    children: [
      {
        path: 'copyright',
        name: 'CopyrightList',
        component: () => import('@/views/copyright/CopyrightListView.vue'),
        meta: { title: '软著申请' },
      },
      {
        path: 'copyright/new',
        name: 'CopyrightNew',
        component: () => import('@/views/copyright/CopyrightNewView.vue'),
        meta: { title: '新建申请' },
      },
      {
        path: 'copyright/:id',
        name: 'CopyrightGenerate',
        component: () => import('@/views/copyright/CopyrightGenerateView.vue'),
        meta: { title: 'AI 生成' },
      },
      {
        path: 'copyright/:id/edit',
        name: 'CopyrightEdit',
        component: () => import('@/views/copyright/CopyrightEditView.vue'),
        meta: { title: '编辑申请信息' },
      },
    ],
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/copyright',
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

function safeRedirect(value: unknown): string {
  return typeof value === 'string' && value.startsWith('/') && !value.startsWith('//')
    ? value
    : '/copyright'
}

router.beforeEach(async (to) => {
  const isPublic = to.matched.some((record) => record.meta.public)

  try {
    await authApi.getCurrentUser()
    if (to.name === 'Login') {
      return safeRedirect(to.query.redirect)
    }
    return true
  } catch {
    if (isPublic) {
      return true
    }
    return {
      name: 'Login',
      query: { redirect: to.fullPath },
    }
  }
})

export default router
