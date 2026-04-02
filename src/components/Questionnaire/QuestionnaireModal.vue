<template>
  <el-dialog
    v-model="visible"
    :title="displayTemplate?.name"
    width="600px"
    :close-on-click-modal="false"
    :close-on-press-escape="false"
    class="questionnaire-modal"
    destroy-on-close
  >
    <!-- 加载状态 -->
    <div v-if="isLoading" class="loading-state">
      <el-skeleton :rows="6" animated />
    </div>

    <!-- 结果展示 -->
    <div v-else-if="showResult" class="result-section">
      <div class="result-card">
        <div class="result-icon" :class="resultIconClass">
          {{ resultIcon }}
        </div>
        <h3 class="result-title">{{ submitResult?.result_level_text || '测评完成' }}</h3>
        <div class="result-score">
          <span class="score-value">{{ submitResult?.total_score }}</span>
          <span class="score-unit">分</span>
        </div>
        <p class="result-summary">{{ submitResult?.result_analysis?.summary }}</p>
        
        <!-- 建议列表 -->
        <div v-if="submitResult?.result_analysis?.suggestions?.length" class="suggestions">
          <h4>建议：</h4>
          <ul>
            <li v-for="(suggestion, idx) in submitResult.result_analysis.suggestions" :key="idx">
              {{ suggestion }}
            </li>
          </ul>
        </div>

        <!-- 高危预警 -->
        <el-alert
          v-if="submitResult?.result_analysis?.alert"
          :title="submitResult.result_analysis.alert.title || '重要提醒'"
          :description="submitResult.result_analysis.alert.message"
          type="error"
          :closable="false"
          show-icon
          class="alert-box"
        />

        <div class="result-actions">
          <el-button type="primary" size="large" @click="handleCloseResult">
            我知道了
          </el-button>
        </div>
      </div>
    </div>

    <!-- 问卷内容 -->
    <template v-else>
      <!-- 进度条 -->
      <div class="progress-section">
        <div class="progress-info">
          <span class="progress-text">问题 {{ currentIndex + 1 }} / {{ totalCount }}</span>
          <span class="progress-percent">{{ progressPercent }}%</span>
        </div>
        <el-progress :percentage="progressPercent" :show-text="false" :stroke-width="8" />
      </div>

      <!-- 单题展示区域 -->
      <div class="question-area">
        <transition name="slide" mode="out-in">
          <div v-if="currentQuestion" :key="currentQuestion.id" class="question-card">
            <div class="question-header">
              <span class="question-number">{{ currentIndex + 1 }}</span>
              <span class="question-tag">单选题</span>
            </div>
            
            <h3 class="question-content">{{ currentQuestion.text }}</h3>
            
            <div class="options-list">
              <div
                v-for="option in currentQuestion.options"
                :key="option.id"
                class="option-card"
                :class="{ 'selected': answers[currentQuestion.id] === option.id }"
                @click="selectOption(option.id)"
              >
                <div class="option-radio">
                  <div class="radio-inner" :class="{ 'checked': answers[currentQuestion.id] === option.id }"></div>
                </div>
                <div class="option-content">
                  <span class="option-label">{{ option.label }}</span>
                  <span class="option-desc">{{ option.desc }}</span>
                </div>
              </div>
            </div>
          </div>
        </transition>
      </div>
    </template>

    <!-- 导航按钮 -->
    <template #footer>
      <div v-if="!showResult && !isLoading" class="dialog-footer">
        <el-button 
          @click="handlePrev" 
          :disabled="currentIndex === 0 || isSubmitting"
          size="large"
        >
          <el-icon><ArrowLeft /></el-icon>
          上一题
        </el-button>
        
        <div class="nav-dots">
          <span
            v-for="(q, index) in displayQuestions"
            :key="q.id"
            class="dot"
            :class="{ 
              'active': index === currentIndex,
              'answered': answers[q.id]
            }"
            @click="jumpToQuestion(index)"
          ></span>
        </div>
        
        <el-button
          v-if="!isLastQuestion"
          type="primary"
          @click="handleNext"
          :disabled="!canProceed"
          size="large"
        >
          下一题
          <el-icon><ArrowRight /></el-icon>
        </el-button>
        
        <el-button
          v-else
          type="primary"
          @click="handleSubmit"
          :loading="isSubmitting"
          :disabled="!canProceed"
          size="large"
        >
          提交
          <el-icon><Check /></el-icon>
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowLeft, ArrowRight, Check } from '@element-plus/icons-vue'
import { useQuestionnaireStore } from '@/stores/questionnaire'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  templateCode: {
    type: String,
    required: true
  }
})

const emit = defineEmits(['update:modelValue', 'submit', 'skip'])

const questionnaireStore = useQuestionnaireStore()

// 状态
const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

const answers = ref({})
const isSubmitting = ref(false)
const currentIndex = ref(0)
const showResult = ref(false)
const submitResult = ref(null)
const isLoading = computed(() => questionnaireStore.isLoading)

// 当前模板数据
const template = computed(() => questionnaireStore.currentTemplate)

