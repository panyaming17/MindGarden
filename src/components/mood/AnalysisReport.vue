<template>
  <div class="analysis-report">
    <!-- 情志状态仪表盘 -->
    <div v-if="hasDashboardData" class="dashboard-section">
      <h3 class="section-title">
        📊 中医情志四维状态仪表盘
        <el-tooltip content="基于中医情志理论，从情志强度、情志快感度、情志紧张度、情志复杂度四个维度综合评估您的情志状态" placement="top">
          <el-icon class="help-icon"><QuestionFilled /></el-icon>
        </el-tooltip>
      </h3>
      <div class="dashboard-grid">
        <!-- 快感度环形图（中医情志快感度） -->
        <div class="dashboard-card">
          <h4 class="dashboard-subtitle">情志快感度</h4>
          <el-tooltip content="展示对话过程中快感度的变化趋势，分为前中后三个阶段，帮助了解快感度的规律" placement="top">
            <el-icon class="help-icon"><QuestionFilled /></el-icon>
          </el-tooltip>
          <div ref="hedonicChart" class="dashboard-chart"></div>
        </div>
        
        <!-- 紧张度柱状图（情绪紧张度） -->
        <div class="dashboard-card">
          <h4 class="dashboard-subtitle">情志紧张度</h4>
          <el-tooltip content="展示对话过程中紧张度的变化趋势，分为前中后三个阶段，帮助了解紧张度的规律" placement="top">
            <el-icon class="help-icon"><QuestionFilled /></el-icon>
            </el-tooltip>
          <div ref="tensionChart" class="dashboard-chart"></div>
        </div>
      </div>
    </div>

    <!-- 情绪强度波浪图 -->
    <div v-if="hasWaveData" class="wave-section">
      <h3 class="section-title">
        🌊 情志强度变化
        <el-tooltip content="展示对话过程中情绪强度的变化趋势，分为前中后三个阶段，帮助了解情绪波动的规律" placement="top">
          <el-icon class="help-icon"><QuestionFilled /></el-icon>
        </el-tooltip>
      </h3>
      <div class="wave-card">
        <div ref="waveChart" class="wave-chart"></div>
      </div>
    </div>

    <!-- 复杂度分布 -->
    <div v-if="hasComplexityData" class="complexity-section">
      <h3 class="section-title">
        🧩 情志复杂度分析
        <el-tooltip content="分析情绪的复杂程度和情绪成分的混合情况，复杂情绪往往包含多种情绪成分" placement="top">
          <el-icon class="help-icon"><QuestionFilled /></el-icon>
        </el-tooltip>
      </h3>
      <div class="complexity-grid">
        <div class="complexity-card">
          <h4 class="complexity-subtitle">整体复杂度</h4>
          <div ref="complexityChart" class="complexity-chart"></div>
        </div>
        <div v-if="hasEmotionMix" class="complexity-card">
          <h4 class="complexity-subtitle">情志占比</h4>
          <div ref="emotionMixChart" class="complexity-chart"></div>
        </div>
      </div>
    </div>

    <!-- 认知分析 -->
    <div v-if="data?.cognitive_analysis" class="analysis-section">
      <h3 class="section-title">
        🧠 认知分析
        <el-tooltip content="基于认知行为疗法(CBT)理论，分析您的思维模式、自动思维和可能的认知偏差" placement="top">
          <el-icon class="help-icon"><QuestionFilled /></el-icon>
        </el-tooltip>
      </h3>
      
      <!-- 常见自动思维 -->
      <div v-if="data.cognitive_analysis.common_automatic_thoughts?.length" class="analysis-card">
        <h4 class="card-subtitle">常见自动思维</h4>
        <div class="thoughts-list">
          <div v-for="(thought, index) in data.cognitive_analysis.common_automatic_thoughts" :key="index" class="thought-item">
            <span class="thought-number">{{ index + 1 }}</span>
            <span class="thought-text">{{ thought }}</span>
          </div>
        </div>
      </div>

      <!-- 思维陷阱 -->
      <div v-if="data.cognitive_analysis.thinking_traps?.length" class="analysis-card">
        <h4 class="card-subtitle">⚠️ 思维陷阱</h4>
        <div class="traps-list">
          <div v-for="(trap, index) in data.cognitive_analysis.thinking_traps" :key="index" class="trap-item">
            <span class="trap-icon">🕳️</span>
            <span class="trap-text">{{ trap }}</span>
          </div>
        </div>
      </div>

      <!-- 核心信念 -->
      <div v-if="data.cognitive_analysis.core_beliefs?.length" class="analysis-card">
        <h4 class="card-subtitle">💎 核心信念</h4>
        <div class="beliefs-list">
          <div v-for="(belief, index) in data.cognitive_analysis.core_beliefs" :key="index" class="belief-item">
            <span class="belief-icon">🔹</span>
            <span class="belief-text">{{ belief }}</span>
          </div>
        </div>
      </div>

      <!-- 思维陷阱统计 -->
      <div v-if="data.cognitive_analysis.trap_counts" class="analysis-card">
        <h4 class="card-subtitle">📊 思维陷阱统计</h4>
        <div ref="trapChart" class="chart-container small"></div>
      </div>
    </div>

    <!-- 中医分析 -->
    <div v-if="data?.tcm_analysis" class="analysis-section">
      <h3 class="section-title">
        🌿 中医视角
        <el-tooltip content="从中医情志学说角度，分析情绪与脏腑、气机的关系，提供中医特色的健康解读" placement="top">
          <el-icon class="help-icon"><QuestionFilled /></el-icon>
        </el-tooltip>
      </h3>
      <div class="tcm-card">
        <div v-if="data.tcm_analysis.dominant_emotion" class="tcm-item">
          <span class="tcm-label">主导情志：</span>
          <span class="tcm-value highlight">{{ data.tcm_analysis.dominant_emotion }}</span>
        </div>
        <div v-if="data.tcm_analysis.related_organs?.length" class="tcm-item">
          <span class="tcm-label">相关脏腑：</span>
          <span class="tcm-value">{{ data.tcm_analysis.related_organs.join('、') }}</span>
        </div>
        <div v-if="data.tcm_analysis.qi_dynamics" class="tcm-item block">
          <span class="tcm-label">气机动态：</span>
          <p class="tcm-text">{{ data.tcm_analysis.qi_dynamics }}</p>
        </div>
        <div v-if="data.tcm_analysis.tcm_interpretation" class="tcm-item block">
          <span class="tcm-label">中医解读：</span>
          <p class="tcm-text">{{ data.tcm_analysis.tcm_interpretation }}</p>
        </div>
      </div>
    </div>

    <!-- 原因分析 -->
    <div v-if="data?.causes" class="analysis-section">
      <h3 class="section-title">
        🔍 原因分析
        <el-tooltip content="从CBT和中医两个角度，深入分析情绪产生的可能原因和机制" placement="top">
          <el-icon class="help-icon"><QuestionFilled /></el-icon>
        </el-tooltip>
      </h3>
      <div class="causes-grid">
        <div v-if="data.causes.cbt_perspective" class="cause-card cbt">
          <h4 class="cause-title">🧠 CBT视角</h4>
          <p class="cause-content">{{ data.causes.cbt_perspective }}</p>
        </div>
        <div v-if="data.causes.tcm_perspective" class="cause-card tcm">
          <h4 class="cause-title">🌿 中医视角</h4>
          <p class="cause-content">{{ data.causes.tcm_perspective }}</p>
        </div>
      </div>
    </div>

    <!-- 情绪趋势 -->
    <div v-if="data?.trends" class="analysis-section">
      <h3 class="section-title">
        📉 情绪趋势
        <el-tooltip content="总结情绪变化的总体趋势和特点，帮助您了解情绪发展的方向" placement="top">
          <el-icon class="help-icon"><QuestionFilled /></el-icon>
        </el-tooltip>
      </h3>
      <div class="trends-card">
        <p class="trends-text">{{ data.trends }}</p>
      </div>
    </div>

    <!-- 无数据提示 -->
    <div v-if="!hasData" class="no-data">
      <div class="no-data-icon">📊</div>
      <p>暂无分析数据</p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import { QuestionFilled } from '@element-plus/icons-vue'

