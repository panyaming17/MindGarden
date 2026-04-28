import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import axios from 'axios'

const API_BASE = '/api/admin/questionnaires'

export interface QuestionnaireTemplate {
  id: number
  code: string
  name: string
  description?: string
  version: number
  is_active: boolean
  created_at: string
  updated_at: string
  question_count: number
}

export interface QuestionnaireRecord {
  id: number
  user_id: string
  username?: string
  template_code: string
  template_name: string
  total_score: number
  result_level: string
  result_level_text: string
  created_at: string
  has_alert: boolean
  alert_level?: string
}

export interface QuestionnaireRecordDetail {
  id: number
  user_id: string
  username?: string
  template_code: string
  template_name: string
  answers: any[]
  total_score: number
  result_level: string
  result_analysis?: any
  created_at: string
  related_alerts: any[]
}

export interface QuestionnaireStats {
  template_code: string
  template_name: string
  total_records: number
  today_records: number
  week_records: number
  avg_score: number
  result_distribution: Record<string, number>
}

export interface ScoringRule {
  id: number
  template_code: string
  rule_type: string
  rule_config: any
  priority: number
  is_active: boolean
  created_at: string
}

export const useAdminQuestionnaireStore = defineStore('adminQuestionnaire', () => {
  // State
  const templates = ref<QuestionnaireTemplate[]>([])
  const records = ref<QuestionnaireRecord[]>([])
  const recordDetail = ref<QuestionnaireRecordDetail | null>(null)
  const statistics = ref<QuestionnaireStats[]>([])
  const scoringRules = ref<ScoringRule[]>([])
  const isLoading = ref(false)
  const totalRecords = ref(0)

  // Getters
  const activeTemplates = computed(() => templates.value.filter(t => t.is_active))
  const inactiveTemplates = computed(() => templates.value.filter(t => !t.is_active))

  // 获取用户ID
  const getUserId = () => {
    const userStr = localStorage.getItem('user')
    if (userStr) {
      try {
        const user = JSON.parse(userStr)
        return user.id || user.user_id
      } catch (e) {
        console.error('Parse user error:', e)
      }
    }
    return null
  }

  // Actions
  const getTemplates = async (is_active?: boolean) => {
    isLoading.value = true
    try {
      const adminId = getUserId()
      // console.log('Getting templates, adminId:', adminId)
      const params: any = { admin_id: adminId }
      if (is_active !== undefined) params.is_active = is_active
      
      const res = await axios.get(`${API_BASE}/templates`, { params })
      // console.log('Templates response:', res.data)
      templates.value = res.data.items
      return res.data
    } catch (error: any) {
      // console.error('Get templates error:', error.response?.data || error.message)
      throw error
    } finally {
      isLoading.value = false
    }
  }

  const getTemplateDetail = async (templateCode: string) => {
    isLoading.value = true
    try {
      const adminId = getUserId()
      const res = await axios.get(`${API_BASE}/templates/${templateCode}`, {
        params: { admin_id: adminId }
      })
      return res.data
    } finally {
      isLoading.value = false
    }
  }

  const updateTemplateStatus = async (templateCode: string, isActive: boolean) => {
    const adminId = getUserId()
    await axios.put(`${API_BASE}/templates/${templateCode}/status`, null, {
      params: { admin_id: adminId, is_active: isActive }
    })
    // 更新本地状态
    const template = templates.value.find(t => t.code === templateCode)
    if (template) {
      template.is_active = isActive
    }
  }

  const getRecords = async (filters: any = {}) => {
    isLoading.value = true
    try {
      const adminId = getUserId()
      // console.log('Getting records, adminId:', adminId)
      const params = {
        admin_id: adminId,
        page: filters.page || 1,
        page_size: filters.page_size || 20,
        ...filters
      }
      const res = await axios.get(`${API_BASE}/records`, { params })
      // console.log('Records response:', res.data)
      records.value = res.data.items
      totalRecords.value = res.data.total
      return res.data
    } catch (error: any) {
      // console.error('Get records error:', error.response?.data || error.message)
      throw error
    } finally {
      isLoading.value = false
    }
  }

  const getRecordDetail = async (recordId: number) => {
    isLoading.value = true
    try {
      const adminId = getUserId()
      const res = await axios.get(`${API_BASE}/records/${recordId}`, {
        params: { admin_id: adminId }
      })
      recordDetail.value = res.data
      return res.data
    } finally {
      isLoading.value = false
    }
  }

  const getStatistics = async (startDate?: string, endDate?: string) => {
    isLoading.value = true
    try {
      const adminId = getUserId()
      const params: any = { admin_id: adminId }
      if (startDate) params.start_date = startDate
      if (endDate) params.end_date = endDate
      
      const res = await axios.get(`${API_BASE}/statistics`, { params })
      statistics.value = res.data
      return res.data
    } finally {
      isLoading.value = false
    }
  }

  const getScoringRules = async (templateCode: string) => {
    isLoading.value = true
    try {
      const adminId = getUserId()
      const res = await axios.get(`${API_BASE}/scoring-rules/${templateCode}`, {
        params: { admin_id: adminId }
      })
      scoringRules.value = res.data
      return res.data
    } finally {
      isLoading.value = false
    }
  }

  const requestRuleUpdate = async (ruleId: number, ruleConfig: any, reason: string) => {
    const adminId = getUserId()
    const res = await axios.post(`${API_BASE}/scoring-rules/${ruleId}/update-request`, {
      admin_id: adminId,
      rule_config: ruleConfig,
      reason
    })
    return res.data
  }

  const reviewRuleUpdate = async (ruleId: number, action: 'approve' | 'reject', comment?: string) => {
    const superAdminId = getUserId()
    const res = await axios.post(`${API_BASE}/scoring-rules/${ruleId}/review`, {
      super_admin_id: superAdminId,
      action,
      comment
    })
    return res.data
  }

  // 创建问卷模板
  const createTemplate = async (data: any) => {
    const adminId = getUserId()
    const res = await axios.post(`${API_BASE}/templates`, {
      admin_id: adminId,
      code: data.code,
      name: data.name,
      description: data.description,
      questions: data.questions
    })
    return res.data
  }

  // 创建评分规则
  const createScoringRule = async (data: any) => {
    const adminId = getUserId()
    const res = await axios.post(`${API_BASE}/scoring-rules`, {
      admin_id: adminId,
      template_code: data.template_code,
      rule_type: data.rule_type,
      rule_config: data.rule_config,
      priority: data.priority || 0
    })
    return res.data
  }

  // 修改答题记录结果等级
  const modifyRecordResult = async (recordId: number, newLevel: string, reason: string) => {
    const adminId = getUserId()
    const res = await axios.put(`${API_BASE}/records/${recordId}/result`, {
      admin_id: adminId,
      new_level: newLevel,
      reason
    })
    return res.data
  }

  // 获取问卷操作日志
  const getLogs = async (filters: any = {}) => {
    isLoading.value = true
    try {
      const adminId = getUserId()
      const params = {
        admin_id: adminId,
        page: filters.page || 1,
        page_size: filters.page_size || 20,
        ...filters
      }
      const res = await axios.get(`${API_BASE}/logs`, { params })
      return res.data
    } finally {
      isLoading.value = false
    }
  }

  return {
    templates,
    records,
    recordDetail,
    statistics,
    scoringRules,
    isLoading,
    totalRecords,
    activeTemplates,
    inactiveTemplates,
    getTemplates,
    getTemplateDetail,
    updateTemplateStatus,
    getRecords,
    getRecordDetail,
    getStatistics,
    getScoringRules,
    requestRuleUpdate,
    reviewRuleUpdate,
    createTemplate,
    createScoringRule,
    modifyRecordResult,
    getLogs
  }
})
