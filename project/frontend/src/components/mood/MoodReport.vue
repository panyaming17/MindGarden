<template>
  <div class="mood-report-container">
    <!-- 页面头部 -->
    <div class="report-header">
      <h1 class="report-title">📊 {{ sessionTitle }}</h1>
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
        <p>正在加载你的专属报告...</p>
      </div>

      <!-- 报告生成中等待状态 -->
      <div v-else-if="isPendingReport && !latestReport" class="pending-state">
        <div class="pending-animation">
          <div class="pending-spinner"></div>
          <div class="pending-dots">
            <span></span><span></span><span></span>
          </div>
        </div>
        <h3 class="pending-title">报告正在生成中</h3>
        <p class="pending-desc">小园正在为你整理本次对话的记录报告、分析报告和调理报告，请稍候...</p>
        <div class="pending-progress">
          <div class="progress-bar">
            <div class="progress-fill generating"></div>
          </div>
        </div>
      </div>

      <!-- 无数据状态 -->
      <div v-else-if="!latestReport && !isPendingReport" class="empty-state">
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
      :modal="true"
      :modal-class="'history-drawer-modal'"
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
            <div class="history-title">{{ item.title}}</div>
            <div class="history-date">{{ formatDate(item.created_at) }}</div>
          </div>
          <div class="history-badge">查看</div>
        </div>
      </div>
    </el-drawer>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick, watch } from 'vue'
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
const sessionTitle = ref('情绪报告')
const isPendingReport = ref(false)  // 是否正在等待报告生成
const pendingSessionId = ref(null)   // 待生成的报告的 session_id

// 监听抽屉状态变化，更新 localStorage
watch(drawer, (newValue) => {
  localStorage.setItem('historyDrawerOpen', newValue ? 'true' : 'false')
  // 触发 storage 事件（在同一页面）
  window.dispatchEvent(new Event('storage'))
})

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

// 加载报告（显示第一条历史报告）
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
      // 按创建时间排序（最新的在前）
      const sortedReports = [...data.reports].sort((a, b) => 
        new Date(b.created_at) - new Date(a.created_at)
      )
      
      // 保存所有报告到历史列表（包含标题）
      historyList.value = sortedReports.map(report => ({
        session_id: report.session_id,
        created_at: report.created_at,
        title: report.title || `对话记录 ${new Date(report.created_at).toLocaleDateString()}`
      }))
      
      // 显示第一条报告（最新的）
      const firstReport = sortedReports[0]

      // 获取完整报告详情
      const sessionResponse = await fetch(`${API_BASE_URL}/report/session/${firstReport.session_id}`)
      
      if (!sessionResponse.ok) {
        throw new Error(`获取报告详情失败: ${sessionResponse.status}`)
      }

      const sessionData = await sessionResponse.json()

      // 合并数据
      latestReport.value = {
        session_id: firstReport.session_id,
        created_at: firstReport.created_at,
        title: firstReport.title || `对话记录 ${new Date(firstReport.created_at).toLocaleDateString()}`,
        record_report_json: sessionData.record_report_json,
        analysis_report_json: sessionData.analysis_report_json,
        treatment_report_json: sessionData.treatment_report_json
      }
      
      // 设置页面标题
      sessionTitle.value = firstReport.title || '情绪报告'

      // console.log('报告加载成功:', latestReport.value)
    } else {
      console.log('暂无报告数据')
      historyList.value = []
    }
  } catch (error) {
    console.error('加载报告失败:', error)
    ElMessage.error('加载报告失败，请稍后重试')
  } finally {
    loading.value = false
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
      record_report_json: sessionData.record_report_json,
      analysis_report_json: sessionData.analysis_report_json,
      treatment_report_json: sessionData.treatment_report_json
    }
    
    // 更新页面标题
    sessionTitle.value = title

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
  // 先检查是否有待查看的报告（从对话结束跳转过来的）
  const pendingSessionIdStr = localStorage.getItem('pendingReportSessionId')
  if (pendingSessionIdStr) {
    // 清除标记，避免下次进入时重复
    localStorage.removeItem('pendingReportSessionId')
    localStorage.removeItem('pendingReportUserId')
    
    // 加载指定会话的报告（可能还在生成中）
    pendingSessionId.value = pendingSessionIdStr
    isPendingReport.value = true
    loadPendingReport(pendingSessionIdStr)
  } else {
    // 正常加载最新的报告
    loadLatestReports()
  }
})