const props = defineProps({
  data: {
    type: Object,
    default: () => ({})
  }
})

// 图表引用
const hedonicChart = ref(null)
const tensionChart = ref(null)
const waveChart = ref(null)
const complexityChart = ref(null)
const emotionMixChart = ref(null)

// 图表实例
let charts = {}

// 是否有仪表盘数据
const hasDashboardData = computed(() => {
  return props.data?.four_dim_summary?.hedonic_distribution ||
         props.data?.four_dim_summary?.tension_distribution ||
         props.data?.emotional_timeline?.hedonic ||
         props.data?.emotional_timeline?.tension
})

// 是否有波浪图数据
const hasWaveData = computed(() => {
  return props.data?.emotional_timeline?.intensity?.length > 0 ||
         props.data?.four_dim_summary?.intensity_values?.length > 0
})

// 是否有复杂度数据
const hasComplexityData = computed(() => {
  return props.data?.four_dim_summary?.complexity_analysis ||
         props.data?.emotional_timeline?.complexity
})

// 是否有情绪混合数据
const hasEmotionMix = computed(() => {
  const complexity = props.data?.four_dim_summary?.complexity_analysis ||
                    props.data?.emotional_timeline?.complexity
  // 新格式：对象 {type: "复杂", emotions: [...]}
  if (complexity && typeof complexity === 'object' && !Array.isArray(complexity)) {
    return complexity.emotions && complexity.emotions.length > 0
  }
  // 旧格式：数组 ["复杂", {忧: 0.4}]
  return Array.isArray(complexity) && complexity.length > 1 && typeof complexity[1] === 'object'
})

