<template>
  <div 
    class="alert-card"
    :class="{ 
      'unacknowledged': !alert.is_acknowledged,
      [alert.level]: true 
    }"
    @click="$emit('click', alert)"
  >
    <div class="card-header">
      <div class="alert-type">
        <span class="type-icon">{{ typeConfig.icon }}</span>
        <span class="type-label">{{ typeConfig.label }}</span>
      </div>
      <div class="alert-level">
        <el-tag 
          :type="levelType" 
          size="small"
          effect="light"
        >
          <span class="level-icon">{{ levelConfig.icon }}</span>
          {{ levelConfig.label }}
        </el-tag>
      </div>
    </div>
    
    <div class="card-body">
      <h4 class="alert-title">{{ alert.title }}</h4>
      <p class="alert-message">{{ alert.message }}</p>
    </div>
    
    <div class="card-footer">
      <div class="alert-time">
        <el-icon><Clock /></el-icon>
        {{ formatTime(alert.created_at) }}
      </div>
      <div class="alert-status">
        <el-tag 
          v-if="alert.is_acknowledged" 
          type="success" 
          size="small"
        >
          已处理
        </el-tag>
        <el-tag 
          v-else 
          type="warning" 
          size="small"
        >
          待处理
        </el-tag>
      </div>
    </div>
    
    <div class="card-actions" @click.stop>
      <el-button
        v-if="!alert.is_acknowledged"
        type="primary"
        size="small"
        @click="$emit('acknowledge', alert.id)"
      >
        <el-icon><Check /></el-icon>
        确认
      </el-button>
      <el-button
        type="info"
        size="small"
        @click="$emit('detail', alert)"
      >
        <el-icon><View /></el-icon>
        详情
      </el-button>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { Clock, Check, View } from '@element-plus/icons-vue'
import { alertTypeConfig, alertLevelConfig } from '@/stores/alert'

const props = defineProps({
  alert: {
    type: Object,
    required: true
  }
})

defineEmits(['click', 'acknowledge', 'detail'])

const typeConfig = computed(() => {
  return alertTypeConfig[props.alert.type] || {
    label: '其他',
    icon: '📌',
    color: '#999'
  }
})

const levelConfig = computed(() => {
  return alertLevelConfig[props.alert.level] || {
    label: '未知',
    color: '#999',
    lightColor: '#f5f5f5',
    icon: '❓'
  }
})

const levelType = computed(() => {
  const typeMap = {
    info: 'info',
    warning: 'warning',
    danger: 'danger'
  }
  return typeMap[props.alert.level] || 'info'
})

const formatTime = (timestamp) => {
  const date = new Date(timestamp)
  const now = new Date()
  const diff = now - date
  
  // 小于1小时
  if (diff < 3600000) {
    const minutes = Math.floor(diff / 60000)
    return minutes < 1 ? '刚刚' : `${minutes}分钟前`
  }
  
  // 小于24小时
  if (diff < 86400000) {
    const hours = Math.floor(diff / 3600000)
    return `${hours}小时前`
  }
  
  // 小于7天
  if (diff < 604800000) {
    const days = Math.floor(diff / 86400000)
    return `${days}天前`
  }
  
  // 默认显示日期
  return date.toLocaleDateString('zh-CN', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}
</script>

<style scoped>
.alert-card {
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(10px);
  border-radius: 16px;
  padding: 16px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.5);
  transition: all 0.3s ease;
  cursor: pointer;
  position: relative;
  overflow: hidden;
}

.alert-card::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 4px;
  background: #ddd;
  transition: all 0.3s ease;
}

.alert-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
}

.alert-card.info::before {
  background: #3498db;
}

.alert-card.warning::before {
  background: #f39c12;
}

.alert-card.danger::before {
  background: #e74c3c;
}

.alert-card.unacknowledged {
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.95) 0%, rgba(255, 248, 240, 0.9) 100%);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.alert-type {
  display: flex;
  align-items: center;
  gap: 6px;
}

.type-icon {
  font-size: 18px;
}

.type-label {
  font-size: 13px;
  color: #666;
  font-weight: 500;
}

.level-icon {
  margin-right: 2px;
}

.card-body {
  margin-bottom: 12px;
}

.alert-title {
  font-size: 15px;
  font-weight: 600;
  color: #2c3e50;
  margin: 0 0 8px 0;
  line-height: 1.4;
}

.alert-message {
  font-size: 13px;
  color: #666;
  margin: 0;
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  padding-bottom: 12px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
}

.alert-time {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: #999;
}

.card-actions {
  display: flex;
  gap: 8px;
}

.card-actions .el-button {
  flex: 1;
}
</style>
