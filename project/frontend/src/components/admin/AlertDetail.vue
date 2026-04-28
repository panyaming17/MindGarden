<template>
  <div class="alert-detail">
    <div class="detail-header">
      <div class="header-main">
        <el-tag :type="getLevelType(alert.level)" effect="dark" size="large">
          {{ getLevelText(alert.level) }}
        </el-tag>
        <el-tag :type="getTypeType(alert.type)" size="large">
          {{ getTypeText(alert.type) }}
        </el-tag>
      </div>
      <div class="header-status">
        <el-tag :type="alert.is_acknowledged ? 'success' : 'warning'" effect="plain">
          {{ alert.is_acknowledged ? '已确认' : '未确认' }}
        </el-tag>
      </div>
    </div>

    <div class="detail-content">
      <div class="content-section">
        <h4>预警标题</h4>
        <p class="title-text">{{ alert.title }}</p>
      </div>

      <div class="content-section">
        <h4>预警内容</h4>
        <p class="message-text">{{ alert.message }}</p>
      </div>

      <div class="content-section">
        <h4>用户信息</h4>
        <div class="info-grid">
          <div class="info-item">
            <span class="info-label">用户ID:</span>
            <span class="info-value">{{ alert.user_id }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">创建时间:</span>
            <span class="info-value">{{ formatDate(alert.created_at) }}</span>
          </div>
          <div class="info-item" v-if="alert.acknowledged_at">
            <span class="info-label">确认时间:</span>
            <span class="info-value">{{ formatDate(alert.acknowledged_at) }}</span>
          </div>
          <div class="info-item" v-if="alert.acknowledged_by">
            <span class="info-label">确认人:</span>
            <span class="info-value">{{ alert.acknowledged_by }}</span>
          </div>
        </div>
      </div>

      <div class="content-section" v-if="alert.source_data">
        <h4>来源数据</h4>
        <pre class="source-data">{{ JSON.stringify(alert.source_data, null, 2) }}</pre>
      </div>
    </div>

    <div class="detail-actions">
      <el-button 
        v-if="!alert.is_acknowledged" 
        type="success" 
        @click="$emit('acknowledge', alert)"
      >
        <el-icon><Check /></el-icon>
        确认预警
      </el-button>
      <el-button type="danger" plain @click="$emit('delete', alert)">
        <el-icon><Delete /></el-icon>
        删除预警
      </el-button>
    </div>
  </div>
</template>

<script setup>
import { Check, Delete } from '@element-plus/icons-vue'

defineProps({
  alert: {
    type: Object,
    required: true
  }
})

defineEmits(['acknowledge', 'delete'])

const getLevelType = (level) => {
  const map = { danger: 'danger', warning: 'warning', info: 'info' }
  return map[level] || 'info'
}

const getLevelText = (level) => {
  const map = { danger: '高危', warning: '中危', info: '低危' }
  return map[level] || level
}

const getTypeType = (type) => {
  const map = { questionnaire: 'primary', emotion: 'success', conversation: 'warning' }
  return map[type] || ''
}

const getTypeText = (type) => {
  const map = { questionnaire: '问卷', emotion: '情绪', conversation: '对话' }
  return map[type] || type
}

const formatDate = (date) => {
  if (!date) return '-'
  return new Date(date).toLocaleString('zh-CN')
}
</script>

<style scoped>
.alert-detail {
  padding: 20px 0;
}

.detail-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  padding-bottom: 20px;
  border-bottom: 1px solid #ebeef5;
}

.header-main {
  display: flex;
  gap: 12px;
}

.content-section {
  margin-bottom: 24px;
}

.content-section h4 {
  font-size: 14px;
  font-weight: 600;
  color: #606266;
  margin: 0 0 12px 0;
}

.title-text {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
  margin: 0;
}

.message-text {
  font-size: 14px;
  color: #606266;
  line-height: 1.6;
  margin: 0;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}

.info-item {
  display: flex;
  gap: 8px;
}

.info-label {
  font-size: 14px;
  color: #909399;
  min-width: 80px;
}

.info-value {
  font-size: 14px;
  color: #303133;
}

.source-data {
  background: #f5f7fa;
  padding: 16px;
  border-radius: 8px;
  font-size: 12px;
  color: #606266;
  overflow-x: auto;
  margin: 0;
}

.detail-actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
  padding-top: 20px;
  border-top: 1px solid #ebeef5;
}
</style>
