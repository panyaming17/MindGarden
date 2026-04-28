<template>
  <div class="emotion-scatter-plot">
    <!-- 时间范围切换 -->
    <div class="plot-header">
      <h3 class="plot-title">中医情志二维坐标图</h3>
      <div class="time-range-selector">
        <el-radio-group v-model="selectedTimeRange" size="small" @change="onTimeRangeChange">
          <el-radio-button label="today">今日</el-radio-button>
          <el-radio-button label="week">本周</el-radio-button>
          <el-radio-button label="month">本月</el-radio-button>
        </el-radio-group>
      </div>
    </div>

    <!-- ECharts 图表容器 -->
    <div class="chart-container" ref="chartContainer"></div>

    <!-- 底部图例 -->
    <div class="legend-footer">
      <div class="plot-legend">
        <div class="legend-items">
          <div class="legend-item" v-for="item in legendItems" :key="item.name">
            <span class="legend-dot" :style="{ backgroundColor: item.color }"></span>
            <span class="legend-text">{{ item.name }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
import { emotionApi } from '@/utils/api'

// Props
const props = defineProps({
  userId: {
    type: String,
    required: true
  }
})

// 响应式数据
const selectedTimeRange = ref('today')
const emotionData = ref([])
const chartInstance = ref(null)
const chartContainer = ref(null)

// 七情图例数据
const legendItems = [
  { name: '喜', color: '#FF69B4' },
  { name: '怒', color: '#FF4D4F' },
  { name: '忧', color: '#1890FF' },
  { name: '思', color: '#52C41A' },
  { name: '悲', color: '#69C0FF' },
  { name: '恐', color: '#722ED1' },
  { name: '惊', color: '#FA8C16' }
]

// 加载情绪数据
const loadEmotionData = async () => {
  try {
    const response = await emotionApi.getEmotionStats2D(props.userId, selectedTimeRange.value)
    // console.log('[EmotionScatterPlot] API 响应:', response)
    
    if (response && response.emotions) {
      emotionData.value = response.emotions
      await nextTick()
      renderChart()
    } else {
      emotionData.value = []
      await nextTick()
      renderChart()
    }
  } catch (error) {
    console.error('加载情绪数据失败:', error)
    ElMessage.error('加载情绪数据失败')
    emotionData.value = []
  }
}

// 渲染 ECharts 图表
const renderChart = () => {
  if (!chartInstance.value) {
    chartInstance.value = echarts.init(chartContainer.value)
  }

  // 准备数据
  const data = emotionData.value.map(emotion => ({
    name: emotion.emotion_name,
    value: [
      emotion.x, // 快感度
      emotion.y, // 强度
      emotion.percentage,
      emotion.count
    ],
    emotion_icon: emotion.emotion_icon,
    itemStyle: {
      color: emotion.color
    }
  }))

  const option = {
    tooltip: {
      trigger: 'item',
      formatter: (params) => {
        if (!params.data || !params.data.value) return ''
        
        // 判断快感度区域
        let hedonicLabel = '中性'
        if (params.data.value[0] < -2) {
          hedonicLabel = '负性'
        } else if (params.data.value[0] > 2) {
          hedonicLabel = '正性'
        }
        
        return `
          <div style="font-weight:bold; font-size:14px; margin-bottom:4px;">${params.name}</div>
          <div style="border-top:1px solid #999; margin:4px 0;"></div>
          <div>快感度：${hedonicLabel}</div>
          <div>平均强度：${params.data.value[1]?.toFixed(2) || '0.00'}</div>
          <div>记录数：${params.data.value[3] || 0}次</div>
          <div>占比：${params.data.value[2]?.toFixed(1) || '0.0'}%</div>
          <div style="border-top:1px solid #999; margin:4px 0;"></div>
          <div>情绪图标：${params.data.emotion_icon || 'N/A'}</div>
        `
      }
    },
    grid: {
      left: '12%',
      right: '8%',
      top: '8%',
      bottom: '12%',
      containLabel: false
    },
    xAxis: {
      type: 'value',
      min: -10,
      max: 10,
      interval: 5,
      name: '快感度',
      nameLocation: 'middle',
      nameGap: 30,
      nameTextStyle: {
        color: '#000',
        fontSize: 12,
        fontWeight: 'bold'
      },
      splitLine: {
        show: true,
        lineStyle: {
          type: 'dashed',
          color: '#e0e0e0'
        }
      },
      axisLabel: {
        formatter: (value) => {
          if (value === -10) return '不愉快\n(负性)'
          if (value === 0) return '0'
          if (value === 10) return '愉快\n(正性)'
          return value.toString()
        },
        color: '#333',
        fontSize: 10,
        fontWeight: 500
      },
      splitArea: {
        show: true,
        areaStyle: {
          color: [
            'rgba(255, 200, 200, 0.1)',  // 负性区域背景
            'rgba(200, 255, 200, 0.1)',  // 中性区域背景
            'rgba(200, 200, 255, 0.1)'   // 正性区域背景
          ]
        }
      }
    },
    yAxis: {
      type: 'value',
      min: 0,
      max: 10,
      interval: 1,
      name: '情志强度',
      nameLocation: 'middle',
      nameGap: 45,
      nameTextStyle: {
        color: '#000',
        fontSize: 12,
        fontWeight: 'bold'
      },
      splitLine: {
        show: true,
        lineStyle: {
          type: 'dashed',
          color: '#e0e0e0'
        }
      },
      axisLabel: {
        color: '#333',
        fontSize: 10,
        fontWeight: 500
      }
    },
    series: [
      {
        name: '七情',
        type: 'scatter',
        data: data,
        symbolSize: (dataItem) => {
          return Math.max(30, Math.min(60, dataItem[2] * 3))
        },
        itemStyle: {
          shadowBlur: 10,
          shadowColor: 'rgba(0, 0, 0, 0.2)'
        },
        label: {
          show: true,
          formatter: (params) => params.name,
          position: 'inside',
          color: '#000',
          fontSize: 12,
          fontWeight: 'bold'
        },
        emphasis: {
          focus: 'series',
          label: {
            show: true
          },
          itemStyle: {
            shadowBlur: 20,
            shadowColor: 'rgba(0, 0, 0, 0.3)'
          }
        }
      }
    ]
  }

  chartInstance.value.setOption(option)
}

// 时间范围变化
const onTimeRangeChange = () => {
  loadEmotionData()
}

// 窗口大小变化时重绘
const handleResize = () => {
  if (chartInstance.value) {
    chartInstance.value.resize()
  }
}

// 暴露刷新方法给父组件
defineExpose({
  refresh: loadEmotionData
})

onMounted(() => {
  loadEmotionData()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  if (chartInstance.value) {
    chartInstance.value.dispose()
  }
  window.removeEventListener('resize', handleResize)
})
</script>

<style scoped>
.emotion-scatter-plot {
  background: #fff;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
}

.plot-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.plot-title {
  font-size: 16px;
  font-weight: 600;
  color: #2c3e50;
  margin: 0;
}

.time-range-selector {
  display: flex;
  align-items: center;
}

.chart-container {
  width: 100%;
  height: 320px;
}

.legend-footer {
  border-top: 1px solid #e8eaed;
}

.plot-legend {
  display: flex;
  justify-content: center;
}

.legend-items {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
}

.legend-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  display: inline-block;
}

.legend-text {
  font-size: 13px;
  color: #606266;
}
</style>
