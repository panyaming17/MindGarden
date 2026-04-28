<template>
  <div class="health-trend-container">
    <!-- 关键指标卡片 -->
    <div class="health-metrics-cards">
      <div class="metric-card" :style="{ borderLeftColor: healthMetrics.health_color }">
        <div class="metric-label">情绪健康指数</div>
        <div class="metric-value" :style="{ color: healthMetrics.health_color }">
          {{ healthMetrics.avg_health_score }}
        </div>
        <div class="metric-level" :style="{ color: healthMetrics.health_color }">
          {{ healthMetrics.health_level }}
        </div>
      </div>
      <div class="metric-card positive">
        <div class="metric-label">积极情绪占比</div>
        <div class="metric-value">{{ healthMetrics.positive_rate }}%</div>
        <div class="metric-trend">
          <el-icon v-if="healthMetrics.positive_rate >= 60" color="#52c41a"><SuccessFilled /></el-icon>
          <el-icon v-else-if="healthMetrics.positive_rate >= 40" color="#faad14"><WarningFilled /></el-icon>
          <el-icon v-else color="#f5222d"><CircleCloseFilled /></el-icon>
          <span :class="getRateLevelClass(healthMetrics.positive_rate)">
            {{ getRateLevelText(healthMetrics.positive_rate) }}
          </span>
        </div>
      </div>
      <div class="metric-card">
        <div class="metric-label">情绪波动率</div>
        <div class="metric-value">{{ healthMetrics.volatility }}</div>
        <div class="metric-trend">
          <el-icon v-if="healthMetrics.volatility <= 15" color="#52c41a"><SuccessFilled /></el-icon>
          <el-icon v-else-if="healthMetrics.volatility <= 25" color="#faad14"><WarningFilled /></el-icon>
          <el-icon v-else color="#f5222d"><CircleCloseFilled /></el-icon>
          <span :class="getVolatilityLevelClass(healthMetrics.volatility)">
            {{ getVolatilityLevelText(healthMetrics.volatility) }}
          </span>
        </div>
      </div>
      <div class="metric-card">
        <div class="metric-label">较上期变化</div>
        <div class="metric-value" :class="getTrendClass(healthMetrics.health_trend)">
          {{ healthMetrics.health_trend > 0 ? '+' : '' }}{{ healthMetrics.health_trend }}
        </div>
        <div class="metric-trend">
          <el-icon v-if="healthMetrics.health_trend > 0" color="#52c41a"><ArrowUp /></el-icon>
          <el-icon v-else-if="healthMetrics.health_trend < 0" color="#f5222d"><ArrowDown /></el-icon>
          <el-icon v-else color="#999"><Minus /></el-icon>
          <span :class="getTrendClass(healthMetrics.health_trend)">
            {{ getTrendText(healthMetrics.health_trend) }}
          </span>
        </div>
      </div>
    </div>

    <!-- 趋势图表 -->
    <div ref="chartContainer" class="trend-chart-container"></div>

    <!-- 健康等级说明 -->
    <div class="health-level-legend">
      <div class="legend-item">
        <span class="legend-dot" style="background: #52c41a;"></span>
        <span class="legend-text">健康 (80-100分)</span>
      </div>
      <div class="legend-item">
        <span class="legend-dot" style="background: #faad14;"></span>
        <span class="legend-text">亚健康 (50-79分)</span>
      </div>
      <div class="legend-item">
        <span class="legend-dot" style="background: #f5222d;"></span>
        <span class="legend-text">需关注 (0-49分)</span>
      </div>
      <div class="legend-divider"></div>
      <div class="legend-item">
        <span class="legend-line positive"></span>
        <span class="legend-text">积极情绪 (70-100分)</span>
      </div>
      <div class="legend-item">
        <span class="legend-line negative"></span>
        <span class="legend-text">消极情绪 (0-69分)</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch, nextTick, computed } from 'vue'
import { SuccessFilled, WarningFilled, CircleCloseFilled, ArrowUp, ArrowDown, Minus } from '@element-plus/icons-vue'

const props = defineProps({
  range: {
    type: String,
    default: '30'
  },
  trendData: {
    type: Array,
    default: () => []
  },
  healthMetrics: {
    type: Object,
    default: () => ({
      avg_health_score: 0,
      health_level: '未知',
      health_color: '#999',
      positive_rate: 0,
      volatility: 0,
      health_trend: 0,
      positive_days: 0,
      negative_days: 0,
      total_days: 0
    })
  }
})

