<template>
  <div class="questionnaire-management">
    <!-- 页面标题 -->
    <div class="page-header">
      <div class="header-title">
        <span class="title-icon">📝</span>
        <h2>问卷管理</h2>
      </div>
      <p class="header-subtitle">管理问卷模板、查看用户答题记录、配置评分规则</p>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-cards">
      <div class="stat-card">
        <div class="stat-icon">📋</div>
        <div class="stat-content">
          <div class="stat-value">{{ totalTemplates }}</div>
          <div class="stat-label">问卷模板</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon">✅</div>
        <div class="stat-content">
          <div class="stat-value">{{ activeTemplatesCount }}</div>
          <div class="stat-label">已启用</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon">📊</div>
        <div class="stat-content">
          <div class="stat-value">{{ totalRecords }}</div>
          <div class="stat-label">答题记录</div>
        </div>
      </div>
      <div class="stat-card warning">
        <div class="stat-icon">🚨</div>
        <div class="stat-content">
          <div class="stat-value">{{ alertRecordsCount }}</div>
          <div class="stat-label">触发预警</div>
        </div>
      </div>
    </div>

    <!-- 标签页 -->
    <el-tabs v-model="activeTab" class="questionnaire-tabs">
      <!-- 答题记录 -->
      <el-tab-pane label="答题记录" name="records">
        <QuestionnaireRecords />
      </el-tab-pane>

      <!-- 问卷模板 -->
      <el-tab-pane label="问卷模板" name="templates">
        <QuestionnaireTemplates />
      </el-tab-pane>

      <!-- 统计分析 -->
      <el-tab-pane label="统计分析" name="statistics">
        <QuestionnaireStatistics />
      </el-tab-pane>

      <!-- 评分规则 -->
      <el-tab-pane label="评分规则" name="rules">
        <ScoringRules />
      </el-tab-pane>

      <!-- 操作日志 -->
      <el-tab-pane label="操作日志" name="logs">
        <QuestionnaireLogs />
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useAdminQuestionnaireStore } from '@/stores/adminQuestionnaire'
import QuestionnaireRecords from './QuestionnaireRecords.vue'
import QuestionnaireTemplates from './QuestionnaireTemplates.vue'
import QuestionnaireStatistics from './QuestionnaireStatistics.vue'
import ScoringRules from './ScoringRules.vue'
import QuestionnaireLogs from './QuestionnaireLogs.vue'

const store = useAdminQuestionnaireStore()
const activeTab = ref('records')

// 统计数据
const totalTemplates = computed(() => store.templates.length)
const activeTemplatesCount = computed(() => store.activeTemplates.length)
const totalRecords = computed(() => store.totalRecords)
const alertRecordsCount = computed(() => 
  store.records.filter(r => r.has_alert).length
)

// 初始化数据
onMounted(async () => {
  await store.getTemplates()
  await store.getRecords()
  await store.getStatistics()
})
</script>

<style scoped>
.questionnaire-management {
  padding: 20px;
}

.page-header {
  margin-bottom: 24px;
}

.header-title {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}

.title-icon {
  font-size: 28px;
}

.header-title h2 {
  font-size: 24px;
  font-weight: 600;
  color: #303133;
  margin: 0;
}

.header-subtitle {
  font-size: 14px;
  color: #909399;
  margin: 0;
  padding-left: 40px;
}

.stats-cards {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
  margin-bottom: 24px;
}

.stat-card {
  display: flex;
  align-items: center;
  padding: 20px;
  border-radius: 12px;
  background: white;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
}

.stat-card.warning {
  border-left: 4px solid #f56c6c;
}

.stat-icon {
  font-size: 32px;
  margin-right: 16px;
}

.stat-content {
  flex: 1;
}

.stat-value {
  font-size: 28px;
  font-weight: 600;
  color: #303133;
  line-height: 1;
}

.stat-label {
  font-size: 14px;
  color: #909399;
  margin-top: 4px;
}

.questionnaire-tabs {
  background: white;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
}

@media (max-width: 1200px) {
  .stats-cards {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .stats-cards {
    grid-template-columns: 1fr;
  }
}
</style>
