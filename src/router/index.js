import { createRouter, createWebHistory } from 'vue-router'
import HomePage from '../views/HomePage.vue'
import AdminPage from '../views/AdminPage.vue'

const routes = [
  {
    path: '/',
    name: 'home',
    component: HomePage,
    meta: { requiresAuth: true }
  },
  {
    path: '/login',
    name: 'login',
    component: () => import('@/components/auth/Login.vue')
  },
  {
    path: '/conversation',
    name: 'conversation',
    component: () => import('@/components/chat/ChatApp.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/multi-agent-test',
    name: 'multiAgentTest',
    component: () => import('@/components/MultiAgentTest/MultiAgentTest.vue'),
    meta: { requiresAuth: true }
  },
   {
    path: '/questionnaire',
    name: 'questionnaire',
    component: () => import('@/components/Questionnaire/MentalQuestionnaire.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/admin',
    name: 'admin',
    component: AdminPage,
    meta: { requiresAuth: true }
  },
  {
    path: '/admin/users',
    name: 'adminUsers',
    component: AdminPage,
    meta: { requiresAuth: true }
  },
  {
    path: '/admin/rules',
    name: 'adminRules',
    component: AdminPage,
    meta: { requiresAuth: true }
  },
  {
    path: '/admin/audit-logs',
    name: 'adminAuditLogs',
    component: AdminPage,
    meta: { requiresAuth: true }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫
router.beforeEach((to, from, next) => {
  // 检查路由是否需要认证
  if (to.meta.requiresAuth) {
    // 检查token是否存在且未过期
    const token = localStorage.getItem('access_token')
    const tokenExpiry = localStorage.getItem('token_expiry')
    const now = Date.now()
    
    if (token && tokenExpiry && now < parseInt(tokenExpiry)) {
      // token有效，允许访问
      next()
    } else {
      // token不存在或已过期，重定向到登录页面
      localStorage.removeItem('access_token')
      localStorage.removeItem('token_expiry')
      localStorage.removeItem('user')
      next('/login')
    }
  } else {
    // 不需要认证的路由，直接访问
    next()
  }
})

export default router