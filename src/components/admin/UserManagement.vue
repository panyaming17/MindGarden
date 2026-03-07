<template>
  <div class="user-management">
    <!-- 搜索和筛选 -->
    <div class="user-filters">
      <div class="search-box">
        <input 
          type="text" 
          v-model="searchQuery" 
          placeholder="搜索用户名或邮箱"
          class="search-input"
          @input="handleSearch"
        >
        <button class="search-button" @click="handleSearch">搜索</button>
      </div>
    </div>
    
    <!-- 用户列表 -->
    <div class="user-list">
      <table class="user-table">
        <thead>
          <tr>
            <th>ID</th>
            <th>用户名</th>
            <th>邮箱</th>
            <th>角色</th>
            <th>状态</th>
            <th>创建时间</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="user in users" :key="user.id">
            <td>{{ user.id }}</td>
            <td>{{ user.username }}</td>
            <td>{{ user.email }}</td>
            <td>{{ getRoleText(user.role) }}</td>
            <td>{{ user.is_active ? '活跃' : '禁用' }}</td>
            <td>{{ formatDate(user.created_at) }}</td>
            <td class="action-buttons">
              <button 
                class="edit-button" 
                @click="editUser(user)"
                :disabled="!canEditUser(user)"
              >
                编辑
              </button>
              <button 
                class="delete-button" 
                @click="deleteUser(user)"
                :disabled="!canDeleteUser(user)"
              >
                删除
              </button>
            </td>
          </tr>
        </tbody>
      </table>
      
      <!-- 空状态 -->
      <div v-if="users.length === 0" class="empty-state">
        暂无用户数据
      </div>
    </div>
    
    <!-- 分页 -->
    <div class="pagination">
      <button 
        class="page-button" 
        @click="changePage(page - 1)"
        :disabled="page === 1"
      >
        上一页
      </button>
      <span class="page-info">
        第 {{ page }} 页，共 {{ totalPages }} 页
      </span>
      <button 
        class="page-button" 
        @click="changePage(page + 1)"
        :disabled="page === totalPages"
      >
        下一页
      </button>
    </div>
    
    <!-- 编辑用户对话框 -->
    <div v-if="isEditDialogVisible" class="dialog-overlay" @click="closeEditDialog">
      <div class="dialog-content" @click.stop>
        <div class="dialog-header">
          <h3>编辑用户</h3>
          <button class="close-button" @click="closeEditDialog">×</button>
        </div>
        <div class="dialog-body">
          <div class="form-group">
            <label>用户名</label>
            <input 
              type="text" 
              v-model="editForm.username" 
              class="form-input"
              disabled
            >
          </div>
          <div class="form-group">
            <label>邮箱</label>
            <input 
              type="email" 
              v-model="editForm.email" 
              class="form-input"
              disabled
            >
          </div>
          <div class="form-group">
            <label>角色</label>
            <select 
              v-model="editForm.role" 
              class="form-select"
              :disabled="!canChangeRole"
            >
              <option value="user">普通用户</option>
              <option value="admin">管理员</option>
              <option value="super_admin" v-if="isSuperAdmin">超级管理员</option>
            </select>
          </div>
          <div class="form-group">
            <label>状态</label>
            <select v-model="editForm.is_active" class="form-select">
              <option value="true">活跃</option>
              <option value="false">禁用</option>
            </select>
          </div>
        </div>
        <div class="dialog-footer">
          <button class="cancel-button" @click="closeEditDialog">取消</button>
          <button class="save-button" @click="saveUser">保存</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'

// 响应式数据
const users = ref([])
const page = ref(1)
const perPage = ref(10)
const total = ref(0)
const searchQuery = ref('')
const isEditDialogVisible = ref(false)
const currentUser = ref(null)
const isSuperAdmin = ref(false)
const canChangeRole = ref(true)

// 编辑表单数据
const editForm = ref({
  username: '',
  email: '',
  role: '',
  is_active: true
})

// API基础URL
const API_BASE_URL = 'http://localhost:8001'

// 计算总页数
const totalPages = computed(() => {
  return Math.ceil(total.value / perPage.value)
})

// 获取角色文本
const getRoleText = (role) => {
  const roleMap = {
    'user': '普通用户',
    'admin': '管理员',
    'super_admin': '超级管理员'
  }
  return roleMap[role] || role
}

// 格式化日期
const formatDate = (dateString) => {
  if (!dateString) return ''
  const date = new Date(dateString)
  return date.toLocaleString('zh-CN')
}

