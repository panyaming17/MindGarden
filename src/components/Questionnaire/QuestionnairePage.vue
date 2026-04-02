<template>
  <div class="questionnaire-page">
    <!-- 页面头部 -->
    <div class="page-header">
      <h2 class="page-title">问卷自查</h2>
      <p class="page-subtitle">定期自查有助于更好地了解自己的情绪状态</p>
    </div>

    <!-- 待测问卷提醒区（后端推送） -->
    <div v-if="dueQuestionnaires.length > 0" class="due-section">
      <div class="section-header">
        <h3 class="section-title">
          <el-icon><Bell /></el-icon>
          待测问卷
          <el-badge :value="dueQuestionnaires.length" class="due-badge" />
        </h3>
        <span class="section-desc">根据您的测评计划，以下问卷需要完成</span>
      </div>
      <div class="due-cards">
        <div
          v-for="due in dueQuestionnaires"
          :key="due.template_code"
          class="due-card"
          :class="{ 'overdue': due.days_overdue > 0 }"
        >
          <div class="due-card-header">
            <div class="due-icon">{{ getQuestionnaireIcon(due.template_code) }}</div>
            <div class="due-info">
              <h4 class="due-name">{{ due.template_name }}</h4>
              <p class="due-time">
                <el-tag v-if="due.days_overdue > 0" type="danger" size="small">逾期 {{ due.days_overdue }} 天</el-tag>
                <el-tag v-else-if="due.days_overdue === 0" type="warning" size="small">今日到期</el-tag>
                <el-tag v-else type="info" size="small">还有 {{ Math.abs(due.days_overdue) }} 天</el-tag>
              </p>
            </div>
          </div>
          <div class="due-card-actions">
            <el-button type="primary" @click="startQuestionnaire(due.template_code)">
              立即测评
            </el-button>
            <el-button text @click="skipQuestionnaire(due.template_code)">
              稍后提醒
            </el-button>
          </div>
        </div>
      </div>
    </div>

    <!-- Tab 切换区域 -->
    <div class="tab-section">
      <el-tabs v-model="activeTab" type="border-card" class="questionnaire-tabs">
        <!-- 全部问卷 Tab -->
        <el-tab-pane label="全部问卷" name="all">
          <div v-if="isLoading && !allQuestionnaires.length" class="loading-state">
            <el-skeleton :rows="3" animated />
          </div>
          <div v-else class="questionnaire-grid">
            <div
              v-for="item in allQuestionnaires"
              :key="item.code"
              class="questionnaire-card"
              :class="{ 
                'due': isDue(item.code),
                'completed': item.lastRecord && !isDue(item.code)
              }"
            >
              <div class="card-status-bar" :class="getStatusClass(item)"></div>
              
              <div class="card-content">
                <div class="card-header">
                  <div class="card-icon">{{ item.icon }}</div>
                  <div class="card-title-wrapper">
                    <h4 class="card-title">{{ item.name }}</h4>
                    <el-tag v-if="isDue(item.code)" type="danger" effect="dark" size="small">待测评</el-tag>
                    <el-tag v-else-if="item.lastRecord" type="success" size="small">已完成</el-tag>
                    <el-tag v-else type="info" size="small">未开始</el-tag>
                  </div>
                </div>
                
                <p class="card-desc">{{ item.description }}</p>
                
                <div class="card-meta">
                  <div class="meta-item">
                    <el-icon><Document /></el-icon>
                    <span>{{ item.questionCount }} 题</span>
                  </div>
                  <div class="meta-item">
                    <el-icon><Timer /></el-icon>
                    <span>约 {{ item.estimatedTime }} 分钟</span>
                  </div>
                </div>

                <!-- 最近测评结果 -->
                <div v-if="item.lastRecord" class="last-result">
                  <div class="result-divider"></div>
                  <div class="result-content">
                    <div class="result-main">
                      <span class="result-score" :class="getScoreClass(item.code, item.lastRecord.total_score)">
                        {{ item.lastRecord.total_score }}
                      </span>
                      <span class="result-unit">分</span>
                      <el-tag :type="getResultType(item.lastRecord.result_level)" size="small" class="result-level">
                        {{ item.lastRecord.result_level_text }}
                      </el-tag>
                    </div>
                    <div class="result-time">
                      上次测评：{{ formatDate(item.lastRecord.created_at) }}
                    </div>
                  </div>
                </div>
              </div>

              <div class="card-actions">
                <el-button
                  v-if="isDue(item.code)"
                  type="primary"
                  size="large"
                  class="action-btn"
                  @click="startQuestionnaire(item.code)"
                >
                  <el-icon><Edit /></el-icon>
                  开始测评
                </el-button>
                <el-button
                  v-else
                  size="large"
                  class="action-btn"
                  @click="startQuestionnaire(item.code)"
                >
                  <el-icon><RefreshRight /></el-icon>
                  {{ item.lastRecord ? '重新测评' : '开始测评' }}
                </el-button>
                <el-button
                  v-if="item.lastRecord"
                  type="info"
                  plain
                  size="large"
                  class="action-btn"
                  @click="viewHistory(item.code)"
                >
                  <el-icon><TrendCharts /></el-icon>
                  历史记录
                </el-button>
              </div>
            </div>
          </div>
        </el-tab-pane>

        <!-- 历史结果 Tab -->
        <el-tab-pane label="历史结果" name="history">
          <div class="history-section">
            <!-- 选择问卷类型 -->
            <div class="history-selector">
              <span class="selector-label">选择问卷：</span>
              <el-radio-group v-model="selectedHistoryCode" size="large">
                <el-radio-button label="PHQ9">PHQ-9 抑郁量表</el-radio-button>
                <el-radio-button label="GAD7">GAD-7 焦虑量表</el-radio-button>
                <el-radio-button label="TCM_CONSTITUTION">中医体质辨识</el-radio-button>
              </el-radio-group>
            </div>

            <!-- 历史记录内容 -->
            <div v-if="selectedHistoryCode" class="history-content">
              <QuestionnaireHistory :template-code="selectedHistoryCode" />
            </div>
          </div>
        </el-tab-pane>
      </el-tabs>
    </div>

    <!-- 问卷弹窗 -->
    <QuestionnaireModal
      v-model="showModal"
      :template-code="currentCode"
      @submit="handleSubmit"
      @skip="handleSkip"
    />

    <!-- 历史记录抽屉（从卡片点击打开） -->
    <el-drawer
      v-model="showHistory"
      title="测评历史"
      size="650px"
      destroy-on-close
    >
      <QuestionnaireHistory
        v-if="showHistory && historyCode"
        :template-code="historyCode"
      />
    </el-drawer>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { Bell, Document, Timer, Edit, RefreshRight, TrendCharts } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useQuestionnaireStore } from '@/stores/questionnaire'
