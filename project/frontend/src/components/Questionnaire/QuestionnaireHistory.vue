<template>
  <div class="questionnaire-history">
    <!-- 加载状态 -->
    <div v-if="isLoading" class="loading-state">
      <el-skeleton :rows="4" animated />
    </div>

    <!-- 无数据状态 -->
    <el-empty v-else-if="!historyData?.records?.length" description="暂无历史记录" />

    <template v-else>
      <!-- 图表区域 -->
      <div class="chart-section">
        <h4 class="section-title">历史趋势</h4>
        <div ref="trendChart" class="trend-chart"></div>
      </div>

      <!-- 历史记录列表 -->
      <div class="history-list-section">
        <h4 class="section-title">测评记录</h4>
        <div class="history-list">
          <div
            v-for="(record, index) in historyData.records"
            :key="record.id"
            class="history-item"
            :class="getScoreClass(record.total_score)"
          >
            <div class="history-header">
              <span class="history-date">{{ formatDateTime(record.created_at) }}</span>
              <el-tag
                :type="getResultType(record.result_level)"
                size="small"
              >
                {{ record.result_level_text }}
              </el-tag>
            </div>
            <div class="history-score">
              <span class="score-value">{{ record.total_score }}</span>
              <span class="score-label">分</span>
            </div>
            <p v-if="record.result_analysis?.summary" class="history-summary">
              {{ record.result_analysis.summary }}
            </p>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useQuestionnaireStore } from '@/stores/questionnaire'

const props = defineProps({
  templateCode: {
    type: String,
    required: true
  }
})

const questionnaireStore = useQuestionnaireStore()
const trendChart = ref(null)
let chartInstance = null

const isLoading = computed(() => questionnaireStore.isLoading)

// 历史数据（适配API返回格式）
const historyData = computed(() => {
  return questionnaireStore.historyRecords[props.templateCode]
})

// 初始化图表
const initChart = () => {
  if (!trendChart.value || !window.echarts) return

  // 如果已有实例，先销毁
  if (chartInstance) {
    chartInstance.dispose()
    chartInstance = null
  }

  const echarts = window.echarts
  chartInstance = echarts.init(trendChart.value)

  const trendData = historyData.value?.trend_data || []

  if (trendData.length === 0) return

  const dates = trendData.map(item => item.date)
  const scores = trendData.map(item => item.score)

  // 根据问卷类型设置不同的Y轴范围和参考线
  let yMax = 27
  let markLines = []

  if (props.templateCode === 'PHQ9') {
    yMax = 27
    markLines = [
      { yAxis: 5, label: '轻度', lineStyle: { color: '#e6a23c', type: 'dashed' } },
      { yAxis: 10, label: '中度', lineStyle: { color: '#f56c6c', type: 'dashed' } },
      { yAxis: 15, label: '重度', lineStyle: { color: '#c45656', type: 'dashed' } },
      { yAxis: 20, label: '极重度', lineStyle: { color: '#722ed1', type: 'dashed' } }
    ]
  } else if (props.templateCode === 'GAD7') {
    yMax = 21
    markLines = [
      { yAxis: 5, label: '轻度', lineStyle: { color: '#e6a23c', type: 'dashed' } },
      { yAxis: 10, label: '中度', lineStyle: { color: '#f56c6c', type: 'dashed' } },
      { yAxis: 15, label: '重度', lineStyle: { color: '#c45656', type: 'dashed' } }
    ]
  }

  const option = {
    tooltip: {
      trigger: 'axis',
      formatter: function(params) {
        const data = params[0]
        return `${data.name}<br/>得分: <strong>${data.value}</strong>`
      }
    },
    grid: {
      left: '50px',
      right: '30px',
      bottom: '50px',
      top: '30px'
    },
    xAxis: {
      type: 'category',
      data: dates,
      axisLabel: {
        rotate: 30,
        fontSize: 11
      }
    },
    yAxis: {
      type: 'value',
      min: 0,
      max: yMax,
      axisLabel: {
        formatter: '{value}分'
      },
      splitLine: {
        lineStyle: {
          type: 'dashed',
          color: '#e0e0e0'
        }
      }
    },
    series: [{
      type: 'line',
      data: scores,
      smooth: true,
      symbol: 'circle',
      symbolSize: 10,
      lineStyle: {
        color: '#667eea',
        width: 3
      },
      itemStyle: {
        color: '#667eea',
        borderWidth: 2,
        borderColor: '#fff'
      },
      areaStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: 'rgba(102, 126, 234, 0.3)' },
          { offset: 1, color: 'rgba(102, 126, 234, 0.05)' }
        ])
      },
      markLine: {
        data: markLines,
        label: {
          position: 'end',
          formatter: '{b}'
        }
      }
    }]
  }

  chartInstance.setOption(option)
}

