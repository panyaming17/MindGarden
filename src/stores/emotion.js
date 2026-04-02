import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

// API 基础配置
const API_BASE_URL = 'http://localhost:8000'

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

    // 打印请求信息到控制台
    console.log('========== 情绪 API 请求 ==========')
    console.log('URL:', fullUrl)
    console.log('Method:', fetchOptions.method || 'GET')
    if (params) console.log('Query Params:', params)
    if (fetchOptions.body) {
      console.log('Request Body:', JSON.parse(fetchOptions.body))
    }
    console.log('====================================')

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

// 情绪标签配置
export const emotionTags = [
  { type: 'happy', icon: '😊', name: '开心', color: '#FFD93D' },
  { type: 'excited', icon: '🤩', name: '兴奋', color: '#FF6B6B' },
  { type: 'calm', icon: '😌', name: '平静', color: '#6BCB77' },
  { type: 'tired', icon: '😴', name: '疲惫', color: '#95A5A6' },
  { type: 'sad', icon: '😢', name: '难过', color: '#74B9FF' },
  { type: 'anxious', icon: '😰', name: '焦虑', color: '#E17055' },
  { type: 'angry', icon: '😠', name: '愤怒', color: '#D63031' },
  { type: 'worried', icon: '😟', name: '担忧', color: '#FD79A8' },
  { type: 'grateful', icon: '🥰', name: '感恩', color: '#FDCB6E' },
  { type: 'confused', icon: '😕', name: '困惑', color: '#A29BFE' },
  { type: 'peaceful', icon: '🧘', name: '安宁', color: '#00B894' },
  { type: 'lonely', icon: '🥺', name: '孤独', color: '#636E72' }
]

export const useEmotionStore = defineStore('emotion', () => {
  // State
  const records = ref([])
  const calendarData = ref({})
  const statistics = ref(null)
  const hasRemind = ref(false)
  const lastRecord = ref(null)
  const remindSettings = ref(null)
  const isLoading = ref(false)

  // Getters
  const todayRecorded = computed(() => {
    const today = new Date().toISOString().split('T')[0]
    return records.value.some(r => r.record_date === today)
  })

  const recentEmotions = computed(() => {
    return records.value.slice(0, 7)
  })

  // Actions
  
  // 记录情绪
  const recordEmotion = async (data) => {
    try {
      isLoading.value = true
      const result = await request('/api/emotions/record', {
        method: 'POST',
        body: JSON.stringify(data)
      })
      // 刷新记录和统计数据
      await fetchRecords()
      await fetchStatistics()
      await checkRemind()
      return result
    } catch (error) {
      console.error('记录情绪失败:', error)
      throw error
    } finally {
      isLoading.value = false
    }
  }

  // 获取历史记录
  const fetchRecords = async (params = {}) => {
    try {
      isLoading.value = true
      const data = await request('/api/emotions/history', { params })
      records.value = data.records || []
      return data
    } catch (error) {
      console.error('获取记录失败:', error)
      return null
    } finally {
      isLoading.value = false
    }
  }

  // 获取日历数据
  const fetchCalendar = async (year, month) => {
    try {
      const data = await request('/api/emotions/calendar', {
        params: { year, month }
      })
      calendarData.value = data
      return data
    } catch (error) {
      console.error('获取日历失败:', error)
      return null
    }
  }

  // 获取统计数据
  const fetchStatistics = async (params = {}) => {
    try {
      const data = await request('/api/emotions/statistics', { params })
      statistics.value = data
      return data
    } catch (error) {
      console.error('获取统计失败:', error)
      return null
    }
  }

  // 检查是否需要提醒
  const checkRemind = async () => {
    try {
      const data = await request('/api/emotions/next-remind')
      hasRemind.value = data.need_remind || false
      lastRecord.value = data.last_record || null
      return data
    } catch (error) {
      console.error('检查提醒失败:', error)
      hasRemind.value = false
      return null
    }
  }

  // 跳过提醒
  const skipRemind = async () => {
    try {
      await request('/api/emotions/skip-remind', { method: 'POST' })
      hasRemind.value = false
    } catch (error) {
      console.error('跳过提醒失败:', error)
    }
  }

  // 获取提醒设置
  const fetchRemindSettings = async () => {
    try {
      const data = await request('/api/emotions/remind-settings')
      remindSettings.value = data
      return data
    } catch (error) {
      console.error('获取提醒设置失败:', error)
      return null
    }
  }

  // 更新提醒设置
  const updateRemindSettings = async (settings) => {
    try {
      const data = await request('/api/emotions/remind-settings', {
        method: 'PUT',
        body: JSON.stringify(settings)
      })
      remindSettings.value = data
      return data
    } catch (error) {
      console.error('更新提醒设置失败:', error)
      throw error
    }
  }

  return {
    // State
    records,
    calendarData,
    statistics,
    hasRemind,
    lastRecord,
    remindSettings,
    isLoading,
    // Getters
    todayRecorded,
    recentEmotions,
    // Actions
    recordEmotion,
    fetchRecords,
    fetchCalendar,
    fetchStatistics,
    checkRemind,
    skipRemind,
    fetchRemindSettings,
    updateRemindSettings
  }
})
