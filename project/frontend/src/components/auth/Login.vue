<template>
  <div class="login-container">
    <!-- 使用现有的背景组件 -->
    <BackGround />
    
    <!-- 登录表单卡片 -->
    <div class="login-card">
      <!-- 切换标签 -->
      <div class="login-tabs">
        <div 
          class="tab" 
          :class="{ active: activeTab === 'login' }"
          @click="activeTab = 'login'"
        >
          登录
        </div>
        <div 
          class="tab" 
          :class="{ active: activeTab === 'register' }"
          @click="activeTab = 'register'"
        >
          注册
        </div>
      </div>
      
      <!-- 登录表单 -->
      <div v-if="activeTab === 'login'" class="login-form">
        <h2 class="form-title">欢迎回来</h2>
        <p class="form-subtitle">请输入您的账号密码登录</p>
        
        <div class="form-group">
          <label for="login-username">用户名</label>
          <input 
            type="text" 
            id="login-username" 
            v-model="loginForm.username"
            placeholder="请输入用户名（中文或字母）"
            class="form-input"
            @input="validateUsername"
          >
          <div v-if="loginErrors.username" class="error-message">{{ loginErrors.username }}</div>
        </div>
        
        <div class="form-group">
          <div class="password-header">
            <label for="login-password">密码</label>
            <a href="#" class="forgot-password" @click.prevent="activeTab = 'reset'">忘记密码？</a>
          </div>
          <input 
            type="password" 
            id="login-password" 
            v-model="loginForm.password"
            placeholder="请输入密码（字母和数字组合）"
            class="form-input"
            @input="validatePassword"
          >
          <div v-if="loginErrors.password" class="error-message">{{ loginErrors.password }}</div>
        </div>
          <div class="ridio-container">
            <label class="radio-item">
              <input 
                type="radio" 
                v-model="loginForm.role"
                value="user"
              >
              <span>普通用户</span>
            </label>
            <label class="radio-item" style="margin-left: 20px;">
              <input 
                type="radio" 
                v-model="loginForm.role"
                value="admin"
              >
              <span>管理员</span>
            </label>
          </div>
        
        <el-button 
          type="primary" 
          class="login-button"
          @click="handleLogin"
          :loading="isLoading"
        >
          登录
        </el-button>
      </div>
      
      <!-- 注册表单 -->
      <div v-if="activeTab === 'register'" class="login-form">
        <h2 class="form-title">创建账号</h2>
        <p class="form-subtitle">填写以下信息注册新账号</p>
        
        <div class="form-group">
          <label for="register-username">用户名</label>
          <input 
            type="text" 
            id="register-username" 
            v-model="registerForm.username"
            placeholder="请输入用户名（中文或字母）"
            class="form-input"
            @input="validateRegisterUsername"
          >
          <div v-if="registerErrors.username" class="error-message">{{ registerErrors.username }}</div>
        </div>
        
        <div class="form-group">
          <label for="register-email">邮箱</label>
          <input 
            type="email" 
            id="register-email" 
            v-model="registerForm.email"
            placeholder="请输入邮箱"
            class="form-input"
            @input="validateEmail"
          >
          <div v-if="registerErrors.email" class="error-message">{{ registerErrors.email }}</div>
        </div>
        
        <div class="form-group">
          <label for="register-code">验证码</label>
          <div class="code-input-container">
            <input 
              type="text" 
              id="register-code" 
              v-model="registerForm.code"
              placeholder="请输入验证码"
              class="form-input code-input"
              @input="validateRegisterCode"
            >
            <button 
              type="button" 
              class="send-code-button"
              @click="sendRegisterCode"
              :disabled="registerCountdown > 0"
            >
              {{ registerCountdown > 0 ? `${registerCountdown}秒后重发` : '发送验证码' }}
            </button>
          </div>
          <div v-if="registerErrors.code" class="error-message">{{ registerErrors.code }}</div>
        </div>
        
        <div class="form-group">
          <label for="register-password">密码</label>
          <input 
            type="password" 
            id="register-password" 
            v-model="registerForm.password"
            placeholder="请输入密码（字母和数字组合，至少6位）"
            class="form-input"
            @input="validateRegisterPassword"
          >
          <div v-if="registerErrors.password" class="error-message">{{ registerErrors.password }}</div>
        </div>
        
        <div class="form-group">
          <label for="register-confirm-password">确认密码</label>
          <input 
            type="password" 
            id="register-confirm-password" 
            v-model="registerForm.confirmPassword"
            placeholder="请再次输入密码"
            class="form-input"
            @input="validateConfirmPassword"
          >
          <div v-if="registerErrors.confirmPassword" class="error-message">{{ registerErrors.confirmPassword }}</div>
        </div>
        
        <el-button 
          type="primary" 
          class="login-button"
          @click="handleRegister"
          :loading="isLoading"
        >
          注册
        </el-button>
      </div>
      
      <!-- 重置密码表单 -->
      <div v-if="activeTab === 'reset'" class="login-form">
        <h2 class="form-title">重置密码</h2>
        <p class="form-subtitle">请输入您的用户名重置密码</p>
        
        <div class="form-group">
          <label for="reset-username">用户名</label>
          <input 
            type="text" 
            id="reset-username" 
            v-model="resetForm.username"
            placeholder="请输入用户名（中文或字母）"
            class="form-input"
            @input="validateResetUsername"
          >
          <div v-if="resetErrors.username" class="error-message">{{ resetErrors.username }}</div>
        </div>
        
        <div class="form-group">
          <label for="reset-email">邮箱</label>
          <input 
            type="email" 
            id="reset-email" 
            v-model="resetForm.email"
            placeholder="请输入注册时的邮箱"
            class="form-input"
            @input="validateResetEmail"
          >
          <div v-if="resetErrors.email" class="error-message">{{ resetErrors.email }}</div>
        </div>
        
        <div class="form-group">
          <label for="reset-code">验证码</label>
          <div class="code-input-container">
            <input 
              type="text" 
              id="reset-code" 
              v-model="resetForm.code"
              placeholder="请输入验证码"
              class="form-input code-input"
              @input="validateResetCode"
            >
            <button 
              type="button" 
              class="send-code-button"
              @click="sendResetCode"
              :disabled="countdown > 0"
            >
              {{ countdown > 0 ? `${countdown}秒后重发` : '发送验证码' }}
            </button>
          </div>
          <div v-if="resetErrors.code" class="error-message">{{ resetErrors.code }}</div>
        </div>
        
        <div class="form-group">
          <label for="reset-new-password">新密码</label>
          <input 
            type="password" 
            id="reset-new-password" 
            v-model="resetForm.newPassword"
            placeholder="请输入新密码（字母和数字组合，至少6位）"
            class="form-input"
            @input="validateResetPassword"
          >
          <div v-if="resetErrors.password" class="error-message">{{ resetErrors.password }}</div>
        </div>
        
        <div class="button-container">
          <el-button 
            type="primary" 
            class="login-button"
            @click="handleResetPassword"
            :loading="isLoading"
          >
            重置密码
          </el-button>
          
          <el-button 
            type="info" 
            class="back-button"
            @click="activeTab = 'login'"
          >
            返回登录
          </el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, watch } from 'vue'