// 是否有数据
const hasData = computed(() => {
  return props.data && (
    props.data.four_dim_summary ||
    props.data.emotional_timeline ||
    props.data.cognitive_analysis ||
    props.data.tcm_analysis ||
    props.data.causes ||
    props.data.trends
  )
})

// 初始化图表
const initCharts = () => {
  console.log('初始化图表...')
  console.log('window.echarts:', typeof window !== 'undefined' ? window.echarts : 'undefined')
  console.log('props.data:', props.data)
  
  if (typeof window === 'undefined' || !window.echarts) {
    console.warn('ECharts 未加载')
    return
  }

  const echarts = window.echarts

  // 快感度环形图（情志平衡环）- 甜甜圈图
  console.log('hedonicChart.value:', hedonicChart.value)
  console.log('hasDashboardData.value:', hasDashboardData.value)
  
  if (hedonicChart.value && hasDashboardData.value) {
    console.log('初始化快感度图表')
    const chart = echarts.init(hedonicChart.value)
    
    // 获取数据（支持多种格式）
    let data = props.data?.four_dim_summary?.hedonic_distribution || 
               props.data?.emotional_timeline?.hedonic
    
    if (data) {
      // 转换为统一格式
      let chartData = []
      let total = 0
      
      if (Array.isArray(data)) {
        // 新格式：数组 [{label: "负性", value: 3}, ...]
        chartData = data.map(item => ({
          name: item.label,
          value: item.value
        }))
        total = data.reduce((sum, item) => sum + item.value, 0)
      } else if (typeof data === 'object') {
        // 旧格式：对象 {负性: 3, 中性: 3, 正性: 0}
        total = Object.values(data).reduce((sum, val) => sum + val, 0)
        chartData = [
          { value: data['负性'] || 0, name: '负性' },
          { value: data['中性'] || 0, name: '中性' },
          { value: data['正性'] || 0, name: '正性' }
        ]
      }
      
      // 计算百分比
      chartData = chartData.map(item => ({
        ...item,
        percent: total > 0 ? Math.round((item.value / total) * 100) : 0
      }))
      
      const option = {
        tooltip: {
          trigger: 'item',
          formatter: '{b}: {c} ({d}%)'
        },
        series: [{
          type: 'pie',
          radius: ['50%', '75%'],
          center: ['50%', '50%'],
          avoidLabelOverlap: false,
          itemStyle: {
            borderRadius: 8,
            borderColor: '#fff',
            borderWidth: 3
          },
          label: {
            show: true,
            position: 'outside',
            formatter: function(params) {
              return params.name + '\n' + params.data.percent + '%'
            },
            fontSize: 13,
            fontWeight: 'bold',
            color: '#555'
          },
          labelLine: {
            show: true,
            length: 15,
            length2: 10,
            lineStyle: {
              color: '#ccc'
            }
          },
          emphasis: {
            label: {
              show: true,
              fontSize: 15,
              fontWeight: 'bold'
            },
            itemStyle: {
              shadowBlur: 10,
              shadowOffsetX: 0,
              shadowColor: 'rgba(0, 0, 0, 0.2)'
            }
          },
          data: [
            { 
              value: chartData[0].value, 
              name: '负性', 
              percent: chartData[0].percent,
              itemStyle: { color: '#94a3b8' }  // 清冷灰蓝
            },
            { 
              value: chartData[1].value, 
              name: '中性', 
              percent: chartData[1].percent,
              itemStyle: { color: '#cbd5e1' }  // 柔和灰
            },
            { 
              value: chartData[2].value, 
              name: '正性', 
              percent: chartData[2].percent,
              itemStyle: { color: '#f9a8d4' }  // 温柔粉
            }
          ]
        }]
      }
      
      chart.setOption(option)
      charts.hedonic = chart
    }
  }

  // 紧张度柱状图（情绪张力）- 三色渐变柱
  if (tensionChart.value && hasDashboardData.value) {
    const chart = echarts.init(tensionChart.value)
    
    // 获取数据
    let data = props.data?.four_dim_summary?.tension_distribution || 
               props.data?.emotional_timeline?.tension
    
    if (data) {
      // 转换为统一格式
      let chartData = []
      let total = 0
      
      if (Array.isArray(data)) {
        // 新格式：数组 [{label: "低", value: 5}, ...]
        chartData = data.map(item => ({
          name: item.label,
          value: item.value
        }))
        total = data.reduce((sum, item) => sum + item.value, 0)
      } else if (typeof data === 'object') {
        // 旧格式：对象 {低: 5, 中: 0, 高: 1}
        total = Object.values(data).reduce((sum, val) => sum + val, 0)
        chartData = [
          { name: '低', value: data['低'] || 0 },
          { name: '中', value: data['中'] || 0 },
          { name: '高', value: data['高'] || 0 }
        ]
      }
      
      // 计算百分比
      chartData = chartData.map(item => ({
        ...item,
        percent: total > 0 ? Math.round((item.value / total) * 100) : 0
      }))
      
      const option = {
        tooltip: {
          trigger: 'axis',
          axisPointer: { type: 'shadow' },
          formatter: '{b}: {c} ({percent}%)'
        },
        grid: {
          left: '3%',
          right: '4%',
          bottom: '3%',
          top: '15%',
          containLabel: true
        },
        xAxis: {
          type: 'category',
          data: ['低', '中', '高'],
          axisLine: { 
            lineStyle: { color: '#e0e0e0' } 
          },
          axisLabel: { 
            color: '#666',
            fontSize: 14,
            fontWeight: 'bold'
          },
          axisTick: { show: false }
        },
        yAxis: {
          type: 'value',
          max: 100,
          axisLine: { show: false },
          axisLabel: { 
            color: '#999',
            formatter: '{value}%'
          },
          splitLine: { 
            lineStyle: { 
              color: '#f0f0f0',
              type: 'dashed'
            } 
          }
        },
        series: [{
          type: 'bar',
          data: [
            { 
              value: chartData[0].percent, 
              percent: chartData[0].percent,
              itemStyle: { 
                color: '#d1fae5',  // 浅绿
                borderRadius: [8, 8, 0, 0]
              } 
            },
            { 
              value: chartData[1].percent, 
              percent: chartData[1].percent,
              itemStyle: { 
                color: '#6ee7b7',  // 中绿
                borderRadius: [8, 8, 0, 0]
              } 
            },
            { 
              value: chartData[2].percent, 
              percent: chartData[2].percent,
              itemStyle: { 
                color: '#10b981',  // 深绿
                borderRadius: [8, 8, 0, 0]
              } 
            }
          ],
          barWidth: '45%',
          label: {
            show: true,
            position: 'top',
            formatter: '{c}%',
            color: '#666',
            fontSize: 13,
            fontWeight: 'bold'
          }
        }]
      }
      
      chart.setOption(option)
      charts.tension = chart
    }
  }

  // 情绪强度波浪图（三阶段）
  if (waveChart.value && hasWaveData.value) {
    const chart = echarts.init(waveChart.value)
    
    // 获取强度数据（支持新格式和旧格式）
    let intensityData = []
    
    // 优先使用 emotional_timeline.intensity
    if (props.data?.emotional_timeline?.intensity) {
      const data = props.data.emotional_timeline.intensity
      if (Array.isArray(data) && data.length > 0) {
        if (typeof data[0] === 'object' && data[0].value !== undefined) {
          // 新格式：[{value: 6.16, timestamp: "..."}, ...]
          intensityData = data.map(item => item.value)
        } else {
          // 旧格式：[6.16, 6.75, ...]
          intensityData = data
        }
      }
    }
    // 如果没有，使用 four_dim_summary.intensity_values
    else if (props.data?.four_dim_summary?.intensity_values) {
      const data = props.data.four_dim_summary.intensity_values
      if (Array.isArray(data) && data.length > 0) {
        if (typeof data[0] === 'object' && data[0].value !== undefined) {
          // 新格式：[{value: 6.16, timestamp: "..."}, ...]
          intensityData = data.map(item => item.value)
        } else {
          // 旧格式：[6.16, 6.75, ...]
          intensityData = data
        }
      }
    }
    
    if (intensityData.length > 0) {
      // 将数据分为前中后三个阶段
      const total = intensityData.length
      const phase1 = intensityData.slice(0, Math.ceil(total / 3))  // 前期
      const phase2 = intensityData.slice(Math.ceil(total / 3), Math.ceil(total * 2 / 3))  // 中期
      const phase3 = intensityData.slice(Math.ceil(total * 2 / 3))  // 后期
      
      // 计算每个阶段的平均强度
      const avg1 = phase1.reduce((sum, val) => sum + val, 0) / phase1.length
      const avg2 = phase2.reduce((sum, val) => sum + val, 0) / phase2.length
      const avg3 = phase3.reduce((sum, val) => sum + val, 0) / phase3.length
      
      const option = {
        tooltip: {
          trigger: 'axis',
          formatter: function(params) {
            const phase = params[0].name
            const value = params[0].value.toFixed(2)
            return `${phase}<br/>平均强度: <strong>${value}</strong>`
          }
        },
        grid: {
          left: '50px',
          right: '30px',
          bottom: '40px',
          top: '30px',
          containLabel: false
        },
        xAxis: {
          type: 'category',
          data: ['前期', '中期', '后期'],
          axisLine: { 
            lineStyle: { color: '#e0e0e0' } 
          },
          axisLabel: { 
            color: '#666',
            fontSize: 14,
            fontWeight: 'bold'
          },
          axisTick: { show: false }
        },
        yAxis: {
          type: 'value',
          name: '强度',
          min: 0,
          max: 10,
          nameTextStyle: {
            color: '#666',
            fontSize: 12,
            padding: [0, 0, 0, -30]
          },
          axisLine: { 
            show: true,
            lineStyle: { color: '#e0e0e0' }
          },
          axisLabel: { 
            color: '#666',
            fontSize: 12
          },
          splitLine: { 
            lineStyle: { 
              color: '#f0f0f0',
              type: 'dashed'
            } 
          }
        },
        series: [{
          name: '情绪强度',
          type: 'line',
          data: [avg1, avg2, avg3],
          smooth: 0.4,  // 波浪效果
          symbol: 'circle',
          symbolSize: 12,
          lineStyle: {
            color: '#667eea',
            width: 4,
            shadowColor: 'rgba(102, 126, 234, 0.3)',
            shadowBlur: 10,
            shadowOffsetY: 5
          },
          itemStyle: {
            color: '#667eea',
            borderWidth: 3,
            borderColor: '#fff',
            shadowColor: 'rgba(102, 126, 234, 0.5)',
            shadowBlur: 8
          },
          areaStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: 'rgba(102, 126, 234, 0.4)' },
              { offset: 1, color: 'rgba(102, 126, 234, 0.05)' }
            ])
          },
          label: {
            show: true,
            position: 'top',
            formatter: function(params) {
              return params.value.toFixed(2)
            },
            color: '#667eea',
            fontSize: 14,
            fontWeight: 'bold'
          }
        }]
      }
      
      chart.setOption(option)
      charts.wave = chart
    }
  }

  // 复杂度饼图
  if (complexityChart.value && hasComplexityData.value) {
    const chart = echarts.init(complexityChart.value)
    
    // 获取复杂度数据
    const complexity = props.data?.four_dim_summary?.complexity_analysis ||
                      props.data?.emotional_timeline?.complexity
    
    let complexityLabel = ''
    
    // 新格式：对象 {type: "复杂", emotions: [...]}
    if (complexity && typeof complexity === 'object' && !Array.isArray(complexity)) {
      complexityLabel = complexity.type || '复杂'
    }
    // 旧格式：数组 ["复杂", {忧: 0.4}]
    else if (Array.isArray(complexity) && complexity.length > 0) {
      complexityLabel = complexity[0]
    }
    
    if (complexityLabel) {
      const option = {
        tooltip: {
          trigger: 'item',
          formatter: '{b}: {c}'
        },
        series: [{
          type: 'pie',
          radius: ['40%', '70%'],
          center: ['50%', '50%'],
          avoidLabelOverlap: false,
          itemStyle: {
            borderRadius: 10,
            borderColor: '#fff',
            borderWidth: 2
          },
          label: {
            show: true,
            position: 'center',
            formatter: function() {
              return complexityLabel
            },
            fontSize: 18,
            fontWeight: 'bold',
            color: complexityLabel === '复杂' ? '#BA68C8' : '#64B5F6'
          },
          emphasis: {
            label: {
              show: true,
              fontSize: 20,
              fontWeight: 'bold'
            }
          },
          data: [
            { 
              value: complexityLabel === '复杂' ? 70 : 30, 
              name: complexityLabel,
              itemStyle: { 
                color: complexityLabel === '复杂' ? '#BA68C8' : '#64B5F6'
              }
            },
            { 
              value: complexityLabel === '复杂' ? 30 : 70, 
              name: complexityLabel === '复杂' ? '简单' : '复杂',
              itemStyle: { 
                color: '#e0e0e0'
              },
              label: { show: false },
              tooltip: { show: false }
            }
          ]
        }]
      }
      
      chart.setOption(option)
      charts.complexity = chart
    }
  }

  // 情绪混合饼图
  if (emotionMixChart.value && hasEmotionMix.value) {
    const chart = echarts.init(emotionMixChart.value)
    
    // 获取情绪混合数据
    const complexity = props.data?.four_dim_summary?.complexity_analysis ||
                      props.data?.emotional_timeline?.complexity
    
    let chartData = []
    
    // 新格式：对象 {type: "复杂", emotions: [{emotion: "忧", value: 0.4}, ...]}
    if (complexity && typeof complexity === 'object' && !Array.isArray(complexity) && complexity.emotions) {
      chartData = complexity.emotions.map(item => ({
        name: item.emotion,
        value: Math.round(item.value * 100)
      }))
    }
    // 旧格式：数组 ["复杂", {忧: 0.4, 思: 0.3, 恐: 0.3}]
    else if (Array.isArray(complexity) && complexity.length > 1 && typeof complexity[1] === 'object') {
      const emotionMix = complexity[1]
      chartData = Object.entries(emotionMix).map(([name, value]) => ({
        name,
        value: Math.round(value * 100)
      }))
    }
    
    if (chartData.length > 0) {
      const option = {
        tooltip: {
          trigger: 'item',
          formatter: '{b}: {c}%'
        },
        legend: {
          orient: 'vertical',
          right: '5%',
          top: 'center',
          textStyle: { color: '#666' }
        },
        series: [{
          type: 'pie',
          radius: ['45%', '70%'],
          center: ['40%', '50%'],
          avoidLabelOverlap: false,
          itemStyle: {
            borderRadius: 8,
            borderColor: '#fff',
            borderWidth: 2
          },
          label: {
            show: false
          },
          emphasis: {
            label: {
              show: true,
              fontSize: 14,
              fontWeight: 'bold'
            }
          },
          data: chartData.map((item, index) => ({
            ...item,
            itemStyle: {
              color: ['#81C784', '#FFB74D', '#E57373', '#64B5F6', '#BA68C8'][index % 5]
            }
          }))
        }]
      }
      
      chart.setOption(option)
      charts.emotionMix = chart
    }
  }
}

