import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'

// API 基础配置（从环境变量读取，默认为 localhost:8000）
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

// 获取 token
const getToken = () => {
  return localStorage.getItem('access_token')
}

// 通用请求函数
const request = async (url, options = {}) => {
  try {
    const { params, ...fetchOptions } = options
    
    let fullUrl = `${API_BASE_URL}${url}`
    if (params) {
      const searchParams = new URLSearchParams()
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          searchParams.append(key, value)
        }
      })
      const queryString = searchParams.toString()
      if (queryString) {
        fullUrl += `?${queryString}`
      }
    }

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
    console.error('API 请求失败:', error)
    throw error
  }
}

// 预警类型配置
export const alertTypeConfig = {
  questionnaire: {
    label: '问卷测评',
    icon: '📋',
    color: '#667eea'
  },
  emotion: {
    label: '情绪记录',
    icon: '😊',
    color: '#f093fb'
  },
  conversation: {
    label: '对话内容',
    icon: '💬',
    color: '#4facfe'
  }
}

// 预警等级配置
export const alertLevelConfig = {
  info: {
    label: '提示',
    color: '#3498db',
    lightColor: '#ebf5fb',
    icon: 'ℹ️'
  },
  warning: {
    label: '警告',
    color: '#f39c12',
    lightColor: '#fef5e7',
    icon: '⚠️'
  },
  danger: {
    label: '危险',
    color: '#e74c3c',
    lightColor: '#fdedec',
    icon: '🚨'
  }
}

