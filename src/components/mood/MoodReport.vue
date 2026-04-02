<template>
  <div class="mood-report-container">
    <!-- 页面头部 -->
    <div class="report-header">
      <h1 class="report-title">📊 情绪报告</h1>
      <p v-if="latestReport" class="report-subtitle">
        {{ latestReport.title || '对话记录' }} · {{ formatDate(latestReport.created_at) }}
      </p>
      <p v-else class="report-subtitle">
        了解你的情绪变化与成长，每次对话都会为你生成专属报告
      </p>
    </div>

    <!-- Tab 切换导航 -->
    <div class="tab-navigation">
      <div 
        v-for="tab in tabs" 
        :key="tab.key"
        :class="['tab-item', { active: activeTab === tab.key }]"
        @click="activeTab = tab.key"
      >
        <span class="tab-icon">{{ tab.icon }}</span>
        <span class="tab-text">{{ tab.label }}</span>
      </div>
    </div>

    <!-- 报告内容区域 -->
    <div class="report-content">
      <!-- 加载状态 -->
      <div v-if="loading" class="loading-state">
        <div class="loading-spinner"></div>
        <p>正在生成你的专属报告...</p>
      </div>

      <!-- 无数据状态 -->
      <div v-else-if="!latestReport" class="empty-state">
        <div class="empty-icon">📝</div>
        <h3>暂无报告数据</h3>
        <p>完成一次对话后，系统将为你生成详细的情绪分析报告</p>
      </div>

      <!-- 记录报告 -->
      <RecordReport 
        v-else-if="activeTab === 'record'"
        :data="latestReport.record_report_json"
      />

      <!-- 分析报告 -->
      <AnalysisReport 
        v-else-if="activeTab === 'analysis'"
        :data="latestReport.analysis_report_json"
      />

      <!-- 调理报告 -->
      <TreatmentReport 
        v-else-if="activeTab === 'treatment'"
        :data="latestReport.treatment_report_json"
        :session-id="latestReport.session_id"
      />
    </div>

    <!-- 历史报告按钮 -->
    <div 
      class="history-button-wrapper"
      :class="{
        'hidden': isHidden && !isHovering,
        'hovering': isHovering,
        [`hidden-${hiddenSide}`]: isHidden
      }"
      :style="{
        right: buttonPosition.x + 'px',
        bottom: buttonPosition.y + 'px'
      }"
      @mousedown="startDrag"
      @mousemove="onDrag"
      @mouseup="endDrag"
      @mouseenter="showButton"
      @mouseleave="hideButton"
    >
      <el-button 
        type="primary" 
        round 
        class="history-button"
        @click="drawer = true"
      >
        📁
      </el-button>
    </div>

    <!-- 历史报告抽屉 -->
    <el-drawer 
      v-model="drawer" 
      title="📁 历史报告" 
      :size="320"
      class="history-drawer"
    >
      <div v-if="loadingHistory" class="drawer-loading">
        <div class="loading-spinner small"></div>
        <p>加载中...</p>
      </div>
      <div v-else-if="historyList.length === 0" class="drawer-empty">
        <p>暂无历史报告</p>
      </div>
      <div v-else class="history-list">
        <div 
          v-for="item in historyList" 
          :key="item.session_id" 
          class="history-item"
          @click="openHistoryReport(item.session_id)"
        >
          <div class="history-info">
            <div class="history-title">{{ item.title || '对话记录' }}</div>
            <div class="history-date">{{ formatDate(item.created_at) }}</div>
          </div>
          <div class="history-badge">查看</div>
        </div>
      </div>
    </el-drawer>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import RecordReport from './RecordReport.vue'
import AnalysisReport from './AnalysisReport.vue'
import TreatmentReport from './TreatmentReport.vue'

// Tab 配置
const tabs = [
  { key: 'record', label: '记录报告', icon: '📝' },
  { key: 'analysis', label: '分析报告', icon: '📊' },
  { key: 'treatment', label: '调理报告', icon: '💊' }
]

// 响应式数据
const activeTab = ref('record')
const loading = ref(true)
const loadingHistory = ref(true)
const drawer = ref(false)
const latestReport = ref(null)
const historyList = ref([])

// 按钮拖拽相关
const buttonPosition = ref({ x: 30, y: 30 })
const isDragging = ref(false)
const dragStart = ref({ x: 0, y: 0 })
const isHidden = ref(false)
const hiddenSide = ref('')
const isHovering = ref(false)

// API 基础 URL
const API_BASE_URL = 'http://localhost:8000/api/v1'