import { useRouter } from 'vue-router'
import BackGround from '../base/BackGround.vue'
import { ElMessage } from 'element-plus'

const router = useRouter()

// API基础URL
const API_BASE_URL = 'http://localhost:8000/api/v1/auth'

// 响应式数据
const activeTab = ref('login')
const isLoading = ref(false)

// 登录表单数据
const loginForm = reactive({
  username: '',
  password: '',
  role: '' // 默认普通用户
})

// 登录错误信息
const loginErrors = reactive({
  username: '',
  password: ''
})

// 注册表单数据
const registerForm = reactive({
  username: '',
  email: '',
  code: '',
  password: '',
  confirmPassword: ''
})

// 注册错误信息
const registerErrors = reactive({
  username: '',
  email: '',
  code: '',
  password: '',
  confirmPassword: ''
})

// 注册验证码倒计时
const registerCountdown = ref(0)

// 重置密码表单数据
const resetForm = reactive({
  username: '',
  email: '',
  code: '',
  newPassword: ''
})

// 重置密码错误信息
const resetErrors = reactive({
  username: '',
  email: '',
  code: '',
  password: ''
})

// 验证码倒计时
const countdown = ref(0)

// 监听activeTab变化，当切换到重置密码标签页时初始化表单
watch(() => activeTab.value, (newTab) => {
  if (newTab === 'reset') {
    // 初始化重置密码表单
    resetForm.username = ''
    resetForm.email = ''
    resetForm.code = ''
    resetForm.newPassword = ''
    
    // 清除错误信息
    resetErrors.username = ''
    resetErrors.email = ''
    resetErrors.code = ''
    resetErrors.password = ''
    
    // 重置倒计时
    countdown.value = 0
  }
})

