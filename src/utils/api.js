// API 请求工具
import { ElMessage } from 'element-plus'

const API_BASE_URL = 'http://localhost:8001/api/v1'

// 获取 token
const getToken = () => {
  return localStorage.getItem('access_token')
}

// 检查 token 是否过期
const isTokenExpired = () => {
  const tokenExpiry = localStorage.getItem('token_expiry')
  return !tokenExpiry || Date.now() > parseInt(tokenExpiry)
}

// 构建带参数的URL
const buildUrl = (url, params) => {
  if (!params) return url
  const searchParams = new URLSearchParams()
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null) {
      searchParams.append(key, value)
    }
  })
  const queryString = searchParams.toString()
  return queryString ? `${url}?${queryString}` : url
}

// 通用请求函数
const request = async (url, options = {}) => {
  try {
    // 检查 token 是否过期
    if (isTokenExpired()) {
      localStorage.removeItem('access_token')
      localStorage.removeItem('token_expiry')
      localStorage.removeItem('user')
      window.location.href = '/login'
      return
    }

    // 处理参数
    const { params, ...fetchOptions } = options
    const fullUrl = buildUrl(`${API_BASE_URL}${url}`, params)

    const response = await fetch(fullUrl, {
      ...fetchOptions,
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${getToken()}`,
        ...fetchOptions.headers
      }
    })

    const data = await response.json()

    if (!response.ok) {
      throw new Error(data.message || data.detail || '请求失败')
    }

    return data
  } catch (error) {
    ElMessage.error(error.message || '网络请求失败，请稍后重试')
    throw error
  }
}

// 认证相关 API
export const authApi = {
  // 登录
  login: (data) => request('/auth/login', {
    method: 'POST',
    body: JSON.stringify(data)
  }),
  
  // 注册
  register: (data) => request('/auth/register', {
    method: 'POST',
    body: JSON.stringify(data)
  }),
  
  // 忘记密码
  forgotPassword: (data) => request('/auth/forgot-password', {
    method: 'POST',
    body: JSON.stringify(data)
  }),
  
  // 重置密码
  resetPassword: (data) => request('/auth/reset-password', {
    method: 'POST',
    body: JSON.stringify(data)
  }),
  
  // 发送验证码
  sendVerificationCode: (data) => request('/auth/send-verification-code', {
    method: 'GET',
    params: data
  })
}

// 对话相关 API
export const chatApi = {
  // 发送消息
  sendMessage: (data) => request('/chat/message', {
    method: 'POST',
    body: JSON.stringify(data)
  }),
  
  // 创建新会话
  createSession: (data) => request('/chat/new-session', {
    method: 'POST',
    body: JSON.stringify(data)
  }),
  
  // 结束会话
  endSession: (data) => request('/chat/end-session', {
    method: 'POST',
    body: JSON.stringify(data)
  }),
  
  // 获取会话列表
  getSessions: (userId) => request('/chat/sessions', {
    params: { user_id: userId }
  }),
  
  // 获取对话历史
  getHistory: (userId, sessionId, limit = 50) => request('/chat/history', {
    params: { user_id: userId, session_id: sessionId, limit }
  })
}

// 报告相关 API
export const reportApi = {
  // 获取会话报告
  getSessionReport: (sessionId) => request(`/report/session/${sessionId}`),
  
  // 获取用户报告列表
  getUserReports: (userId) => request(`/report/user/${userId}`)
}

// 情绪日记相关 API
export const moodApi = {
  // 添加/更新情绪记录
  saveEntry: (data) => request('/mood/entry', {
    method: 'POST',
    body: JSON.stringify(data)
  }),
  
  // 获取日历数据
  getCalendar: (userId, year, month) => request('/mood/calendar', {
    params: { user_id: userId, year, month }
  }),
  
  // 获取情绪趋势
  getTrend: (userId, startDate, endDate) => request('/mood/trend', {
    params: { user_id: userId, start_date: startDate, end_date: endDate }
  })
}

// 问卷相关 API
export const questionnaireApi = {
  // 获取问卷列表
  getList: () => request('/questionnaire/list'),
  
  // 获取问卷详情
  getQuestionnaire: (id) => request(`/questionnaire/${id}`),
  
  // 提交问卷结果
  submit: (data) => request('/questionnaire/submit', {
    method: 'POST',
    body: JSON.stringify(data)
  }),
  
  // 获取问卷历史
  getHistory: (userId) => request('/questionnaire/history', {
    params: { user_id: userId }
  })
}

// 预警相关 API
export const alertApi = {
  // 获取预警列表
  getList: (userId) => request('/alert/list', {
    params: { user_id: userId }
  }),
  
  // 确认预警
  acknowledge: (alertId) => request('/alert/acknowledge', {
    method: 'POST',
    body: JSON.stringify({ alert_id: alertId })
  })
}

// 管理员相关 API
export const adminApi = {
  // 用户管理
  getUsers: (params) => request('/admin/users', {
    params
  }),
  
  addUser: (data) => request('/admin/users', {
    method: 'POST',
    body: JSON.stringify(data)
  }),
  
  updateUser: (id, data) => request(`/admin/users/${id}`, {
    method: 'PUT',
    body: JSON.stringify(data)
  }),
  
  deleteUser: (id) => request(`/admin/users/${id}`, {
    method: 'DELETE'
  }),
  
  // 策略管理
  getStrategies: (params) => request('/admin/strategies', {
    params
  }),
  
  addStrategy: (data) => request('/admin/strategies', {
    method: 'POST',
    body: JSON.stringify(data)
  }),
  
  updateStrategy: (id, data) => request(`/admin/strategies/${id}`, {
    method: 'PUT',
    body: JSON.stringify(data)
  }),
  
  deleteStrategy: (id) => request(`/admin/strategies/${id}`, {
    method: 'DELETE'
  }),
  
  // 日志管理
  getLogs: (params) => request('/admin/logs', {
    params
  })
}

export default {
  authApi,
  chatApi,
  reportApi,
  moodApi,
  questionnaireApi,
  alertApi,
  adminApi
}