// 销毁图表
const disposeCharts = () => {
  Object.values(charts).forEach(chart => {
    if (chart && !chart.isDisposed()) {
      chart.dispose()
    }
  })
  charts = {}
}

// 监听数据变化
watch(() => props.data, () => {
  nextTick(() => {
    disposeCharts()
    initCharts()
  })
}, { deep: true })

// 组件挂载
onMounted(() => {
  nextTick(() => {
    initCharts()
  })
  
  // 窗口大小变化时重新渲染
  window.addEventListener('resize', () => {
    Object.values(charts).forEach(chart => {
      if (chart && !chart.isDisposed()) {
        chart.resize()
      }
    })
  })
})
</script>

<style scoped>
.analysis-report {
  padding: 8px;
}

/* 情志状态仪表盘 */
.dashboard-section {
  margin-bottom: 32px;
}

.dashboard-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20px;
}

.dashboard-card {
  background: rgba(255, 255, 255, 0.9);
  border-radius: 20px;
  padding: 24px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.06);
  border: 1px solid rgba(0, 0, 0, 0.04);
  text-align: center;
}

.dashboard-subtitle {
  font-size: 15px;
  font-weight: 600;
  color: #64748b;
  margin-bottom: 16px;
  letter-spacing: 1px;
}

.dashboard-chart {
  height: 240px;
  width: 100%;
}

