<template>
  <div class="user-settings-page">
    <div class="page-header">
      <h1>设置</h1>
      <button class="back-button" @click="goBack">
        <el-icon><ArrowLeft /></el-icon> 返回
      </button>
    </div>
    
    <div class="settings-container">
      <!-- 登录设置 -->
      <div class="settings-section">
        <h3>登录设置</h3>
        <div class="settings-card">
          <h4>修改密码</h4>
          <el-form :model="passwordForm" label-width="120px" class="password-form">
            <el-form-item label="当前密码" prop="currentPassword">
              <el-input v-model="passwordForm.currentPassword" type="password" placeholder="请输入当前密码" />
            </el-form-item>
            <el-form-item label="新密码" prop="newPassword">
              <el-input v-model="passwordForm.newPassword" type="password" placeholder="请输入新密码" />
            </el-form-item>
            <el-form-item label="确认密码" prop="confirmPassword">
              <el-input v-model="passwordForm.confirmPassword" type="password" placeholder="请确认新密码" />
            </el-form-item>
            <div class="form-actions">
              <el-button @click="resetPasswordForm">重置</el-button>
              <el-button type="primary" @click="changePassword">修改密码</el-button>
            </div>
          </el-form>
        </div>
        
        <div class="settings-card">
          <h4>登录方式</h4>
          <div class="login-methods">
            <div class="login-method-item">
              <span class="method-name">邮箱登录</span>
              <span class="method-status">{{ user.email ? '已绑定' : '未绑定' }}</span>
              <el-button v-if="!user.email" size="small" @click="bindEmail">绑定邮箱</el-button>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 安全设置 -->
      <div class="settings-section">
        <h3>安全设置</h3>
        <div class="settings-card">
          <h4>账户安全</h4>
          <div class="security-item">
            <span class="item-name">登录保护</span>
            <el-switch v-model="securitySettings.loginProtection" />
            <span class="item-desc">开启后，新设备登录需要验证</span>
          </div>
          <div class="security-item">
            <span class="item-name">两步验证</span>
            <el-switch v-model="securitySettings.twoFactorAuth" />
            <span class="item-desc">开启后，登录需要验证码</span>
          </div>
          <div class="security-item">
            <span class="item-name">敏感操作验证</span>
            <el-switch v-model="securitySettings.sensitiveOperation" />
            <span class="item-desc">开启后，敏感操作需要验证</span>
          </div>
        </div>
        
        <div class="settings-card">
          <h4>登录历史</h4>
          <div v-if="loginHistory.length > 0" class="login-history-list">
            <div v-for="(item, index) in loginHistory" :key="index" class="login-history-item">
              <div class="history-info">
                <span class="history-device">{{ item.device }}</span>
                <span class="history-ip">{{ item.ip }}</span>
              </div>
              <div class="history-time">{{ formatDate(item.timestamp) }}</div>
            </div>
          </div>
          <div v-else class="empty-history">
            暂无登录历史
          </div>
        </div>
      </div>
      
      <!-- 系统设置 -->
      <div class="settings-section">
        <h3>系统设置</h3>
        <div class="settings-card">
          <h4>通知设置</h4>
          <div class="notification-item">
            <span class="item-name">邮件通知</span>
            <el-switch v-model="systemSettings.emailNotification" />
          </div>
          <div class="notification-item">
            <span class="item-name">短信通知</span>
            <el-switch v-model="systemSettings.smsNotification" />
          </div>
          <div class="notification-item">
            <span class="item-name">站内通知</span>
            <el-switch v-model="systemSettings.siteNotification" />
          </div>
        </div>
        
        <div class="settings-card">
          <h4>数据管理</h4>
          <div class="data-management">
            <el-button type="primary" @click="exportData">导出个人数据</el-button>
            <el-button type="danger" @click="clearCache">清除缓存</el-button>
            <el-button @click="resetSettings">重置所有设置</el-button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ArrowLeft } from '@element-plus/icons-vue'