// 格式化日期
const formatDate = (dateString) => {
  if (!dateString) return '-'
  const date = new Date(dateString)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// 加载最新报告
const loadLatestReports = async () => {
  try {
    const storedUser = localStorage.getItem('user')
    if (!storedUser) {
      console.error('用户未登录')
      loading.value = false
      return
    }

    const userData = JSON.parse(storedUser)
    const userId = userData.id

    if (!userId) {
      console.error('用户ID不存在')
      loading.value = false
      return
    }

    // 获取用户所有报告列表
    const response = await fetch(`${API_BASE_URL}/report/user/${userId}`)
    
    if (!response.ok) {
      throw new Error(`获取报告列表失败: ${response.status}`)
    }

    const data = await response.json()
    
    if (data.reports && data.reports.length > 0) {
      // 按创建时间排序，获取最新的报告
      const sortedReports = [...data.reports].sort((a, b) => 
        new Date(b.created_at) - new Date(a.created_at)
      )
      const latestReportData = sortedReports[0]

      // 获取完整报告
      const sessionResponse = await fetch(`${API_BASE_URL}/report/session/${latestReportData.session_id}`)
      
      if (!sessionResponse.ok) {
        throw new Error(`获取报告详情失败: ${sessionResponse.status}`)
      }

      const sessionData = await sessionResponse.json()

      // 合并数据
      latestReport.value = {
        session_id: latestReportData.session_id,
        created_at: latestReportData.created_at,
        title: latestReportData.title || `对话记录 ${new Date(latestReportData.created_at).toLocaleDateString()}`,
        record_report_json: sessionData.record_report,
        analysis_report_json: sessionData.analysis_report,
        treatment_report_json: sessionData.treatment_report
      }

      console.log('最新报告加载成功:', latestReport.value)
    } else {
      console.log('暂无报告数据')
    }
  } catch (error) {
    console.error('加载报告失败:', error)
    ElMessage.error('加载报告失败，请稍后重试')
  } finally {
    loading.value = false
  }
}

// 加载历史报告列表
const loadHistoryList = async () => {
  try {
    const storedUser = localStorage.getItem('user')
    if (!storedUser) {
      loadingHistory.value = false
      return
    }

    const userData = JSON.parse(storedUser)
    const userId = userData.id

    if (!userId) {
      loadingHistory.value = false
      return
    }

    const response = await fetch(`${API_BASE_URL}/report/user/${userId}`)
    
    if (!response.ok) {
      throw new Error(`获取历史报告失败: ${response.status}`)
    }

    const data = await response.json()

    if (data.reports && data.reports.length > 0) {
      const sortedReports = [...data.reports].sort((a, b) => 
        new Date(b.created_at) - new Date(a.created_at)
      )

      const reportsWithTitle = sortedReports.map(report => ({
        ...report,
        title: report.title || `对话记录 ${new Date(report.created_at).toLocaleDateString()}`
      }))

      // 排除最新的报告
      historyList.value = reportsWithTitle.slice(1)
    } else {
      historyList.value = []
    }
  } catch (error) {
    console.error('加载历史报告失败:', error)
  } finally {
    loadingHistory.value = false
  }
}

// 打开历史报告
const openHistoryReport = async (sessionId) => {
  drawer.value = false
  loading.value = true

  try {
    const response = await fetch(`${API_BASE_URL}/report/session/${sessionId}`)
    
    if (!response.ok) {
      throw new Error(`获取报告失败: ${response.status}`)
    }

    const sessionData = await response.json()

    const historyItem = historyList.value.find(item => item.session_id === sessionId)
    const createdAt = historyItem ? historyItem.created_at : new Date().toISOString()
    const title = historyItem ? historyItem.title : `对话记录 ${new Date(createdAt).toLocaleDateString()}`

    latestReport.value = {
      session_id: sessionId,
      created_at: createdAt,
      title: title,
      record_report_json: sessionData.record_report,
      analysis_report_json: sessionData.analysis_report,
      treatment_report_json: sessionData.treatment_report
    }

    ElMessage.success('报告加载成功')
  } catch (error) {
    console.error('加载历史报告失败:', error)
    ElMessage.error('加载报告失败，请稍后重试')
  } finally {
    loading.value = false
  }
}

// 拖拽功能
const startDrag = (event) => {
  isDragging.value = true
  dragStart.value = {
    x: event.clientX - (window.innerWidth - buttonPosition.value.x),
    y: event.clientY - (window.innerHeight - buttonPosition.value.y)
  }
}

const onDrag = (event) => {
  if (!isDragging.value) return

  const newX = window.innerWidth - (event.clientX - dragStart.value.x)
  const newY = window.innerHeight - (event.clientY - dragStart.value.y)

  buttonPosition.value.x = Math.max(20, Math.min(newX, window.innerWidth - 80))
  buttonPosition.value.y = Math.max(20, Math.min(newY, window.innerHeight - 80))
}

const endDrag = () => {
  isDragging.value = false

  const threshold = 50
  const windowWidth = window.innerWidth
  const windowHeight = window.innerHeight

  if (buttonPosition.value.x < threshold) {
    isHidden.value = true
    hiddenSide.value = 'right'
  } else if (windowWidth - buttonPosition.value.x < threshold) {
    isHidden.value = true
    hiddenSide.value = 'left'
  } else if (buttonPosition.value.y < threshold) {
    isHidden.value = true
    hiddenSide.value = 'bottom'
  } else if (windowHeight - buttonPosition.value.y < threshold) {
    isHidden.value = true
    hiddenSide.value = 'top'
  } else {
    isHidden.value = false
    hiddenSide.value = ''
  }
}

const showButton = () => {
  isHovering.value = true
}

const hideButton = () => {
  if (!isDragging.value) {
    isHovering.value = false
  }
}

// 初始化
onMounted(() => {
  loadLatestReports()
  loadHistoryList()
})
</script>

<style scoped>
.mood-report-container {
  max-width: 1000px;
  margin: 0 auto;
  padding: 24px;
  min-height: 100%;
}

/* 头部样式 */
.report-header {
  text-align: center;
  margin-bottom: 32px;
}

.report-title {
  font-size: 28px;
  font-weight: 600;
  color: #2c3e50;
  margin-bottom: 8px;
}

.report-subtitle {
  font-size: 14px;
  color: #7f8c8d;
}

/* Tab 导航 */
.tab-navigation {
  display: flex;
  justify-content: center;
  gap: 12px;
  margin-bottom: 24px;
  padding: 4px;
  background: rgba(255, 255, 255, 0.6);
  backdrop-filter: blur(10px);
  border-radius: 16px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
}

.tab-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 24px;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.3s ease;
  background: transparent;
}

