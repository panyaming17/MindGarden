<template>
  <div class="admin-layout">
    <!-- 侧边栏 -->
    <div class="admin-sidebar">
      <div class="sidebar-header">
        <h2>后台管理</h2>
      </div>
      <div class="sidebar-menu">
        <div 
          class="menu-item" 
          :class="{ active: currentRoute === '/admin/users' }"
          @click="navigateTo('/admin/users')"
        >
          <span class="menu-icon">👥</span>
          <span>用户管理</span>
        </div>
        <div 
          class="menu-item" 
          :class="{ active: currentRoute === '/admin/rules' }"
          @click="navigateTo('/admin/rules')"
        >
          <span class="menu-icon">📋</span>
          <span>规则管理</span>
        </div>
        <div 
          class="menu-item" 
          :class="{ active: currentRoute === '/admin/audit-logs' }"
          @click="navigateTo('/admin/audit-logs')"
        >
          <span class="menu-icon">📊</span>
          <span>审计日志</span>
        </div>
        <!-- 可以添加更多菜单项 -->
      </div>
      <div class="sidebar-footer">
        <div class="user-info">
          <span>{{ userName }}</span>
          <button class="logout-button" @click="logout">退出登录</button>
        </div>
      </div>
    </div>
    
    <!-- 主内容区 -->
    <div class="admin-content">
      <div class="content-header">
        <h1>{{ pageTitle }}</h1>
      </div>
      <div class="content-body">
        <slot></slot>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const pageTitle = ref('后台管理系统')
// 获取管理员的用户名和角色
const userName = ref('')
const userRole = ref('')

// 计算当前路由
const currentRoute = computed(() => {
  return router.currentRoute.value.path
})

// 导航到指定路由
const navigateTo = (path) => {
  router.push(path)
}

// 退出登录
const logout = () => {
  localStorage.removeItem('access_token')
  localStorage.removeItem('user')
  localStorage.removeItem('token_expiry')
  router.push('/login')
}

// 加载用户信息
onMounted(() => {
  const storedUser = localStorage.getItem('user')
  if (storedUser) {
    try {
      const user = JSON.parse(storedUser)
      // 根据角色设置显示文本
      if (user.role === 'super_admin') {
        userRole.value = '超级管理员'
      } else if (user.role === 'admin') {
        userRole.value = '管理员'
      }
      // 显示用户名和角色
      userName.value = `${user.username || '管理员'} ${userRole.value}`
    } catch (error) {
      console.error('Failed to parse user data:', error)
    }
  }
})
</script>

<style scoped>
.admin-layout {
  display: flex;
  height: 100vh;
  background-color: #f5f5f5;
}

/* 侧边栏 */
.admin-sidebar {
  width: 200px;
  background-color: #333;
  color: white;
  display: flex;
  flex-direction: column;
}

.sidebar-header {
  padding: 20px;
  border-bottom: 1px solid #444;
}

.sidebar-header h2 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
}

.sidebar-menu {
  flex: 1;
  padding: 20px 0;
}

.menu-item {
  display: flex;
  align-items: center;
  padding: 12px 20px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.menu-item:hover {
  background-color: #444;
}

.menu-item.active {
  background-color: #007bff;
}

.menu-icon {
  margin-right: 10px;
  font-size: 16px;
}

.sidebar-footer {
  padding: 20px;
  border-top: 1px solid #444;
}

.user-info {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.logout-button {
  padding: 8px 12px;
  background-color: #dc3545;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  transition: background-color 0.3s ease;
}

.logout-button:hover {
  background-color: #c82333;
}

/* 主内容区 */
.admin-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.content-header {
  padding: 20px;
  background-color: white;
  border-bottom: 1px solid #e0e0e0;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.content-header h1 {
  margin: 0;
  font-size: 24px;
  font-weight: 600;
  color: #333;
}

.content-body {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .admin-sidebar {
    width: 160px;
  }
  
  .menu-item {
    padding: 10px 15px;
  }
  
  .content-header {
    padding: 15px;
  }
  
  .content-header h1 {
    font-size: 20px;
  }
  
  .content-body {
    padding: 15px;
  }
}
</style>