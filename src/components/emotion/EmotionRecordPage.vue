<template>
  <div class="emotion-record-page">
    <!-- 页面标题 -->
    <div class="page-header">
      <h2 class="page-title">情绪记录</h2>
    </div>

    <!-- 主体内容区 -->
    <div class="main-grid">
      <!-- 第一行：快速记录 + 日历 -->
      <div class="grid-row row-1">
        <!-- 左上：快速记录 -->
        <div class="quick-record-section">
          <div class="section-header">
            <h3 class="section-title">记录此刻心情</h3>
            <p class="section-subtitle">选择表情，记录当下</p>
          </div>
          <div class="quick-emotions">
            <div
              v-for="emotion in quickEmotions"
              :key="emotion.type"
              class="quick-emotion-item"
              @click="quickRecord(emotion)"
            >
              <span class="emotion-icon">{{ emotion.icon }}</span>
            </div>
          </div>
          <el-button type="primary" class="full-record-btn" @click="showQuickModal = true">
            <el-icon><Edit /></el-icon>
            完整记录
          </el-button>
        </div>

        <!-- 右上：日历 -->
        <div class="calendar-section">
          <div class="section-header">
            <h3 class="section-title">日历</h3>
            <div class="calendar-nav">
              <el-button circle size="small" @click="prevMonth">
                <el-icon><ArrowLeft /></el-icon>
              </el-button>
              <span class="current-month">{{ currentYear }}年{{ currentMonth }}月</span>
              <el-button circle size="small" @click="nextMonth">
                <el-icon><ArrowRight /></el-icon>
              </el-button>
            </div>
          </div>
          <div class="weekdays">
            <span v-for="day in weekDays" :key="day" class="weekday">{{ day }}</span>
          </div>
          <div class="calendar-grid">
            <div
              v-for="(day, index) in calendarDays"
              :key="index"
              class="calendar-day"
              :class="{
                'other-month': !day.isCurrentMonth,
                'today': day.isToday,
                'has-record': day.record
              }"
              @click="handleDayClick(day)"
            >
              <span class="day-number">{{ day.date }}</span>
              <span v-if="day.record" class="day-dot" :style="{ background: getEmotionColor(day.record.emotion_type) }"></span>
            </div>
          </div>
        </div>
      </div>

      <!-- 第二行：情绪趋势 + 情绪分布 + 历史记录 -->
      <div class="grid-row row-2">
        <!-- 左下：趋势图表 -->
        <div class="trend-section">
          <div class="section-header">
            <h3 class="section-title">情绪趋势</h3>
            <el-radio-group v-model="trendRange" size="small">
              <el-radio-button label="7">近7天</el-radio-button>
              <el-radio-button label="30">近30天</el-radio-button>
              <el-radio-button label="90">近3个月</el-radio-button>
            </el-radio-group>
          </div>
          <div class="trend-chart-wrapper">
            <EmotionTrendChart :range="trendRange" />
          </div>
        </div>

        <!-- 中下：情绪分布 -->
        <div class="distribution-section">
          <div class="section-header">
            <h3 class="section-title">情绪分布</h3>
          </div>
          <div ref="distributionChart" class="chart-container"></div>
          <div class="distribution-legend">
            <div
              v-for="item in distributionData.slice(0, 5)"
              :key="item.type"
              class="legend-item"
            >
              <span class="legend-color" :style="{ background: item.color }"></span>
              <span class="legend-name">{{ item.name }}</span>
              <span class="legend-percent">{{ item.percent }}%</span>
            </div>
          </div>
        </div>

        <!-- 右下：历史记录 -->
        <div class="history-section">
          <div class="section-header">
            <h3 class="section-title">历史记录</h3>
          </div>
          <div class="history-list">
            <div
              v-for="record in emotionStore.records.slice(0, 8)"
              :key="record.id"
              class="history-item"
            >
              <div class="history-emotion">
                <span class="emotion-icon">{{ record.emotion_icon }}</span>
                <span class="emotion-name">{{ getEmotionName(record.emotion_type) }}</span>
              </div>
              <div class="history-info">
                <span class="history-date">{{ formatDate(record.record_date) }}</span>
                <span class="history-time">{{ record.record_time }}</span>
              </div>
            </div>
            <el-empty v-if="emotionStore.records.length === 0" description="暂无记录" />
          </div>
        </div>
      </div>
    </div>

    <!-- 快速记录弹窗 -->
    <EmotionQuickModal v-model="showQuickModal" @submit="handleRecordSubmit" />

    <!-- 日期详情弹窗 -->
    <el-dialog
      v-model="showDayDetail"
      :title="selectedDay?.date + '日情绪记录'"
      width="400px"
      class="day-detail-modal"
    >
      <div v-if="selectedDay?.record" class="day-record">
        <div class="record-emotion">
          <span class="emotion-icon-large">{{ selectedDay.record.emotion_icon }}</span>
          <span class="emotion-name">{{ getEmotionName(selectedDay.record.emotion_type) }}</span>
        </div>
        <p v-if="selectedDay.record.signature" class="record-signature">
          {{ selectedDay.record.signature }}
        </p>
        <p class="record-time">记录时间：{{ selectedDay.record.record_time }}</p>
      </div>
      <div v-else class="day-empty">
        <p>这一天还没有记录情绪</p>
        <el-button type="primary" @click="handleSupplementRecord">
          补录情绪
        </el-button>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import { Edit, ArrowLeft, ArrowRight } from '@element-plus/icons-vue'