import QuestionnaireModal from './QuestionnaireModal.vue'
import QuestionnaireHistory from './QuestionnaireHistory.vue'

const questionnaireStore = useQuestionnaireStore()

// 状态
const activeTab = ref('all')
const showModal = ref(false)
const showHistory = ref(false)
const currentCode = ref('')
const historyCode = ref('')
const selectedHistoryCode = ref('PHQ9')

// 加载状态
const isLoading = computed(() => questionnaireStore.isLoading)

// 问卷基础配置
const questionnaireConfigs = {
  PHQ9: {
    name: 'PHQ-9 抑郁量表',
    description: '用于筛查和评估抑郁症状的严重程度，是国际通用的抑郁自评工具',
    icon: '😔',
    questionCount: 9,
    estimatedTime: 2
  },
  GAD7: {
    name: 'GAD-7 焦虑量表',
    description: '用于筛查和评估焦虑症状的严重程度，快速识别广泛性焦虑',
    icon: '😰',
    questionCount: 7,
    estimatedTime: 2
  },
  TCM_CONSTITUTION: {
    name: '中医体质辨识',
    description: '根据中医体质学说评估您的体质类型，了解身体特质',
    icon: '🌿',
    questionCount: 60,
    estimatedTime: 10
  }
}

// 待测问卷列表（来自后端推送）
const dueQuestionnaires = computed(() => {
  return questionnaireStore.nextDueList
})

// 所有问卷列表（合并配置和后端数据）
const allQuestionnaires = computed(() => {
  const dueList = questionnaireStore.nextDueList
  
  return Object.entries(questionnaireConfigs).map(([code, config]) => {
    const dueItem = dueList.find(item => item.template_code === code)
    const history = questionnaireStore.historyRecords[code]
    
    return {
      code,
      ...config,
      isDue: !!dueItem,
      dueInfo: dueItem,
      lastRecord: history?.records?.[0]
    }
  })
})

// 检查是否待测
const isDue = (code) => {
  return dueQuestionnaires.value.some(item => item.template_code === code)
}

