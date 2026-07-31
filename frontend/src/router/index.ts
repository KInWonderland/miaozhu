import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
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

export default router