/* 情绪强度波浪图 */
.wave-section {
  margin-bottom: 32px;
}

.wave-card {
  background: rgba(255, 255, 255, 0.9);
  border-radius: 20px;
  padding: 24px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.06);
  border: 1px solid rgba(0, 0, 0, 0.04);
}

.wave-chart {
  height: 240px;
  width: 100%;
}

/* 复杂度分析 */
.complexity-section {
  margin-bottom: 32px;
}

.complexity-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 20px;
}

.complexity-card {
  background: rgba(255, 255, 255, 0.9);
  border-radius: 20px;
  padding: 24px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.06);
  border: 1px solid rgba(0, 0, 0, 0.04);
  text-align: center;
}

.complexity-subtitle {
  font-size: 14px;
  font-weight: 600;
  color: #64748b;
  margin-bottom: 16px;
  letter-spacing: 1px;
}

.complexity-chart {
  height: 180px;
  width: 100%;
}

/* 分析部分 */
.analysis-section {
  margin-bottom: 32px;
}

.section-title {
  font-size: 18px;
  font-weight: 600;
  color: #2c3e50;
  margin-bottom: 20px;
  padding-bottom: 12px;
  border-bottom: 2px solid #e8e8e8;
  display: flex;
  align-items: center;
  gap: 8px;
}