.tab-item:hover {
  background: rgba(255, 255, 255, 0.8);
}

.tab-item.active {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}

.tab-icon {
  font-size: 18px;
}

.tab-text {
  font-size: 14px;
  font-weight: 500;
}

/* 报告内容区域 */
.report-content {
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(10px);
  border-radius: 20px;
  padding: 24px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05);
  min-height: 400px;
}

/* 加载状态 */
.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  color: #7f8c8d;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 3px solid #e0e0e0;
  border-top-color: #667eea;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 16px;
}

.loading-spinner.small {
  width: 24px;
  height: 24px;
  border-width: 2px;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

/* 空状态 */
.empty-state {
  text-align: center;
  padding: 60px 20px;
  color: #7f8c8d;
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 16px;
}

.empty-state h3 {
  font-size: 18px;
  font-weight: 600;
  color: #2c3e50;
  margin-bottom: 8px;
}

/* 历史报告按钮 */
.history-button-wrapper {
  position: fixed;
  z-index: 999;
  cursor: move;
  transition: all 0.3s ease;
}

.history-button {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  font-size: 22px;
  display: flex;
  justify-content: center;
  align-items: center;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  cursor: pointer;
  transition: all 0.3s ease;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
}

.history-button:hover {
  transform: scale(1.05);
  box-shadow: 0 6px 16px rgba(102, 126, 234, 0.3);
}

/* 隐藏状态 */
.history-button-wrapper.hidden-right {
  right: -34px !important;
}

.history-button-wrapper.hidden-left {
  left: -34px !important;
  right: auto !important;
}

.history-button-wrapper.hidden-bottom {
  bottom: -34px !important;
}

.history-button-wrapper.hidden-top {
  top: -34px !important;
  bottom: auto !important;
}

.history-button-wrapper.hovering.hidden-right {
  right: 30px !important;
}

.history-button-wrapper.hovering.hidden-left {
  left: 30px !important;
}

.history-button-wrapper.hovering.hidden-bottom {
  bottom: 30px !important;
}

.history-button-wrapper.hovering.hidden-top {
  top: 30px !important;
}

/* 抽屉样式 */
.history-drawer :deep(.el-drawer__header) {
  margin-bottom: 0;
  padding: 16px 20px;
  border-bottom: 1px solid #e8e8e8;
}

.drawer-loading,
.drawer-empty {
  text-align: center;
  padding: 40px 20px;
  color: #7f8c8d;
}

.history-list {
  padding: 8px 0;
}

.history-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid #f0f0f0;
  cursor: pointer;
  transition: all 0.2s ease;
}

.history-item:hover {
  background: #f8f9fa;
}

.history-info {
  flex: 1;
}

.history-title {
  font-size: 14px;
  font-weight: 500;
  color: #2c3e50;
  margin-bottom: 4px;
}

.history-date {
  font-size: 12px;
  color: #95a5a6;
}

.history-badge {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}

/* 响应式 */
@media (max-width: 768px) {
  .mood-report-container {
    padding: 16px;
  }

  .report-title {
    font-size: 24px;
  }

  .tab-navigation {
    gap: 8px;
  }

  .tab-item {
    padding: 10px 16px;
  }

  .tab-text {
    font-size: 13px;
  }

  .report-content {
    padding: 16px;
  }
}
</style>