// 获取问卷图标
const getQuestionnaireIcon = (code) => {
  return questionnaireConfigs[code]?.icon || '📝'
}

// 获取状态样式类
const getStatusClass = (item) => {
  if (isDue(item.code)) return 'status-due'
  if (item.lastRecord) return 'status-completed'
  return 'status-pending'
}

// 初始化
onMounted(async () => {
  await questionnaireStore.checkDueQuestionnaires()
  // 预加载历史记录
  await Promise.all(
    Object.keys(questionnaireConfigs).map(code => 
      questionnaireStore.loadHistory(code)
    )
  )
})

// 监听 Tab 切换，切换到历史记录时加载数据
watch(activeTab, async (newTab) => {
  if (newTab === 'history' && selectedHistoryCode.value) {
    await questionnaireStore.loadHistory(selectedHistoryCode.value)
  }
})

// 监听选择的问卷变化
watch(selectedHistoryCode, async (newCode) => {
  if (newCode) {
    await questionnaireStore.loadHistory(newCode)
  }
})

// 开始测评
const startQuestionnaire = (code) => {
  currentCode.value = code
  showModal.value = true
}

// 跳过问卷
const skipQuestionnaire = async (code) => {
  try {
    await ElMessageBox.confirm(
      '跳过后我们会在下次登录时再次提醒您，是否确认跳过？',
      '提示',
      {
        confirmButtonText: '确认跳过',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    await questionnaireStore.skipQuestionnaire(code)
    ElMessage.info('已跳过本次问卷')
  } catch (error) {
    // 用户取消或API错误
    if (error !== 'cancel') {
      console.error('跳过问卷失败:', error)
    }
  }
}

// 查看历史（从卡片点击）
const viewHistory = (code) => {
  historyCode.value = code
  showHistory.value = true
}

// 提交成功
const handleSubmit = (result) => {
  ElMessage.success('问卷提交成功')
  // 刷新历史记录
  questionnaireStore.loadHistory(currentCode.value)
}

// 跳过
const handleSkip = () => {
  // 已自动刷新待测列表
}

// 格式化日期
const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit'
  })
}

// 获取分数样式类
const getScoreClass = (code, score) => {
  if (code === 'PHQ9' || code === 'GAD7') {
    if (score <= 4) return 'score-normal'
    if (score <= 9) return 'score-mild'
    if (score <= 14) return 'score-moderate'
    return 'score-severe'
  }
  return 'score-normal'
}

// 获取结果类型
const getResultType = (level) => {
  const typeMap = {
    'none': 'success',
    'normal': 'success',
    'mild': 'warning',
    'moderate': 'danger',
    'moderately_severe': 'danger',
    'severe': 'danger'
  }
  return typeMap[level] || 'info'
}
</script>

<style scoped>
.questionnaire-page {
  padding: 32px;
  max-width: 1400px;
  margin: 0 auto;
  min-height: 100%;
}

.page-header {
  text-align: center;
  margin-bottom: 32px;
}

.page-title {
  font-size: 32px;
  font-weight: 600;
  color: #2c3e50;
  margin-bottom: 8px;
}

.page-subtitle {
  font-size: 16px;
  color: #666;
}

/* 分区头部 */
.section-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 18px;
  font-weight: 600;
  color: #2c3e50;
  margin: 0;
}

.section-title .el-icon {
  color: #667eea;
}

.section-desc {
  font-size: 14px;
  color: #999;
}

.due-badge :deep(.el-badge__content) {
  background-color: #f56c6c;
}

/* 待测问卷区 */
.due-section {
  margin-bottom: 32px;
  padding: 24px;
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(10px);
  border-radius: 20px;
  border: 1px solid rgba(255, 255, 255, 0.5);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05);
}

.due-cards {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 16px;
}

.due-card {
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(10px);
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.5);
  transition: all 0.3s ease;
}

.due-card.overdue {
  border-color: #f56c6c;
  background: rgba(255, 245, 245, 0.9);
}

.due-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
}

.due-card-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.due-icon {
  font-size: 36px;
  line-height: 1;
}

.due-info {
  flex: 1;
}

.due-name {
  font-size: 16px;
  font-weight: 600;
  color: #2c3e50;
  margin: 0 0 4px 0;
}

.due-time {
  margin: 0;
}

.due-card-actions {
  display: flex;
  gap: 12px;
}

