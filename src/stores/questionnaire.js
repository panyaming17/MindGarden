import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

// API 基础配置
const API_BASE_URL = 'http://localhost:8000'

// 获取 token
const getToken = () => {
  return localStorage.getItem('access_token')
}

// 获取当前用户 ID
const getUserId = () => {
  const userStr = localStorage.getItem('user')

  if (userStr && userStr !== 'null' && userStr !== 'undefined') {
    try {
      const user = JSON.parse(userStr)
      const userId = user.id || user.user_id || user.username || user.userId || user.user

      if (userId && userId !== 'anonymous') {
        return String(userId)
      }
    } catch (error) {
      console.error('解析用户信息失败:', error)
    }
  }

  console.error('无法获取用户 ID，请确保已登录')
  throw new Error('用户未登录')
}

// 通用请求函数
const request = async (url, options = {}) => {
  try {
    const { params, ...fetchOptions } = options

    let fullUrl = `${API_BASE_URL}${url}`

    const allParams = {
      user_id: getUserId(),
      ...params
    }

    if (allParams && Object.keys(allParams).length > 0) {
      const searchParams = new URLSearchParams()
      Object.entries(allParams).forEach(([key, value]) => {
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

    if (data && typeof data === 'object' && 'code' in data) {
      if (data.code !== 200) {
        throw new Error(data.message || '请求失败')
      }
      return data.data
    }

    return data
  } catch (error) {
    console.error('API 请求失败:', error)
    throw error
  }
}

export const useQuestionnaireStore = defineStore('questionnaire', () => {
  const nextDueList = ref([])
  const currentTemplate = ref(null)
  const historyRecords = ref({})
  const hasCheckedToday = ref(false)
  const isLoading = ref(false)
  const lastSubmitResult = ref(null)

  const hasDueQuestionnaires = computed(() => nextDueList.value.length > 0)
  const dueCount = computed(() => nextDueList.value.length)

  const checkDueQuestionnaires = async () => {
    try {
      isLoading.value = true
      const data = await request('/api/questionnaires/next-due')
      nextDueList.value = Array.isArray(data) ? data : []
      hasCheckedToday.value = true
      return nextDueList.value
    } catch (error) {
      console.error('检查待测问卷失败:', error)
      nextDueList.value = []
      return []
    } finally {
      isLoading.value = false
    }
  }

  const loadTemplate = async (code) => {
    try {
      isLoading.value = true
      const data = await request(`/api/questionnaires/${code}/template`)
      currentTemplate.value = data
      return data
    } catch (error) {
      console.error('加载问卷模板失败:', error)
      throw error
    } finally {
      isLoading.value = false
    }
  }

  const submitAnswers = async (code, answers) => {
    try {
      isLoading.value = true
      const data = await request('/api/questionnaires/submit', {
        method: 'POST',
        body: JSON.stringify({
          template_code: code,
          answers: answers
        })
      })
      lastSubmitResult.value = data
      await checkDueQuestionnaires()
      return data
    } catch (error) {
      console.error('提交问卷失败:', error)
      throw error
    } finally {
      isLoading.value = false
    }
  }

  const skipQuestionnaire = async (code) => {
    try {
      await request('/api/questionnaires/skip', {
        method: 'POST',
        body: JSON.stringify({
          template_code: code
        })
      })
      await checkDueQuestionnaires()
    } catch (error) {
      console.error('跳过问卷失败:', error)
      throw error
    }
  }

  const loadHistory = async (code, limit = 5) => {
    try {
      const data = await request('/api/questionnaires/history', {
        params: { template_code: code, limit }
      })
      historyRecords.value[code] = data
      return data
    } catch (error) {
      console.error('加载历史记录失败:', error)
      const emptyData = {
        template_code: code,
        template_name: '',
        records: [],
        trend_data: []
      }
      historyRecords.value[code] = emptyData
      return emptyData
    }
  }

  const clearCurrentTemplate = () => {
    currentTemplate.value = null
  }

  const clearLastSubmitResult = () => {
    lastSubmitResult.value = null
  }

  return {
    nextDueList,
    currentTemplate,
    historyRecords,
    hasCheckedToday,
    isLoading,
    lastSubmitResult,
    hasDueQuestionnaires,
    dueCount,
    checkDueQuestionnaires,
    loadTemplate,
    submitAnswers,
    skipQuestionnaire,
    loadHistory,
    clearCurrentTemplate,
    clearLastSubmitResult
  }
})