.help-icon {
  font-size: 16px;
  color: #94a3b8;
  cursor: pointer;
  transition: color 0.3s ease;
}

.help-icon:hover {
  color: #667eea;
}

.analysis-card {
  background: rgba(255, 255, 255, 0.9);
  border-radius: 16px;
  padding: 20px;
  margin-bottom: 16px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
  border: 1px solid rgba(0, 0, 0, 0.05);
}

.card-subtitle {
  font-size: 15px;
  font-weight: 600;
  color: #667eea;
  margin-bottom: 16px;
}

/* 思维列表 */
.thoughts-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.thought-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 12px 16px;
  background: #f8f9fa;
  border-radius: 12px;
  border-left: 3px solid #667eea;
}

.thought-number {
  width: 24px;
  height: 24px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 600;
  flex-shrink: 0;
}

.thought-text {
  flex: 1;
  font-size: 14px;
  color: #555;
  line-height: 1.5;
}

/* 陷阱列表 */
.traps-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.trap-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  background: #FFF3E0;
  border-radius: 10px;
  font-size: 14px;
  color: #E65100;
}

.trap-icon {
  font-size: 16px;
}

/* 信念列表 */
.beliefs-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.belief-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  background: #E8EAF6;
  border-radius: 10px;
  font-size: 14px;
  color: #3949AB;
}

