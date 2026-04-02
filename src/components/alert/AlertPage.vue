<template>
  <div class="alert-page">
    <!-- 页面标题 -->
    <div class="page-header">
      <div class="header-title">
        <span class="title-icon">🔔</span>
        <h2>预警提醒</h2>
        <el-badge 
          v-if="unacknowledgedCount > 0" 
          :value="unacknowledgedCount" 
          class="title-badge"
          type="danger"
        />
      </div>
      <p class="header-subtitle">实时监测您的情绪状态，及时发现潜在风险</p>
    </div>

    <!-- 连接状态提示 -->
    <div 
      v-if="showConnectionStatus" 
      class="connection-status"
      :class="connectionStatus"
    >
      <el-icon v-if="connectionStatus === 'connecting'" class="is-loading">
        <Loading />
      </el-icon>
      <el-icon v-else-if="connectionStatus === 'connected'">
        <CircleCheck />
      </el-icon>
      <el-icon v-else-if="connectionStatus === 'polling'">
        <Timer />
      </el-icon>
      <span>{{ connectionMessage }}</span>
    </div>

    <!-- 缓存状态提示 -->
    <div v-if="isUsingCache" class="cache-status">
      <el-icon><Warning /></el-icon>
      <span>当前显示缓存数据，上次更新：{{ formatLastUpdate }}</span>
      <el-button link size="small" @click="refreshData">
        <el-icon><Refresh /></el-icon>
        刷新
      </el-button>
    </div>

    <!-- 统计卡片 -->
    <AlertStats />

    <!-- 主内容区 -->
    <div class="main-content">
      <!-- 左侧日历 -->
      <div class="calendar-section">
        <AlertCalendar />
      </div>

      <!-- 右侧列表 -->
      <div class="list-section">
        <!-- 筛选器 -->
        <AlertFilter />
        
        <!-- 预警列表 -->
        <div class="list-container">
          <AlertList
            :is-loading="isLoading"
            @card-click="handleCardClick"
            @acknowledge="handleAcknowledge"
            @detail="handleDetail"
          />
        </div>
      </div>
    </div>

    <!-- 详情弹窗 -->
    <AlertDetailModal
      v-model="detailModalVisible"
      :alert="selectedAlert"
      @acknowledge="handleAcknowledge"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useAlertStore } from '@/stores/alert'
import { Loading, CircleCheck, Timer, Warning, Refresh } from '@element-plus/icons-vue'
import AlertStats from './AlertStats.vue'
import AlertCalendar from './AlertCalendar.vue'
import AlertFilter from './AlertFilter.vue'
import AlertList from './AlertList.vue'
import AlertDetailModal from './AlertDetailModal.vue'

const alertStore = useAlertStore()

const isLoading = computed(() => alertStore.isLoading)
const unacknowledgedCount = computed(() => alertStore.unacknowledgedCount)
const connectionStatus = computed(() => alertStore.connectionStatus)
const connectionMessage = computed(() => alertStore.connectionMessage)
const isUsingCache = computed(() => alertStore.isUsingCache)
const lastSuccessfulFetch = computed(() => alertStore.lastSuccessfulFetch)

// 格式化上次更新时间
const formatLastUpdate = computed(() => {
  if (!lastSuccessfulFetch.value) return '-'
  const date = new Date(lastSuccessfulFetch.value)
  return date.toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
})

// 手动刷新数据
const refreshData = () => {
  alertStore.fetchAlerts({ useCache: false, silent: false })
}

// 是否显示连接状态（连接成功后3秒自动隐藏）
const showConnectionStatus = computed(() => {
  // 连接中、轮询模式、断线时始终显示
  if (connectionStatus.value === 'connecting' || 
      connectionStatus.value === 'polling' || 
      connectionStatus.value === 'disconnected') {
    return true
  }
  // 连接成功时显示3秒后隐藏
  return true
})

const detailModalVisible = ref(false)
const selectedAlert = ref(null)

onMounted(() => {
  // 加载预警列表
  alertStore.fetchAlerts()
  
  // 连接WebSocket
  const user = JSON.parse(localStorage.getItem('user') || '{}')
  if (user.id) {
    alertStore.connectWebSocket(user.id)
  }
})

onUnmounted(() => {
  // 断开WebSocket
  alertStore.disconnectWebSocket()
})

const handleCardClick = (alert) => {
  selectedAlert.value = alert
  detailModalVisible.value = true
}

const handleAcknowledge = async (alertId) => {
  try {
    await alertStore.acknowledgeAlert(alertId)
  } catch (error) {
    console.error('确认预警失败:', error)
  }
}

const handleDetail = (alert) => {
  selectedAlert.value = alert
  detailModalVisible.value = true
}
</script>

<style scoped>
.alert-page {
  padding: 32px;
  max-width: 1600px;
  margin: 0 auto;
  min-height: 100%;
}

.page-header {
  margin-bottom: 24px;
}

.header-title {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}

.title-icon {
  font-size: 32px;
}

.header-title h2 {
  font-size: 28px;
  font-weight: 600;
  color: #2c3e50;
  margin: 0;
}

.title-badge :deep(.el-badge__content) {
  font-size: 12px;
  padding: 0 6px;
  height: 18px;
  line-height: 18px;
}

.header-subtitle {
  font-size: 14px;
  color: #7f8c8d;
  margin: 0;
  padding-left: 44px;
}

.connection-status {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  border-radius: 8px;
  margin-bottom: 20px;
  font-size: 13px;
  transition: all 0.3s ease;
}

.connection-status.connecting {
  background: rgba(102, 126, 234, 0.1);
  color: #667eea;
  border: 1px solid rgba(102, 126, 234, 0.2);
}

.connection-status.connected {
  background: rgba(39, 174, 96, 0.1);
  color: #27ae60;
  border: 1px solid rgba(39, 174, 96, 0.2);
}

.connection-status.polling {
  background: rgba(243, 156, 18, 0.1);
  color: #f39c12;
  border: 1px solid rgba(243, 156, 18, 0.2);
}

.connection-status.disconnected {
  background: rgba(231, 76, 60, 0.1);
  color: #e74c3c;
  border: 1px solid rgba(231, 76, 60, 0.2);
}

.connection-status .el-icon {
  font-size: 16px;
}

.connection-status .is-loading {
  animation: rotating 2s linear infinite;
}

@keyframes rotating {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

.cache-status {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  background: rgba(243, 156, 18, 0.1);
  color: #f39c12;
  border: 1px solid rgba(243, 156, 18, 0.2);
  border-radius: 8px;
  margin-bottom: 20px;
  font-size: 13px;
}

.cache-status .el-icon {
  font-size: 16px;
}

.cache-status .el-button {
  margin-left: auto;
}

.main-content {
  display: grid;
  grid-template-columns: 320px 1fr;
  gap: 24px;
  align-items: start;
}

.calendar-section {
  position: sticky;
  top: 24px;
}

.list-section {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.list-container {
  background: rgba(255, 255, 255, 0.6);
  backdrop-filter: blur(10px);
  border-radius: 16px;
  padding: 20px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.5);
}

@media (max-width: 1024px) {
  .main-content {
    grid-template-columns: 1fr;
  }
  
  .calendar-section {
    position: static;
    max-width: 400px;
    margin: 0 auto;
  }
}

@media (max-width: 768px) {
  .alert-page {
    padding: 16px;
  }
  
  .header-title h2 {
    font-size: 24px;
  }
  
  .header-subtitle {
    padding-left: 0;
  }
}
</style>
