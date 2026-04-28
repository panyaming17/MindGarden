<template>
  <el-dialog
    v-model="visible"
    title="记录此刻心情"
    width="500px"
    :close-on-click-modal="true"
    class="emotion-quick-modal"
    destroy-on-close
  >
    <!-- 最近使用 -->
    <div v-if="recentEmotions.length > 0" class="recent-section">
      <span class="section-label">最近使用</span>
      <div class="recent-list">
        <div
          v-for="emotion in recentEmotions"
          :key="emotion.type"
          class="recent-item"
          :class="{ 'selected': selectedType === emotion.type }"
          @click="selectEmotion(emotion)"
        >
          <span class="recent-icon">{{ emotion.icon }}</span>
          <span class="recent-name">{{ emotion.name }}</span>
        </div>
      </div>
    </div>

    <!-- 所有情绪 -->
    <div class="emotion-section">
      <span class="section-label">选择情绪</span>
      <div class="emotion-grid">
        <div
          v-for="emotion in emotionTags"
          :key="emotion.type"
          class="emotion-item"
          :class="{ 'selected': selectedType === emotion.type }"
          :style="{ '--emotion-color': emotion.color }"
          @click="selectEmotion(emotion)"
        >
          <span class="emotion-icon">{{ emotion.icon }}</span>
          <span class="emotion-name">{{ emotion.name }}</span>
        </div>
        <!-- 添加自定义情绪按钮 -->
        <div class="emotion-item add-custom-btn" @click="showCustomModal = true">
          <span class="emotion-icon">
            <el-icon><Plus /></el-icon>
          </span>
          <span class="emotion-name">自定义</span>
        </div>
      </div>
    </div>

    <!-- 签名输入 -->
    <div class="signature-section">
      <span class="section-label">此刻心情（选填，最多 50 字）</span>
      <el-input
        v-model="signature"
        type="textarea"
        :rows="3"
        placeholder="记录下此刻的感受..."
        maxlength="50"
        show-word-limit
        resize="none"
      />
    </div>

    <!-- 时间段选择（仅补录模式显示） -->
    <div v-if="props.isSupplement" class="time-slot-section">
      <span class="section-label">选择补录时间段</span>
      <el-select
        v-model="selectedTimeSlot"
        placeholder="请选择时间段"
        size="large"
        style="width: 100%"
        :disabled="isLoading"
      >
        <el-option
          v-for="slot in availableTimeSlots"
          :key="slot.value"
          :label="slot.label"
          :value="slot.value"
          :disabled="slot.disabled"
        >
          <span>{{ slot.label }}</span>
          <span v-if="slot.disabled" style="color: #909399; font-size: 12px;">（已记录）</span>
        </el-option>
      </el-select>
    </div>

    <!-- 底部按钮 -->
    <template #footer>
      <div class="dialog-footer">
        <el-button @click="visible = false" size="large">取消</el-button>
        <el-button
          type="primary"
          size="large"
          :loading="isLoading"
          :disabled="!selectedType"
          @click="handleSubmit"
        >
          记录心情
        </el-button>
      </div>
    </template>
  </el-dialog>

  <!-- 自定义情绪弹窗 -->
  <CustomEmotionModal
    v-model="showCustomModal"
    :auto-save="true"
    :supplement-date="props.isSupplement ? props.supplementDate : ''"
    @submit="handleCustomEmotionSubmit"
  />
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { useEmotionStore, emotionTags } from '@/stores/emotion'
import CustomEmotionModal from './CustomEmotionModal.vue'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  isSupplement: {
    type: Boolean,
    default: false
  },
  supplementDate: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['update:modelValue', 'submit'])

const emotionStore = useEmotionStore()

// 状态
const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

const selectedType = ref('')
const selectedEmotion = ref(null)
const signature = ref('')
const isLoading = ref(false)
const selectedTimeSlot = ref('')  // 选中的时间段
const existingRecords = ref([])   // 该日期已有的记录

// 生成 24 小时时间段选项
const availableTimeSlots = computed(() => {
  const slots = []
  for (let hour = 0; hour < 24; hour++) {
    const timeSlot = `${hour.toString().padStart(2, '0')}:00`
    const nextHour = (hour + 1) % 24
    const timeSlotEnd = `${nextHour.toString().padStart(2, '0')}:00`
    const label = `${timeSlot} - ${timeSlotEnd}`
    
    // 检查该时间段是否已有记录
    const isOccupied = existingRecords.value.some(record => {
      const recordHour = parseInt(record.record_time.substring(0, 2))
      return recordHour === hour
    })
    
    slots.push({
      value: timeSlot,
      label: label,
      disabled: isOccupied
    })
  }
  return slots
})