const chartContainer = ref(null)
let chartInstance = null
let resizeObserver = null

// 获取积极情绪等级样式
const getRateLevelClass = (rate) => {
  if (rate >= 60) return 'level-good'
  if (rate >= 40) return 'level-warning'
  return 'level-danger'
}

const getRateLevelText = (rate) => {
  if (rate >= 60) return '良好'
  if (rate >= 40) return '一般'
  return '需关注'
}

// 获取波动率等级样式
const getVolatilityLevelClass = (volatility) => {
  if (volatility <= 15) return 'level-good'
  if (volatility <= 25) return 'level-warning'
  return 'level-danger'
}

const getVolatilityLevelText = (volatility) => {
  if (volatility <= 15) return '稳定'
  if (volatility <= 25) return '波动'
  return '剧烈'
}

// 获取趋势样式
const getTrendClass = (trend) => {
  if (trend > 0) return 'trend-up'
  if (trend < 0) return 'trend-down'
  return 'trend-flat'
}

const getTrendText = (trend) => {
  if (trend > 0) return '上升'
  if (trend < 0) return '下降'
  return '持平'
}

// 生成趋势数据
const generateTrendData = () => {
  const days = parseInt(props.range)
  const dates = []
  const values = []
  const healthLevels = []
  const polarityLabels = []
  const polarityColors = []

  // 如果没有趋势数据，返回空数据
  if (!props.trendData || props.trendData.length === 0) {
    for (let i = days - 1; i >= 0; i--) {
      const date = new Date()
      date.setDate(date.getDate() - i)
      dates.push(date.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' }))
      values.push(null)
      healthLevels.push(null)
      polarityLabels.push(null)
      polarityColors.push(null)
    }
    return { dates, values, healthLevels, polarityLabels, polarityColors }
  }

  // 构建日期到数据的映射
  const dateScoreMap = new Map()
  const dateLevelMap = new Map()
  const datePolarityMap = new Map()
  const datePolarityColorMap = new Map()
  props.trendData.forEach(item => {
    if (item.date) {
      // 后端返回的日期格式是 YYYY-MM-DD，需要转换为前端显示的格式
      const date = new Date(item.date)
      const dateStr = date.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })
      dateScoreMap.set(dateStr, item.health_score || 50)
      dateLevelMap.set(dateStr, item.health_level || '亚健康')
      datePolarityMap.set(dateStr, item.polarity_label || '未知')
      datePolarityColorMap.set(dateStr, item.polarity_color || '#999')
    }
  })

  // 生成日期范围和对应的值
  for (let i = days - 1; i >= 0; i--) {
    const date = new Date()
    date.setDate(date.getDate() - i)
    const dateStr = date.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })
    dates.push(dateStr)

    if (dateScoreMap.has(dateStr)) {
      values.push(dateScoreMap.get(dateStr))
      healthLevels.push(dateLevelMap.get(dateStr))
      polarityLabels.push(datePolarityMap.get(dateStr))
      polarityColors.push(datePolarityColorMap.get(dateStr))
    } else {
      values.push(null)
      healthLevels.push(null)
      polarityLabels.push(null)
      polarityColors.push(null)
    }
  }

  return { dates, values, healthLevels, polarityLabels, polarityColors }
}

// 初始化图表
const initChart = () => {
  if (!window.echarts || !chartContainer.value) return

  // 如果已存在实例，先销毁
  if (chartInstance) {
    chartInstance.dispose()
  }

  chartInstance = window.echarts.init(chartContainer.value)
  updateChart()
}

