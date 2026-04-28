<template>
  <el-dialog
    v-model="visible"
    title="预警详情"
    width="600px"
    destroy-on-close
    class="alert-detail-modal"
  >
    <div v-if="alert" class="detail-content">
      <!-- 头部信息 -->
      <div class="detail-header">
        <div class="alert-badge" :style="{ background: levelConfig.lightColor, borderColor: levelConfig.color }">
          <span class="badge-icon">{{ levelConfig.icon }}</span>
          <span class="badge-text" :style="{ color: levelConfig.color }">{{ levelConfig.label }}</span>
        </div>
        <div class="alert-meta">
          <span class="meta-item">
            <span class="meta-icon">{{ typeConfig.icon }}</span>
            {{ typeConfig.label }}
          </span>
          <span class="meta-divider">|</span>
          <span class="meta-item">
            <el-icon><Clock /></el-icon>
            {{ formatDateTime(alert.created_at) }}
          </span>
        </div>
      </div>

      <!-- 主要内容 -->
      <div class="detail-body">
        <h3 class="detail-title">{{ alert.title }}</h3>
        <p class="detail-message">{{ alert.message }}</p>

        <!-- 关联数据展示 -->
        <div v-if="alert.sourceData" class="source-data">
          <div class="section-title">关联数据</div>
          
          <!-- 问卷数据 -->
          <div v-if="alert.type === 'questionnaire'" class="data-card">
            <div class="data-header">
              <span class="data-icon">📋</span>
              <span class="data-name">{{ alert.sourceData.templateName || '问卷测评' }}</span>
            </div>
            <div class="data-content">
              <div class="score-display">
                <span class="score-value" :style="{ color: levelConfig.color }">
                  {{ alert.sourceData.score }}
                </span>
                <span class="score-label">分</span>
              </div>
              <div class="data-details">
                <p><strong>测评结果：</strong>{{ alert.sourceData.result }}</p>
                <p><strong>测评时间：</strong>{{ formatDate(alert.sourceData.date) }}</p>
              </div>
            </div>
          </div>

          <!-- 情绪数据 -->
          <div v-else-if="alert.type === 'emotion'" class="data-card">
            <div class="data-header">
              <span class="data-icon">😊</span>
              <span class="data-name">情绪记录</span>
            </div>
            <div class="data-content">
              <div class="emotion-timeline">
                <div 
                  v-for="(record, index) in alert.sourceData.records" 
                  :key="index"
                  class="timeline-item"
                >
                  <div class="timeline-dot" :style="{ background: getEmotionColor(record.emotion) }"></div>
                  <div class="timeline-content">
                    <span class="emotion-name">{{ record.emotion }}</span>
                    <span class="emotion-date">{{ formatDate(record.date) }}</span>
                  </div>
                </div>
              </div>
              <p class="data-summary">{{ alert.sourceData.summary }}</p>
            </div>
          </div>

          <!-- 对话数据 -->
          <div v-else-if="alert.type === 'conversation'" class="data-card">
            <div class="data-header">
              <span class="data-icon">💬</span>
              <span class="data-name">对话内容</span>
            </div>
            <div class="data-content">
              <div class="conversation-preview">
                <p class="preview-text">{{ alert.sourceData.preview }}</p>
              </div>
              <div class="risk-indicators">
                <div class="indicator">
                  <span class="indicator-label">情绪强度：</span>
                  <el-progress 
                    :percentage="alert.sourceData.emotionIntensity * 100" 
                    :color="levelConfig.color"
                    :stroke-width="8"
                  />
                </div>
                <div class="indicator">
                  <span class="indicator-label">危机信号：</span>
                  <el-tag v-if="alert.sourceData.crisisDetected" type="danger" size="small">检测到</el-tag>
                  <el-tag v-else type="success" size="small">未检测</el-tag>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 处理信息 -->
        <div v-if="alert.is_acknowledged" class="acknowledge-info">
          <div class="section-title">处理信息</div>
          <div class="info-content">
            <p><strong>处理状态：</strong><el-tag type="success">已处理</el-tag></p>
            <p><strong>处理时间：</strong>{{ formatDateTime(alert.acknowledged_at) }}</p>
            <p v-if="alert.acknowledged_by"><strong>处理人：</strong>{{ alert.acknowledged_by }}</p>
          </div>
        </div>
      </div>
    </div>

    <!-- 底部操作 -->
    <template #footer>
      <div class="modal-footer">
        <el-button @click="visible = false">关闭</el-button>
        <el-button
          v-if="alert && !alert.is_acknowledged"
          type="primary"
          @click="handleAcknowledge"
        >
          <el-icon><Check /></el-icon>
          确认处理
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup>
import { computed } from 'vue'
import { Clock, Check } from '@element-plus/icons-vue'
import { alertTypeConfig, alertLevelConfig } from '@/stores/alert'
import { ElMessage } from 'element-plus'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  alert: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['update:modelValue', 'acknowledge'])

const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