import { useEmotionStore, emotionTags } from '@/stores/emotion'
import EmotionQuickModal from './EmotionQuickModal.vue'
import EmotionTrendChart from './EmotionTrendChart.vue'

const emotionStore = useEmotionStore()

// 状态
const showQuickModal = ref(false)
const showDayDetail = ref(false)
const selectedDay = ref(null)
const currentYear = ref(new Date().getFullYear())
const currentMonth = ref(new Date().getMonth() + 1)
const trendRange = ref('30')
const distributionChart = ref(null)

// 星期标题
const weekDays = ['日', '一', '二', '三', '四', '五', '六']

// 快速记录的情绪（显示前6个）
const quickEmotions = emotionTags.slice(0, 6)

// 分布数据
const distributionData = computed(() => {
  const counts = {}
  emotionStore.records.forEach(r => {
    counts[r.emotion_type] = (counts[r.emotion_type] || 0) + 1
  })
  
  const total = emotionStore.records.length || 1
  return Object.entries(counts).map(([type, count]) => {
    const emotion = emotionTags.find(e => e.type === type)
    return {
      type,
      name: emotion?.name || type,
      color: emotion?.color || '#999',
      count,
      percent: Math.round((count / total) * 100)
    }
  }).sort((a, b) => b.count - a.count)
})

// 日历数据
const calendarDays = computed(() => {
  const days = []
  const firstDay = new Date(currentYear.value, currentMonth.value - 1, 1)
  const lastDay = new Date(currentYear.value, currentMonth.value, 0)
  const prevLastDay = new Date(currentYear.value, currentMonth.value - 1, 0)
  
  const firstDayWeek = firstDay.getDay()
  for (let i = firstDayWeek - 1; i >= 0; i--) {
    const date = prevLastDay.getDate() - i
    days.push({
      date,
      isCurrentMonth: false,
      isToday: false,
      record: null
    })
  }
  
  const today = new Date()
  for (let i = 1; i <= lastDay.getDate(); i++) {
    const dateStr = `${currentYear.value}-${String(currentMonth.value).padStart(2, '0')}-${String(i).padStart(2, '0')}`
    const record = emotionStore.records.find(r => r.record_date === dateStr)
    
    days.push({
      date: i,
      isCurrentMonth: true,
      isToday: today.getFullYear() === currentYear.value && 
               today.getMonth() + 1 === currentMonth.value && 
               today.getDate() === i,
      record
    })
  }
  
  const remaining = 42 - days.length
  for (let i = 1; i <= remaining; i++) {
    days.push({
      date: i,
      isCurrentMonth: false,
      isToday: false,
      record: null
    })
  }
  
  return days
})

