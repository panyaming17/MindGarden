<template>
  <div class="record-detail" v-if="record">
    <div class="detail-header">
      <div class="user-section">
        <h3>{{ record.username || '未知用户' }}</h3>
        <p class="user-id">用户ID: {{ record.user_id }}</p>
      </div>
      <div class="score-section">
        <div class="score-value" :class="getScoreClass(record.result_level)">
          {{ record.total_score }}分
        </div>
        <el-tag :type="getLevelType(record.result_level)" effect="dark" size="large">
          {{ getLevelText(record.result_level) }}
        </el-tag>
        <el-button type="primary" size="small" @click="showModifyDialog" style="margin-top: 8px;">
          修正结果
        </el-button>
      </div>
    </div>

    <div class="detail-section">
      <h4>答题详情</h4>
      <div class="answers-list">
        <div v-for="(answer, index) in record.answers" :key="index" class="answer-item">
          <div class="question">{{ index + 1 }}. {{ answer.question_text || answer.question_id }}</div>
          <div class="answer">
            <span class="option">选项: {{ answer.option_text || answer.option_id }}</span>
            <span class="score">得分: {{ answer.score }}</span>
          </div>
        </div>
      </div>
    </div>

    <div class="detail-section" v-if="record.related_alerts && record.related_alerts.length > 0">
      <h4>关联预警</h4>
      <div class="alerts-list">
        <div v-for="alert in record.related_alerts" :key="alert.id" class="alert-item">
          <el-tag :type="alert.level === 'danger' ? 'danger' : 'warning'" effect="dark" size="small">
            {{ alert.level === 'danger' ? '高危' : '中危' }}
          </el-tag>
          <span class="alert-title">{{ alert.title }}</span>
          <span class="alert-time">{{ formatDate(alert.created_at) }}</span>
          <el-tag v-if="alert.is_acknowledged" type="success" size="small">已确认</el-tag>
          <el-tag v-else type="warning" size="small">未确认</el-tag>
        </div>
      </div>
    </div>

    <!-- 修正结果等级弹窗 -->
    <el-dialog v-model="modifyDialogVisible" title="修正结果等级" width="500px">
      <el-form :model="modifyForm" label-width="100px">
        <el-form-item label="当前等级">
          <el-tag :type="getLevelType(record.result_level)" effect="dark">
            {{ getLevelText(record.result_level) }}
          </el-tag>
        </el-form-item>
        <el-form-item label="新等级">
          <el-select v-model="modifyForm.newLevel" placeholder="请选择新等级">
            <el-option label="正常" value="none" />
            <el-option label="轻度" value="mild" />
            <el-option label="中度" value="moderate" />
            <el-option label="中重度" value="moderately_severe" />
            <el-option label="重度" value="severe" />
          </el-select>
        </el-form-item>
        <el-form-item label="修正原因">
          <el-input v-model="modifyForm.reason" type="textarea" rows="3" placeholder="请输入修正原因" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="modifyDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitModify">确认修正</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useAdminQuestionnaireStore } from '@/stores/adminQuestionnaire'
import { ElMessage, ElMessageBox } from 'element-plus'

const props = defineProps({
  record: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['modified'])

const store = useAdminQuestionnaireStore()
const modifyDialogVisible = ref(false)
const modifyForm = reactive({
  newLevel: '',
  reason: ''
})

const getScoreClass = (level) => {
  const map = { none: 'success', mild: 'warning', moderate: 'warning', moderately_severe: 'danger', severe: 'danger' }
  return map[level] || ''
}

const getLevelType = (level) => {
  const map = { none: 'success', mild: 'warning', moderate: 'warning', moderately_severe: 'danger', severe: 'danger' }
  return map[level] || 'info'
}

const getLevelText = (level) => {
  const map = { none: '正常', mild: '轻度', moderate: '中度', moderately_severe: '中重度', severe: '重度' }
  return map[level] || level
}

const formatDate = (date) => {
  return date ? new Date(date).toLocaleString('zh-CN') : '-'
}

const showModifyDialog = () => {
  modifyForm.newLevel = props.record.result_level
  modifyForm.reason = ''
  modifyDialogVisible.value = true
}

const submitModify = async () => {
  if (!modifyForm.newLevel) {
    ElMessage.warning('请选择新等级')
    return
  }
  if (!modifyForm.reason) {
    ElMessage.warning('请输入修正原因')
    return
  }
  
  try {
    await ElMessageBox.confirm(
      `确定要将结果等级从 "${getLevelText(props.record.result_level)}" 修改为 "${getLevelText(modifyForm.newLevel)}" 吗？`,
      '确认修正',
      { confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning' }
    )
    
    await store.modifyRecordResult(props.record.id, modifyForm.newLevel, modifyForm.reason)
    ElMessage.success('结果等级已修正')
    modifyDialogVisible.value = false
    emit('modified')
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('修正失败: ' + (error.message || '未知错误'))
    }
  }
}
</script>

<style scoped>
.record-detail {
  padding: 20px 0;
}
.detail-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-bottom: 20px;
  border-bottom: 1px solid #ebeef5;
  margin-bottom: 20px;
}
.user-section h3 {
  margin: 0 0 8px 0;
  font-size: 20px;
}
.user-id {
  color: #909399;
  font-size: 14px;
  margin: 0;
}
.score-section {
  text-align: center;
}
.score-value {
  font-size: 36px;
  font-weight: 600;
  margin-bottom: 8px;
}
.score-value.success { color: #67c23a; }
.score-value.warning { color: #e6a23c; }
.score-value.danger { color: #f56c6c; }
.detail-section {
  margin-bottom: 24px;
}
.detail-section h4 {
  font-size: 16px;
  font-weight: 600;
  margin: 0 0 16px 0;
  color: #303133;
}
.answers-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.answer-item {
  padding: 12px;
  background: #f5f7fa;
  border-radius: 8px;
}
.question {
  font-weight: 500;
  margin-bottom: 8px;
  color: #303133;
}
.answer {
  display: flex;
  gap: 16px;
  font-size: 14px;
  color: #606266;
}
.alerts-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.alert-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: #fef0f0;
  border-radius: 8px;
}
.alert-title {
  flex: 1;
  font-weight: 500;
}
.alert-time {
  color: #909399;
  font-size: 14px;
}
</style>