// 验证用户名（中文或字母）
const validateUsername = () => {
  const username = loginForm.username.trim()
  if (!username) {
    loginErrors.username = '请输入用户名'
  } else if (!/^[\u4e00-\u9fa5a-zA-Z]+$/.test(username)) {
    loginErrors.username = '用户名只能包含中文或字母'
  } else {
    loginErrors.username = ''
  }
}

// 验证密码（字母和数字组合）
const validatePassword = () => {
  const password = loginForm.password
  // 如果用户选择的是管理员角色，不验证密码规范
  if (loginForm.role === 'admin') {
    if (!password) {
      loginErrors.password = '请输入密码'
    } else {
      loginErrors.password = ''
    }
    return
  }
  // 普通用户的密码验证
  if (!password) {
    loginErrors.password = '请输入密码'
  } else if (password.length < 6) {
    loginErrors.password = '密码长度至少为6位'
  } else if (!/(?=.*[a-zA-Z])(?=.*\d)/.test(password)) {
    loginErrors.password = '密码必须包含字母和数字'
  } else {
    loginErrors.password = ''
  }
}

// 验证注册用户名
const validateRegisterUsername = () => {
  const username = registerForm.username.trim()
  if (!username) {
    registerErrors.username = '请输入用户名'
  } else if (!/^[\u4e00-\u9fa5a-zA-Z]+$/.test(username)) {
    registerErrors.username = '用户名只能包含中文或字母'
  } else {
    registerErrors.username = ''
  }
}

// 验证邮箱
const validateEmail = () => {
  const email = registerForm.email.trim()
  if (!email) {
    registerErrors.email = '请输入邮箱'
  } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
    registerErrors.email = '请输入有效的邮箱地址'
  } else {
    registerErrors.email = ''
  }
}

// 验证注册密码
const validateRegisterPassword = () => {
  const password = registerForm.password
  if (!password) {
    registerErrors.password = '请输入密码'
  } else if (password.length < 6) {
    registerErrors.password = '密码长度至少为6位'
  } else if (!/(?=.*[a-zA-Z])(?=.*\d)/.test(password)) {
    registerErrors.password = '密码必须包含字母和数字'
  } else {
    registerErrors.password = ''
  }
  // 同时验证确认密码
  validateConfirmPassword()
}

// 验证确认密码
const validateConfirmPassword = () => {
  const confirmPassword = registerForm.confirmPassword
  if (!confirmPassword) {
    registerErrors.confirmPassword = '请确认密码'
  } else if (confirmPassword !== registerForm.password) {
    registerErrors.confirmPassword = '两次输入的密码不一致'
  } else {
    registerErrors.confirmPassword = ''
  }
}

