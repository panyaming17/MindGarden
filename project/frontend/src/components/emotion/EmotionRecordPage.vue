<template>
  <div class="emotion-record-page">
    <!-- 页面标题 -->
    <div class="page-header">
      <h2 class="page-title">情绪记录</h2>
    </div>

    <!-- 区块1：快速记录 | 时间线 | 日历（三列并排 20:40:40） -->
    <div class="block-quick-record">
      <!-- 左：快速记录 20% -->
      <div class="quick-record-section-inner">
          <div class="section-header">
            <h3 class="section-title">记录今日心情</h3>
          </div>
        <div class="quick-emotion-grid">
          <div
            v-for="emotion in emotionTags"
            :key="emotion.type"
            class="quick-emotion-cell"
            :class="{ 'selected': selectedEmotion?.type === emotion.type }"
            @click="selectEmotion(emotion)"
          >
            <span class="cell-icon">{{ emotion.icon }}</span>
            <span class="cell-name">{{ emotion.name }}</span>
          </div>
          <!-- 添加自定义情绪按钮（一次性使用） -->
          <div class="quick-emotion-cell add-custom-btn" @click="showCustomEmotionModal = true">
            <span class="cell-icon">
              <el-icon><Plus /></el-icon>
            </span>
            <span class="cell-name">自定义</span>
          </div>
        </div>
        <div class="quick-input-row">
          <input
            ref="quickInputRef"
            v-model="quickInputText"
            class="quick-input"
            maxlength="50"
            :placeholder="selectedEmotion ? '按回车记录情绪...' : '先选择上方情绪，再记录感受...'"
            @keydown.enter.prevent="submitQuickRecord"
            :disabled="!selectedEmotion"
          />
          <span class="input-count">{{ quickInputText.length }} / 50</span>
        </div>
        <!-- 记录按钮 -->
        <div class="quick-submit-row">
          <el-button
            type="primary"
            size="small"
            :disabled="!selectedEmotion"
            :loading="emotionStore.isLoading"
            @click="submitQuickRecord"
            class="record-btn"
          >
            <el-icon><Check /></el-icon>
            记录情绪
          </el-button>
          <span v-if="selectedEmotion" class="selected-hint">
            已选择: {{ selectedEmotion.name }}
          </span>
        </div>
      </div>

      <!-- 中：今日情绪时间线 40% -->
      <EmotionTimeline
        :records="todayRecordsList"
        :loading="timelineLoading"
        @updated="onTimelineUpdated"
        @deleted="onTimelineDeleted"
        @viewAll="onViewAllRecords"
      />

      <!-- 右：日历 40% -->
      <div class="calendar-section">
        <div class="section-header">
          <div class="calendar-title-wrapper">
            <h3 class="section-title">日历</h3>
            <span v-if="consecutiveDays > 0" class="consecutive-days" :class="{ 'broken': isStreakBroken }">
              <el-icon><Calendar /></el-icon>
              已连续记录 {{ consecutiveDays }} 天
            </span>
          </div>
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
              'has-record': day.record,
              'past': day.dateStatus === 'past',
              'future': day.dateStatus === 'future'
            }"
            @click="day.dateStatus !== 'future' && handleDayClick(day)"
          >
            <span class="day-number">{{ day.date }}</span>
            <span v-if="day.record" class="day-dot" :style="{ background: getEmotionColor(day.record.emotion_type) }"></span>
          </div>
        </div>
      </div>
    </div>

    <!-- 区块 2：散点图 + 分布 -->
    <div class="flex-row row-stats">
      <!-- 中医情志二维坐标图 -->
      <EmotionScatterPlot ref="scatterPlotRef" :userId="currentUserId" class="scatter-plot-component" />

      <!-- 情绪分布 -->
      <div class="distribution-section">
        <div class="section-header">
          <h3 class="section-title">情绪分布</h3>
          <el-radio-group v-model="distributionRange" size="small">
            <el-radio-button label="1">今日</el-radio-button>
            <el-radio-button label="7">近 7 天</el-radio-button>
            <el-radio-button label="30">近 1 月</el-radio-button>
            <el-radio-button label="90">近 3 月</el-radio-button>
          </el-radio-group>
        </div>
        <div ref="distributionChart" class="chart-container"></div>
        <div class="distribution-legend">
          <div
            v-for="item in distributionData"
            :key="item.type"
            class="legend-item"
          >
            <span class="legend-color" :style="{ background: item.color }"></span>
            <span class="legend-name">{{ item.name }}</span>
            <span class="legend-percent">{{ item.percent }}%</span>
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

    <!-- 日期详情浮窗 -->
    <DayDetailModal
      v-model="dayDetailVisible"
      :date="selectedDay?.dateStr"
      :date-records="selectedDayRecords"
      @refresh="refreshDayDetail"
    />

    <!-- 自定义情绪弹窗 -->
    <CustomEmotionModal
      v-model="showCustomEmotionModal"
      @submit="handleCustomEmotionSubmit"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import { Edit, ArrowLeft, ArrowRight, Calendar, Plus, Check } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { useEmotionStore, emotionTags } from '@/stores/emotion'