.due-card-actions .el-button {
  flex: 1;
}

/* Tab 区域 */
.tab-section {
  margin-bottom: 40px;
}

.questionnaire-tabs {
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(10px);
  border-radius: 20px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.5);
}

.questionnaire-tabs :deep(.el-tabs__header) {
  margin-bottom: 0;
  background: rgba(255, 255, 255, 0.6);
  backdrop-filter: blur(10px);
  border-radius: 20px 20px 0 0;
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
}

.questionnaire-tabs :deep(.el-tabs__nav-wrap) {
  padding: 4px;
}

.questionnaire-tabs :deep(.el-tabs__item) {
  font-size: 15px;
  font-weight: 500;
  padding: 0 24px;
  height: 48px;
  line-height: 48px;
  border-radius: 12px;
  margin: 4px;
  transition: all 0.3s ease;
}

.questionnaire-tabs :deep(.el-tabs__item:hover) {
  background: rgba(255, 255, 255, 0.8);
  color: #667eea;
}

.questionnaire-tabs :deep(.el-tabs__item.is-active) {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}

.questionnaire-tabs :deep(.el-tabs__active-bar) {
  display: none;
}

.questionnaire-tabs :deep(.el-tabs__content) {
  padding: 24px;
  background: rgba(255, 255, 255, 0.5);
  border-radius: 0 0 20px 20px;
}

/* 加载状态 */
.loading-state {
  padding: 40px 20px;
}

/* 全部问卷 Tab */
.questionnaire-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(360px, 1fr));
  gap: 24px;
}

.questionnaire-card {
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(10px);
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.5);
  transition: all 0.3s ease;
  display: flex;
  flex-direction: column;
}

.questionnaire-card:hover {
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
}

.questionnaire-card.due {
  border-color: #f56c6c;
}

.questionnaire-card.completed {
  border-color: #67c23a;
}

.card-status-bar {
  height: 4px;
  background: #e0e0e0;
}

.card-status-bar.status-due {
  background: linear-gradient(90deg, #f56c6c 0%, #ff9d9d 100%);
}

.card-status-bar.status-completed {
  background: linear-gradient(90deg, #67c23a 0%, #95d475 100%);
}

.card-status-bar.status-pending {
  background: linear-gradient(90deg, #909399 0%, #c0c4cc 100%);
}

.card-content {
  padding: 24px;
  flex: 1;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.card-icon {
  font-size: 40px;
  line-height: 1;
}

.card-title-wrapper {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.card-title {
  font-size: 18px;
  font-weight: 600;
  color: #2c3e50;
  margin: 0;
}

.card-desc {
  font-size: 14px;
  color: #666;
  line-height: 1.6;
  margin-bottom: 16px;
}

.card-meta {
  display: flex;
  gap: 20px;
  margin-bottom: 16px;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: #999;
}

.meta-item .el-icon {
  font-size: 14px;
}

/* 最近结果 */
.last-result {
  margin-top: 16px;
}

.result-divider {
  height: 1px;
  background: #e8e8e8;
  margin-bottom: 16px;
}

.result-content {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.result-main {
  display: flex;
  align-items: baseline;
  gap: 8px;
}

.result-score {
  font-size: 36px;
  font-weight: 700;
}

.result-unit {
  font-size: 14px;
  color: #666;
  margin-right: 8px;
}

.result-level {
  font-size: 12px;
}

.result-time {
  font-size: 12px;
  color: #999;
}

.score-normal {
  color: #67c23a;
}

.score-mild {
  color: #e6a23c;
}

.score-moderate {
  color: #f56c6c;
}

.score-severe {
  color: #c45656;
}

/* 操作按钮 */
.card-actions {
  padding: 16px 24px;
  background: #f8f9fa;
  display: flex;
  gap: 12px;
}

.action-btn {
  flex: 1;
}

.action-btn .el-icon {
  margin-right: 4px;
}

/* 历史结果 Tab */
.history-section {
  padding: 16px 0;
}

.history-selector {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 1px solid #e8e8e8;
}

.selector-label {
  font-size: 14px;
  color: #666;
  font-weight: 500;
}

.history-content {
  min-height: 400px;
}

/* 响应式 */
@media (max-width: 768px) {
  .questionnaire-page {
    padding: 16px;
  }
  
  .questionnaire-grid {
    grid-template-columns: 1fr;
  }
  
  .due-cards {
    grid-template-columns: 1fr;
  }
  
  .history-selector {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
