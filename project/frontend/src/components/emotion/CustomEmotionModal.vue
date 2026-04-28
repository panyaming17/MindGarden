<template>
  <el-dialog
    v-model="visible"
    title="添加自定义情绪"
    width="420px"
    :close-on-click-modal="true"
    class="custom-emotion-modal"
    destroy-on-close
  >
    <div class="custom-emotion-form">
      <!-- 情绪图标选择 -->
      <div class="form-item">
        <label class="form-label">选择图标</label>
        <div class="icon-grid">
          <div
            v-for="icon in emotionIcons"
            :key="icon"
            class="icon-item"
            :class="{ 'selected': selectedIcon === icon }"
            @click="selectedIcon = icon"
          >
            <span class="icon-emoji">{{ icon }}</span>
          </div>
        </div>
      </div>

      <!-- 情绪名称 -->
      <div class="form-item">
        <label class="form-label">情绪名称</label>
        <el-input
          v-model="emotionName"
          placeholder="给情绪起个名字，如：期待、满足..."
          maxlength="6"
          show-word-limit
        />
      </div>

      <!-- AI 智能分析结果 -->
      <div class="form-item" v-if="emotionName.trim().length >= 1">
        <label class="form-label">
          AI 智能分析
          <span class="label-hint">（基于 RAG 技术自动识别）</span>
        </label>
        
        <!-- 加载中 -->
        <div v-if="isRagLoading" class="rag-loading">
          <el-icon class="is-loading"><Loading /></el-icon>
          <span>AI 正在分析情绪特征...</span>
        </div>

        <!-- 分析结果 -->
        <div v-else-if="ragResult" class="rag-result-section">
          <!-- 中医七情推荐 -->
          <div class="rag-tcm-result">
            <div class="tcm-badge">
              <span class="tcm-icon">{{ getTcmIcon(ragResult.tcm_name) }}</span>
              <span class="tcm-name">{{ ragResult.tcm_name }}</span>
            </div>
          </div>
        </div>

        <!-- 分析失败 -->
        <div v-else-if="ragError" class="rag-error">
          <el-icon><Warning /></el-icon>
          <span>AI 分析暂时不可用，将使用默认分类</span>
        </div>
      </div>

      <!-- 提示信息 -->
      <div v-else class="form-item">
        <div class="input-hint">
          <el-icon><InfoFilled /></el-icon>
          <span>输入情绪名称后，AI 将自动分析并推荐最适合的中医七情分类</span>
        </div>
      </div>

      <!-- 预览 -->
      <div class="form-item">
        <label class="form-label">预览</label>
        <div class="preview-box" :style="{ background: selectedColor + '20', borderColor: selectedColor }">
          <span class="preview-icon">{{ selectedIcon }}</span>
          <span class="preview-name" :style="{ color: selectedColor }">{{ emotionName || '自定义情绪' }}</span>
          <span v-if="ragResult?.tcm?.recommended?.tcm_name" class="preview-tcm">
            ({{ ragResult.tcm.recommended.tcm_name }})
          </span>
        </div>
      </div>
    </div>

    <!-- 底部按钮 -->
    <template #footer>
      <div class="dialog-footer">
        <el-button @click="visible = false" size="large" :disabled="isSubmitting">取消</el-button>
        <el-button
          type="primary"
          size="large"
          :disabled="!canSubmit || isSubmitting"
          :loading="isSubmitting"
          @click="handleSubmit"
        >
          {{ isSubmitting ? '保存中...' : '添加' }}
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { Check, Star, Loading, InfoFilled, Warning } from '@element-plus/icons-vue'
import { useEmotionStore } from '@/stores/emotion'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  // 是否自动保存：true=直接保存（情绪记录页/日历补录页），false=只返回数据
  autoSave: {
    type: Boolean,
    default: true
  },
  // 补录日期（可选）
  supplementDate: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['update:modelValue', 'submit'])

const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

// 可选图标
const emotionIcons = [
  '✨', '💫', '💭', '💡', '🌟', '🔥', '💎', '🎈',
  '🌈', '🍀', '🌸', '🌺', '🌻', '🌙', '⭐', '☀️',
  '💪', '👍', '🙌', '🤝', '💐', '🎉', '🎊', '🎁',
  '💖', '💗', '💓', '💕', '❤️', '🧡', '💛', '💚',
  '😎', '🤓', '🧐', '🤔', '🤗', '🤭', '🤫', '🤠'
]

// 表单数据
const selectedIcon = ref('✨')
const emotionName = ref('')
const selectedColor = ref('#667eea') // 默认颜色

// RAG 推荐相关
const ragResult = ref(null)
const isRagLoading = ref(false)
const ragError = ref(false)

// 获取emotion store
const emotionStore = useEmotionStore()

// 简单的防抖函数实现
function debounce(fn, delay) {
  let timer = null
  return function (...args) {
    if (timer) clearTimeout(timer)
    timer = setTimeout(() => {
      fn.apply(this, args)
    }, delay)
  }
}

