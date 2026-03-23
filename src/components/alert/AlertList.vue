<template>
  <div class="alert-list">
    <h3>预警提醒</h3>
    
    <div v-if="alerts.length === 0" class="empty-state">
      <el-empty description="暂无预警信息" />
    </div>
    
    <div v-else class="alert-items">
      <div 
        v-for="alert in alerts" 
        :key="alert.id" 
        class="alert-item"
        :class="{ 'unacknowledged': !alert.is_acknowledged, 'danger': alert.alert_level === 'danger' }"
      >
        <div class="alert-header">
          <div class="alert-type">
            <span class="type-badge" :class="alert.alert_type">
              {{ alert.alert_type === 'session' ? '会话预警' : '趋势预警' }}
            </span>
            <span class="level-badge" :class="alert.alert_level">
              {{ alert.alert_level === 'warning' ? '警告' : '危险' }}
            </span>
          </div>
          <div class="alert-time">
            {{ formatDate(alert.created_at) }}
          </div>
        </div>
        
        <div class="alert-content">
          {{ alert.message }}
        </div>
        
        <div class="alert-actions">
          <el-button 
            v-if="!alert.is_acknowledged" 
            type="primary" 
            size="small"
            @click="acknowledgeAlert(alert.id)"
          >
            确认处理
          </el-button>
          <el-button 
            type="info" 
            size="small"
            @click="viewDetails(alert)"
          >
            查看详情
          </el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElEmpty } from 'element-plus'
import { alertApi } from '@/utils/api'

// 响应式数据
const alerts = ref([])
const isLoading = ref(false)

// 方法
const formatDate = (timestamp) => {
  return new Date(timestamp).toLocaleString('zh-CN')
}

const acknowledgeAlert = async (alertId) => {
  try {
    // 调用 API 确认预警
    await alertApi.acknowledge(alertId)
    
    // 更新本地数据
    const alert = alerts.value.find(item => item.id === alertId)
    if (alert) {
      alert.is_acknowledged = true
    }
    
    ElMessage.success('预警已确认')
  } catch (error) {
    ElMessage.error('确认失败，请重试')
  }
}

const viewDetails = (alert) => {
  // 查看预警详情
  console.log('查看预警详情:', alert)
  ElMessage.info('查看预警详情功能开发中')
}

// 组件挂载时
onMounted(() => {
  // 加载预警列表
  loadAlerts()
})

const loadAlerts = async () => {
  try {
    isLoading.value = true
    const user = JSON.parse(localStorage.getItem('user'))
    if (!user?.id) {
      ElMessage.error('用户未登录')
      return
    }
    
    const data = await alertApi.getList(user.id)
    alerts.value = data
  } catch (error) {
    console.error('加载预警失败:', error)
    ElMessage.error('加载预警失败')
  } finally {
    isLoading.value = false
  }
}
</script>

<style scoped>
.alert-list {
  background: white;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.alert-list h3 {
  font-size: 18px;
  font-weight: 500;
  margin-bottom: 20px;
  color: #34495e;
  border-bottom: 2px solid #42b983;
  padding-bottom: 10px;
}

.empty-state {
  padding: 40px 0;
}

.alert-items {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.alert-item {
  padding: 16px;
  border-radius: 8px;
  border: 1px solid #e0e0e0;
  transition: all 0.3s ease;
}

.alert-item:hover {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.alert-item.unacknowledged {
  border-left: 4px solid #ff9800;
  background-color: #fff8e1;
}

.alert-item.danger {
  border-left: 4px solid #f44336;
  background-color: #ffebee;
}

.alert-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.alert-type {
  display: flex;
  gap: 8px;
}

.type-badge, .level-badge {
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}

.type-badge.session {
  background-color: #e3f2fd;
  color: #1976d2;
}

.type-badge.trend {
  background-color: #e8f5e8;
  color: #388e3c;
}

.level-badge.warning {
  background-color: #fff3e0;
  color: #f57c00;
}

.level-badge.danger {
  background-color: #ffebee;
  color: #d32f2f;
}

.alert-time {
  font-size: 12px;
  color: #666;
}

.alert-content {
  margin-bottom: 16px;
  line-height: 1.5;
  color: #333;
}

.alert-actions {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
}

@media (max-width: 768px) {
  .alert-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
  
  .alert-actions {
    justify-content: flex-start;
  }
}
</style>