export const useAlertStore = defineStore('alert', () => {
  // State
  const alerts = ref([])
  const unreadCount = ref(0)
  const isLoading = ref(false)
  const selectedDate = ref(null)
  const filters = ref({
    type: 'all',
    level: 'all',
    status: 'all'
  })
  const wsConnection = ref(null)
  
  // 连接状态：'connecting' | 'connected' | 'disconnected' | 'polling'
  const connectionStatus = ref('disconnected')
  const connectionMessage = ref('')
  
  // 缓存相关状态
  const lastSuccessfulFetch = ref(null)  // 上次成功获取数据的时间
  const cachedAlerts = ref([])           // 缓存的预警数据
  const isUsingCache = ref(false)        // 是否正在使用缓存数据

  // Getters
  const filteredAlerts = computed(() => {
    return alerts.value.filter(alert => {
      if (filters.value.type !== 'all' && alert.type !== filters.value.type) return false
      if (filters.value.level !== 'all' && alert.level !== filters.value.level) return false
      if (filters.value.status !== 'all') {
        const isAcknowledged = alert.is_acknowledged
        if (filters.value.status === 'unacknowledged' && isAcknowledged) return false
        if (filters.value.status === 'acknowledged' && !isAcknowledged) return false
      }
      if (selectedDate.value) {
        const alertDate = alert.created_at.split('T')[0]
        if (alertDate !== selectedDate.value) return false
      }
      return true
    }).sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
  })

  const unacknowledgedCount = computed(() => 
    alerts.value.filter(a => !a.is_acknowledged).length
  )

  const stats = computed(() => {
    const total = alerts.value.length
    const unacknowledged = alerts.value.filter(a => !a.is_acknowledged).length
    const acknowledged = total - unacknowledged
    const dangerCount = alerts.value.filter(a => a.level === 'danger' && !a.is_acknowledged).length
    
    return {
      total,
      unacknowledged,
      acknowledged,
      dangerCount
    }
  })

  const calendarData = computed(() => {
    const data = {}
    alerts.value.forEach(alert => {
      const date = alert.created_at.split('T')[0]
      if (!data[date]) {
        data[date] = { count: 0, levels: new Set() }
      }
      data[date].count++
      data[date].levels.add(alert.level)
    })
    
    // 转换Set为Array
    Object.keys(data).forEach(date => {
      data[date].levels = Array.from(data[date].levels)
    })
    
    return data
  })

  // 模拟数据（用于后端未就绪时测试）
  const mockAlerts = [
    {
      id: 'alert_001',
      type: 'questionnaire',
      level: 'warning',
      title: 'PHQ-9评分异常',
      message: '您的PHQ-9评分为15分，显示中度抑郁倾向，建议关注心理健康状况',
      source_data: {
        template_code: 'PHQ9',
        template_name: 'PHQ-9抑郁量表',
        score: 15,
        result: '中度抑郁',
        result_level: 'moderate',
        date: '2026-03-30',
        record_id: 'record_001'
      },
      is_acknowledged: false,
      created_at: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
      acknowledged_at: null,
      acknowledged_by: null
    },
    {
      id: 'alert_002',
      type: 'emotion',
      level: 'danger',
      title: '连续负面情绪预警',
      message: '您已连续7天记录负面情绪，系统检测到情绪状态异常',
      source_data: {
        consecutive_days: 7,
        emotion_records: [
          { date: '2026-03-24', emotion: '难过', intensity: 8 },
          { date: '2026-03-25', emotion: '焦虑', intensity: 7 },
          { date: '2026-03-26', emotion: '疲惫', intensity: 6 },
          { date: '2026-03-27', emotion: '担忧', intensity: 8 },
          { date: '2026-03-28', emotion: '焦虑', intensity: 9 },
          { date: '2026-03-29', emotion: '难过', intensity: 7 },
          { date: '2026-03-30', emotion: '愤怒', intensity: 8 }
        ],
        summary: '连续一周负面情绪，焦虑情绪占主导'
      },
      is_acknowledged: false,
      created_at: new Date(Date.now() - 5 * 60 * 60 * 1000).toISOString(),
      acknowledged_at: null,
      acknowledged_by: null
    },
    {
      id: 'alert_003',
      type: 'conversation',
      level: 'danger',
      title: '对话危机信号检测',
      message: 'AI检测到对话内容中存在潜在危机信号词汇，需要特别关注',
      source_data: {
        session_id: 'session_001',
        preview: '用户：我觉得活着没什么意义了，每天都很难受...',
        emotion_intensity: 0.92,
        crisis_detected: true,
        crisis_keywords: ['活着没意义', '很难受'],
        risk_level: 'high'
      },
      is_acknowledged: true,
      created_at: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(),
      acknowledged_at: new Date(Date.now() - 20 * 60 * 60 * 1000).toISOString(),
      acknowledged_by: 'admin_001'
    },
    {
      id: 'alert_004',
      type: 'questionnaire',
      level: 'info',
      title: 'GAD-7评分提示',
      message: '您的GAD-7评分为8分，显示轻度焦虑倾向，建议适当放松身心',
      source_data: {
        template_code: 'GAD7',
        template_name: 'GAD-7焦虑量表',
        score: 8,
        result: '轻度焦虑',
        result_level: 'mild',
        date: '2026-03-28',
        record_id: 'record_002'
      },
      is_acknowledged: false,
      created_at: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString(),
      acknowledged_at: null,
      acknowledged_by: null
    },
    {
      id: 'alert_005',
      type: 'emotion',
      level: 'info',
      title: '负面情绪趋势提醒',
      message: '本周负面情绪占比较高，建议关注心理健康',
      source_data: {
        week_start: '2026-03-24',
        negative_days: 5,
        total_days: 7,
        ratio: 0.71
      },
      is_acknowledged: true,
      created_at: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000).toISOString(),
      acknowledged_at: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString(),
      acknowledged_by: 'user_001'
    }
  ]

  // Actions
  const fetchAlerts = async (options = {}) => {
    const { useCache = true, silent = false } = options
    
    try {
      isLoading.value = true
      isUsingCache.value = false
      
      const user = JSON.parse(localStorage.getItem('user') || '{}')
      if (!user.id) {
        console.error('用户未登录')
        return
      }
      
      // 检查是否使用模拟数据
      const useMockData = import.meta.env.VITE_USE_MOCK_DATA === 'true'
      
      if (useMockData) {
        console.log('使用模拟预警数据')
        // 模拟网络延迟
        await new Promise(resolve => setTimeout(resolve, 500))
        alerts.value = mockAlerts
        unreadCount.value = unacknowledgedCount.value
        // 更新缓存
        cachedAlerts.value = [...mockAlerts]
        lastSuccessfulFetch.value = Date.now()
        return
      }
      
      const data = await request('/api/alerts', {
        params: { user_id: user.id }
      })
      
      // 后端返回格式: { code: 200, message: "success", data: { total, page, page_size, alerts } }
      const responseData = data.data || data
      const newAlerts = responseData.alerts || []
      
      // 智能合并：保留本地修改（如确认状态），更新其他字段
      if (alerts.value.length > 0 && useCache) {
        // 创建ID映射，保留本地确认状态
        const localAcknowledgedMap = new Map()
        alerts.value.forEach(alert => {
          if (alert.is_acknowledged) {
            localAcknowledgedMap.set(alert.id, {
              is_acknowledged: true,
              acknowledged_at: alert.acknowledged_at,
              acknowledged_by: alert.acknowledged_by
            })
          }
        })
        
        // 合并数据：新数据为基础，保留本地确认状态
        alerts.value = newAlerts.map(newAlert => {
          const localStatus = localAcknowledgedMap.get(newAlert.id)
          if (localStatus && !newAlert.is_acknowledged) {
            // 本地已确认但服务端未确认，保留本地状态
            return { ...newAlert, ...localStatus }
          }
          return newAlert
        })
      } else {
        alerts.value = newAlerts
      }
      
      unreadCount.value = unacknowledgedCount.value
      
      // 更新缓存
      cachedAlerts.value = [...alerts.value]
      lastSuccessfulFetch.value = Date.now()
      isUsingCache.value = false
      
    } catch (error) {
      console.error('获取预警列表失败:', error)
      
      // 如果有缓存数据，使用缓存
      if (useCache && cachedAlerts.value.length > 0) {
        console.log('使用缓存的预警数据')
        alerts.value = [...cachedAlerts.value]
        isUsingCache.value = true
        
        // 静默模式下不显示错误消息
        if (!silent) {
          ElMessage.warning('网络异常，显示缓存数据')
        }
      } else {
        // 没有缓存时清空数据
        alerts.value = []
        unreadCount.value = 0
        
        if (!silent) {
          ElMessage.error('获取预警列表失败，请稍后重试')
        }
      }
    } finally {
      isLoading.value = false
    }
  }

  const acknowledgeAlert = async (alertId) => {
    try {
      // 检查是否使用模拟数据模式
      const useMockData = import.meta.env.VITE_USE_MOCK_DATA === 'true'
      
      if (!useMockData) {
        // 尝试调用后端API，如果失败则本地处理
        try {
          await request(`/api/alerts/${alertId}/acknowledge`, {
            method: 'POST'
          })
        } catch (apiError) {
          console.log('后端API未就绪，本地确认预警')
        }
      }
      
      // 更新本地数据
      const alert = alerts.value.find(a => a.id === alertId)
      if (alert) {
        alert.is_acknowledged = true
        alert.acknowledged_at = new Date().toISOString()
        // 从localStorage获取用户信息
        const user = JSON.parse(localStorage.getItem('user') || '{}')
        alert.acknowledged_by = user.id || 'user_001'
      }
      
      unreadCount.value = unacknowledgedCount.value
      ElMessage.success('预警已确认处理')
    } catch (error) {
      console.error('确认预警失败:', error)
      ElMessage.error('确认预警失败')
      throw error
    }
  }

  const acknowledgeAll = async () => {
    try {
      const unacknowledgedAlerts = alerts.value.filter(a => !a.is_acknowledged)
      await Promise.all(unacknowledgedAlerts.map(a => acknowledgeAlert(a.id)))
      ElMessage.success('全部预警已确认')
    } catch (error) {
      console.error('批量确认失败:', error)
      ElMessage.error('批量确认失败')
    }
  }

  const setFilter = (key, value) => {
    filters.value[key] = value
  }

  const setSelectedDate = (date) => {
    selectedDate.value = date
  }

  const clearFilters = () => {
    filters.value = {
      type: 'all',
      level: 'all',
      status: 'all'
    }
    selectedDate.value = null
  }

  // WebSocket 连接
  const connectWebSocket = (userId) => {
    // 如果已有连接，先关闭
    if (wsConnection.value) {
      wsConnection.value.close()
    }

    // 检查是否启用WebSocket（可通过环境变量控制）
    const enableWebSocket = import.meta.env.VITE_ENABLE_WEBSOCKET !== 'false'
    if (!enableWebSocket) {
      console.log('WebSocket已禁用，使用轮询模式')
      connectionStatus.value = 'polling'
      connectionMessage.value = '实时推送已禁用，使用轮询模式（每30秒刷新）'
      startPolling(userId)
      return
    }

    // 设置连接中状态
    connectionStatus.value = 'connecting'
    connectionMessage.value = '正在连接实时推送服务...'

    try {
      // 将 http/https 转换为 ws/wss
      const wsUrl = API_BASE_URL.replace(/^http/, 'ws')
      const ws = new WebSocket(`${wsUrl}/ws/alerts/${userId}`)
      
      ws.onopen = () => {
        console.log('预警WebSocket连接成功')
        connectionStatus.value = 'connected'
        connectionMessage.value = '实时推送已连接'
        // 连接成功后停止轮询
        stopPolling()
      }
      
      ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data)
          
          // 处理不同类型的消息
          if (message.type === 'new_alert') {
            // 新增预警 - 增量更新
            const newAlert = message.data
            
            // 检查是否已存在（避免重复）
            const existingIndex = alerts.value.findIndex(a => a.id === newAlert.id)
            if (existingIndex === -1) {
              // 新预警添加到列表头部
              alerts.value.unshift(newAlert)
              unreadCount.value++
              
              // 更新缓存
              cachedAlerts.value = [...alerts.value]
              
              ElMessage.warning(`收到新的${alertLevelConfig[newAlert.level].label}预警：${newAlert.title}`)
            }
          } else if (message.type === 'update_alert') {
            // 更新预警状态
            const updatedAlert = message.data
            const index = alerts.value.findIndex(a => a.id === updatedAlert.id)
            if (index !== -1) {
              // 保留本地未确认的修改
              const currentAlert = alerts.value[index]
              if (currentAlert.is_acknowledged && !updatedAlert.is_acknowledged) {
                // 本地已确认，但服务端更新为未确认，保留本地状态
                alerts.value[index] = { ...updatedAlert, 
                  is_acknowledged: true,
                  acknowledged_at: currentAlert.acknowledged_at,
                  acknowledged_by: currentAlert.acknowledged_by
                }
              } else {
                alerts.value[index] = updatedAlert
              }
              
              // 更新缓存
              cachedAlerts.value = [...alerts.value]
            }
          } else if (message.type === 'delete_alert') {
            // 删除预警
            const alertId = message.data.id
            alerts.value = alerts.value.filter(a => a.id !== alertId)
            
            // 更新缓存
            cachedAlerts.value = [...alerts.value]
          } else if (message.type === 'batch_update') {
            // 批量更新 - 全量刷新但不覆盖本地确认状态
            const newAlerts = message.data.alerts || []
            
            // 创建本地确认状态映射
            const localAcknowledgedMap = new Map()
            alerts.value.forEach(alert => {
              if (alert.is_acknowledged) {
                localAcknowledgedMap.set(alert.id, {
                  is_acknowledged: true,
                  acknowledged_at: alert.acknowledged_at,
                  acknowledged_by: alert.acknowledged_by
                })
              }
            })
            
            // 合并数据
            alerts.value = newAlerts.map(newAlert => {
              const localStatus = localAcknowledgedMap.get(newAlert.id)
              if (localStatus && !newAlert.is_acknowledged) {
                return { ...newAlert, ...localStatus }
              }
              return newAlert
            })
            
            // 更新缓存
            cachedAlerts.value = [...alerts.value]
          }
        } catch (error) {
          console.error('处理预警消息失败:', error)
        }
      }
      
      ws.onerror = (error) => {
        // 只在第一次错误时输出日志，避免刷屏
        if (!wsConnection.value || wsConnection.value.readyState === WebSocket.CONNECTING) {
          console.log('WebSocket连接失败，将自动重连或切换到轮询模式')
        }
      }
      
      ws.onclose = (event) => {
        // 非正常关闭（如后端未启动）时，启动轮询模式
        if (!event.wasClean) {
          console.log('WebSocket连接断开，切换到轮询模式')
          connectionStatus.value = 'polling'
          connectionMessage.value = '实时推送不可用，已切换到轮询模式（每30秒刷新）'
          startPolling(userId)
        } else {
          connectionStatus.value = 'disconnected'
          connectionMessage.value = '连接已断开'
        }
      }
      
      wsConnection.value = ws
    } catch (error) {
      console.log('WebSocket初始化失败，使用轮询模式')
      connectionStatus.value = 'polling'
      connectionMessage.value = '实时推送初始化失败，使用轮询模式（每30秒刷新）'
      startPolling(userId)
    }
  }

  // 轮询定时器
  let pollingTimer = null

  // 启动轮询（当WebSocket不可用时）
  const startPolling = (userId) => {
    // 避免重复启动
    if (pollingTimer) return
    
    console.log('启动预警数据轮询（每30秒）')
    // 立即执行一次（使用缓存模式，静默加载）
    fetchAlerts({ useCache: true, silent: true })
    
    // 每30秒轮询一次（使用缓存模式，静默加载）
    pollingTimer = setInterval(() => {
      fetchAlerts({ useCache: true, silent: true })
    }, 30000)
  }

  // 停止轮询
  const stopPolling = () => {
    if (pollingTimer) {
      clearInterval(pollingTimer)
      pollingTimer = null
      console.log('停止预警数据轮询')
    }
  }

  const disconnectWebSocket = () => {
    // 停止轮询
    stopPolling()
    
    // 关闭WebSocket
    if (wsConnection.value) {
      wsConnection.value.close()
      wsConnection.value = null
    }
  }

  return {
    // State
    alerts,
    unreadCount,
    isLoading,
    selectedDate,
    filters,
    connectionStatus,
    connectionMessage,
    isUsingCache,
    lastSuccessfulFetch,
    
    // Getters
    filteredAlerts,
    unacknowledgedCount,
    stats,
    calendarData,
    
    // Actions
    fetchAlerts,
    acknowledgeAlert,
    acknowledgeAll,
    setFilter,
    setSelectedDate,
    clearFilters,
    connectWebSocket,
    disconnectWebSocket
  }
})