// 加载待生成的报告（带轮询）
const loadPendingReport = async (sessionId) => {
  loading.value = true
  
  try {
    // 先尝试获取报告状态
    const statusResponse = await fetch(`${API_BASE_URL}/chat/report-status/${sessionId}`)
    
    if (!statusResponse.ok) {
      throw new Error(`获取报告状态失败: ${statusResponse.status}`)
    }
    
    const statusData = await statusResponse.json()
    
    // 检查报告是否已生成完成
    if (statusData.status?.record_report === 'completed' && 
        statusData.status?.analysis_report === 'completed' &&
        statusData.status?.treatment_report === 'completed') {
      // 报告已完成，获取完整报告
      const reportResponse = await fetch(`${API_BASE_URL}/report/session/${sessionId}`)
      
      if (!reportResponse.ok) {
        throw new Error(`获取报告详情失败: ${reportResponse.status}`)
      }
      
      const sessionData = await reportResponse.json()
      
      latestReport.value = {
        session_id: sessionId,
        created_at: sessionData.created_at || new Date().toISOString(),
        title: sessionData.title || `对话记录 ${new Date().toLocaleDateString()}`,
        record_report_json: sessionData.record_report_json,
        analysis_report_json: sessionData.analysis_report_json,
        treatment_report_json: sessionData.treatment_report_json
      }
      sessionTitle.value = sessionData.title || '情绪报告'
      isPendingReport.value = false
      loading.value = false
      
      // 同时加载历史列表
      loadHistoryList()
      
      ElMessage.success('报告已生成完成！')
    } else {
      // 报告还在生成中，显示等待状态并开始轮询
      latestReport.value = null
      isPendingReport.value = true
      loading.value = false
      
      // 开始轮询
      startPendingPolling(sessionId)
    }
  } catch (error) {
    console.error('获取待生成报告失败:', error)
    // 可能报告还没创建，开始轮询
    isPendingReport.value = true
    loading.value = false
    startPendingPolling(sessionId)
  }
}

// 轮询待生成的报告状态
let pendingPollingTimer = null

const startPendingPolling = (sessionId) => {
  // console.log('开始轮询报告状态:', sessionId)
  
  // 每3秒轮询一次
  pendingPollingTimer = setInterval(async () => {
    try {
      const statusResponse = await fetch(`${API_BASE_URL}/chat/report-status/${sessionId}`)
      
      if (!statusResponse.ok) return
      
      const statusData = await statusResponse.json()
      
      // 检查三份报告是否都完成了
      if (statusData.status?.record_report === 'completed' && 
          statusData.status?.analysis_report === 'completed' &&
          statusData.status?.treatment_report === 'completed') {
        // 报告完成了，停止轮询并加载完整报告
        stopPendingPolling()
        
        // 获取完整报告
        const reportResponse = await fetch(`${API_BASE_URL}/report/session/${sessionId}`)
        const reportData = await reportResponse.json()
        
        latestReport.value = {
          session_id: sessionId,
          created_at: reportData.created_at || new Date().toISOString(),
          title: reportData.title || `对话记录 ${new Date().toLocaleDateString()}`,
          record_report_json: reportData.record_report_json,
          analysis_report_json: reportData.analysis_report_json,
          treatment_report_json: reportData.treatment_report_json
        }
        sessionTitle.value = reportData.title || '情绪报告'
        isPendingReport.value = false
        
        // 加载历史列表
        loadHistoryList()
        
        ElMessage.success('报告生成完成！')
      }
    } catch (error) {
      console.error('轮询报告状态失败:', error)
    }
  }, 3000)
}