// 初始化
onMounted(async () => {
  await emotionStore.fetchRecords()
  initDistributionChart()
})

// 初始化分布图
const initDistributionChart = () => {
  if (!window.echarts || !distributionChart.value) return

  const distInstance = window.echarts.init(distributionChart.value)

  distInstance.setOption({
    tooltip: {
      trigger: 'item',
      formatter: '{b}: {c} ({d}%)'
    },
    series: [{
      type: 'pie',
      radius: ['40%', '70%'],
      center: ['50%', '50%'],
      avoidLabelOverlap: false,
      itemStyle: {
        borderRadius: 6,
        borderColor: '#fff',
        borderWidth: 2
      },
      label: {
        show: false
      },
      data: distributionData.value.map(item => ({
        name: item.name,
        value: item.count,
        itemStyle: { color: item.color }
      }))
    }]
  })
}

// 月份导航
const prevMonth = () => {
  if (currentMonth.value === 1) {
    currentMonth.value = 12
    currentYear.value--
  } else {
    currentMonth.value--
  }
}

const nextMonth = () => {
  if (currentMonth.value === 12) {
    currentMonth.value = 1
    currentYear.value++
  } else {
    currentMonth.value++
  }
}

// 点击日期
const handleDayClick = (day) => {
  selectedDay.value = day
  showDayDetail.value = true
}

// 快速记录
const quickRecord = async (emotion) => {
  const data = {
    emotion_type: emotion.type,
    emotion_icon: emotion.icon,
    emotion_name: emotion.name,
    emotion_color: emotion.color,
    signature: '',
    record_date: new Date().toISOString().split('T')[0],
    record_time: new Date().toTimeString().slice(0, 8)
  }
  try {
    await emotionStore.recordEmotion(data)
  } catch (error) {
    console.error('快速记录失败:', error)
  }
}

// 补录情绪
const handleSupplementRecord = () => {
  showDayDetail.value = false
  showQuickModal.value = true
}

// 记录提交成功
const handleRecordSubmit = () => {
  emotionStore.fetchRecords()
  initCharts()
}

// 格式化日期
const formatDate = (dateStr) => {
  const date = new Date(dateStr)
  return `${date.getMonth() + 1}/${date.getDate()}`
}

// 获取情绪颜色
const getEmotionColor = (type) => {
  const emotion = emotionTags.find(e => e.type === type)
  return emotion?.color || '#999'
}

// 获取情绪名称
const getEmotionName = (type) => {
  const emotion = emotionTags.find(e => e.type === type)
  return emotion?.name || type
}
</script>

<style scoped>
.emotion-record-page {
  padding: 24px 40px;
  max-width: 100%;
  min-height: 100%;
}

/* 页面标题 */
.page-header {
  margin-bottom: 24px;
}

.page-title {
  font-size: 28px;
  font-weight: 600;
  color: #2c3e50;
}

/* 主体网格 */
.main-grid {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

/* 网格行 */
.grid-row {
  display: flex;
  gap: 32px;
}

.row-1 {
  height: 35%;
}

.row-2 {
  height: 390px;
}

/* 区块通用样式 */
.grid-row > div {
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(10px);
  border-radius: 20px;
  padding: 24px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.5);
  display: flex;
  flex-direction: column;
}

/* 区块头部 */
.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.section-title {
  font-size: 18px;
  font-weight: 600;
  color: #2c3e50;
  margin: 0;
}

.section-subtitle {
  font-size: 13px;
  color: #999;
  margin: 4px 0 0 0;
}

/* 第一行布局 */
.quick-record-section {
  width: 30%;
  flex-shrink: 0;
}

.quick-emotions {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  flex: 1;
  margin-bottom: 16px;
}

.quick-emotion-item {
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f8f9fa;
  border-radius: 16px;
  cursor: pointer;
  transition: all 0.3s ease;
  border: 2px solid transparent;
}

