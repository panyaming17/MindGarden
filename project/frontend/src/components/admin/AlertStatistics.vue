<template>
  <div class="alert-statistics">
    <div class="section-header">
      <h3>预警统计分析</h3>
      <div class="date-range">
        <el-date-picker
          v-model="dateRange"
          type="daterange"
          range-separator="至"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
          :shortcuts="dateShortcuts"
          @change="handleDateChange"
        />
      </div>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-grid">
      <div class="stat-item">
        <div class="stat-label">预警总数</div>
        <div class="stat-value">{{ stats?.total || 0 }}</div>
      </div>
      <div class="stat-item">
        <div class="stat-label">已确认</div>
        <div class="stat-value success">{{ stats?.acknowledged || 0 }}</div>
      </div>
      <div class="stat-item">
        <div class="stat-label">未确认</div>
        <div class="stat-value warning">{{ stats?.unacknowledged || 0 }}</div>
      </div>
      <div class="stat-item">
        <div class="stat-label">平均响应时间</div>
        <div class="stat-value">{{ formatResponseTime(stats?.avg_response_time_hours) }}</div>
      </div>
    </div>

    <!-- 类型分布 -->
    <div class="chart-section">
      <h4>预警类型分布</h4>
      <div class="type-distribution">
        <div class="type-item">
          <div class="type-icon">📝</div>
          <div class="type-info">
            <div class="type-name">问卷预警</div>
            <div class="type-count">{{ stats?.by_type?.questionnaire || 0 }}</div>
          </div>
        </div>
        <div class="type-item">
          <div class="type-icon">😊</div>
          <div class="type-info">
            <div class="type-name">情绪预警</div>
            <div class="type-count">{{ stats?.by_type?.emotion || 0 }}</div>
          </div>
        </div>
        <div class="type-item">
          <div class="type-icon">💬</div>
          <div class="type-info">
            <div class="type-name">对话预警</div>
            <div class="type-count">{{ stats?.by_type?.conversation || 0 }}</div>
          </div>
        </div>
      </div>
    </div>

    <!-- 等级分布 -->
    <div class="chart-section">
      <h4>预警等级分布</h4>
      <div class="level-distribution">
        <div class="level-item danger">
          <div class="level-bar">
            <div 
              class="level-fill" 
              :style="{ width: getLevelPercentage('danger') + '%' }"
            ></div>
          </div>
          <div class="level-info">
            <span class="level-name">高危</span>
            <span class="level-count">{{ stats?.by_level?.danger || 0 }}</span>
          </div>
        </div>
        <div class="level-item warning">
          <div class="level-bar">
            <div 
              class="level-fill" 
              :style="{ width: getLevelPercentage('warning') + '%' }"
            ></div>
          </div>
          <div class="level-info">
            <span class="level-name">中危</span>
            <span class="level-count">{{ stats?.by_level?.warning || 0 }}</span>
          </div>
        </div>
        <div class="level-item info">
          <div class="level-bar">
            <div 
              class="level-fill" 
              :style="{ width: getLevelPercentage('info') + '%' }"
            ></div>
          </div>
          <div class="level-info">
            <span class="level-name">低危</span>
            <span class="level-count">{{ stats?.by_level?.info || 0 }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 趋势数据 -->
    <div class="chart-section" v-if="trendData.length > 0">
      <h4>预警趋势（最近30天）</h4>
      <div class="trend-list">
        <div v-for="item in trendData" :key="item.date" class="trend-item">
          <div class="trend-date">{{ item.date }}</div>
          <div class="trend-bar">
            <div 
              class="trend-fill" 
              :style="{ width: getTrendPercentage(item.count) + '%' }"
            ></div>
          </div>
          <div class="trend-count">{{ item.count }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useAdminAlertStore } from '@/stores/adminAlert'

const store = useAdminAlertStore()

const dateRange = ref([])
const stats = ref(null)

const dateShortcuts = [
  {
    text: '最近7天',
    value: () => {
      const end = new Date()
      const start = new Date()
      start.setTime(start.getTime() - 3600 * 1000 * 24 * 7)
      return [start, end]
    }
  },
  {
    text: '最近30天',
    value: () => {
      const end = new Date()
      const start = new Date()
      start.setTime(start.getTime() - 3600 * 1000 * 24 * 30)
      return [start, end]
    }
  },
  {
    text: '本月',
    value: () => {
      const end = new Date()
      const start = new Date(end.getFullYear(), end.getMonth(), 1)
      return [start, end]
    }
  }
]

const trendData = computed(() => {
  if (!stats.value?.trend) return []
  return Object.entries(stats.value.trend)
    .map(([date, count]) => ({ date, count }))
    .sort((a, b) => a.date.localeCompare(b.date))
    .slice(-30)
})

const getLevelPercentage = (level) => {
  if (!stats.value?.by_level) return 0
  const total = stats.value.total || 1
  const count = stats.value.by_level[level] || 0
  return Math.round((count / total) * 100)
}

const getTrendPercentage = (count) => {
  if (!trendData.value.length) return 0
  const max = Math.max(...trendData.value.map(d => d.count))
  return max > 0 ? (count / max) * 100 : 0
}

const formatResponseTime = (hours) => {
  if (!hours || hours === 0) return '-'
  if (hours < 1) return Math.round(hours * 60) + '分钟'
  if (hours < 24) return Math.round(hours) + '小时'
  return Math.round(hours / 24) + '天'
}

const handleDateChange = async () => {
  if (!dateRange.value || dateRange.value.length !== 2) return
  
  const startDate = dateRange.value[0].toISOString().split('T')[0]
  const endDate = dateRange.value[1].toISOString().split('T')[0]
  
  stats.value = await store.getStatistics(startDate, endDate)
}

onMounted(() => {
  // 默认加载最近30天
  const end = new Date()
  const start = new Date()
  start.setTime(start.getTime() - 3600 * 1000 * 24 * 30)
  dateRange.value = [start, end]
  handleDateChange()
})
</script>

<style scoped>
.alert-statistics {
  padding: 20px 0;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.section-header h3 {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
  margin: 0;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
  margin-bottom: 32px;
}

.stat-item {
  text-align: center;
  padding: 20px;
  background: #f5f7fa;
  border-radius: 8px;
}

.stat-label {
  font-size: 14px;
  color: #606266;
  margin-bottom: 8px;
}

.stat-value {
  font-size: 28px;
  font-weight: 600;
  color: #303133;
}

.stat-value.success {
  color: #67c23a;
}

.stat-value.warning {
  color: #e6a23c;
}

.chart-section {
  margin-bottom: 32px;
}

.chart-section h4 {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  margin: 0 0 16px 0;
}

.type-distribution {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
}

.type-item {
  display: flex;
  align-items: center;
  padding: 16px;
  background: #f5f7fa;
  border-radius: 8px;
}

.type-icon {
  font-size: 32px;
  margin-right: 16px;
}

.type-info {
  flex: 1;
}

.type-name {
  font-size: 14px;
  color: #606266;
  margin-bottom: 4px;
}

.type-count {
  font-size: 24px;
  font-weight: 600;
  color: #303133;
}

.level-distribution {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.level-item {
  display: flex;
  align-items: center;
  gap: 16px;
}

.level-bar {
  flex: 1;
  height: 24px;
  background: #ebeef5;
  border-radius: 12px;
  overflow: hidden;
}

.level-fill {
  height: 100%;
  border-radius: 12px;
  transition: width 0.3s ease;
}

.level-item.danger .level-fill {
  background: #f56c6c;
}

.level-item.warning .level-fill {
  background: #e6a23c;
}

.level-item.info .level-fill {
  background: #409eff;
}

.level-info {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 100px;
}

.level-name {
  font-size: 14px;
  color: #606266;
}

.level-count {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}

.trend-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.trend-item {
  display: flex;
  align-items: center;
  gap: 12px;
}

.trend-date {
  width: 100px;
  font-size: 14px;
  color: #606266;
}

.trend-bar {
  flex: 1;
  height: 20px;
  background: #ebeef5;
  border-radius: 10px;
  overflow: hidden;
}

.trend-fill {
  height: 100%;
  background: #409eff;
  border-radius: 10px;
  transition: width 0.3s ease;
}

.trend-count {
  width: 40px;
  text-align: right;
  font-size: 14px;
  color: #606266;
}

@media (max-width: 768px) {
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .type-distribution {
    grid-template-columns: 1fr;
  }
  
  .section-header {
    flex-direction: column;
    gap: 12px;
    align-items: flex-start;
  }
}
</style>