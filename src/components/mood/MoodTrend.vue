<template>
  <div class="mood-trend">
    <h2 class="trend-title">情绪趋势</h2>
    <div class="trend-controls">
      <el-select v-model="timeRange" @change="updateTrendData" placeholder="选择时间范围">
        <el-option label="年" value="365" />
        <el-option label="月" value="30" />
        <el-option label="周" value="7" />
      </el-select>
    </div>
    
    <div class="trend-content">
      <div class="chart-container">
        <canvas ref="trendChart"></canvas>
      </div>
      
      <div class="trend-summary">
        <div class="summary-title">情绪总结</div>
        <div class="summary-item">
          <div class="summary-label">平均情绪强度</div>
          <div class="summary-value">{{ averageIntensity.toFixed(1) }}</div>
        </div>
        <div class="summary-item">
          <div class="summary-label">最常见情绪</div>
          <div class="summary-value">{{ mostCommonMood }}</div>
        </div>
        <div class="summary-item">
          <div class="summary-label">情绪稳定性</div>
          <div class="summary-value">{{ stabilityLevel }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import Chart from 'chart.js/auto'

// 组件属性
const props = defineProps({
  trendData: {
    type: Object,
    default: () => ({
      dates: [],
      intensities: [],
      labels: []
    })
  }
})

// 响应式数据
const trendChart = ref(null)
const chartInstance = ref(null)
const timeRange = ref('7')

// 计算属性
const averageIntensity = computed(() => {
  if (props.trendData.intensities.length === 0) return 0
  const sum = props.trendData.intensities.reduce((acc, val) => acc + val, 0)
  return sum / props.trendData.intensities.length
})

const mostCommonMood = computed(() => {
  if (props.trendData.labels.length === 0) return '无数据'
  const moodCount = {}
  props.trendData.labels.forEach(mood => {
    moodCount[mood] = (moodCount[mood] || 0) + 1
  })
  return Object.keys(moodCount).reduce((a, b) => moodCount[a] > moodCount[b] ? a : b)
})

const stabilityLevel = computed(() => {
  if (props.trendData.intensities.length < 2) return '稳定'
  const values = props.trendData.intensities
  const mean = values.reduce((acc, val) => acc + val, 0) / values.length
  const variance = values.reduce((acc, val) => acc + Math.pow(val - mean, 2), 0) / values.length
  const stdDev = Math.sqrt(variance)
  
  if (stdDev < 1) return '非常稳定'
  if (stdDev < 2) return '稳定'
  if (stdDev < 3) return '中等稳定'
  return '不稳定'
})

// 方法
const createChart = () => {
  if (trendChart.value) {
    // 销毁旧图表
    if (chartInstance.value) {
      chartInstance.value.destroy()
    }
    
    // 中医七情情绪
    const sevenEmotions = ['喜', '怒', '忧', '思', '悲', '恐', '惊']
    const emotionEmojis = ['😊', '😠', '😟', '😔', '😢', '😨', '😰']
    
    // 创建新图表
    chartInstance.value = new Chart(trendChart.value, {
      type: 'line',
      data: {
        labels: ['周一', '周二', '周三', '周四', '周五', '周六', '周日'],
        datasets: [
          {
            label: '情绪强度',
            data: props.trendData.intensities.length > 0 ? props.trendData.intensities : [0, 0, 0, 0, 0, 0, 0],
            borderColor: '#3498db',
            backgroundColor: 'rgba(52, 152, 219, 0.1)',
            borderWidth: 2,
            fill: true,
            tension: 0.4
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          y: {
            beginAtZero: true,
            min: 0,
            max: 7,
            stepSize: 1,
            title: {
              display: true,
              text: '中医七情情绪'
            },
            ticks: {
              callback: function(value) {
                const index = Math.round(value) - 1
                if (index >= 0 && index < sevenEmotions.length) {
                  return `${emotionEmojis[index]} ${sevenEmotions[index]}`
                }
                return ''
              }
            }
          },
          x: {
            title: {
              display: true,
              text: '星期'
            }
          }
        },
        plugins: {
          legend: {
            display: true
          },
          tooltip: {
            callbacks: {
              afterLabel: function(context) {
                const index = context.dataIndex
                return `情绪: ${props.trendData.labels[index] || '无'}`
              }
            }
          }
        }
      }
    })
  }
}

const updateTrendData = () => {
  // 模拟根据时间范围更新数据
  // 实际项目中应该调用 API 获取对应时间范围的数据
  console.log('更新时间范围:', timeRange.value)
}

// 监听数据变化
watch(() => props.trendData, () => {
  nextTick(() => {
    createChart()
  })
}, { deep: true })

// 组件挂载时
onMounted(() => {
  nextTick(() => {
    createChart()
  })
})
</script>

<style scoped>
.mood-trend {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.trend-title {
  font-size: 20px;
  font-weight: 600;
  color: #2c3e50;
  margin-bottom: 16px;
}

.trend-controls {
  margin-bottom: 20px;
  display: flex;
  justify-content: flex-end;
}

.trend-content {
  flex: 1;
  display: flex;
  gap: 30px;
}

.chart-container {
  flex: 1;
  height: 80%;
  min-height: 200px;
  overflow: hidden;
}

.trend-summary {
  width: 500px;
  background: #f8f9fa;
  padding: 20px;
  border-radius: 8px;
  display: flex;
  flex-direction: column;
}

.summary-title {
  font-size: 16px;
  font-weight: 600;
  color: #333;
  margin-bottom: 16px;
  border-bottom: 1px solid #e0e0e0;
  padding-bottom: 8px;
}

.summary-item {
  margin-bottom: 16px;
}

.summary-label {
  font-size: 14px;
  color: #666;
  margin-bottom: 4px;
}

.summary-value {
  font-size: 18px;
  font-weight: 600;
  color: #333;
}

@media (max-width: 768px) {
  .trend-content {
    flex-direction: column;
  }
  
  .trend-summary {
    width: 100%;
  }
  
  .chart-container {
    height: 250px;
  }
}
</style>