.quick-emotion-item:hover {
  transform: scale(1.05);
  background: white;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.quick-emotion-item .emotion-icon {
  font-size: 40px;
  line-height: 1;
}

.full-record-btn {
  width: 100%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  border-radius: 12px;
  height: 48px;
  font-size: 15px;
}

/* 第一行右侧：日历 */
.calendar-section {
  flex: 1;
}

.calendar-nav {
  display: flex;
  align-items: center;
  gap: 12px;
}

.current-month {
  font-size: 14px;
  font-weight: 500;
  color: #2c3e50;
  min-width: 100px;
  text-align: center;
}

.weekdays {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 4px;
  margin-bottom: 8px;
}

.weekday {
  text-align: center;
  font-size: 12px;
  color: #999;
  padding: 4px;
  font-weight: 500;
}

.calendar-grid {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 4px;
  flex: 1;
}

.calendar-day {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
  position: relative;
  min-height: 36px;
}

.calendar-day:hover {
  background: #f0f0f0;
}

.calendar-day.other-month {
  opacity: 0.3;
}

.calendar-day.today {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.calendar-day.today .day-number {
  color: white;
}

.day-number {
  font-size: 13px;
  color: #2c3e50;
  font-weight: 500;
}

.day-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  margin-top: 2px;
}

/* 第二行布局 */
.trend-section {
  width: 32%;
  flex-shrink: 0;
}

.trend-chart-wrapper {
  flex: 1;
  min-height: 0;
  position: relative;
}

/* 情绪分布 */
.distribution-section {
  flex: 1;
}

.distribution-section .chart-container {
  height: 200px;
  margin-bottom: 12px;
}

.distribution-legend {
  display: flex;
  flex-direction: column;
  gap: 8px;
  overflow-y: auto;
  max-height: 120px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 10px;
  background: #f8f9fa;
  border-radius: 8px;
}

.legend-color {
  width: 12px;
  height: 12px;
  border-radius: 3px;
}

.legend-name {
  flex: 1;
  font-size: 13px;
  color: #2c3e50;
}

.legend-percent {
  font-size: 13px;
  font-weight: 600;
  color: #667eea;
}

/* 历史记录 */
.history-section {
  width: 30%;
  flex-shrink: 0;
}

.history-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  overflow-y: auto;
  flex: 1;
}

.history-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  background: #f8f9fa;
  border-radius: 10px;
  transition: all 0.2s ease;
}

.history-item:hover {
  background: white;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.history-emotion {
  display: flex;
  align-items: center;
  gap: 6px;
}

.history-emotion .emotion-icon {
  font-size: 20px;
}

.history-emotion .emotion-name {
  font-size: 14px;
  font-weight: 500;
  color: #2c3e50;
}

.history-info {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 2px;
}

.history-date {
  font-size: 12px;
  color: #666;
}

.history-time {
  font-size: 11px;
  color: #999;
}

/* 日期详情弹窗 */
.day-detail-modal :deep(.el-dialog__body) {
  padding: 24px;
}

.day-record {
  text-align: center;
}

.record-emotion {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  margin-bottom: 16px;
}

.emotion-icon-large {
  font-size: 64px;
  line-height: 1;
}

.record-emotion .emotion-name {
  font-size: 20px;
  font-weight: 600;
  color: #2c3e50;
}

.record-signature {
  font-size: 16px;
  color: #555;
  line-height: 1.6;
  padding: 16px;
  background: #f8f9fa;
  border-radius: 12px;
  margin-bottom: 16px;
}

.record-time {
  font-size: 14px;
  color: #999;
}

.day-empty {
  text-align: center;
  padding: 32px;
}

.day-empty p {
  font-size: 16px;
  color: #666;
  margin-bottom: 20px;
}

/* 响应式 */
@media (max-width: 1200px) {
  .grid-row {
    flex-direction: column;
  }
  
  .row-1,
  .row-2 {
    height: auto;
  }
  
  .quick-record-section,
  .calendar-section,
  .trend-section,
  .history-section {
    width: 100%;
  }
  
  .quick-emotions {
    max-height: 200px;
  }
}
</style>
