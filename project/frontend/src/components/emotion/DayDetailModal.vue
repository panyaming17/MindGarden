<template>
  <el-dialog
    v-model="visible"
    :title="dialogTitle"
    width="700px"
    destroy-on-close
    class="day-detail-modal"
  >
    <div class="modal-content">
      <!-- 趋势图区域 -->
      <div class="trend-section">
        <h4 class="section-title">情绪趋势</h4>
        <div ref="trendChartRef" class="trend-chart"></div>
      </div>

      <!-- 统计信息 -->
      <div class="stats-section" v-if="dayStats.length > 0">
        <h4 class="section-title">情绪分布</h4>
        <div class="stats-list">
          <div v-for="stat in dayStats" :key="stat.type" class="stat-item">
            <span class="stat-emoji">{{ stat.icon }}</span>
            <span class="stat-name">{{ stat.name }}</span>
            <el-progress
              :percentage="stat.percentage"
              :color="stat.color"
              :stroke-width="8"
              :show-text="false"
            />
            <span class="stat-percent">{{ stat.percentage }}%</span>
            <span class="stat-count">{{ stat.count }}条</span>
          </div>
        </div>
      </div>

      <!-- 记录列表 -->
      <div class="records-section">
        <h4 class="section-title">
          记录详情
          <span class="record-count">({{ dayRecords.length }}/{{ maxRecords }}条)</span>
        </h4>
        <div class="records-list">
          <div 
            v-for="record in dayRecords" 
            :key="record.id" 
            class="record-item"
            @mouseenter="hoverId = record.id"
            @mouseleave="hoverId = null"
          >
            <span class="record-time">{{ formatTime(record.record_time) }}</span>
            <span class="record-emoji">{{ record.emotion_icon }}</span>
            <span 
              v-if="editingId !== record.id"
              class="record-name"
              :class="{ 
                'record-name-empty': !record.signature,
                'record-name-readonly': !canEditOrDelete(record)
              }"
              @click="canEditOrDelete(record) ? startEdit(record) : null"
            >
              {{ record.signature || (canEditOrDelete(record) ? '点击添加标签' : '(不可编辑)') }}
            </span>
            <input
              v-else
              ref="tagInput"
              class="record-name-input"
              v-model="editingText"
              maxlength="50"
              placeholder="输入标签后，点击输入框外部实现保存"
              @blur="saveEdit(record)"
              @keydown.escape="cancelEdit"
            />
            <button
              v-show="hoverId === record.id && canEditOrDelete(record)"
              class="record-delete"
              title="删除此条记录"
              @click.stop="handleDelete(record)"
            >×</button>
          </div>
          <el-empty v-if="dayRecords.length === 0" description="暂无记录" />
        </div>
      </div>

      <!-- 补录按钮（只有过去的日期才显示） -->
      <div class="action-section" v-if="canSupplement">
        <el-button type="primary" @click="openAddModal">
          <el-icon><Plus /></el-icon>
          补录情绪
        </el-button>
        <span class="add-hint">还可补录 {{ maxRecords - dayRecords.length }} 条</span>
      </div>
      <div class="action-section" v-else-if="dayRecords.length >= maxRecords">
        <el-alert type="warning" :closable="false" show-icon>
          <template #title>今日记录已达上限（{{ maxRecords }}条）</template>
        </el-alert>
      </div>
    </div>

    <!-- 补录弹窗 -->
    <EmotionQuickModal
      v-model="showAddModal"
      :is-supplement="true"
      :supplement-date="date"
      @submit="handleAddSuccess"
    />
  </el-dialog>
</template>

<script setup>
import { ref, computed, watch, nextTick, onMounted } from 'vue'
import { Plus } from '@element-plus/icons-vue'
import { useEmotionStore, emotionTags } from '@/stores/emotion'
import EmotionQuickModal from './EmotionQuickModal.vue'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  date: {
    type: String,
    default: ''
  },
  dateRecords: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['update:modelValue', 'refresh'])

const emotionStore = useEmotionStore()
const maxRecords = 24
const trendChartRef = ref(null)
let chartInstance = null
const showAddModal = ref(false)

// 编辑相关状态
const hoverId = ref(null)
const editingId = ref(null)
const editingText = ref('')
const tagInput = ref(null)
// 补录操作开始时间（用户点击补录按钮的时间）
const supplementStartTime = ref(null)

const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

// 判断是否可以补录（只有过去的日期才可以补录）
const canSupplement = computed(() => {
  if (!props.date) return false
  
  const today = new Date().toISOString().split('T')[0]
  // 如果日期小于今天，说明是过去的日期，可以补录
  return props.date < today && dayRecords.value.length < maxRecords
})