// 检查是否可以编辑用户
const canEditUser = (user) => {
  if (user.role === 'super_admin' && !isSuperAdmin.value) {
    return false
  }
  return true
}

// 检查是否可以删除用户
const canDeleteUser = (user) => {
  if (user.role === 'super_admin' && !isSuperAdmin.value) {
    return false
  }
  return true
}

// 加载用户列表
const loadUsers = async () => {
  try {
    const token = localStorage.getItem('access_token')
    if (!token) {
      ElMessage.error('未登录或登录已过期')
      return
    }

    const url = `${API_BASE_URL}/api/admin/users?page=${page.value}&per_page=${perPage.value}&search=${encodeURIComponent(searchQuery.value)}`
    const response = await fetch(url, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    })

    if (!response.ok) {
      throw new Error('获取用户列表失败')
    }

    const data = await response.json()
    users.value = data.items
    total.value = data.total
  } catch (error) {
    console.error('Error loading users:', error)
    ElMessage.error(error.message || '获取用户列表失败')
    // 仅在开发环境使用模拟数据
    if (import.meta.env.DEV) {
      // 模拟数据
      users.value = [
        {
          id: 'user_c4ff00af9c2bc7d1',
          username: 'admin',
          email: 'admin@example.com',
          is_active: true,
          role: 'super_admin',
          created_at: '2026-03-03T01:16:07',
          updated_at: '2026-03-03T01:16:07'
        },
        {
          id: 'user_1234567890abcdef',
          username: 'user1',
          email: 'user1@example.com',
          is_active: true,
          role: 'user',
          created_at: '2026-03-02T10:00:00',
          updated_at: '2026-03-02T10:00:00'
        }
      ]
      total.value = 2
    }
  }
}

// 处理搜索
const handleSearch = () => {
  page.value = 1
  loadUsers()
}

// 切换页码
const changePage = (newPage) => {
  if (newPage < 1 || newPage > totalPages.value) {
    return
  }
  page.value = newPage
  loadUsers()
}

// 编辑用户
const editUser = (user) => {
  currentUser.value = user
  editForm.value = {
    username: user.username,
    email: user.email,
    role: user.role,
    is_active: user.is_active
  }
  canChangeRole.value = !(user.role === 'super_admin' && !isSuperAdmin.value)
  isEditDialogVisible.value = true
}

// 关闭编辑对话框
const closeEditDialog = () => {
  isEditDialogVisible.value = false
  currentUser.value = null
}

// 保存用户信息
const saveUser = async () => {
  if (!currentUser.value) return

  try {
    const token = localStorage.getItem('access_token')
    if (!token) {
      ElMessage.error('未登录或登录已过期')
      return
    }

    const url = `${API_BASE_URL}/api/admin/users/${currentUser.value.id}`
    const response = await fetch(url, {
      method: 'PATCH',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        role: editForm.value.role,
        is_active: editForm.value.is_active === 'true'
      })
    })

    if (!response.ok) {
      throw new Error('更新用户信息失败')
    }

    ElMessage.success('用户信息更新成功')
    closeEditDialog()
    loadUsers()
  } catch (error) {
    console.error('Error updating user:', error)
    ElMessage.error(error.message || '更新用户信息失败')
    // 仅在开发环境使用模拟数据
    if (import.meta.env.DEV) {
      ElMessage.success('模拟更新成功')
      closeEditDialog()
      loadUsers()
    }
  }
}

// 删除用户
const deleteUser = async (user) => {
  if (!confirm('确定要删除该用户吗？')) return

  try {
    const token = localStorage.getItem('access_token')
    if (!token) {
      ElMessage.error('未登录或登录已过期')
      return
    }

    const url = `${API_BASE_URL}/api/admin/users/${user.id}`
    const response = await fetch(url, {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    })

    if (!response.ok) {
      throw new Error('删除用户失败')
    }

    ElMessage.success('用户删除成功')
    loadUsers()
  } catch (error) {
    console.error('Error deleting user:', error)
    ElMessage.error(error.message || '删除用户失败')
    // 仅在开发环境使用模拟数据
    if (import.meta.env.DEV) {
      ElMessage.success('模拟删除成功')
      loadUsers()
    }
  }
}