// 自定义情绪（一次性使用，不保存到列表）
const showCustomModal = ref(false)

// 处理自定义情绪添加（一次性使用）
const handleCustomEmotionSubmit = (customEmotion) => {
  console.log('[EmotionQuickModal] handleCustomEmotionSubmit 被调用')
  // console.log('[EmotionQuickModal] 接收到的 customEmotion:', customEmotion)
  
  // 自定义情绪已经在 CustomEmotionModal 中保存了
  // 直接关闭 EmotionQuickModal 并触发刷新
  ElMessage.success(props.isSupplement ? '补录成功！' : '情绪记录成功！')
  emit('submit', customEmotion)
  visible.value = false
}

// 最近使用的情绪（从本地存储读取）
const recentEmotions = computed(() => {
  const stored = localStorage.getItem('recent_emotions')
  if (stored) {
    const types = JSON.parse(stored)
    return types.map(type => emotionTags.find(e => e.type === type)).filter(Boolean)
  }
  return []
})

// 选择情绪
const selectEmotion = (emotion) => {
  selectedType.value = emotion.type
  selectedEmotion.value = emotion
}

// 保存到最近使用
const saveRecentEmotion = (type) => {
  const stored = localStorage.getItem('recent_emotions')
  let recent = stored ? JSON.parse(stored) : []
  
  // 移除已存在的
  recent = recent.filter(t => t !== type)
  // 添加到开头
  recent.unshift(type)
  // 只保留最近 5 个
  recent = recent.slice(0, 5)
  
  localStorage.setItem('recent_emotions', JSON.stringify(recent))
}

// 提交
const handleSubmit = async () => {
  if (!selectedType.value) {
    ElMessage.warning('请选择一种情绪')
    return
  }

  // 补录模式需要选择时间段
  if (props.isSupplement && !selectedTimeSlot.value) {
    ElMessage.warning('请选择补录时间段')
    return
  }

  console.log('[EmotionQuickModal] handleSubmit 被调用')
  // console.log('[EmotionQuickModal] selectedType:', selectedType.value)
  // console.log('[EmotionQuickModal] selectedEmotion:', selectedEmotion.value)

  try {
    isLoading.value = true

    // 判断使用哪个日期：补录模式使用 supplementDate，否则使用当前日期
    const recordDate = props.isSupplement && props.supplementDate
      ? props.supplementDate
      : new Date().toISOString().split('T')[0]

    // 使用时间选择的小时，补录模式使用选择的时间，否则使用当前时间
    let recordTime = new Date().toTimeString().slice(0, 8)
    if (props.isSupplement && selectedTimeSlot.value) {
      const hour = selectedTimeSlot.value.substring(0, 2)
      recordTime = `${hour}:00:00`
    }

    // 准备提交数据
    const data = {
      emotion_type: selectedType.value,
      emotion_icon: selectedEmotion.value?.icon,
      emotion_name: selectedEmotion.value?.name,
      emotion_color: selectedEmotion.value?.color,
      signature: signature.value.trim(),
      record_date: recordDate,
      record_time: recordTime,
      // 自定义情绪的额外字段
      tcm_emotion: selectedEmotion.value?.tcmEmotion || null,
      category_type: selectedEmotion.value?.categoryType || null,
      category_name: selectedEmotion.value?.categoryName || null,
      category_polarity: selectedEmotion.value?.categoryPolarity || null,
      health_score: selectedEmotion.value?.healthScore || null
    }

    // console.log('[EmotionQuickModal] 提交数据:', data)

    await emotionStore.recordEmotion(data)

    // 保存到最近使用
    saveRecentEmotion(selectedType.value)

    ElMessage.success(props.isSupplement ? '补录成功！' : '情绪记录成功！')
    emit('submit', data)
    visible.value = false

    // 重置表单
    selectedType.value = ''
    selectedEmotion.value = null
    signature.value = ''
    selectedTimeSlot.value = ''

  } catch (error) {
    console.error('[EmotionQuickModal] 记录失败:', error)
    
    // 检查是否是时间限制错误
    if (error.message && error.message.includes('距离上次记录时间不足')) {
      ElMessage.error({
        message: error.message,
        duration: 5000,
        showClose: true
      })
    } else {
      ElMessage.error(props.isSupplement ? '补录失败，请重试' : '记录失败，请重试')
    }
  } finally {
    isLoading.value = false
  }
}

