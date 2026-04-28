import { defineStore } from 'pinia'
import { ref } from 'vue'
import axios from 'axios'

const API_BASE = '/api'

export const useAlertStore = defineStore('alert', () => {
  // State
  const alerts = ref([])
  const unreadCount = ref(0)
  const ws = ref<WebSocket | null>(null)

  // Actions
  const getAlerts = async (filters: any = {}) => {
    const userId = localStorage.getItem('user_id')
    const params = new URLSearchParams({ user_id: userId || '', ...filters })
    const res = await axios.get(`${API_BASE}/alerts?${params}`)
    alerts.value = res.data.data.alerts
    return res.data.data
  }

  const getStats = async () => {
    const userId = localStorage.getItem('user_id')
    const res = await axios.get(`${API_BASE}/alerts/stats?user_id=${userId}`)
    unreadCount.value = res.data.data.unacknowledged
    return res.data.data
  }

  const acknowledgeAlert = async (alertId: string) => {
    const userId = localStorage.getItem('user_id')
    await axios.post(`${API_BASE}/alerts/${alertId}/acknowledge`, {
      user_id: userId
    })
    unreadCount.value = Math.max(0, unreadCount.value - 1)
  }

  const batchAcknowledge = async (alertIds: string[]) => {
    const userId = localStorage.getItem('user_id')
    await axios.post(`${API_BASE}/alerts/batch/acknowledge`, {
      user_id: userId,
      alert_ids: alertIds
    })
  }

  // WebSocket
  const initWebSocket = () => {
    const userId = localStorage.getItem('user_id')
    if (!userId || ws.value) return

    const token = localStorage.getItem('token')
    ws.value = new WebSocket(`ws://localhost:8001/api/ws/alerts/${userId}?token=${token}`)

    ws.value.onopen = () => {
      console.log('WebSocket connected')
    }

    ws.value.onmessage = (event) => {
      const message = JSON.parse(event.data)
      handleWebSocketMessage(message)
    }

    ws.value.onclose = () => {
      console.log('WebSocket disconnected, reconnecting...')
      setTimeout(initWebSocket, 3000)
    }
  }

  const handleWebSocketMessage = (message: any) => {
    switch (message.type) {
      case 'new_alert':
        alerts.value.unshift(message.data)
        unreadCount.value++
        // 显示桌面通知
        showNotification(message.data)
        break
      case 'update_alert':
        const index = alerts.value.findIndex(a => a.id === message.data.id)
        if (index !== -1) {
          alerts.value[index] = { ...alerts.value[index], ...message.data }
        }
        break
      case 'delete_alert':
        alerts.value = alerts.value.filter(a => a.id !== message.data.id)
        break
      case 'ping':
        ws.value?.send(JSON.stringify({ type: 'pong', timestamp: new Date().toISOString() }))
        break
    }
  }

  const showNotification = (alert: any) => {
    if (Notification.permission === 'granted') {
      new Notification(alert.title, {
        body: alert.message,
        icon: alert.level === 'danger' ? '/danger.png' : '/warning.png'
      })
    }
  }

  return {
    alerts,
    unreadCount,
    getAlerts,
    getStats,
    acknowledgeAlert,
    batchAcknowledge,
    initWebSocket
  }
})