import EmotionQuickModal from './EmotionQuickModal.vue'
import EmotionTrendChart from './EmotionTrendChart.vue'
import EmotionHealthTrend from './EmotionHealthTrend.vue'
import EmotionTimeline from './EmotionTimeline.vue'
import DayDetailModal from './DayDetailModal.vue'
import CustomEmotionModal from './CustomEmotionModal.vue'
import EmotionScatterPlot from './EmotionScatterPlot.vue'

const emotionStore = useEmotionStore()

// 状态
const showQuickModal = ref(false)
const showDayDetail = ref(false)
const scatterPlotRef = ref(null)
const selectedDay = ref(null)

// 日期详情浮窗
const dayDetailVisible = ref(false)
const selectedDayRecords = ref([])
const currentYear = ref(new Date().getFullYear())
const currentMonth = ref(new Date().getMonth() + 1)
const trendRange = ref('30')
const distributionRange = ref('1')  // 默认显示"今日"
const distributionChart = ref(null)
let distributionChartInstance = null
const timelineLoading = ref(false)
const todayRecordsList = computed(() => emotionStore.todayRecords)

// 快速记录状态
const selectedEmotion = ref(null)
const quickInputText = ref('')
const quickInputRef = ref(null)

// 当前用户 ID
const currentUserId = computed(() => {
  const user = localStorage.getItem('user')
  // console.log('[EmotionRecordPage] localStorage user:', user)
  if (user) {
    try {
      const userData = JSON.parse(user)
      const userId = userData.id || userData.userId || ''
      // console.log('[EmotionRecordPage] currentUserId:', userId)
      return userId
    } catch (e) {
      console.error('解析用户数据失败:', e)
      return ''
    }
  }
  console.log('[EmotionRecordPage] 未找到用户 ID，返回空字符串')
  return ''
})

// 自定义情绪（一次性使用，不保存到列表）
const showCustomEmotionModal = ref(false)

// 处理自定义情绪添加（一次性使用）
const handleCustomEmotionSubmit = async (customEmotion) => {
  // console.log('[handleCustomEmotionSubmit] 自定义情绪已保存:', customEmotion)
  
  // 直接选中自定义情绪，不添加到情绪列表
  selectedEmotion.value = customEmotion
  
  // 刷新时间线
  try {
    await emotionStore.fetchTodayRecords()
    console.log('[handleCustomEmotionSubmit] 时间线已刷新')
  } catch (e) {
    console.warn('刷新时间线失败:', e)
  }
  
  // 刷新散点图和情绪分布（延迟一点，确保组件已挂载）
  console.log('[handleCustomEmotionSubmit] 准备刷新散点图和情绪分布')
  nextTick(() => {
    if (scatterPlotRef.value && scatterPlotRef.value.refresh) {
      console.log('[handleCustomEmotionSubmit] 刷新散点图')
      scatterPlotRef.value.refresh()
    } else {
      console.warn('[handleCustomEmotionSubmit] 散点图组件未就绪')
    }
    
    // 刷新情绪分布
    console.log('[handleCustomEmotionSubmit] 准备刷新情绪分布')
    loadDistributionStatistics(1).then(() => {
      console.log('[handleCustomEmotionSubmit] 分布数据已加载，更新图表')
      updateDistributionChart()
    })
  })
}

// 星期标题
const weekDays = ['日', '一', '二', '三', '四', '五', '六']