// 更新图表数据
const updateChart = () => {
  if (!chartInstance) return

  const trendData = generateTrendData()

  // 计算健康区域标记
  const markAreas = [
    // 健康区域 (80-100)
    {
      name: '健康',
      yAxis: 80,
      yAxisMax: 100,
      itemStyle: {
        color: 'rgba(82, 196, 26, 0.1)'
      }
    },
    // 亚健康区域 (50-79)
    {
      name: '亚健康',
      yAxis: 50,
      yAxisMax: 79,
      itemStyle: {
        color: 'rgba(250, 173, 20, 0.1)'
      }
    },
    // 需关注区域 (0-49)
    {
      name: '需关注',
      yAxis: 0,
      yAxisMax: 49,
      itemStyle: {
        color: 'rgba(245, 34, 45, 0.1)'
      }
    }
  ]

  chartInstance.setOption({
    tooltip: {
      trigger: 'axis',
      formatter: function(params) {
        // params[0] 是正负情绪区域（无数据），params[1] 是主情绪曲线
        const data = params[1] || params[0]
        if (!data || data.value === null) {
          return `${data?.name || ''}<br/>无记录`
        }
        // 找到对应的健康等级和正负性
        const index = trendData.dates.indexOf(data.name)
        const level = trendData.healthLevels[index] || '未知'
        const polarity = trendData.polarityLabels[index] || '未知'
        const polarityColor = trendData.polarityColors[index] || '#999'
        const color = data.value >= 80 ? '#52c41a' : data.value >= 50 ? '#faad14' : '#f5222d'
        return `${data.name}<br/>健康指数: <span style="color:${color};font-weight:bold">${data.value}</span><br/>状态: ${level}<br/>情绪性质: <span style="color:${polarityColor};font-weight:bold">${polarity}</span>`
      }
    },
    grid: {
      left: '12%',
      right: '12%',
      bottom: '15%',
      top: '15%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: trendData.dates,
      axisLabel: {
        fontSize: 11,
        color: '#555',
        rotate: props.range === '90' ? 45 : 0
      },
      axisLine: {
        lineStyle: { color: '#ccc' }
      },
      axisTick: { show: false }
    },
    yAxis: {
      type: 'value',
      min: 0,
      max: 100,
      name: '健康指数',
      nameTextStyle: {
        color: '#666',
        fontSize: 12
      },
      splitLine: {
        lineStyle: {
          type: 'dashed',
          color: '#e0e0e0'
        }
      },
      axisLabel: {
        fontSize: 11,
        color: '#555'
      }
    },
    series: [
      // 正负情绪区域背景标注（放在第一个，作为底层背景）
      {
        type: 'line',
        data: [],
        markArea: {
          silent: true,
          data: [
            [
              { yAxis: 70, itemStyle: { color: 'rgba(82, 196, 26, 0.05)' } },
              { yAxis: 100 }
            ],
            [
              { yAxis: 0, itemStyle: { color: 'rgba(245, 34, 45, 0.05)' } },
              { yAxis: 70 }
            ]
          ]
        }
      },
      // 主情绪曲线
      {
        type: 'line',
        data: trendData.values,
        smooth: true,
        symbol: 'circle',
        symbolSize: 8,
        connectNulls: false,
        lineStyle: {
          width: 3,
          color: new window.echarts.graphic.LinearGradient(0, 0, 1, 0, [
            { offset: 0, color: '#667eea' },
            { offset: 1, color: '#764ba2' }
          ])
        },
        itemStyle: {
          color: function(params) {
            const value = params.value
            if (value >= 80) return '#52c41a'
            if (value >= 50) return '#faad14'
            return '#f5222d'
          },
          borderWidth: 2,
          borderColor: '#fff'
        },
        areaStyle: {
          color: new window.echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(102, 126, 234, 0.4)' },
            { offset: 0.5, color: 'rgba(102, 126, 234, 0.2)' },
            { offset: 1, color: 'rgba(102, 126, 234, 0.05)' }
          ])
        },
        markArea: {
          silent: true,
          data: [
            [{ yAxis: 80 }, { yAxis: 100 }],
            [{ yAxis: 50 }, { yAxis: 80 }],
            [{ yAxis: 0 }, { yAxis: 50 }]
          ],
          itemStyle: {
            color: function(params) {
              if (params.dataIndex === 0) return 'rgba(82, 196, 26, 0.08)'
              if (params.dataIndex === 1) return 'rgba(250, 173, 20, 0.08)'
              return 'rgba(245, 34, 45, 0.08)'
            }
          }
        },
        markLine: {
          silent: true,
          symbol: 'none',
          lineStyle: {
            type: 'dashed',
            width: 1
          },
          data: [
            { 
              yAxis: 80, 
              lineStyle: { color: '#52c41a' }, 
              label: { 
                formatter: '健康线 80', 
                position: 'start',
                color: '#52c41a',
                backgroundColor: 'rgba(255,255,255,0.95)',
                padding: [3, 8],
                borderRadius: 4,
                fontSize: 11,
                fontWeight: 'bold',
                borderColor: '#52c41a',
                borderWidth: 1
              } 
            },
            { 
              yAxis: 70, 
              lineStyle: { color: '#36A2EB', width: 2, type: 'solid' }, 
              label: { 
                formatter: '正负分界 70', 
                position: 'end',
                color: '#36A2EB',
                backgroundColor: 'rgba(255,255,255,0.95)',
                padding: [3, 8],
                borderRadius: 4,
                fontSize: 11,
                fontWeight: 'bold',
                borderColor: '#36A2EB',
                borderWidth: 1
              } 
            },
            { 
              yAxis: 50, 
              lineStyle: { color: '#faad14' }, 
              label: { 
                formatter: '警戒线 50', 
                position: 'start',
                color: '#faad14',
                backgroundColor: 'rgba(255,255,255,0.95)',
                padding: [3, 8],
                borderRadius: 4,
                fontSize: 11,
                fontWeight: 'bold',
                borderColor: '#faad14',
                borderWidth: 1
              } 
            }
          ]
        }
      }
    ]
  }, true)
}