// 监听弹窗打开，加载已有记录数据
watch(() => props.modelValue, async (newVal) => {
  if (newVal && props.isSupplement && props.supplementDate) {
    // 补录模式，加载该日期的已有记录
    try {
      const records = await emotionStore.fetchDayRecords(props.supplementDate)
      existingRecords.value = records || []
      // console.log('[EmotionQuickModal] 加载已有记录:', existingRecords.value)
    } catch (e) {
      console.error('加载已有记录失败:', e)
    }
  }
}, { immediate: true })

// 监听弹窗打开，重置状态
watch(() => props.modelValue, (newVal) => {
  if (newVal) {
    selectedType.value = ''
    selectedEmotion.value = null
    signature.value = ''
    selectedTimeSlot.value = ''
  }
})
</script>

<style scoped>
.emotion-quick-modal :deep(.el-dialog) {
  border-radius: 20px;
  overflow: hidden;
}

.emotion-quick-modal :deep(.el-dialog__header) {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px 24px;
  margin: 0;
}

.emotion-quick-modal :deep(.el-dialog__title) {
  color: white;
  font-size: 18px;
  font-weight: 600;
}

.emotion-quick-modal :deep(.el-dialog__headerbtn .el-dialog__close) {
  color: white;
}

.emotion-quick-modal :deep(.el-dialog__body) {
  padding: 24px;
  background: #f8f9fa;
}

.emotion-quick-modal :deep(.el-dialog__footer) {
  background: white;
  border-top: 1px solid #e8e8e8;
  padding: 16px 24px;
}

/* 分区标签 */
.section-label {
  display: block;
  font-size: 14px;
  color: #666;
  margin-bottom: 12px;
  font-weight: 500;
}

/* 最近使用 */
.recent-section {
  margin-bottom: 20px;
}

.recent-list {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.recent-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  background: white;
  border-radius: 20px;
  cursor: pointer;
  transition: all 0.3s ease;
  border: 2px solid transparent;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.recent-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.recent-item.selected {
  border-color: #667eea;
  background: #f0f7ff;
}

.recent-icon {
  font-size: 20px;
}

.recent-name {
  font-size: 14px;
  color: #555;
}

/* 情绪网格 */
.emotion-section {
  margin-bottom: 20px;
}

.emotion-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
}

.emotion-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  padding: 16px 8px;
  background: white;
  border-radius: 16px;
  cursor: pointer;
  transition: all 0.3s ease;
  border: 2px solid transparent;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.emotion-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
}

.emotion-item.selected {
  border-color: var(--emotion-color, #667eea);
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%);
}

/* 添加自定义情绪按钮 */
.emotion-item.add-custom-btn {
  background: linear-gradient(135deg, #f5f7fa 0%, #e4e8ec 100%);
  border: 2px dashed #c0c4cc;
}

.emotion-item.add-custom-btn:hover {
  background: linear-gradient(135deg, #eef2ff 0%, #e0e7ff 100%);
  border-color: #667eea;
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(102, 126, 234, 0.2);
}

.emotion-item.add-custom-btn .emotion-icon {
  font-size: 28px;
  color: #909399;
}

.emotion-item.add-custom-btn:hover .emotion-icon {
  color: #667eea;
}

.emotion-item.add-custom-btn .emotion-name {
  color: #909399;
}

.emotion-item.add-custom-btn:hover .emotion-name {
  color: #667eea;
}

.emotion-icon {
  font-size: 32px;
  line-height: 1;
}

.emotion-name {
  font-size: 13px;
  color: #555;
  font-weight: 500;
}

/* 签名输入 */
.signature-section {
  margin-bottom: 8px;
}

.signature-section :deep(.el-textarea__inner) {
  border-radius: 12px;
  padding: 12px;
  font-size: 14px;
}

/* 时间段选择 */
.time-slot-section {
  margin-bottom: 8px;
}

.time-slot-section :deep(.el-select) {
  width: 100%;
}

/* 底部按钮 */
.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

.dialog-footer .el-button--primary {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
}

.dialog-footer .el-button--primary:hover {
  background: linear-gradient(135deg, #5a6fd6 0%, #6a4190 100%);
}

.dialog-footer .el-button--primary.is-disabled {
  background: #c0c4cc;
}
</style>
