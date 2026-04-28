import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import axios from 'axios'

const API_BASE = '/api'

export interface Alert {
  id: string
  user_id: string
  username?: string
  type: 'questionnaire' | 'emotion' | 'conversation'
  level: 'info' | 'warning' | 'danger'
  title: string
  message: string
  is_acknowledged: boolean
  acknowledged_by?: string
  acknowledged_at?: string
  created_at: string
  source_data?: any
}

export interface AlertStats {
  total: number
  acknowledged: number
  unacknowledged: number
  by_type: {
    questionnaire: number
    emotion: number
    conversation: number
  }
  by_level: {
    info: number
    warning: number
    danger: number
  }
  trend: Record<string, number>
  avg_response_time_hours: number
}

export interface HighRiskUser {
  user_id: string
  username: string
  email: string
  alert_count: number
  danger_count: number
}

export interface UserAlertProfile {
  user_info: {
    id: string
    username: string
    email: string
    created_at: string
  }
  alert_summary: {
    total: number
    unacknowledged: number
    by_type: Record<string, number>
    by_level: Record<string, number>
  }
  emotion_trend: Array<{
    date: string
    emotion: string
    type: string
  }>
  questionnaire_history: Array<{
    date: string
    template_code: string
    score: number
    result_level: string
  }>
  recent_alerts: Array<{
    id: string
    title: string
    level: string
    created_at: string
  }>
  risk_assessment: string
}

export const useAdminAlertStore = defineStore('adminAlert', () => {
  // State
  const alerts = ref<Alert[]>([])
  const total = ref(0)
  const stats = ref<AlertStats | null>(null)
  const highRiskUsers = ref<HighRiskUser[]>([])
  const userProfile = ref<UserAlertProfile | null>(null)
  const isLoading = ref(false)
  const currentPage = ref(1)
  const pageSize = ref(20)

  // Getters
  const dangerAlerts = computed(() => alerts.value.filter(a => a.level === 'danger'))
  const unacknowledgedAlerts = computed(() => alerts.value.filter(a => !a.is_acknowledged))

  // 获取用户ID
  const getUserId = () => {
    // 首先尝试从 user 对象获取
    const userStr = localStorage.getItem('user')
    // console.log('getUserId - userStr:', userStr)
    if (userStr) {
      try {
        const user = JSON.parse(userStr)
        // console.log('getUserId - parsed user:', user)
        const userId = user.id || user.user_id
        if (userId) {
          // console.log('getUserId - returning from user:', userId)
          return userId
        }
      } catch (e) {
        console.error('Parse user error:', e)
      }
    }
    
    // 备用：从 token 中解析
    const token = localStorage.getItem('access_token')
    if (token) {
      try {
        // JWT token 的 payload 在第二部分
        const payload = JSON.parse(atob(token.split('.')[1]))
        // console.log('getUserId - parsed from token:', payload)
        return payload.sub || payload.user_id || null
      } catch (e) {
        console.error('Parse token error:', e)
      }
    }
    
    console.log('getUserId - returning null')
    return null
  }

  // Actions
  const getAllAlerts = async (filters: any = {}) => {
    isLoading.value = true
    try {
      const adminId = getUserId()
      const params = new URLSearchParams({
        admin_id: adminId || '',
        page: String(currentPage.value),
        page_size: String(pageSize.value),
        ...filters
      })
      const res = await axios.get(`${API_BASE}/admin/alerts?${params}`)
      alerts.value = res.data.data.alerts
      total.value = res.data.data.total
      return res.data.data
    } finally {
      isLoading.value = false
    }
  }

  const getStatistics = async (startDate: string, endDate: string) => {
    const adminId = getUserId()
    const res = await axios.get(`${API_BASE}/admin/alerts/statistics`, {
      params: { admin_id: adminId, start_date: startDate, end_date: endDate }
    })
    stats.value = res.data.data
    return res.data.data
  }

  const getHighRiskUsers = async (topN: number = 10) => {
    const adminId = getUserId()
    const res = await axios.get(`${API_BASE}/admin/alerts/high-risk-users`, {
      params: { admin_id: adminId, top_n: topN }
    })
    highRiskUsers.value = res.data.data.users
    return res.data.data
  }

  const getUserProfile = async (userId: string, days: number = 30) => {
    const adminId = getUserId()
    const res = await axios.get(`${API_BASE}/admin/alerts/users/${userId}/profile`, {
      params: { admin_id: adminId, days }
    })
    userProfile.value = res.data.data
    return res.data.data
  }

  const deleteAlert = async (alertId: string, reason: string) => {
    const adminId = getUserId()
    await axios.delete(`${API_BASE}/admin/alerts/${alertId}`, {
      params: { admin_id: adminId, reason }
    })
    // 从列表中移除
    alerts.value = alerts.value.filter(a => a.id !== alertId)
  }

  const batchDeleteAlerts = async (alertIds: string[], reason: string) => {
    const adminId = getUserId()
    await axios.post(`${API_BASE}/admin/alerts/batch-delete`, {
      admin_id: adminId,
      alert_ids: alertIds,
      reason
    })
    // 从列表中移除
    alerts.value = alerts.value.filter(a => !alertIds.includes(a.id))
  }

  const acknowledgeAlert = async (alertId: string) => {
    const adminId = getUserId()
    await axios.post(`${API_BASE}/alerts/${alertId}/acknowledge`, {
      user_id: adminId,
      notes: '管理员确认'
    })
    // 更新本地状态
    const alert = alerts.value.find(a => a.id === alertId)
    if (alert) {
      alert.is_acknowledged = true
      alert.acknowledged_by = adminId
    }
  }

  // WebSocket for real-time alerts
  const ws = ref<WebSocket | null>(null)

  const initWebSocket = () => {
    const adminId = getUserId()
    if (!adminId || ws.value) return

    const token = localStorage.getItem('access_token')
    ws.value = new WebSocket(`ws://localhost:8000/api/admin/ws/alerts/${adminId}?token=${token}`)

    ws.value.onopen = () => {
      console.log('Admin WebSocket connected')
    }

    ws.value.onmessage = (event) => {
      const message = JSON.parse(event.data)
      handleWebSocketMessage(message)
    }

    ws.value.onclose = () => {
      console.log('Admin WebSocket disconnected, reconnecting...')
      setTimeout(initWebSocket, 3000)
    }
  }

  const handleWebSocketMessage = (message: any) => {
    switch (message.type) {
      case 'new_alert':
        // 新预警，添加到列表开头
        alerts.value.unshift(message.data)
        total.value++
        break
      case 'update_alert':
        // 更新预警
        const index = alerts.value.findIndex(a => a.id === message.data.id)
        if (index !== -1) {
          alerts.value[index] = { ...alerts.value[index], ...message.data }
        }
        break
      case 'delete_alert':
        // 删除预警
        alerts.value = alerts.value.filter(a => a.id !== message.data.id)
        total.value--
        break
      case 'ping':
        ws.value?.send(JSON.stringify({ type: 'pong', timestamp: new Date().toISOString() }))
        break
    }
  }

  const disconnectWebSocket = () => {
    ws.value?.close()
    ws.value = null
  }

  return {
    alerts,
    total,
    stats,
    highRiskUsers,
    userProfile,
    isLoading,
    currentPage,
    pageSize,
    dangerAlerts,
    unacknowledgedAlerts,
    getAllAlerts,
    getStatistics,
    getHighRiskUsers,
    getUserProfile,
    deleteAlert,
    batchDeleteAlerts,
    acknowledgeAlert,
    initWebSocket,
    disconnectWebSocket
  }
})