// 验证注册验证码
const validateRegisterCode = () => {
  const code = registerForm.code.trim()
  if (!code) {
    registerErrors.code = '请输入验证码'
  } else if (!/^\d{6}$/.test(code)) {
    registerErrors.code = '验证码为6位数字'
  } else {
    registerErrors.code = ''
  }
}

// 发送注册验证码
const sendRegisterCode = async () => {
  // 验证邮箱
  validateEmail()
  
  if (registerErrors.email) {
    return
  }
  
  try {
    // 调用发送验证码API
    await request(`${API_BASE_URL}/send-verification-code`, {
      method: 'POST',
      body: JSON.stringify({
        email: registerForm.email,
        type:'register'
      })
    })
    
    ElMessage.success('验证码已发送，请查收')
    
    // 开始倒计时
    registerCountdown.value = 60
    const timer = setInterval(() => {
      registerCountdown.value--
      if (registerCountdown.value <= 0) {
        clearInterval(timer)
      }
    }, 1000)
  } catch (error) {
    if (error.message.includes('400')) {
      ElMessage.error('邮箱已被注册')
    } else {
      ElMessage.error(error.message || '发送验证码失败，请稍后重试')
    }
  }
}

// 验证重置用户名
const validateResetUsername = () => {
  const username = resetForm.username.trim()
  if (!username) {
    resetErrors.username = '请输入用户名'
  } else if (!/^[\u4e00-\u9fa5a-zA-Z]+$/.test(username)) {
    resetErrors.username = '用户名只能包含中文或字母'
  } else {
    resetErrors.username = ''
  }
}

// 验证重置密码
const validateResetPassword = () => {
  const password = resetForm.newPassword
  if (!password) {
    resetErrors.password = '请输入新密码'
  } else if (password.length < 6) {
    resetErrors.password = '密码长度至少为6位'
  } else if (!/(?=.*[a-zA-Z])(?=.*\d)/.test(password)) {
    resetErrors.password = '密码必须包含字母和数字'
  } else {
    resetErrors.password = ''
  }
}

// 验证重置邮箱
const validateResetEmail = () => {
  const email = resetForm.email.trim()
  if (!email) {
    resetErrors.email = '请输入邮箱'
  } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
    resetErrors.email = '请输入有效的邮箱地址'
  } else {
    resetErrors.email = ''
  }
}

// 验证重置验证码
const validateResetCode = () => {
  const code = resetForm.code.trim()
  if (!code) {
    resetErrors.code = '请输入验证码'
  } else if (!/^\d{6}$/.test(code)) {
    resetErrors.code = '验证码为6位数字'
  } else {
    resetErrors.code = ''
  }
}

// 发送重置验证码
const sendResetCode = async () => {
  // 验证用户名和邮箱
  validateResetUsername()
  validateResetEmail()
  
  if (resetErrors.username || resetErrors.email) {
    return
  }
  
  try {
    // 调用发送验证码API
    await request(`${API_BASE_URL}/forgot-password`, {
      method: 'POST',
      body: JSON.stringify({
        username: resetForm.username,
        email: resetForm.email
      })
    })
    
    ElMessage.success('验证码已发送，请查收')
    
    // 开始倒计时
    countdown.value = 60
    const timer = setInterval(() => {
      countdown.value--
      if (countdown.value <= 0) {
        clearInterval(timer)
      }
    }, 1000)
  } catch (error) {
    if (error.message.includes('404')) {
      ElMessage.error('用户名或邮箱错误')
    } else {
      ElMessage.error(error.message || '发送验证码失败，请稍后重试')
    }
  }
}

// 通用请求函数
const request = async (url, options = {}) => {
  try {
    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers
      }
    })

    const data = await response.json()

    if (!response.ok) {
      throw new Error(data.detail || '请求失败')
    }

    return data
  } catch (error) {
    throw error
  }
}