// 处理大小变化
const handleResize = () => {
  if (chartInstance) {
    chartInstance.resize()
  }
}

// 监听范围变化
watch(() => props.range, () => {
  nextTick(() => updateChart())
})

// 监听趋势数据变化
watch(() => props.trendData, () => {
  nextTick(() => updateChart())
}, { deep: true })

// 监听健康指标变化
watch(() => props.healthMetrics, () => {
  nextTick(() => updateChart())
}, { deep: true })

onMounted(() => {
  nextTick(() => {
    initChart()

    // 使用 ResizeObserver 监听容器大小变化
    if (window.ResizeObserver) {
      resizeObserver = new ResizeObserver(() => {
        handleResize()
      })
      resizeObserver.observe(chartContainer.value)
    } else {
      // 降级方案：监听 window resize
      window.addEventListener('resize', handleResize)
    }
  })
})

onUnmounted(() => {
  if (resizeObserver) {
    resizeObserver.disconnect()
  }
  window.removeEventListener('resize', handleResize)
  if (chartInstance) {
    chartInstance.dispose()
    chartInstance = null
  }
})
</script>

<style scoped>
.health-trend-container {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
}

/* 关键指标卡片 */
.health-metrics-cards {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 8px;
  margin-bottom: 12px;
}

.metric-card {
  background: #f8f9fa;
  border-radius: 10px;
  padding: 8px 10px;
  border-left: 3px solid #667eea;
  transition: all 0.3s ease;
}

.metric-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.metric-card.positive {
  border-left-color: #52c41a;
}

.metric-label {
  font-size: 11px;
  color: #666;
  margin-bottom: 2px;
}

.metric-value {
  font-size: 20px;
  font-weight: 700;
  color: #2c3e50;
  line-height: 1.2;
}

.metric-level {
  font-size: 11px;
  font-weight: 500;
  margin-top: 1px;
}

.metric-trend {
  display: flex;
  align-items: center;
  gap: 3px;
  margin-top: 2px;
  font-size: 11px;
}

.level-good {
  color: #52c41a;
}

.level-warning {
  color: #faad14;
}

.level-danger {
  color: #f5222d;
}

.trend-up {
  color: #52c41a;
}

.trend-down {
  color: #f5222d;
}

.trend-flat {
  color: #999;
}

/* 趋势图表 */
.trend-chart-container {
  flex: 1;
  min-height: 200px;
  width: 100%;
}

/* 健康等级说明 */
.health-level-legend {
  display: flex;
  justify-content: center;
  gap: 16px;
  padding-top: 8px;
  border-top: 1px solid #eee;
  margin-top: 6px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 4px;
}

.legend-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.legend-line {
  width: 16px;
  height: 2px;
  border-radius: 2px;
}

.legend-line.positive {
  background: #52c41a;
}

.legend-line.negative {
  background: #f5222d;
}

.legend-divider {
  width: 1px;
  height: 16px;
  background: #ddd;
  margin: 0 8px;
}

.legend-text {
  font-size: 12px;
  color: #666;
}

/* 响应式 */
@media (max-width: 1200px) {
  .health-metrics-cards {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .health-metrics-cards {
    grid-template-columns: repeat(2, 1fr);
    gap: 8px;
  }

  .metric-card {
    padding: 10px;
  }

  .metric-value {
    font-size: 20px;
  }

  .health-level-legend {
    flex-wrap: wrap;
    gap: 12px;
  }
}
</style>