// RAG 智能推荐函数（使用中医七情推荐）
const fetchRAGRecommendation = debounce(async (emotionName) => {
  if (!emotionName || emotionName.trim().length < 1) {
    ragResult.value = null
    ragError.value = false
    return
  }

  isRagLoading.value = true
  ragError.value = false
  
  try {
    const result = await emotionStore.ragRecommendTCM(emotionName.trim())
    if (result) {
      ragResult.value = result
    } else {
      ragError.value = true
    }
  } catch (error) {
    console.error('RAG 推荐失败:', error)
    ragError.value = true
  } finally {
    isRagLoading.value = false
  }
}, 500)

// 监听情绪名称变化，触发RAG推荐
watch(() => emotionName.value, (newVal) => {
  fetchRAGRecommendation(newVal)
})

// 获取情绪性质图标
const getPolarityIcon = (polarity) => {
  switch (polarity) {
    case 'positive': return '😊'
    case 'neutral': return '😐'
    case 'negative': return '😔'
    default: return '😐'
  }
}

// 获取中医七情图标
const getTcmIcon = (tcmName) => {
  const iconMap = {
    '喜': '😊',
    '怒': '😠',
    '忧': '😟',
    '思': '🤔',
    '悲': '😢',
    '恐': '😰',
    '惊': '😲'
  }
  return iconMap[tcmName] || '😐'
}

// 是否可以提交
const canSubmit = computed(() => {
  return emotionName.value.trim().length > 0 && selectedIcon.value
})

// 提交状态
const isSubmitting = ref(false)

// 提交
const handleSubmit = async () => {
  if (!canSubmit.value) {
    ElMessage.warning('请填写完整信息')
    return
  }

  // 使用 RAG 推荐的中医七情结果，如果没有则使用默认值
  const tcmInfo = ragResult.value || {
    tcm_name: '思'
  }

  // 准备情绪数据
  const customEmotionData = {
    type: `custom_${Date.now()}`,
    icon: selectedIcon.value,
    name: emotionName.value.trim(),
    color: selectedColor.value,
    tcmEmotion: tcmInfo.tcm_name,
    // 使用"其他"分类
    categoryType: 'other',
    categoryName: '其他',
    categoryPolarity: 'neutral',
    healthScore: 55
  }

  // 如果需要自动保存（情绪记录页/日历补录页）
  if (props.autoSave) {
    try {
      isSubmitting.value = true
      
      // 判断使用哪个日期：补录模式使用 supplementDate，否则使用当前日期
      const recordDate = props.supplementDate || new Date().toISOString().split('T')[0]
      
      // 准备保存数据
      const submitData = {
        emotion_type: customEmotionData.type,
        emotion_icon: customEmotionData.icon,
        emotion_name: customEmotionData.name,
        emotion_color: customEmotionData.color,
        signature: emotionName.value.trim(),
        record_date: recordDate,
        record_time: new Date().toTimeString().slice(0, 8),
        // 传递 RAG 分析的中医七情结果
        tcm_emotion: customEmotionData.tcmEmotion,
        category_type: customEmotionData.categoryType,
        category_name: customEmotionData.categoryName,
        category_polarity: customEmotionData.categoryPolarity,
        health_score: customEmotionData.healthScore
      }

      // console.log('[CustomEmotionModal] 准备保存自定义情绪:', submitData)

      // 调用 API 保存
      const emotionStore = useEmotionStore()
      const result = await emotionStore.recordEmotion(submitData)
      
      // console.log('[CustomEmotionModal] 自定义情绪保存成功:', result)
      ElMessage.success('情绪已记录')
      
      // 触发刷新事件
      emit('submit', result.data)
      visible.value = false
    } catch (error) {
      console.error('[CustomEmotionModal] 保存失败:', error)
      ElMessage.error('保存失败：' + (error.message || '未知错误'))
    } finally {
      isSubmitting.value = false
    }
  } else {
    // 如果不需要自动保存，只返回数据
    // console.log('[CustomEmotionModal] 返回自定义情绪数据:', customEmotionData)
    ElMessage.success('情绪已添加')
    emit('submit', customEmotionData)
    visible.value = false
  }
}

// 监听弹窗打开，重置状态
watch(() => props.modelValue, (newVal) => {
  if (newVal) {
    selectedIcon.value = '✨'
    emotionName.value = ''
    selectedColor.value = '#667eea'
    ragResult.value = null
    ragError.value = false
    isRagLoading.value = false
    isSubmitting.value = false
  }
})
</script>

<style scoped>
.custom-emotion-modal :deep(.el-dialog) {
  border-radius: 20px;
  overflow: hidden;
}

.custom-emotion-modal :deep(.el-dialog__header) {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px 24px;
  margin: 0;
}