const stopPendingPolling = () => {
  if (pendingPollingTimer) {
    clearInterval(pendingPollingTimer)
    pendingPollingTimer = null
  }
}

// 加载历史报告列表
const loadHistoryList = async () => {
  loadingHistory.value = true
  
  try {
    const storedUser = localStorage.getItem('user')
    if (!storedUser) return
    
    const userData = JSON.parse(storedUser)
    const userId = userData.id
    
    const response = await fetch(`${API_BASE_URL}/report/user/${userId}`)
    
    if (!response.ok) return
    
    const data = await response.json()
    
    if (data.reports && data.reports.length > 0) {
      const sortedReports = [...data.reports].sort((a, b) => 
        new Date(b.created_at) - new Date(a.created_at)
      )
      
      historyList.value = sortedReports.map(report => ({
        session_id: report.session_id,
        created_at: report.created_at,
        title: report.title || `对话记录 ${new Date(report.created_at).toLocaleDateString()}`
      }))
    }
  } catch (error) {
    console.error('加载历史报告列表失败:', error)
  } finally {
    loadingHistory.value = false
  }
}

// 组件卸载时清理轮询定时器
onUnmounted(() => {
  stopPendingPolling()
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

/* 报告生成中等待状态 */
.pending-state {
  text-align: center;
  padding: 80px 20px;
  color: #667eea;
}

.pending-animation {
  position: relative;
  width: 80px;
  height: 80px;
  margin: 0 auto 24px;
}

.pending-spinner {
  width: 60px;
  height: 60px;
  border: 4px solid #e8eaf6;
  border-top-color: #667eea;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto;
}

.pending-dots {
  display: flex;
  justify-content: center;
  gap: 6px;
  position: absolute;
  bottom: 0;
  left: 50%;
  transform: translateX(-50%);
}

.pending-dots span {
  width: 8px;
  height: 8px;
  background: #667eea;
  border-radius: 50%;
  animation: bounce 1.4s ease-in-out infinite;
}

.pending-dots span:nth-child(1) { animation-delay: 0s; }
.pending-dots span:nth-child(2) { animation-delay: 0.2s; }
.pending-dots span:nth-child(3) { animation-delay: 0.4s; }

@keyframes bounce {
  0%, 80%, 100% { transform: scale(0.6); opacity: 0.5; }
  40% { transform: scale(1); opacity: 1; }
}

.pending-title {
  font-size: 20px;
  font-weight: 600;
  color: #667eea;
  margin-bottom: 12px;
}

.pending-desc {
  font-size: 14px;
  color: #95a5a6;
  line-height: 1.6;
  max-width: 360px;
  margin: 0 auto 24px;
}

.pending-progress {
  max-width: 300px;
  margin: 0 auto;
}

.progress-bar {
  width: 100%;
  height: 6px;
  background: #e8eaf6;
  border-radius: 3px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  border-radius: 3px;
  transition: width 0.3s ease;
}

.progress-fill.generating {
  width: 60%;
  background: linear-gradient(90deg, #667eea, #764ba2, #667eea);
  background-size: 200% 100%;
  animation: shimmer 2s linear infinite;
}

@keyframes shimmer {
  0% { background-position: -200% 0; }
  100% { background-position: 200% 0; }
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

/* 遮罩层样式 */
.history-drawer-modal {
  background-color: rgba(0, 0, 0, 0.5) !important;
  backdrop-filter: blur(2px);
  z-index: 2001 !important;
}

/* 确保遮罩层正确显示 */
:deep(.el-overlay) {
  background-color: rgba(0, 0, 0, 0.5);
  z-index: 2001 !important;
}

/* 抽屉本身的 z-index 也要提高 */
:deep(.el-drawer) {
  z-index: 2002 !important;
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
