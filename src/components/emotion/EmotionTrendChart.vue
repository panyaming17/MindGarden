<template>
  <div ref="chartContainer" class="trend-chart-container"></div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { useEmotionStore } from '@/stores/emotion'

const props = defineProps({
  range: {
    type: String,
    default: '30'
  }
})

const emotionStore = useEmotionStore()
const chartContainer = ref(null)
let chartInstance = null
let resizeObserver = null

// 情绪分值映射
const emotionScoreMap = {
  'happy': 8, 'excited': 9, 'grateful': 8, 'peaceful': 7, 'calm': 6,
  'tired': 4, 'confused': 4, 'lonely': 3,
  'sad': 2, 'anxious': 2, 'worried': 3, 'angry': 1
}

// 生成趋势数据
const generateTrendData = () => {
  const days = parseInt(props.range)
  const dates = []
  const values = []

  for (let i = days - 1; i >= 0; i--) {
    const date = new Date()
    date.setDate(date.getDate() - i)
    dates.push(date.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' }))

    const record = emotionStore.records.find(r => {
      const recordDate = new Date(r.record_date)
      return recordDate.toDateString() === date.toDateString()
    })

    if (record) {
      values.push(emotionScoreMap[record.emotion_type] || 5)
    } else {
      values.push(null)
    }
  }

  return { dates, values }
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

  chartInstance.setOption({
    tooltip: {
      trigger: 'axis',
      formatter: function(params) {
        const data = params[0]
        if (data.value === null) {
          return `${data.name}<br/>无记录`
        }
        return `${data.name}<br/>情绪指数: ${data.value}`
      }
    },
    grid: {
      left: '10%',
      right: '5%',
      bottom: '15%',
      top: '10%',
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
      max: 10,
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
    series: [{
      type: 'line',
      data: trendData.values,
      smooth: true,
      symbol: 'circle',
      symbolSize: 6,
      connectNulls: false,
      lineStyle: {
        color: '#667eea',
        width: 2
      },
      itemStyle: {
        color: '#667eea',
        borderWidth: 2,
        borderColor: '#fff'
      },
      areaStyle: {
        color: new window.echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: 'rgba(102, 126, 234, 0.3)' },
          { offset: 1, color: 'rgba(102, 126, 234, 0.05)' }
        ])
      }
    }]
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

// 监听记录变化
watch(() => emotionStore.records, () => {
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
.trend-chart-container {
  width: 100%;
  height: 100%;
  min-height: 0;
}
</style>