.custom-emotion-modal :deep(.el-dialog__title) {
  color: white;
  font-size: 18px;
  font-weight: 600;
}

.custom-emotion-modal :deep(.el-dialog__headerbtn .el-dialog__close) {
  color: white;
}

.custom-emotion-modal :deep(.el-dialog__body) {
  padding: 24px;
  background: #f8f9fa;
}

.custom-emotion-modal :deep(.el-dialog__footer) {
  background: white;
  border-top: 1px solid #e8e8e8;
  padding: 16px 24px;
}

.custom-emotion-form {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.form-item {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.form-label {
  font-size: 14px;
  color: #555;
  font-weight: 500;
}

.label-hint {
  font-size: 12px;
  color: #999;
  font-weight: normal;
}

/* 图标网格 */
.icon-grid {
  display: grid;
  grid-template-columns: repeat(8, 1fr);
  gap: 8px;
}

.icon-item {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  background: white;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s ease;
  border: 2px solid transparent;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.06);
}

.icon-item:hover {
  transform: scale(1.1);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.icon-item.selected {
  border-color: #667eea;
  background: #f0f7ff;
}

.icon-emoji {
  font-size: 20px;
  line-height: 1;
}

/* 颜色网格 */
.color-grid {
  display: grid;
  grid-template-columns: repeat(10, 1fr);
  gap: 8px;
}

.color-item {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 2px solid transparent;
}

.color-item:hover {
  transform: scale(1.15);
}

.color-item.selected {
  border-color: #333;
  box-shadow: 0 0 0 2px white, 0 0 0 4px #667eea;
}

.check-icon {
  color: white;
  font-size: 14px;
  font-weight: bold;
}

/* 输入提示 */
.input-hint {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  background: #e6f7ff;
  border-radius: 10px;
  color: #1890ff;
  font-size: 13px;
}

/* RAG加载状态 */
.rag-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 20px;
  background: white;
  border-radius: 12px;
  color: #667eea;
  font-size: 14px;
}

/* RAG结果区域 */
.rag-result-section {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 16px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.result-label {
  font-size: 12px;
  color: #999;
  margin-bottom: 8px;
}

/* 情绪分类徽章 */
.rag-category-result {
  border-bottom: 1px solid #f0f0f0;
  padding-bottom: 12px;
}

.category-badge {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  border-radius: 20px;
  font-size: 14px;
  font-weight: 500;
}

.category-badge.positive {
  background: #f6ffed;
  color: #52c41a;
  border: 1px solid #b7eb8f;
}

.category-badge.neutral {
  background: #fffbe6;
  color: #faad14;
  border: 1px solid #ffe58f;
}

.category-badge.negative {
  background: #fff2f0;
  color: #f5222d;
  border: 1px solid #ffccc7;
}

.badge-icon {
  font-size: 16px;
}

.badge-confidence {
  font-size: 11px;
  opacity: 0.8;
  margin-left: 4px;
}

/* 中医七情徽章 */
.rag-tcm-result {
  padding-bottom: 8px;
}

.tcm-badge {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: linear-gradient(135deg, #f0f7ff 0%, #e6f7ff 100%);
  border: 1px solid #91d5ff;
  border-radius: 20px;
  font-size: 14px;
  color: #1890ff;
  font-weight: 500;
}

.tcm-icon {
  font-size: 18px;
}

.tcm-confidence {
  font-size: 11px;
  opacity: 0.8;
  margin-left: 4px;
}

.tcm-description {
  margin-top: 8px;
  padding: 8px 12px;
  background: #f5f7fa;
  border-radius: 8px;
  font-size: 12px;
  color: #666;
  border-left: 3px solid #667eea;
}

/* 备选推荐 */
.rag-alternatives {
  border-top: 1px dashed #e8e8e8;
  padding-top: 12px;
}

.alternatives-title {
  font-size: 12px;
  color: #999;
  margin-bottom: 8px;
}

.alternatives-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.alternative-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  background: #f5f5f5;
  border-radius: 12px;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.alternative-item:hover {
  background: #e6f7ff;
  color: #1890ff;
}

.alt-confidence {
  font-size: 10px;
  color: #999;
}

/* 错误状态 */
.rag-error {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 16px;
  background: #fff2f0;
  border-radius: 10px;
  color: #f5222d;
  font-size: 13px;
}

/* 预览 */
.preview-box {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 16px;
  background: white;
  border-radius: 12px;
  border: 2px dashed;
}

.preview-icon {
  font-size: 32px;
}

.preview-name {
  font-size: 16px;
  font-weight: 600;
}

.preview-tcm {
  font-size: 14px;
  color: #667eea;
  font-weight: 500;
  margin-left: 4px;
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

/* 响应式 */
@media (max-width: 480px) {
  .icon-grid {
    grid-template-columns: repeat(6, 1fr);
  }

  .color-grid {
    grid-template-columns: repeat(5, 1fr);
  }
}
</style>