// 检查当前用户是否为超级管理员
const checkUserRole = () => {
  const storedUser = localStorage.getItem('user')
  if (storedUser) {
    try {
      const user = JSON.parse(storedUser)
      isSuperAdmin.value = user.role === 'super_admin'
    } catch (error) {
      console.error('Failed to parse user data:', error)
    }
  }
}

// 初始化
onMounted(() => {
  checkUserRole()
  loadUsers()
})
</script>

<style scoped>
.user-management {
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  padding: 20px;
}

/* 搜索和筛选 */
.user-filters {
  margin-bottom: 20px;
}

.search-box {
  display: flex;
  gap: 10px;
}

.search-input {
  flex: 1;
  padding: 10px 15px;
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  font-size: 14px;
}

.search-button {
  padding: 10px 20px;
  background-color: #007bff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  transition: background-color 0.3s ease;
}

.search-button:hover {
  background-color: #0069d9;
}

/* 用户列表 */
.user-list {
  margin-bottom: 20px;
}

.user-table {
  width: 100%;
  border-collapse: collapse;
}

.user-table th,
.user-table td {
  padding: 12px;
  text-align: left;
  border-bottom: 1px solid #e0e0e0;
}

.user-table th {
  background-color: #f8f9fa;
  font-weight: 600;
  color: #333;
}

.user-table tr:hover {
  background-color: #f8f9fa;
}

.action-buttons {
  display: flex;
  gap: 10px;
}

.edit-button,
.delete-button {
  padding: 6px 12px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  transition: background-color 0.3s ease;
  font-size: 14px;
}

.edit-button {
  background-color: #28a745;
  color: white;
}

.edit-button:hover:not(:disabled) {
  background-color: #218838;
}

.delete-button {
  background-color: #dc3545;
  color: white;
}

.delete-button:hover:not(:disabled) {
  background-color: #c82333;
}

.edit-button:disabled,
.delete-button:disabled {
  background-color: #6c757d;
  cursor: not-allowed;
}

/* 空状态 */
.empty-state {
  text-align: center;
  padding: 40px;
  color: #6c757d;
  font-size: 16px;
}

/* 分页 */
.pagination {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
}

.page-button {
  padding: 8px 16px;
  background-color: #f8f9fa;
  border: 1px solid #dee2e6;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.page-button:hover:not(:disabled) {
  background-color: #e2e6ea;
  border-color: #dae0e5;
}

.page-button:disabled {
  background-color: #f8f9fa;
  border-color: #dee2e6;
  color: #6c757d;
  cursor: not-allowed;
}

.page-info {
  font-size: 14px;
  color: #6c757d;
}

/* 对话框 */
.dialog-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.dialog-content {
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  width: 90%;
  max-width: 500px;
  overflow: hidden;
}

.dialog-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px;
  border-bottom: 1px solid #e0e0e0;
}

.dialog-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #333;
}

.close-button {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: #6c757d;
  padding: 0;
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  transition: background-color 0.3s ease;
}

.close-button:hover {
  background-color: #f8f9fa;
}

.dialog-body {
  padding: 20px;
}

.form-group {
  margin-bottom: 15px;
}

.form-group label {
  display: block;
  margin-bottom: 5px;
  font-weight: 500;
  color: #333;
  font-size: 14px;
}

.form-input,
.form-select {
  width: 100%;
  padding: 10px;
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  font-size: 14px;
}

.form-input:disabled {
  background-color: #f8f9fa;
  cursor: not-allowed;
}

.dialog-footer {
  display: flex;
  gap: 10px;
  justify-content: flex-end;
  padding: 20px;
  border-top: 1px solid #e0e0e0;
  background-color: #f8f9fa;
}

.cancel-button,
.save-button {
  padding: 10px 20px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  transition: background-color 0.3s ease;
  font-size: 14px;
}

.cancel-button {
  background-color: #6c757d;
  color: white;
}

.cancel-button:hover {
  background-color: #5a6268;
}

.save-button {
  background-color: #007bff;
  color: white;
}

.save-button:hover {
  background-color: #0069d9;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .user-management {
    padding: 15px;
  }
  
  .user-table th,
  .user-table td {
    padding: 8px;
    font-size: 14px;
  }
  
  .action-buttons {
    flex-direction: column;
    gap: 5px;
  }
  
  .edit-button,
  .delete-button {
    padding: 4px 8px;
    font-size: 12px;
  }
  
  .dialog-content {
    width: 95%;
  }
  
  .dialog-header,
  .dialog-body,
  .dialog-footer {
    padding: 15px;
  }
}
</style>