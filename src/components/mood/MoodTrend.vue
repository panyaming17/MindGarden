<template>
  <div class="mood-trend">
    <div class="trend-controls">
      <el-select v-model="timeRange" @change="updateTrendData" placeholder="选择时间范围">
        <el-option label="近7天" value="7" />
        <el-option label="近30天" value="30" />
        <el-option label="近90天" value="90" />
      </el-select>
    </div>
    
    <div class="chart-container">
      <canvas ref="trendChart"></canvas>
    </div>
    
    <div class="trend-stats">
      <div class="stat-item">
        <div class="stat-label">平均情绪强度</div>
        <div class="stat-value">{{ averageIntensity.toFixed(1) }}</div>
      </div>
      <div class="stat-item">
        <div class="stat-label">最常见情绪</div>
        <div class="stat-value">{{ mostCommonMood }}</div>
      </div>
      <div class="stat-item">
        <div class="stat-label">情绪稳定性</div>
        <div class="stat-value">{{ stabilityLevel }}</div>
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
    
    // 创建新图表
    chartInstance.value = new Chart(trendChart.value, {
      type: 'line',
      data: {
        labels: props.trendData.dates,
        datasets: [
          {
            label: '情绪强度',
            data: props.trendData.intensities,
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
            max: 10,
            title: {
              display: true,
              text: '情绪强度'
            }
          },
          x: {
            title: {
              display: true,
              text: '日期'
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
                return `情绪: ${props.trendData.labels[index]}`
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
}

.trend-controls {
  margin-bottom: 20px;
  display: flex;
  justify-content: flex-end;
}

.chart-container {
  height: 300px;
  margin-bottom: 20px;
}

.trend-stats {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
}

.stat-item {
  background: #f8f9fa;
  padding: 16px;
  border-radius: 8px;
  text-align: center;
}

.stat-label {
  font-size: 14px;
  color: #666;
  margin-bottom: 8px;
}

.stat-value {
  font-size: 20px;
  font-weight: 600;
  color: #333;
}

@media (max-width: 768px) {
  .trend-stats {
    grid-template-columns: 1fr;
  }
  
  .chart-container {
    height: 250px;
  }
}
</style>
