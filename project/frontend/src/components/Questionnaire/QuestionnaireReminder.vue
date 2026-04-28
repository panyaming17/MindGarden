<template>
  <el-dialog
    v-model="visible"
    title="问卷自查提醒"
    width="450px"
    :close-on-click-modal="false"
    class="questionnaire-reminder"
  >
    <div class="reminder-content">
      <div class="reminder-icon-wrapper">
        <el-icon class="reminder-icon"><Bell /></el-icon>
      </div>
      <p class="reminder-title">
        您有 <strong class="highlight">{{ dueList.length }}</strong> 份待完成的问卷
      </p>
      <div class="due-list">
        <div
          v-for="item in dueList"
          :key="item.template_code"
          class="due-item"
        >
          <span class="due-name">{{ item.template_name }}</span>
          <el-tag
            v-if="item.days_overdue > 0"
            type="danger"
            size="small"
            class="due-tag"
          >
            逾期{{ item.days_overdue }}天
          </el-tag>
          <el-tag
            v-else-if="item.days_overdue === 0"
            type="warning"
            size="small"
            class="due-tag"
          >
            今日到期
          </el-tag>
          <el-tag
            v-else
            type="info"
            size="small"
            class="due-tag"
          >
            还有{{ Math.abs(item.days_overdue) }}天
          </el-tag>
        </div>
      </div>
      <p class="reminder-tip">定期自查有助于更好地了解自己的情绪状态</p>
    </div>
    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handlePostpone" :disabled="isLoading" :loading="isSkipping">
          稍后再说
        </el-button>
        <el-button
          type="primary"
          @click="handleStart"
          :loading="isLoading"
        >
          去测评
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, computed } from 'vue'
import { Bell } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { useQuestionnaireStore } from '@/stores/questionnaire'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:modelValue', 'start'])

const questionnaireStore = useQuestionnaireStore()

// 状态
const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

const isSkipping = ref(false)

// 从 store 获取加载状态
const isLoading = computed(() => questionnaireStore.isLoading)

// 待测列表
const dueList = computed(() => questionnaireStore.nextDueList)

// 稍后提醒（跳过所有）
const handlePostpone = async () => {
  if (dueList.value.length === 0) {
    visible.value = false
    return
  }

  isSkipping.value = true
  try {
    // 跳过所有待测问卷
    const skipPromises = dueList.value.map(item => 
      questionnaireStore.skipQuestionnaire(item.template_code)
    )
    await Promise.all(skipPromises)
    
    ElMessage.success('已为您安排下次提醒')
    visible.value = false
    emit('postpone')
  } catch (error) {
    console.error('跳过问卷失败:', error)
    ElMessage.error('操作失败，请重试')
  } finally {
    isSkipping.value = false
  }
}

// 开始测评（打开第一个问卷）
const handleStart = () => {
  if (dueList.value.length > 0) {
    emit('start', dueList.value[0].template_code)
    visible.value = false
  }
}
</script>

<style scoped>
.questionnaire-reminder :deep(.el-dialog__body) {
  padding: 30px 20px;
}

.reminder-content {
  text-align: center;
}

.reminder-icon-wrapper {
  width: 64px;
  height: 64px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 20px;
}

.reminder-icon {
  font-size: 32px;
  color: white;
}

.reminder-title {
  font-size: 18px;
  color: #2c3e50;
  margin-bottom: 20px;
}

.highlight {
  color: #f56c6c;
  font-size: 24px;
}

.due-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 20px;
  text-align: left;
}

.due-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  background: #f5f7fa;
  border-radius: 8px;
}

.due-name {
  font-size: 15px;
  color: #2c3e50;
  font-weight: 500;
}

.due-tag {
  margin-left: 8px;
}

.reminder-tip {
  font-size: 13px;
  color: #909399;
  margin-top: 16px;
}

.dialog-footer {
  display: flex;
  justify-content: space-between;
}
</style>