export default {
  name: 'UserSettings',
  components: {
    ArrowLeft
  },
  setup() {
    const router = useRouter()
    const user = ref({})
    
    // 密码表单
    const passwordForm = ref({
      currentPassword: '',
      newPassword: '',
      confirmPassword: ''
    })
    
    // 安全设置
    const securitySettings = ref({
      loginProtection: false,
      twoFactorAuth: false,
      sensitiveOperation: true
    })
    
    // 系统设置
    const systemSettings = ref({
      emailNotification: true,
      smsNotification: false,
      siteNotification: true
    })
    
    // 登录历史
    const loginHistory = ref([
      {
        device: 'Chrome on Windows',
        ip: '192.168.1.1',
        timestamp: new Date().toISOString()
      },
      {
        device: 'Safari on Mac',
        ip: '192.168.1.2',
        timestamp: new Date(Date.now() - 86400000).toISOString()
      }
    ])
    
    // 加载用户数据
    const loadUserData = () => {
      const storedUser = localStorage.getItem('user')
      if (storedUser) {
        try {
          const parsedUser = JSON.parse(storedUser)
          user.value = {
            name: parsedUser.username || parsedUser.name,
            email: parsedUser.email
          }
        } catch (error) {
          console.error('加载用户数据失败:', error)
          user.value = {}
        }
      }
    }
    
    // 加载设置
    const loadSettings = () => {
      const storedSecuritySettings = localStorage.getItem('securitySettings')
      const storedSystemSettings = localStorage.getItem('systemSettings')
      
      if (storedSecuritySettings) {
        try {
          securitySettings.value = JSON.parse(storedSecuritySettings)
        } catch (error) {
          console.error('加载安全设置失败:', error)
        }
      }
      
      if (storedSystemSettings) {
        try {
          systemSettings.value = JSON.parse(storedSystemSettings)
        } catch (error) {
          console.error('加载系统设置失败:', error)
        }
      }
    }
    
    // 保存设置
    const saveSettings = () => {
      localStorage.setItem('securitySettings', JSON.stringify(securitySettings.value))
      localStorage.setItem('systemSettings', JSON.stringify(systemSettings.value))
      ElMessage.success('设置保存成功')
    }
    
    // 修改密码
    const changePassword = () => {
      if (!passwordForm.value.currentPassword) {
        ElMessage.warning('请输入当前密码')
        return
      }
      if (!passwordForm.value.newPassword) {
        ElMessage.warning('请输入新密码')
        return
      }
      if (passwordForm.value.newPassword !== passwordForm.value.confirmPassword) {
        ElMessage.error('两次输入的密码不一致')
        return
      }
      // 这里可以添加密码修改的API调用
      ElMessage.success('密码修改成功')
      resetPasswordForm()
    }
    
    // 重置密码表单
    const resetPasswordForm = () => {
      passwordForm.value = {
        currentPassword: '',
        newPassword: '',
        confirmPassword: ''
      }
    }
    
    // 绑定邮箱
    const bindEmail = () => {
      ElMessage.info('邮箱绑定功能开发中')
    }
    

    
    // 导出数据
    const exportData = () => {
      ElMessage.success('数据导出成功')
    }
    
    // 清除缓存
    const clearCache = () => {
      localStorage.removeItem('conversationCache')
      ElMessage.success('缓存清除成功')
    }
    
    // 重置所有设置
    const resetSettings = () => {
      if (confirm('确定要重置所有设置吗？')) {
        securitySettings.value = {
          loginProtection: false,
          twoFactorAuth: false,
          sensitiveOperation: true
        }
        systemSettings.value = {
          emailNotification: true,
          smsNotification: false,
          siteNotification: true
        }
        saveSettings()
        ElMessage.success('设置已重置')
      }
    }
    
    // 格式化日期
    const formatDate = (dateString) => {
      if (!dateString) return ''
      const date = new Date(dateString)
      return date.toLocaleString('zh-CN')
    }
    
    // 返回上一页
    const goBack = () => {
      router.back()
    }
    
    // 初始化
    onMounted(() => {
      loadUserData()
      loadSettings()
    })
    
    return {
      user,
      passwordForm,
      securitySettings,
      systemSettings,
      loginHistory,
      changePassword,
      resetPasswordForm,
      bindEmail,
      exportData,
      clearCache,
      resetSettings,
      formatDate,
      goBack,
      saveSettings
    }
  }
}
</script>

<style scoped>
.user-settings-page {
  padding: 20px;
  min-height: 100vh;
  background-color: #F9E0C9;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
  padding-bottom: 15px;
  border-bottom: 1px solid #e4e7ed;
}

.page-header h1 {
  margin: 0;
  font-size: 24px;
  color: #303133;
}

.back-button {
  display: flex;
  align-items: center;
  gap: 5px;
  color: #606266;
  transition: all 0.3s ease;
}

.back-button:hover {
  color: #4CAF50;
}

.settings-container {
  max-width: 800px;
  margin: 0 auto;
}

.settings-section {
  margin-bottom: 40px;
}

.settings-section h3 {
  margin: 0 0 20px;
  font-size: 16px;
  font-weight: 500;
  color: #303133;
  padding-bottom: 10px;
  border-bottom: 1px solid #e4e7ed;
}

.settings-card {
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  padding: 20px;
  margin-bottom: 20px;
}

.settings-card h4 {
  margin: 0 0 20px;
  font-size: 14px;
  font-weight: 500;
  color: #606266;
}

.password-form {
  margin-bottom: 20px;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 20px;
}

.login-methods {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.login-method-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 0;
  border-bottom: 1px solid #e4e7ed;
}

.login-method-item:last-child {
  border-bottom: none;
}

.method-name {
  font-size: 14px;
  color: #303133;
}

.method-status {
  font-size: 12px;
  color: #909399;
  margin-right: 10px;
}

.security-item,
.notification-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 0;
  border-bottom: 1px solid #e4e7ed;
}

.security-item:last-child,
.notification-item:last-child {
  border-bottom: none;
}

.item-name {
  font-size: 14px;
  color: #303133;
}

.item-desc {
  font-size: 12px;
  color: #909399;
  margin-left: 20px;
  flex: 1;
  text-align: right;
}

.login-history-list {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.login-history-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 0;
  border-bottom: 1px solid #e4e7ed;
}

.login-history-item:last-child {
  border-bottom: none;
}

.history-info {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.history-device {
  font-size: 14px;
  color: #303133;
}

.history-ip {
  font-size: 12px;
  color: #909399;
}

.history-time {
  font-size: 12px;
  color: #909399;
}

.empty-history {
  text-align: center;
  padding: 40px 0;
  color: #909399;
  font-size: 14px;
}

.data-management {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

@media (max-width: 768px) {
  .settings-card {
    padding: 15px;
  }
  
  .page-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }
  
  .login-method-item,
  .security-item,
  .notification-item {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }
  
  .item-desc {
    text-align: left;
    margin-left: 0;
  }
  
  .data-management {
    flex-direction: column;
  }
  
  .form-actions {
    flex-direction: column;
  }
}
</style>