// 问题列表（适配API返回格式）
const displayQuestions = computed(() => {
  return template.value?.questions || []
})

// 使用API数据或mock数据
const displayTemplate = computed(() => {
  return template.value
})

// 当前题目
const currentQuestion = computed(() => {
  return displayQuestions.value[currentIndex.value]
})

// 计算属性
const totalCount = computed(() => displayQuestions.value.length || 0)
const isLastQuestion = computed(() => currentIndex.value === totalCount.value - 1)
const canProceed = computed(() => {
  return !!answers.value[currentQuestion.value?.id]
})
const progressPercent = computed(() => {
  if (totalCount.value === 0) return 0
  return Math.round((Object.keys(answers.value).length / totalCount.value) * 100)
})

// 结果图标
const resultIcon = computed(() => {
  const level = submitResult.value?.result_level
  const score = submitResult.value?.total_score || 0
  
  if (props.templateCode === 'PHQ9' || props.templateCode === 'GAD7') {
    if (score <= 4) return '😊'
    if (score <= 9) return '😐'
    if (score <= 14) return '😟'
    return '😥'
  }
  return '📝'
})

const resultIconClass = computed(() => {
  const score = submitResult.value?.total_score || 0
  if (score <= 4) return 'icon-normal'
  if (score <= 9) return 'icon-mild'
  if (score <= 14) return 'icon-moderate'
  return 'icon-severe'
})

// 监听弹窗打开
watch(() => props.modelValue, async (newVal) => {
  if (newVal && props.templateCode) {
    answers.value = {}
    currentIndex.value = 0
    showResult.value = false
    submitResult.value = null
    
    try {
      await questionnaireStore.loadTemplate(props.templateCode)
    } catch (error) {
      ElMessage.error('加载问卷失败，请重试')
      visible.value = false
    }
  }
})

// 选择选项
const selectOption = (optionId) => {
  if (currentQuestion.value) {
    answers.value[currentQuestion.value.id] = optionId
    
    // 自动跳到下一题（延迟一点让用户看到选中效果）
    setTimeout(() => {
      if (currentIndex.value < totalCount.value - 1) {
        currentIndex.value++
      }
    }, 300)
  }
}

// 上一题
const handlePrev = () => {
  if (currentIndex.value > 0) {
    currentIndex.value--
  }
}

// 下一题
const handleNext = () => {
  if (!canProceed.value) {
    ElMessage.warning('请先选择答案')
    return
  }
  if (currentIndex.value < totalCount.value - 1) {
    currentIndex.value++
  }
}

// 跳转到指定题目
const jumpToQuestion = (index) => {
  // 只能跳转到已答过的题目或当前题目
  if (index <= currentIndex.value || answers.value[displayQuestions.value[index]?.id]) {
    currentIndex.value = index
  }
}

// 提交问卷
const handleSubmit = async () => {
  if (!canProceed.value) {
    ElMessage.warning('请先选择答案')
    return
  }

  // 检查是否所有题目都已回答
  const unansweredQuestions = displayQuestions.value.filter(q => !answers.value[q.id])
  if (unansweredQuestions.length > 0) {
    try {
      await ElMessageBox.confirm(
        `还有 ${unansweredQuestions.length} 道题未回答，是否继续提交？`,
        '提示',
        {
          confirmButtonText: '继续提交',
          cancelButtonText: '继续答题',
          type: 'warning'
        }
      )
    } catch {
      // 用户选择继续答题，跳转到第一个未答题目
      const firstUnansweredIndex = displayQuestions.value.findIndex(q => !answers.value[q.id])
      if (firstUnansweredIndex !== -1) {
        currentIndex.value = firstUnansweredIndex
      }
      return
    }
  }

  // 构建答案数组（适配API格式）
  const answersArray = Object.entries(answers.value).map(([questionId, optionId]) => {
    const question = displayQuestions.value.find(q => q.id === questionId)
    const option = question?.options.find(o => o.id === optionId)
    return {
      question_id: questionId,
      option_id: optionId,
      score: option?.score || 0
    }
  })

  try {
    isSubmitting.value = true
    const result = await questionnaireStore.submitAnswers(props.templateCode, answersArray)
    submitResult.value = result
    showResult.value = true
    emit('submit', result)
  } catch (error) {
    ElMessage.error(error.message || '提交失败，请重试')
  } finally {
    isSubmitting.value = false
  }
}

// 关闭结果页
const handleCloseResult = () => {
  visible.value = false
  showResult.value = false
  submitResult.value = null
}
</script>

<style scoped>
.questionnaire-modal :deep(.el-dialog) {
  border-radius: 20px;
  overflow: hidden;
}

.questionnaire-modal :deep(.el-dialog__header) {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px 24px;
  margin: 0;
}

.questionnaire-modal :deep(.el-dialog__title) {
  color: white;
  font-size: 18px;
  font-weight: 600;
}

.questionnaire-modal :deep(.el-dialog__headerbtn .el-dialog__close) {
  color: white;
}

.questionnaire-modal :deep(.el-dialog__body) {
  padding: 24px;
  background: #f5f7fa;
  min-height: 400px;
}