const dialogTitle = computed(() => {
  if (!props.date) return ''
  const date = new Date(props.date)
  return `${date.getMonth() + 1}月${date.getDate()}日 情绪记录`
})

const dayRecords = computed(() => props.dateRecords || [])

// 情绪分布统计
const dayStats = computed(() => {
  const records = dayRecords.value
  if (records.length === 0) return []

  // 按 emotion_name 分组，收集每个情绪的图标和颜色
  const groups = {}
  records.forEach(r => {
    const key = r.emotion_name || r.emotion_type
    if (!groups[key]) {
      groups[key] = {
        name: key,
        icon: r.emotion_icon, // 使用该情绪的图标
        color: r.emotion_color, // 使用该情绪的颜色
        count: 0
      }
    }
    groups[key].count += 1
  })

  const total = records.length
  return Object.values(groups).map(stat => ({
    ...stat,
    percentage: Math.round((stat.count / total) * 100)
  })).sort((a, b) => b.count - a.count)
})

const formatTime = (timeStr) => {
  if (!timeStr) return ''
  return timeStr.substring(0, 5)
}

// 初始化趋势图
const initTrendChart = () => {
  if (!window.echarts || !trendChartRef.value || dayRecords.value.length === 0) return

  if (chartInstance) {
    chartInstance.dispose()
  }

  chartInstance = window.echarts.init(trendChartRef.value)
  updateChart()
}

// 更新图表 - 单Y轴百分比，用颜色标识情绪
const updateChart = () => {
  if (!chartInstance || dayRecords.value.length === 0) return

  const records = [...dayRecords.value].sort((a, b) => a.record_time.localeCompare(b.record_time))

  // 计算当天情绪分布（用于百分比）
  const emotionCounts = {}
  records.forEach(r => {
    emotionCounts[r.emotion_type] = (emotionCounts[r.emotion_type] || 0) + 1
  })
  const total = records.length

  const times = records.map(r => r.record_time.substring(0, 5))
  const emotions = records.map(r => r.emotion_name)
  const emotionTypes_list = records.map(r => r.emotion_type)
  const intensities = records.map(r => r.four_dim_intensity || 5)  // 使用情志强度，默认值为 5

  // 数据：情志强度
  const data = intensities

  chartInstance.setOption({
    tooltip: {
      trigger: 'axis',
      formatter: function(params) {
        const idx = params[0].dataIndex
        const emotionName = emotions[idx]
        const intensity = data[idx]
        return `${params[0].name}<br/>情绪：${emotionName}<br/>情志强度：${intensity.toFixed(1)}`
      }
    },
    grid: {
      left: '18%',
      right: '8%',
      bottom: '15%',
      top: '15%'
    },
    xAxis: {
      type: 'category',
      data: times,
      axisLabel: {
        fontSize: 11,
        rotate: records.length > 8 ? 45 : 0
      }
    },
    yAxis: {
      type: 'value',
      min: 0,
      max: 10,
      interval: 2,
      name: '情志强度',
      nameLocation: 'middle',
      nameGap: 40,
      nameTextStyle: {
        fontSize: 12,
        color: '#555',
        fontWeight: 'bold'
      },
      axisLabel: {
        formatter: '{value}',
        fontSize: 11
      },
      splitLine: {
        lineStyle: {
          type: 'dashed',
          color: '#e0e0e0'
        }
      }
    },
    series: [{
      name: '情绪占比',
      type: 'line',
      data: data,
      smooth: true,
      symbol: 'circle',
      symbolSize: 10,
      lineStyle: {
        width: 3
      },
      itemStyle: {
        color: function(params) {
          const type = emotionTypes_list[params.dataIndex]
          const emotion = emotionTags.find(e => e.type === type)
          return emotion?.color || '#999'
        }
      },
      areaStyle: {
        color: new window.echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: 'rgba(102, 126, 234, 0.2)' },
          { offset: 1, color: 'rgba(102, 126, 234, 0.02)' }
        ])
      }
    }]
  })
}

const openAddModal = () => {
  // 记录补录操作开始时间
  supplementStartTime.value = new Date()
  // console.log('[DayDetailModal] 补录操作开始时间:', supplementStartTime.value)
  showAddModal.value = true
}

const handleAddSuccess = () => {
  emit('refresh')
}