const typeConfig = computed(() => {
  if (!props.alert) return { label: '', icon: '', color: '' }
  return alertTypeConfig[props.alert.type] || {
    label: '其他',
    icon: '📌',
    color: '#999'
  }
})

const levelConfig = computed(() => {
  if (!props.alert) return { label: '', icon: '', color: '', lightColor: '' }
  return alertLevelConfig[props.alert.level] || {
    label: '未知',
    color: '#999',
    lightColor: '#f5f5f5',
    icon: '❓'
  }
})

const formatDateTime = (timestamp) => {
  if (!timestamp) return '-'
  return new Date(timestamp).toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleDateString('zh-CN', {
    month: 'short',
    day: 'numeric'
  })
}

const getEmotionColor = (emotion) => {
  const colorMap = {
    '开心': '#FFD93D',
    '兴奋': '#FF6B6B',
    '平静': '#6BCB77',
    '疲惫': '#95A5A6',
    '难过': '#74B9FF',
    '焦虑': '#E17055',
    '愤怒': '#D63031',
    '担忧': '#FD79A8'
  }
  return colorMap[emotion] || '#999'
}

const handleAcknowledge = () => {
  if (props.alert) {
    emit('acknowledge', props.alert.id)
    visible.value = false
  }
}
</script>

<style scoped>
.alert-detail-modal :deep(.el-dialog__header) {
  margin-right: 0;
  padding: 20px 24px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
}

.alert-detail-modal :deep(.el-dialog__body) {
  padding: 24px;
}

.alert-detail-modal :deep(.el-dialog__footer) {
  padding: 16px 24px;
  border-top: 1px solid rgba(0, 0, 0, 0.05);
}

.detail-content {
  max-height: 60vh;
  overflow-y: auto;
}

.detail-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
}

.alert-badge {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border-radius: 20px;
  border: 2px solid;
}

.badge-icon {
  font-size: 16px;
}

.badge-text {
  font-size: 14px;
  font-weight: 600;
}

.alert-meta {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 13px;
  color: #666;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 4px;
}

.meta-icon {
  font-size: 14px;
}

.meta-divider {
  color: #ddd;
}

.detail-body {
  padding: 0 4px;
}

.detail-title {
  font-size: 18px;
  font-weight: 600;
  color: #2c3e50;
  margin: 0 0 12px 0;
}

.detail-message {
  font-size: 14px;
  color: #666;
  line-height: 1.6;
  margin: 0 0 20px 0;
  padding: 16px;
  background: rgba(0, 0, 0, 0.02);
  border-radius: 8px;
}

.section-title {
  font-size: 14px;
  font-weight: 600;
  color: #333;
  margin-bottom: 12px;
  padding-left: 8px;
  border-left: 3px solid #667eea;
}

.source-data {
  margin-bottom: 20px;
}

.data-card {
  background: rgba(255, 255, 255, 0.8);
  border: 1px solid rgba(0, 0, 0, 0.06);
  border-radius: 12px;
  overflow: hidden;
}

.data-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  background: rgba(0, 0, 0, 0.02);
  border-bottom: 1px solid rgba(0, 0, 0, 0.04);
}

.data-icon {
  font-size: 18px;
}

.data-name {
  font-size: 14px;
  font-weight: 500;
  color: #333;
}

.data-content {
  padding: 16px;
}

.score-display {
  display: flex;
  align-items: baseline;
  gap: 4px;
  margin-bottom: 12px;
}

.score-value {
  font-size: 36px;
  font-weight: 700;
}

.score-label {
  font-size: 14px;
  color: #666;
}

.data-details p {
  margin: 8px 0;
  font-size: 13px;
  color: #666;
}

.emotion-timeline {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 12px;
}

.timeline-item {
  display: flex;
  align-items: center;
  gap: 12px;
}

.timeline-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  flex-shrink: 0;
}

.timeline-content {
  display: flex;
  justify-content: space-between;
  flex: 1;
  font-size: 13px;
}

.emotion-name {
  font-weight: 500;
  color: #333;
}

.emotion-date {
  color: #999;
}

.data-summary {
  font-size: 13px;
  color: #666;
  font-style: italic;
  padding-top: 12px;
  border-top: 1px dashed rgba(0, 0, 0, 0.1);
}

.conversation-preview {
  background: rgba(102, 126, 234, 0.05);
  padding: 12px;
  border-radius: 8px;
  margin-bottom: 12px;
}

.preview-text {
  margin: 0;
  font-size: 13px;
  color: #666;
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.risk-indicators {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.indicator {
  display: flex;
  align-items: center;
  gap: 12px;
}

.indicator-label {
  font-size: 13px;
  color: #666;
  white-space: nowrap;
  width: 80px;
}

.indicator :deep(.el-progress) {
  flex: 1;
}

.acknowledge-info {
  padding: 16px;
  background: rgba(39, 174, 96, 0.05);
  border-radius: 12px;
  border: 1px solid rgba(39, 174, 96, 0.1);
}

.info-content p {
  margin: 8px 0;
  font-size: 13px;
  color: #666;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}
</style>