// 连续记录天数
const consecutiveDays = computed(() => {
  const records = emotionStore.records || []
  if (records.length === 0) return 0

  // 按日期去重并排序
  const dates = [...new Set(records.map(r => r.record_date))].sort().reverse()
  if (dates.length === 0) return 0

  const today = new Date().toISOString().split('T')[0]
  const yesterday = new Date(Date.now() - 86400000).toISOString().split('T')[0]

  // 如果今天没有记录，且昨天也没有记录，则断签
  if (dates[0] !== today && dates[0] !== yesterday) {
    return 0
  }

  // 计算连续天数
  let streak = 1
  for (let i = 1; i < dates.length; i++) {
    const prevDate = new Date(dates[i - 1])
    const currDate = new Date(dates[i])
    const diffDays = (prevDate - currDate) / (1000 * 60 * 60 * 24)

    if (diffDays === 1) {
      streak++
    } else {
      break
    }
  }

  return streak
})

// 是否断签（今天和昨天都没有记录）
const isStreakBroken = computed(() => {
  const records = emotionStore.records || []
  const dates = [...new Set(records.map(r => r.record_date))]
  const today = new Date().toISOString().split('T')[0]
  const yesterday = new Date(Date.now() - 86400000).toISOString().split('T')[0]

  return !dates.includes(today) && !dates.includes(yesterday) && dates.length > 0
})

// 分布数据 - 基于分布专用的统计数据
const distributionData = computed(() => {
  const stats = emotionStore.distributionStatistics
  if (stats?.data?.distribution) {
    return stats.data.distribution
  }
  // 如果没有统计数据，返回空数组
  return []
})

// 趋势数据 - 基于统计数据
const trendData = computed(() => {
  const stats = emotionStore.statistics
  if (stats?.data?.trend) {
    return stats.data.trend
  }
  return []
})

// 健康指标数据 - 从统计数据中获取
const healthMetrics = computed(() => {
  const stats = emotionStore.statistics
  if (stats?.data?.health_metrics) {
    return stats.data.health_metrics
  }
  // 返回默认值
  return {
    avg_health_score: 0,
    health_level: '未知',
    health_color: '#999',
    positive_rate: 0,
    volatility: 0,
    health_trend: 0,
    positive_days: 0,
    negative_days: 0,
    total_days: 0
  }
})

// 监听趋势范围变化，重新获取统计数据
watch(() => trendRange.value, async (newRange) => {
  await loadStatistics(parseInt(newRange))
})

// 监听分布范围变化，重新获取分布统计数据
watch(() => distributionRange.value, async (newRange) => {
  await loadDistributionStatistics(parseInt(newRange))
})

// 监听分布统计数据变化，更新分布图
watch(() => emotionStore.distributionStatistics, () => {
  nextTick(() => {
    updateDistributionChart()
  })
}, { deep: true })