// 销毁图表
const disposeChart = () => {
  if (chartInstance) {
    chartInstance.dispose()
    chartInstance = null
  }
}

// 监听数据变化
watch(() => historyData.value, () => {
  if (chartInstance) {
    chartInstance.dispose()
    chartInstance = null
  }
  initChart()
}, { deep: true })

// 监听code变化
watch(() => props.templateCode, async (newCode) => {
  if (newCode) {
    await questionnaireStore.loadHistory(newCode)
  }
})

// 窗口大小变化处理函数
let handleResize = null

onMounted(async () => {
  await questionnaireStore.loadHistory(props.templateCode)
  initChart()

  // 监听窗口大小变化
  handleResize = () => {
    chartInstance?.resize()
  }
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  // 移除窗口大小监听
  if (handleResize) {
    window.removeEventListener('resize', handleResize)
  }
  // 销毁图表实例
  disposeChart()
})

// 格式化日期时间
const formatDateTime = (dateStr) => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// 获取结果类型
const getResultType = (level) => {
  const typeMap = {
    'none': 'success',
    'normal': 'success',
    'mild': 'warning',
    'moderate': 'danger',
    'moderately_severe': 'danger',
    'severe': 'danger'
  }
  return typeMap[level] || 'info'
}

// 获取分数样式类
const getScoreClass = (score) => {
  if (props.templateCode === 'PHQ9' || props.templateCode === 'GAD7') {
    if (score <= 4) return 'score-normal'
    if (score <= 9) return 'score-mild'
    if (score <= 14) return 'score-moderate'
    return 'score-severe'
  }
  return 'score-normal'
}
</script>

<style scoped>
.questionnaire-history {
  padding: 16px;
}

.loading-state {
  padding: 40px 20px;
}

.chart-section {
  margin-bottom: 32px;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  color: #2c3e50;
  margin-bottom: 16px;
}

.trend-chart {
  height: 300px;
  width: 100%;
}

.history-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.history-item {
  padding: 16px;
  background: #f5f7fa;
  border-radius: 12px;
  border-left: 4px solid #909399;
  transition: all 0.3s ease;
}

.history-item:hover {
  transform: translateX(4px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.history-item.score-normal {
  border-left-color: #67c23a;
}

.history-item.score-mild {
  border-left-color: #e6a23c;
}

.history-item.score-moderate {
  border-left-color: #f56c6c;
}

.history-item.score-severe {
  border-left-color: #c45656;
}

.history-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.history-date {
  font-size: 13px;
  color: #666;
}

.history-score {
  display: flex;
  align-items: baseline;
  gap: 4px;
  margin-bottom: 8px;
}

.score-value {
  font-size: 28px;
  font-weight: 700;
}

.score-normal .score-value {
  color: #67c23a;
}

.score-mild .score-value {
  color: #e6a23c;
}

.score-moderate .score-value {
  color: #f56c6c;
}

.score-severe .score-value {
  color: #c45656;
}

.score-label {
  font-size: 14px;
  color: #666;
}

.history-summary {
  font-size: 13px;
  color: #666;
  line-height: 1.6;
  margin: 0;
}
</style>