.belief-icon {
  font-size: 12px;
}

/* 中医卡片 */
.tcm-card {
  background: rgba(255, 255, 255, 0.9);
  border-radius: 16px;
  padding: 20px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
  border: 1px solid rgba(0, 0, 0, 0.05);
}

.tcm-item {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
  padding-bottom: 12px;
  border-bottom: 1px solid #f0f0f0;
}

.tcm-item:last-child {
  margin-bottom: 0;
  padding-bottom: 0;
  border-bottom: none;
}

.tcm-item.block {
  flex-direction: column;
  align-items: flex-start;
  gap: 8px;
}

.tcm-label {
  font-size: 14px;
  color: #666;
  font-weight: 500;
  flex-shrink: 0;
}

.tcm-value {
  font-size: 14px;
  color: #2c3e50;
}

.tcm-value.highlight {
  background: linear-gradient(135deg, #81C784 0%, #4CAF50 100%);
  color: white;
  padding: 4px 12px;
  border-radius: 12px;
  font-weight: 500;
}

.tcm-text {
  font-size: 14px;
  color: #555;
  line-height: 1.6;
  margin: 0;
}

/* 原因分析 */
.causes-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 16px;
}

.cause-card {
  background: rgba(255, 255, 255, 0.9);
  border-radius: 16px;
  padding: 20px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
  border: 1px solid rgba(0, 0, 0, 0.05);
}