// 日历数据 - 使用从后端获取的日历数据
const calendarDays = computed(() => {
  const days = []
  const firstDay = new Date(currentYear.value, currentMonth.value - 1, 1)
  const lastDay = new Date(currentYear.value, currentMonth.value, 0)
  const prevLastDay = new Date(currentYear.value, currentMonth.value - 1, 0)

  // 从后端日历数据中获取记录映射
  // 注意：后端返回的数据结构是 { code, message, data: { year, month, days } }
  // 每个day的格式是: { date: '2026-04-05', day: 5, has_record: true, record: { ... } }
  const calendarRecords = emotionStore.calendarData?.data?.days || emotionStore.calendarData?.days || []
  const recordMap = new Map()
  calendarRecords.forEach(r => {
    if (r.date && r.has_record && r.record) {
      recordMap.set(r.date, r.record)
    }
  })
  
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
  const todayStr = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`

  for (let i = 1; i <= lastDay.getDate(); i++) {
    const dateStr = `${currentYear.value}-${String(currentMonth.value).padStart(2, '0')}-${String(i).padStart(2, '0')}`
    const record = recordMap.get(dateStr) || null

    // 判断日期状态：past(过去), today(今天), future(未来)
    let dateStatus = 'past'
    if (dateStr === todayStr) {
      dateStatus = 'today'
    } else if (dateStr > todayStr) {
      dateStatus = 'future'
    }

    days.push({
      date: i,
      dateStr,
      isCurrentMonth: true,
      isToday: dateStatus === 'today',
      dateStatus,
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
  // 加载统计数据（用于趋势图表）
  await loadStatistics(parseInt(trendRange.value))
  // 加载分布统计数据（用于分布图表）
  await loadDistributionStatistics(parseInt(distributionRange.value))
  // 加载当前月份日历数据
  await loadCalendarData()
  initDistributionChart()
  // 加载今日时间线记录
  timelineLoading.value = true
  try {
    await emotionStore.fetchTodayRecords()
  } catch (e) {
    console.warn('加载今日记录失败:', e)
  } finally {
    timelineLoading.value = false
  }
})

// 初始化分布图
const initDistributionChart = () => {
  if (!window.echarts || !distributionChart.value) return

  // 如果已存在实例，先销毁
  if (distributionChartInstance) {
    distributionChartInstance.dispose()
  }

  distributionChartInstance = window.echarts.init(distributionChart.value)
  updateDistributionChart()
}

// 更新分布图数据
const updateDistributionChart = () => {
  if (!distributionChartInstance) return

  const data = distributionData.value
  if (!data || data.length === 0) {
    // 没有数据时显示空状态
    distributionChartInstance.setOption({
      title: {
        text: '暂无数据',
        left: 'center',
        top: 'center',
        textStyle: {
          color: '#999',
          fontSize: 14
        }
      },
      series: [{
        type: 'pie',
        radius: ['40%', '70%'],
        data: []
      }]
    })
    return
  }

  distributionChartInstance.setOption({
    title: { show: false },
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
      data: data.map(item => ({
        name: item.name,
        value: item.count,
        itemStyle: { color: item.color }
      }))
    }]
  })
}

// 月份导航
const prevMonth = async () => {
  if (currentMonth.value === 1) {
    currentMonth.value = 12
    currentYear.value--
  } else {
    currentMonth.value--
  }
  // 加载对应月份的日历数据
  await loadCalendarData()
}

const nextMonth = async () => {
  if (currentMonth.value === 12) {
    currentMonth.value = 1
    currentYear.value++
  } else {
    currentMonth.value++
  }
  // 加载对应月份的日历数据
  await loadCalendarData()
}

// 加载日历数据
const loadCalendarData = async () => {
  try {
    await emotionStore.fetchCalendar(currentYear.value, currentMonth.value)
  } catch (e) {
    console.warn('加载日历数据失败:', e)
  }
}

// 加载统计数据
const loadStatistics = async (days = 30) => {
  try {
    await emotionStore.fetchStatistics({ days })
  } catch (e) {
    console.warn('加载统计数据失败:', e)
  }
}

// 加载分布统计数据
const loadDistributionStatistics = async (days = 30) => {
  try {
    await emotionStore.fetchDistributionStatistics({ days })
  } catch (e) {
    console.warn('加载分布统计数据失败:', e)
  }
}

// 点击日期
const handleDayClick = async (day) => {
  if (day.dateStatus === 'future') return

  // 检查是否在可补录范围内（当天或过去 7 天内）
  const today = new Date().toISOString().split('T')[0]
  const sevenDaysAgo = new Date()
  sevenDaysAgo.setDate(sevenDaysAgo.getDate() - 7)
  const sevenDaysAgoStr = sevenDaysAgo.toISOString().split('T')[0]
  
  const isWithinRange = day.dateStr >= sevenDaysAgoStr && day.dateStr <= today
  
  // 如果超出 7 天范围且没有记录，显示提示
  if (!isWithinRange) {
    // 先获取记录，看看是否有数据
    try {
      const records = await emotionStore.fetchDayRecords(day.dateStr)
      if (!records || records.length === 0) {
        // 没有记录且超出范围，显示提示
        ElMessage.warning({
          message: `${day.dateStr} 已超过 7 天补录期限，无法补录情绪`,
          duration: 3000
        })
        return
      }
    } catch (e) {
      console.error('获取日期记录失败:', e)
    }
  }

  // 获取该日期的所有记录
  const dateStr = day.dateStr

  try {
    const records = await emotionStore.fetchDayRecords(dateStr)
    selectedDay.value = { ...day, dateStr }
    selectedDayRecords.value = records || []
    dayDetailVisible.value = true
  } catch (e) {
    console.error('获取日期记录失败:', e)
    // 即使没有记录也打开弹窗
    selectedDay.value = { ...day, dateStr }
    selectedDayRecords.value = []
    dayDetailVisible.value = true
  }
}

// 刷新日期详情
const refreshDayDetail = async () => {
  if (!selectedDay.value) return
  try {
    // 刷新浮窗内的记录列表
    const records = await emotionStore.fetchDayRecords(selectedDay.value.dateStr)
    selectedDayRecords.value = records || []

    // 刷新日历数据 - 确保小点标记更新
    await loadCalendarData()

    // 刷新趋势统计数据
    await loadStatistics(parseInt(trendRange.value))

    // 刷新分布统计数据
    await loadDistributionStatistics(parseInt(distributionRange.value))
    
    // 刷新散点图
    if (scatterPlotRef.value && scatterPlotRef.value.refresh) {
      console.log('[refreshDayDetail] 刷新散点图')
      scatterPlotRef.value.refresh()
    }
    
    // 刷新情绪分布（手动更新图表）
    console.log('[refreshDayDetail] 分布数据已加载，更新图表')
    updateDistributionChart()
  } catch (e) {
    console.error('刷新日期记录失败:', e)
  }
}

// 选择情绪
const selectEmotion = (emotion) => {
  if (selectedEmotion.value?.type === emotion.type) {
    selectedEmotion.value = null
    return
  }
  selectedEmotion.value = emotion
  nextTick(() => {
    quickInputRef.value?.focus()
  })
}

// 提交快速记录（回车或点击）
const submitQuickRecord = async () => {
  // console.log('[submitQuickRecord] 开始提交, selectedEmotion:', selectedEmotion.value, 'quickInputText:', quickInputText.value)

  if (!selectedEmotion.value) {
    console.warn('[submitQuickRecord] 未选择情绪，无法提交')
    alert('请先选择一个表情再记录情绪')
    return
  }

  const emotion = selectedEmotion.value
  const data = {
    emotion_type: emotion.type,
    emotion_icon: emotion.icon,
    emotion_name: emotion.name,
    emotion_color: emotion.color,
    signature: quickInputText.value.trim(),
    record_date: new Date().toISOString().split('T')[0],
    record_time: new Date().toTimeString().slice(0, 8),
    // 自定义情绪的额外字段
    tcm_emotion: emotion.tcmEmotion || null,
    category_type: emotion.categoryType || null,
    category_name: emotion.categoryName || null,
    category_polarity: emotion.categoryPolarity || null,
    health_score: emotion.healthScore || null
  }

  // console.log('[submitQuickRecord] 提交数据:', data)

  try {
    const result = await emotionStore.recordEmotion(data)
    // console.log('[submitQuickRecord] 记录成功:', result)

    // 重置状态
    selectedEmotion.value = null
    quickInputText.value = ''
    console.log('[submitQuickRecord] 状态已重置')

    // 刷新时间线
    try {
      await emotionStore.fetchTodayRecords()
      console.log('[submitQuickRecord] 时间线已刷新')
    } catch (e) {
      console.warn('刷新时间线失败:', e)
    }
    
    // 刷新散点图（延迟一点，确保组件已挂载）
    console.log('[submitQuickRecord] 准备刷新散点图')
    nextTick(() => {
      if (scatterPlotRef.value && scatterPlotRef.value.refresh) {
        console.log('[submitQuickRecord] 刷新散点图')
        scatterPlotRef.value.refresh()
      } else {
        console.warn('[submitQuickRecord] 散点图组件未就绪')
      }
      
      // 刷新情绪分布（与散点图同步）
      console.log('[submitQuickRecord] 准备刷新情绪分布')
      loadDistributionStatistics(1).then(() => {
        console.log('[submitQuickRecord] 分布数据已加载，更新图表')
        updateDistributionChart()
      })
    })
  } catch (error) {
    console.error('[submitQuickRecord] 记录失败:', error)
    
    // 检查是否是时间限制错误
    if (error.message && error.message.includes('距离上次记录时间不足')) {
      ElMessage.error({
        message: error.message,
        duration: 5000,
        showClose: true
      })
    } else {
      ElMessage.error('记录失败：' + (error.message || '未知错误'))
    }
  }
}

// 补录情绪
const handleSupplementRecord = () => {
  showDayDetail.value = false
  showQuickModal.value = true
}

// 记录提交成功
const handleRecordSubmit = async () => {
  console.log('[EmotionRecordPage] handleRecordSubmit 被调用')
  // console.log('[EmotionRecordPage] scatterPlotRef:', scatterPlotRef.value)
  
  try {
    await emotionStore.fetchRecords()
  } catch (e) {
    console.warn('刷新记录列表失败:', e)
  }
  // 刷新时间线和图表
  try { await emotionStore.fetchTodayRecords() } catch (e2) {}
  initCharts()
  
  // 刷新散点图（延迟一点，确保组件已挂载）
  // console.log('[EmotionRecordPage] 准备刷新散点图，ref:', scatterPlotRef.value)
  nextTick(() => {
    // console.log('[EmotionRecordPage] nextTick 中，ref:', scatterPlotRef.value)
    if (scatterPlotRef.value && scatterPlotRef.value.refresh) {
      console.log('[EmotionRecordPage] 刷新散点图')
      scatterPlotRef.value.refresh()
    } else {
      console.warn('[EmotionRecordPage] 散点图组件未就绪')
      // console.warn('  - scatterPlotRef.value:', scatterPlotRef.value)
      // console.warn('  - scatterPlotRef.value?.refresh:', scatterPlotRef.value?.refresh)
    }
    
    // 刷新情绪分布（与散点图同步）
    console.log('[EmotionRecordPage] 准备刷新情绪分布')
    loadDistributionStatistics(1).then(() => {
      console.log('[EmotionRecordPage] 分布数据已加载，更新图表')
      updateDistributionChart()
    })
  })
}

// 初始化所有图表
const initCharts = () => {
  nextTick(() => {
    initDistributionChart()
  })
}

// 时间线事件
const onTimelineUpdated = async () => {
  initCharts()
}

const onTimelineDeleted = async () => {
  await emotionStore.fetchRecords()
  initCharts()
  
  // 刷新散点图
  nextTick(() => {
    if (scatterPlotRef.value && scatterPlotRef.value.refresh) {
      console.log('[onTimelineDeleted] 刷新散点图')
      scatterPlotRef.value.refresh()
    }
    
    // 刷新情绪分布
    console.log('[onTimelineDeleted] 准备刷新情绪分布')
    loadDistributionStatistics(1).then(() => {
      console.log('[onTimelineDeleted] 分布数据已加载，更新图表')
      updateDistributionChart()
    })
  })
}

const onViewAllRecords = () => {
  // 可以跳转到完整历史或展开更多
  console.log('查看全部记录')
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
  padding: 16px 0px 16px 20px;
  max-width: 100%;
  min-height: 100%;
}

/* 页面标题 */
.page-header {
  margin-bottom: 16px;
  text-align: center;
}

.page-title {
  font-size: 28px;
  font-weight: 600;
  color: #2c3e50;
}

/* 区块1：快速记录 | 时间线 | 日历（三列并排 20:40:40） */
.block-quick-record {
  display: flex;
  gap: 20px;
  margin-bottom: 24px;
  align-items: stretch;
}

/* 左：快速记录 */
.quick-record-section-inner {
  width: 20%;
  flex-shrink: 0;
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(10px);
  border-radius: 20px;
  padding: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.5);
  display: flex;
  flex-direction: column;
  max-height: 380px;
}

/* 中：今日情绪时间线 */
.emotion-timeline {
  width: 35%;
  flex-shrink: 0;
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(10px);
  border-radius: 20px;
  padding: 24px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.5);
  display: flex;
  flex-direction: column;
  max-height: 380px;
  overflow: hidden;
}

/* 网格行 - 使用 Flex 布局 */
.flex-row {
  display: flex;
  gap: 24px;
  margin-bottom: 24px;
}

/* 第一排：快速记录 | 时间线 | 日历（1:2:2 比例） */
.block-quick-record {
  display: flex;
  gap: 24px;
}

/* 第二排：趋势 + 分布（60:40） */
.row-stats {
  display: flex;
  flex-direction: row;
  gap: 24px;
  width: 100%;
  min-height: 400px;
}

/* 区块通用样式 */
.flex-row > div {
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
  /* margin-bottom: 16px; */
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

/* 快速记录表情网格（4列×3行，带文字标识） */
.quick-emotion-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 6px;
  margin-bottom: 10px;
}

.quick-emotion-cell {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: #f8f9fa;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s ease;
  border: 2px solid transparent;
  padding: 4px 2px;
}

.quick-emotion-cell:hover {
  background: #eef2ff;
  transform: scale(1.03);
}

.quick-emotion-cell.selected {
  background: #eef2ff;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.15);
}

.cell-icon {
  font-size: 20px;
  line-height: 1.2;
}

.cell-name {
  font-size: 11px;
  color: #666;
  margin-top: 1px;
  white-space: nowrap;
}

.quick-emotion-cell.selected .cell-name {
  color: #667eea;
  font-weight: 500;
}

/* 添加自定义情绪按钮 */
.quick-emotion-cell.add-custom-btn {
  background: linear-gradient(135deg, #f5f7fa 0%, #e4e8ec 100%);
  border: 2px dashed #c0c4cc;
}

.quick-emotion-cell.add-custom-btn:hover {
  background: linear-gradient(135deg, #eef2ff 0%, #e0e7ff 100%);
  border-color: #667eea;
  transform: scale(1.03);
}

.quick-emotion-cell.add-custom-btn .cell-icon {
  font-size: 20px;
  color: #909399;
}

.quick-emotion-cell.add-custom-btn:hover .cell-icon {
  color: #667eea;
}

.quick-emotion-cell.add-custom-btn .cell-name {
  color: #909399;
  font-size: 10px;
}

.quick-emotion-cell.add-custom-btn:hover .cell-name {
  color: #667eea;
}

/* 提交按钮区域 */
.quick-submit-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 10px;
  gap: 8px;
}

.record-btn {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  flex-shrink: 0;
}

.record-btn:hover {
  background: linear-gradient(135deg, #5a6fd6 0%, #6a4190 100%);
}

.record-btn.is-disabled {
  background: #c0c4cc;
}

.selected-hint {
  font-size: 12px;
  color: #667eea;
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* 快速输入框 */
.quick-input-row {
  position: relative;
  margin-top: 8px;
}

.quick-input {
  width: 100%;
  height: 34px;
  padding: 0 42px 0 12px;
  border: 1.5px solid #e0e0e0;
  border-radius: 8px;
  font-size: 13px;
  color: #333;
  outline: none;
  transition: border-color 0.2s;
  box-sizing: border-box;
  background: #fafafa;
}

.quick-input:focus {
  border-color: #667eea;
  background: #fff;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.quick-input::placeholder {
  color: #bbb;
}

.input-count {
  position: absolute;
  right: 10px;
  top: 50%;
  transform: translateY(-50%);
  font-size: 11px;
  color: #ccc;
  pointer-events: none;
}

/* 右：日历 */
.calendar-section {
  width: 40%;
  flex-shrink: 0;
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(10px);
  border-radius: 20px;
  padding: 20px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.5);
  display: flex;
  flex-direction: column;
  max-height: 380px;
}

.calendar-title-wrapper {
  display: flex;
  align-items: center;
  gap: 12px;
}

.consecutive-days {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: #52c41a;
  background: #f6ffed;
  border: 1px solid #b7eb8f;
  padding: 2px 8px;
  border-radius: 12px;
  font-weight: 500;
}

.consecutive-days.broken {
  color: #faad14;
  background: #fffbe6;
  border-color: #ffe58f;
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

/* 过去日期样式 */
.calendar-day.past {
  opacity: 1;
}

.calendar-day.past .day-number {
  color: #2c3e50;
}

/* 未来日期样式 */
.calendar-day.future {
  opacity: 0.4;
  cursor: not-allowed;
}

.calendar-day.future .day-number {
  color: #b0b0b0;
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

/* 情志二维图组件 */
.scatter-plot-component {
  width: 50%;
  flex-shrink: 0;
  max-height: 400px;
  /* 组件内部有自己的卡片样式 */
}

/* 情绪分布 */
.distribution-section {
  width: 47%;
  flex-shrink: 0;
  max-height: 400px;
}

.distribution-section .chart-container {
  height: 180px;
  margin-bottom: 12px;
  width: 100%;
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
  .block-quick-record {
    flex-direction: column;
  }

  .quick-record-section-inner {
    width: 100%;
  }

  .block-quick-record > .emotion-timeline {
    width: 100%;
  }

  .flex-row {
    flex-direction: column;
  }

  .trend-section,
  .distribution-section {
    width: 100%;
  }
}
</style>
