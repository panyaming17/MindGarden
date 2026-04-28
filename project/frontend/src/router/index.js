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
    path: '/questionnaire',
    name: 'questionnaire',
    component: HomePage,
    meta: { requiresAuth: true }
  },
  {
    path: '/mood',
    name: 'mood',
    component: HomePage,
    meta: { requiresAuth: true }
  },
     {
    path: '/RecordReport',
    name: 'RecordReport',
    component: () => import('@/components/reports/RecordReport.vue'),
    meta: { requiresAuth: true }
  },
     {
    path: '/AnalysisReport',
    name: 'AnalysisReport',
    component: () => import('@/components/reports/AnalysisReport.vue'),
    meta: { requiresAuth: true }
  },
     {
    path: '/SuggestionReport',
    name: 'SuggestionReport',
    component: () => import('@/components/reports/SuggestionReport.vue'),
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
  },
  {
    path: '/admin/alerts',
    name: 'adminAlerts',
    component: AdminPage,
    meta: { requiresAuth: true }
  },
  {
    path: '/admin/questionnaires',
    name: 'adminQuestionnaires',
    component: AdminPage,
    meta: { requiresAuth: true }
  },
  {
    path: '/alerts',
    name: 'alerts',
    component: HomePage,
    meta: { requiresAuth: true }
  },
  { path: '/reports', name: 'reports', component: HomePage, meta: { requiresAuth: true } },
  { path: '/user/profile', name: 'userProfile', component: () => import('@/components/user/UserProfile.vue'), meta: { requiresAuth: true } },
  { path: '/user/settings', name: 'userSettings', component: () => import('@/components/user/UserSettings.vue'), meta: { requiresAuth: true } }
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
    
    // 调试信息
    // console.log('路由守卫检查:', {
    //   path: to.path,
    //   hasToken: !!token,
    //   tokenExpiry: tokenExpiry,
    //   now: now,
    //   isValid: token && tokenExpiry && now < parseInt(tokenExpiry)
    // })
    
    // 更健壮的验证逻辑
    const expiryTime = parseInt(tokenExpiry) || 0
    const isTokenValid = token && expiryTime > 0 && now < expiryTime
    
    if (isTokenValid) {
      // token有效，允许访问
      next()
    } else {
      // token不存在或已过期，重定向到登录页面
      console.log('Token无效或已过期，重定向到登录页')
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