// 登录处理
const handleLogin = async () => {
  // 验证所有字段
  validateUsername()
  validatePassword()
  
  // 检查是否有错误
  if (loginErrors.username || loginErrors.password) {
    return
  }
  
  try {
    isLoading.value = true
    
    // 调用登录API
    const data = await request(`${API_BASE_URL}/login`, {
      method: 'POST',
      body: JSON.stringify({
        username: loginForm.username,
        password: loginForm.password,
      })
    })
  
    // 保存token到localStorage，并设置过期时间（24小时）
    localStorage.setItem('access_token', data.access_token)
    // 使用后端返回的用户信息，包括角色
    const userWithRole = {
      ...data.user
      // 移除角色覆盖，使用后端返回的角色信息
    }
    // 打印后端返回的参数到控制台
    // console.log('登录接口返回的参数:', data)
    // console.log('保存到localStorage的用户信息:', userWithRole)
    localStorage.setItem('user', JSON.stringify(userWithRole))
    const tokenExpiry = Date.now() + 24 * 60 * 60 * 1000 // 24小时过期
    localStorage.setItem('token_expiry', tokenExpiry.toString())
    
    // 登录成功
    ElMessage.success('登录成功')
    
    // 获取用户信息，根据角色跳转到不同页面
    const storedUser = localStorage.getItem('user')
    if (storedUser) {
      try {
        const user = JSON.parse(storedUser)
        if (user.role === 'super_admin' || user.role === 'admin') {
          // 跳转到后台页面
          router.push('/admin')
        } else {
          // 跳转到首页
          router.push('/')
        }
      } catch (error) {
        console.error('Failed to parse user data:', error)
        router.push('/')
      }
    } else {
      router.push('/')
    }
  } catch (error) {
    if (error.message.includes('401')) {
      ElMessage.error('用户名或密码错误')
    } else {
      ElMessage.error(error.message || '登录失败，请稍后重试')
    }
  } finally {
    isLoading.value = false
  }
}

// 注册处理
const handleRegister = async () => {
  // 验证所有字段
  validateRegisterUsername()
  validateEmail()
  validateRegisterCode()
  validateRegisterPassword()
  validateConfirmPassword()
  
  // 检查是否有错误
  if (registerErrors.username || registerErrors.email || registerErrors.code || registerErrors.password || registerErrors.confirmPassword) {
    return
  }
  
  try {
    isLoading.value = true
    
    // 调用注册API
    await request(`${API_BASE_URL}/register`, {
      method: 'POST',
      body: JSON.stringify({
        username: registerForm.username,
        email: registerForm.email,
        code: registerForm.code,
        password: registerForm.password,
        role:'user'
      })
    })
    
    // 注册成功
    ElMessage.success('注册成功，请登录')
    activeTab.value = 'login'
  } catch (error) {
    if (error.message.includes('400')) {
      if (error.message.includes('验证码')) {
        ElMessage.error('验证码错误或已过期')
      } else {
        ElMessage.error('用户名或邮箱已存在')
      }
    } else {
      ElMessage.error(error.message || '注册失败，请稍后重试')
    }
  } finally {
    isLoading.value = false
  }
}

// 重置密码处理
const handleResetPassword = async () => {
  // 验证所有字段
  validateResetUsername()
  validateResetEmail()
  validateResetCode()
  validateResetPassword()
  
  // 检查是否有错误
  if (resetErrors.username || resetErrors.email || resetErrors.code || resetErrors.password) {
    return
  }
  
  try {
    isLoading.value = true
    
    // 调用重置密码API
    await request(`${API_BASE_URL}/reset-password`, { 
      method: 'POST',
      body: JSON.stringify({
        username: resetForm.username,
        email: resetForm.email,
        code: resetForm.code,
        new_password: resetForm.newPassword
      })
    })
    
    // 重置成功
    ElMessage.success('密码重置成功，请登录')
    activeTab.value = 'login'
  } catch (error) {
    if (error.message.includes('404')) {
      ElMessage.error('用户不存在')
    } else if (error.message.includes('400')) {
      ElMessage.error('验证码错误或已过期')
    } else {
      ElMessage.error(error.message || '密码重置失败，请稍后重试')
    }
  } finally {
    isLoading.value = false
  }
}
</script>

