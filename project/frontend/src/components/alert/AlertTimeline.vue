<template>
  <div class="alert-timeline">
    <!-- 筛选栏 -->
    <div class="filter-bar">
      <a-select v-model:value="filters.type" placeholder="类型" style="width: 120px">
        <a-select-option value="">全部</a-select-option>
        <a-select-option value="questionnaire">问卷</a-select-option>
        <a-select-option value="emotion">情绪</a-select-option>
        <a-select-option value="conversation">对话</a-select-option>
      </a-select>
      <a-select v-model:value="filters.level" placeholder="等级" style="width: 120px">
        <a-select-option value="">全部</a-select-option>
        <a-select-option value="info">提示</a-select-option>
        <a-select-option value="warning">警告</a-select-option>
        <a-select-option value="danger">危险</a-select-option>
      </a-select>
      <a-select v-model:value="filters.status" placeholder="状态" style="width: 120px">
        <a-select-option value="">全部</a-select-option>
        <a-select-option value="unacknowledged">未确认</a-select-option>
        <a-select-option value="acknowledged">已确认</a-select-option>
      </a-select>
      <a-range-picker v-model:value="filters.dateRange" />
      <a-button type="primary" @click="fetchAlerts">查询</a-button>
    </div>

    <!-- 快捷筛选 -->
    <div class="quick-filters">
      <a-tag :class="{ active: activeFilter === 'all' }" @click="setFilter('all')">
        全部({{ counts.total }})
      </a-tag>
      <a-tag color="red" :class="{ active: activeFilter === 'danger' }" @click="setFilter('danger')">
        危险({{ counts.danger }})
      </a-tag>
      <a-tag color="orange" :class="{ active: activeFilter === 'warning' }" @click="setFilter('warning')">
        警告({{ counts.warning }})
      </a-tag>
      <a-tag :class="{ active: activeFilter === 'unacknowledged' }" @click="setFilter('unacknowledged')">
        未确认({{ counts.unacknowledged }})
      </a-tag>
    </div>

    <!-- 时间线列表 -->
    <a-timeline v-if="alerts.length > 0">
      <a-timeline-item
        v-for="alert in alerts"
        :key="alert.id"
        :color="getLevelColor(alert.level)"
      >
        <template #dot>
          <AlertOutlined v-if="alert.level === 'info'" />
          <WarningOutlined v-else-if="alert.level === 'warning'" />
          <StopOutlined v-else-if="alert.level === 'danger'" class="danger-icon" />
        </template>
        
        <div class="alert-card" :class="{ 'unacknowledged': !alert.is_acknowledged }" @click="showDetail(alert)">
          <div class="alert-header">
            <span class="alert-time">{{ formatTime(alert.created_at) }}</span>
            <a-tag :color="getLevelColor(alert.level)">{{ getLevelText(alert.level) }}</a-tag>
            <a-tag>{{ getTypeText(alert.type) }}</a-tag>
          </div>
          <h4 class="alert-title">{{ alert.title }}</h4>
          <p class="alert-message">{{ alert.message }}</p>
          <div class="alert-actions">
            <a-button v-if="!alert.is_acknowledged" type="primary" size="small" @click.stop="acknowledge(alert.id)">
              确认
            </a-button>
            <a-tag v-else color="success">已确认</a-tag>
          </div>
        </div>
      </a-timeline-item>
    </a-timeline>

    <!-- 空状态 -->
    <a-empty v-else description="暂无预警提醒">
      <template #image>
        <SmileOutlined style="font-size: 64px; color: #52c41a;" />
      </template>
      <p>您的心理状态良好，继续保持！</p>
      <a-button type="primary" @click="$router.push('/emotion/record')">去记录情绪</a-button>
    </a-empty>

    <!-- 详情抽屉 -->
    <a-drawer
      v-model:visible="detailVisible"
      title="预警详情"
      placement="right"
      width="500"
    >
      <AlertDetail v-if="selectedAlert" :alert="selectedAlert" />
    </a-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { AlertOutlined, WarningOutlined, StopOutlined, SmileOutlined } from '@ant-design/icons-vue'
import { message } from 'ant-design-vue'
import { useAlertStore } from '@/stores/alert'
import AlertDetail from '@/components/admin/AlertDetail.vue'

const alertStore = useAlertStore()

const alerts = ref([])
const counts = reactive({ total: 0, danger: 0, warning: 0, unacknowledged: 0 })
const filters = reactive({ type: '', level: '', status: '', dateRange: null })
const activeFilter = ref('all')
const detailVisible = ref(false)
const selectedAlert = ref(null)

const fetchAlerts = async () => {
  const res = await alertStore.getAlerts(filters)
  alerts.value = res.alerts
  updateCounts()
}

const updateCounts = async () => {
  const stats = await alertStore.getStats()
  counts.total = stats.total
  counts.danger = stats.by_level?.danger || 0
  counts.warning = stats.by_level?.warning || 0
  counts.unacknowledged = stats.unacknowledged
}

const setFilter = (type: string) => {
  activeFilter.value = type
  if (type === 'all') {
    filters.level = ''
    filters.status = ''
  } else if (type === 'danger' || type === 'warning') {
    filters.level = type
    filters.status = ''
  } else if (type === 'unacknowledged') {
    filters.status = type
    filters.level = ''
  }
  fetchAlerts()
}

const acknowledge = async (id: string) => {
  await alertStore.acknowledgeAlert(id)
  message.success('已确认预警')
  fetchAlerts()
}

const showDetail = (alert: any) => {
  selectedAlert.value = alert
  detailVisible.value = true
}

const getLevelColor = (level: string) => {
  const colors = { info: 'blue', warning: 'orange', danger: 'red' }
  return colors[level] || 'blue'
}

const getLevelText = (level: string) => {
  const texts = { info: '提示', warning: '警告', danger: '危险' }
  return texts[level] || level
}

const getTypeText = (type: string) => {
  const texts = { questionnaire: '问卷', emotion: '情绪', conversation: '对话' }
  return texts[type] || type
}

const formatTime = (time: string) => {
  return new Date(time).toLocaleString('zh-CN')
}

onMounted(() => {
  fetchAlerts()
  alertStore.initWebSocket()
})
</script>

<style scoped>
.alert-timeline {
  padding: 20px;
}

.filter-bar {
  display: flex;
  gap: 10px;
  margin-bottom: 16px;
}

.quick-filters {
  margin-bottom: 20px;
}

.quick-filters .ant-tag {
  cursor: pointer;
  margin-right: 8px;
}

.quick-filters .ant-tag.active {
  font-weight: bold;
  box-shadow: 0 0 0 2px #1890ff;
}

.alert-card {
  padding: 16px;
  background: #fafafa;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s;
}

.alert-card:hover {
  background: #f0f0f0;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.alert-card.unacknowledged {
  border-left: 4px solid #ff4d4f;
}

.alert-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.alert-time {
  color: #999;
  font-size: 12px;
}

.alert-title {
  margin: 0 0 8px 0;
  font-size: 16px;
}

.alert-message {
  color: #666;
  margin-bottom: 12px;
}

.danger-icon {
  color: #ff4d4f;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.2); }
}
</style>