.questionnaire-modal :deep(.el-dialog__footer) {
  background: white;
  border-top: 1px solid #e8e8e8;
  padding: 16px 24px;
}

/* 加载状态 */
.loading-state {
  padding: 40px 20px;
}

/* 结果展示 */
.result-section {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 400px;
}

.result-card {
  background: white;
  border-radius: 16px;
  padding: 40px;
  text-align: center;
  max-width: 480px;
  width: 100%;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
}

.result-icon {
  font-size: 64px;
  margin-bottom: 16px;
}

.icon-normal {
  animation: bounce 1s ease infinite;
}

.icon-mild {
  animation: pulse 2s ease infinite;
}

.icon-moderate,
.icon-severe {
  animation: shake 0.5s ease;
}

@keyframes bounce {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-10px); }
}

@keyframes pulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.1); }
}

@keyframes shake {
  0%, 100% { transform: translateX(0); }
  25% { transform: translateX(-5px); }
  75% { transform: translateX(5px); }
}

.result-title {
  font-size: 22px;
  color: #2c3e50;
  margin-bottom: 16px;
  font-weight: 600;
}

.result-score {
  margin-bottom: 16px;
}

.score-value {
  font-size: 48px;
  font-weight: 700;
  color: #667eea;
}

.score-unit {
  font-size: 18px;
  color: #666;
  margin-left: 4px;
}

.result-summary {
  font-size: 15px;
  color: #666;
  line-height: 1.6;
  margin-bottom: 24px;
}

.suggestions {
  text-align: left;
  background: #f8f9fa;
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 20px;
}

.suggestions h4 {
  font-size: 15px;
  color: #2c3e50;
  margin-bottom: 12px;
}

.suggestions ul {
  margin: 0;
  padding-left: 20px;
}

.suggestions li {
  font-size: 14px;
  color: #666;
  line-height: 1.8;
}

.alert-box {
  margin-bottom: 24px;
  text-align: left;
}

.result-actions {
  margin-top: 24px;
}

.result-actions .el-button {
  min-width: 140px;
}

/* 进度条区域 */
.progress-section {
  margin-bottom: 24px;
}

.progress-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.progress-text {
  font-size: 14px;
  color: #666;
  font-weight: 500;
}

.progress-percent {
  font-size: 14px;
  color: #667eea;
  font-weight: 600;
}

.progress-section :deep(.el-progress-bar__outer) {
  border-radius: 10px;
  background-color: #e0e0e0;
}

.progress-section :deep(.el-progress-bar__inner) {
  border-radius: 10px;
  background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
}

/* 题目区域 */
.question-area {
  min-height: 300px;
}

.question-card {
  background: white;
  border-radius: 16px;
  padding: 28px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
}

.question-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 20px;
}

.question-number {
  width: 36px;
  height: 36px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  font-weight: 600;
}

.question-tag {
  font-size: 12px;
  color: #999;
  background: #f0f0f0;
  padding: 4px 12px;
  border-radius: 12px;
}

.question-content {
  font-size: 18px;
  color: #2c3e50;
  line-height: 1.6;
  margin-bottom: 28px;
  font-weight: 500;
}

/* 选项列表 */
.options-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.option-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px 20px;
  background: #f8f9fa;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.3s ease;
  border: 2px solid transparent;
}

.option-card:hover {
  background: #e8f0fe;
  border-color: #667eea;
}

.option-card.selected {
  background: #667eea;
  border-color: #667eea;
}

.option-radio {
  width: 22px;
  height: 22px;
  border: 2px solid #ccc;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: all 0.3s ease;
}

.option-card.selected .option-radio {
  border-color: white;
}

.radio-inner {
  width: 10px;
  height: 10px;
  background: transparent;
  border-radius: 50%;
  transition: all 0.3s ease;
}

.radio-inner.checked {
  background: white;
}

.option-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.option-label {
  font-size: 15px;
  color: #555;
  transition: all 0.3s ease;
}

.option-desc {
  font-size: 13px;
  color: #999;
  transition: all 0.3s ease;
}

.option-card.selected .option-label,
.option-card.selected .option-desc {
  color: white;
}

/* 底部导航 */
.dialog-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.dialog-footer .el-button {
  min-width: 100px;
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

/* 导航点 */
.nav-dots {
  display: flex;
  gap: 8px;
  justify-content: center;
  flex: 1;
  margin: 0 20px;
}

.dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #e0e0e0;
  cursor: pointer;
  transition: all 0.3s ease;
}

.dot:hover {
  background: #b0b0b0;
}

.dot.active {
  background: #667eea;
  width: 24px;
  border-radius: 4px;
}

.dot.answered {
  background: #67c23a;
}

.dot.answered.active {
  background: #667eea;
}

/* 过渡动画 */
.slide-enter-active,
.slide-leave-active {
  transition: all 0.3s ease;
}

.slide-enter-from {
  opacity: 0;
  transform: translateX(30px);
}

.slide-leave-to {
  opacity: 0;
  transform: translateX(-30px);
}
</style>
