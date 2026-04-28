<template>
  <div class="questionnaire-statistics">
    <div v-for="stat in store.statistics" :key="stat.template_code" class="stat-card">
      <div class="stat-header">
        <h3>{{ stat.template_name }}</h3>
        <el-tag type="info">{{ stat.total_records }}条记录</el-tag>
      </div>
      <div class="stat-body">
        <div class="stat-row">
          <div class="stat-item">
            <div class="stat-value">{{ stat.today_records }}</div>
            <div class="stat-label">今日</div>
          </div>
          <div class="stat-item">
            <div class="stat-value">{{ stat.week_records }}</div>
            <div class="stat-label">本周</div>
          </div>
          <div class="stat-item">
            <div class="stat-value">{{ stat.avg_score }}</div>
            <div class="stat-label">平均分</div>
          </div>
        </div>
        <div class="distribution">
          <h4>结果分布</h4>
          <div class="dist-bars">
            <div v-for="(count, level) in stat.result_distribution" :key="level" class="dist-item">
              <span class="dist-label">{{ getLevelText(level) }}</span>
              <div class="dist-bar">
                <div class="dist-fill" :style="{ width: getPercentage(count, stat.total_records) + '%' }"></div>
              </div>
              <span class="dist-count">{{ count }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { useAdminQuestionnaireStore } from '@/stores/adminQuestionnaire'

const store = useAdminQuestionnaireStore()

const getLevelText = (level) => {
  const map = { none: '正常', mild: '轻度', moderate: '中度', moderately_severe: '中重度', severe: '重度', unknown: '未知' }
  return map[level] || level
}

const getPercentage = (count, total) => {
  return total > 0 ? Math.round((count / total) * 100) : 0
}
</script>

<style scoped>
.questionnaire-statistics { padding: 20px 0; }
.stat-card {
  background: white;
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 20px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
}
.stat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 16px;
  border-bottom: 1px solid #ebeef5;
}
.stat-header h3 { margin: 0; font-size: 18px; }
.stat-row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
  margin-bottom: 20px;
}
.stat-item {
  text-align: center;
  padding: 16px;
  background: #f5f7fa;
  border-radius: 8px;
}
.stat-value {
  font-size: 24px;
  font-weight: 600;
  color: #303133;
}
.stat-label {
  font-size: 14px;
  color: #909399;
  margin-top: 4px;
}
.distribution h4 {
  font-size: 14px;
  color: #606266;
  margin: 0 0 12px 0;
}
.dist-bars {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.dist-item {
  display: flex;
  align-items: center;
  gap: 12px;
}
.dist-label {
  width: 80px;
  font-size: 14px;
  color: #606266;
}
.dist-bar {
  flex: 1;
  height: 20px;
  background: #ebeef5;
  border-radius: 10px;
  overflow: hidden;
}
.dist-fill {
  height: 100%;
  background: #409eff;
  border-radius: 10px;
  transition: width 0.3s ease;
}
.dist-count {
  width: 40px;
  text-align: right;
  font-size: 14px;
  color: #606266;
}
</style>
