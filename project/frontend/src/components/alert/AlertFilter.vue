<template>
  <div class="alert-filter">
    <div class="filter-group">
      <span class="filter-label">类型：</span>
      <el-radio-group v-model="filters.type" size="small" @change="handleTypeChange">
        <el-radio-button label="all">全部</el-radio-button>
        <el-radio-button label="questionnaire">📋 问卷</el-radio-button>
        <el-radio-button label="emotion">😊 情绪</el-radio-button>
        <el-radio-button label="conversation">💬 对话</el-radio-button>
      </el-radio-group>
    </div>
    
    <div class="filter-group">
      <span class="filter-label">等级：</span>
      <el-radio-group v-model="filters.level" size="small" @change="handleLevelChange">
        <el-radio-button label="all">全部</el-radio-button>
        <el-radio-button label="info">
          <span class="level-dot" style="background: #3498db;"></span>
          提示
        </el-radio-button>
        <el-radio-button label="warning">
          <span class="level-dot" style="background: #f39c12;"></span>
          警告
        </el-radio-button>
        <el-radio-button label="danger">
          <span class="level-dot" style="background: #e74c3c;"></span>
          危险
        </el-radio-button>
      </el-radio-group>
    </div>
    
    <div class="filter-group">
      <span class="filter-label">状态：</span>
      <el-radio-group v-model="filters.status" size="small" @change="handleStatusChange">
        <el-radio-button label="all">全部</el-radio-button>
        <el-radio-button label="unacknowledged">⏳ 待处理</el-radio-button>
        <el-radio-button label="acknowledged">✅ 已处理</el-radio-button>
      </el-radio-group>
    </div>
    
    <div class="filter-actions">
      <el-button 
        v-if="hasActiveFilters" 
        type="info" 
        link 
        size="small"
        @click="clearAllFilters"
      >
        <el-icon><Close /></el-icon>
        清除筛选
      </el-button>
      
      <el-button 
        v-if="showAcknowledgeAll && unacknowledgedCount > 0"
        type="primary"
        size="small"
        @click="handleAcknowledgeAll"
      >
        <el-icon><Check /></el-icon>
        全部确认
      </el-button>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { Close, Check } from '@element-plus/icons-vue'
import { useAlertStore } from '@/stores/alert'

const alertStore = useAlertStore()

const filters = computed(() => alertStore.filters)
const unacknowledgedCount = computed(() => alertStore.unacknowledgedCount)

const hasActiveFilters = computed(() => {
  return filters.value.type !== 'all' || 
         filters.value.level !== 'all' || 
         filters.value.status !== 'all'
})

const showAcknowledgeAll = computed(() => {
  return filters.value.status === 'unacknowledged' || filters.value.status === 'all'
})

const handleTypeChange = (value) => {
  alertStore.setFilter('type', value)
}

const handleLevelChange = (value) => {
  alertStore.setFilter('level', value)
}

const handleStatusChange = (value) => {
  alertStore.setFilter('status', value)
}

const clearAllFilters = () => {
  alertStore.clearFilters()
}

const handleAcknowledgeAll = () => {
  alertStore.acknowledgeAll()
}
</script>

<style scoped>
.alert-filter {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 20px;
  padding: 16px 20px;
  background: rgba(255, 255, 255, 0.6);
  backdrop-filter: blur(10px);
  border-radius: 12px;
  margin-bottom: 20px;
}

.filter-group {
  display: flex;
  align-items: center;
  gap: 8px;
}

.filter-label {
  font-size: 14px;
  color: #666;
  font-weight: 500;
  white-space: nowrap;
}

.level-dot {
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  margin-right: 4px;
}

.filter-actions {
  margin-left: auto;
  display: flex;
  gap: 12px;
}

:deep(.el-radio-button__inner) {
  display: flex;
  align-items: center;
  gap: 4px;
}

@media (max-width: 768px) {
  .alert-filter {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .filter-group {
    width: 100%;
  }
  
  .filter-actions {
    margin-left: 0;
    width: 100%;
    justify-content: flex-end;
  }
}
</style>