// 判断记录是否可以编辑或删除
// 只有本次补录操作创建的情绪记录才可以编辑/删除
// 判断标准：记录的创建时间是否晚于补录操作开始时间
const canEditOrDelete = (record) => {
  // 如果没有补录开始时间，默认不可编辑
  if (!supplementStartTime.value || !record.created_at) return false
  
  const recordTime = new Date(record.created_at)
  
  // 如果记录的创建时间晚于补录开始时间，说明是本次补录的，可以编辑/删除
  return recordTime > supplementStartTime.value
}

// 编辑相关函数
function startEdit(record) {
  editingId.value = record.id
  editingText.value = record.signature || ''
  nextTick(() => {
    if (tagInput.value) {
      const input = Array.isArray(tagInput.value) ? tagInput.value[0] : tagInput.value
      if (input) input.focus()
    }
  })
}

async function saveEdit(record) {
  if (!editingText.value.trim() && !record.signature) {
    cancelEdit()
    return
  }
  try {
    await emotionStore.updateRecord(record.id, editingText.value.trim())
    emit('refresh')
  } catch (e) {
    console.error('保存标签失败:', e)
  } finally {
    cancelEdit()
  }
}

function cancelEdit() {
  editingId.value = null
  editingText.value = ''
}

async function handleDelete(record) {
  try {
    await emotionStore.deleteRecord(record.id)
    emit('refresh')
  } catch (e) {
    console.error('删除失败:', e)
  }
}

watch(() => visible.value, (val) => {
  if (val) {
    // 重置补录开始时间
    supplementStartTime.value = null
    nextTick(() => {
      initTrendChart()
    })
  }
})

watch(() => dayRecords.value, () => {
  nextTick(() => {
    updateChart()
  })
}, { deep: true })

onMounted(() => {
  if (visible.value) {
    initTrendChart()
  }
})
</script>

<style scoped>
.modal-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.section-title {
  font-size: 14px;
  font-weight: 600;
  color: #2c3e50;
  margin: 0 0 12px 0;
  display: flex;
  align-items: center;
  gap: 8px;
}

.record-count {
  font-size: 12px;
  color: #909399;
  font-weight: normal;
}

.trend-chart {
  width: 100%;
  height: 200px;
}

.stats-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: #f5f7fa;
  border-radius: 8px;
}

.stat-emoji {
  font-size: 18px;
}

.stat-name {
  font-size: 13px;
  color: #606266;
  min-width: 60px;
}

.stat-item :deep(.el-progress) {
  flex: 1;
}

.stat-percent {
  font-size: 12px;
  color: #909399;
  min-width: 40px;
  text-align: right;
}

.stat-count {
  font-size: 12px;
  color: #909399;
  min-width: 50px;
  text-align: right;
}

.records-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 200px;
  overflow-y: auto;
}

.record-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  background: #f5f7fa;
  border-radius: 8px;
  transition: background 0.2s;
  position: relative;
}

.record-item:hover {
  background: #e8eaed;
}

.record-time {
  font-size: 13px;
  color: #909399;
  font-family: monospace;
  min-width: 45px;
}

.record-emoji {
  font-size: 20px;
}

.record-name {
  flex: 1;
  font-size: 14px;
  color: #2c3e50;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 6px;
  transition: background 0.2s;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.record-name:hover {
  background: #dfe1e5;
}

.record-name-readonly {
  cursor: not-allowed;
  color: #909399;
}

.record-name-readonly:hover {
  background: transparent;
}

.record-name-empty {
  color: #b2bec3;
  font-style: italic;
}

.record-name-input {
  flex: 1;
  font-size: 14px;
  color: #2c3e50;
  padding: 4px 8px;
  border: 1.5px solid #74b9ff;
  border-radius: 6px;
  outline: none;
  background: #fff;
  font-family: inherit;
}

.record-name-input:focus {
  border-color: #0984e3;
  box-shadow: 0 0 0 3px rgba(9, 132, 227, 0.15);
}

.record-delete {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  border: none;
  background: #ff7675;
  color: #fff;
  font-size: 14px;
  line-height: 1;
  cursor: pointer;
  opacity: 0;
  transition: opacity 0.2s, transform 0.15s;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.record-item:hover .record-delete {
  opacity: 1;
}

.record-delete:hover {
  transform: scale(1.15);
  background: #d63031;
}

.action-section {
  display: flex;
  align-items: center;
  gap: 12px;
  padding-top: 12px;
  border-top: 1px solid #e4e7ed;
}

.add-hint {
  font-size: 12px;
  color: #909399;
}

:deep(.el-dialog__body) {
  padding: 20px;
}
</style>