<style scoped>
.login-container {
  position: relative;
  width: 100vw;
  height: 100vh;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
}

.login-card {
  position: relative;
  z-index: 10;
  background-color: rgba(255, 255, 255, 0.95);
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  backdrop-filter: blur(10px);
  padding: 30px;
  width: 100%;
  max-width: 400px;
}

.login-tabs {
  display: flex;
  margin-bottom: 30px;
  border-bottom: 1px solid #E0E0E0;
}

.tab {
  flex: 1;
  padding: 12px 0;
  text-align: center;
  cursor: pointer;
  font-size: 16px;
  color: #666;
  transition: all 0.3s ease;
  border-bottom: 2px solid transparent;
}

.tab.active {
  color: #4CAF50;
  border-bottom-color: #4CAF50;
  font-weight: 500;
}

.login-form {
  width: 100%;
}

.form-title {
  font-size: 24px;
  font-weight: 600;
  color: #333;
  margin-bottom: 8px;
  text-align: center;
}

.form-subtitle {
  font-size: 14px;
  color: #999;
  margin-bottom: 30px;
  text-align: center;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  font-size: 14px;
  font-weight: 500;
  color: #333;
  margin-bottom: 8px;
}

.form-input {
  width: 100%;
  padding: 12px 16px;
  border: 1px solid #E0E0E0;
  border-radius: 8px;
  font-size: 14px;
  transition: all 0.3s ease;
  background-color: rgba(255, 255, 255, 0.8);
}

.form-input:focus {
  outline: none;
  border-color: #4CAF50;
  box-shadow: 0 0 0 2px rgba(76, 175, 80, 0.1);
}

/* 错误信息样式 */
.error-message {
  font-size: 12px;
  color: #F56C6C;
  margin-top: 4px;
  min-height: 16px;
  line-height: 16px;
}

/* 验证码输入容器 */
.code-input-container {
  display: flex;
  gap: 10px;
  align-items: center;
}

.code-input {
  flex: 1;
}

.send-code-button {
  padding: 0 16px;
  height: 40px;
  background-color: #4CAF50;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.3s ease;
}

.send-code-button:hover:not(:disabled) {
  background-color: #45a049;
}

.send-code-button:disabled {
  background-color: #ccc;
  cursor: not-allowed;
}

.password-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.forgot-password {
  font-size: 12px;
  color: #4CAF50;
  text-decoration: none;
  transition: color 0.3s ease;
}

.forgot-password:hover {
  color: #45a049;
}

.login-button {
  width: 100%;
  padding: 14px 0;
  font-size: 16px;
  font-weight: 500;
  border-radius: 8px;
  margin-top: 10px;
  transition: all 0.3s ease;
}

.back-button {
  width: 100%;
  padding: 14px 0;
  font-size: 16px;
  margin-top: 10px;
  border-radius: 8px;
  transition: all 0.3s ease;
}

.button-container {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.button-container .login-button,
.button-container .back-button {
  margin-top: 0;
  margin-left: 0 !important;
}

/* 单选按钮组样式 */
.ridio-container{
  display: flex;
  margin-left: 5px;
  margin-bottom: 8px;
}

.radio-item {
  display: flex;
  align-items: center;
  /* gap: 6px; */
  cursor: pointer;
  font-size: 14px;
  color: #333;
}

.radio-item input[type="radio"] {
  width: 16px;
  height: 16px;
  cursor: pointer;
  display: flex;
  align-items: center;
}

.radio-item span{
  
  margin-left: 5px;
}

/* 响应式设计 */
@media (max-width: 480px) {
  .login-card {
    margin: 0 20px;
    padding: 20px;
  }
  
  .form-title {
    font-size: 20px;
  }
  
  .form-subtitle {
    font-size: 12px;
  }

}
</style>