.cause-card.cbt {
  border-left: 4px solid #667eea;
}

.cause-card.tcm {
  border-left: 4px solid #81C784;
}

.cause-title {
  font-size: 15px;
  font-weight: 600;
  margin-bottom: 12px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.cause-card.cbt .cause-title {
  color: #667eea;
}

.cause-card.tcm .cause-title {
  color: #4CAF50;
}

.cause-content {
  font-size: 14px;
  color: #555;
  line-height: 1.6;
}

/* 趋势卡片 */
.trends-card {
  background: linear-gradient(135deg, #FFF8E1 0%, #FFECB3 100%);
  border-radius: 16px;
  padding: 20px;
  border: 1px solid rgba(255, 183, 77, 0.3);
}

.trends-text {
  font-size: 15px;
  color: #F57F17;
  line-height: 1.7;
  margin: 0;
}

/* 无数据 */
.no-data {
  text-align: center;
  padding: 60px 20px;
  color: #95a5a6;
}

.no-data-icon {
  font-size: 48px;
  margin-bottom: 16px;
  opacity: 0.5;
}

/* 响应式 */
@media (max-width: 768px) {
  .charts-section {
    grid-template-columns: 1fr;
  }

  .causes-grid {
    grid-template-columns: 1fr;
  }

  .summary-cards {
    flex-direction: column;
  }
}
</style>
