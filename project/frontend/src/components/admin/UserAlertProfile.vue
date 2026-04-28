<template>
  <div class="user-alert-profile" v-loading="isLoading">
    <div v-if="profile" class="profile-content">
      <!-- 用户信息 -->
      <div class="user-header">
        <div class="user-avatar">
          {{ profile.user_info.username.charAt(0).toUpperCase() }}
        </div>
        <div class="user-meta">
          <h3>{{ profile.user_info.username }}</h3>
          <p>{{ profile.user_info.email }}</p>
          <p class="user-id">ID: {{ profile.user_info.id }}</p>
        </div>
        <div class="risk-badge" :class="getRiskClass(profile.risk_assessment)">
          {{ profile.risk_assessment }}
        </div>
      </div>

      <!-- 预警摘要 -->
      <div class="summary-section">
        <h4>预警摘要</h4>
        <div class="summary-grid">
          <div class="summary-item">
            <div class="summary-value">{{ profile.alert_summary.total }}</div>
            <div class="summary-label">总预警数</div>
          </div>
          <div class="summary-item warning">
            <div class="summary-value">{{ profile.alert_summary.unacknowledged }}</div>
            <div class="summary-label">未确认</div>
          </div>
          <div class="summary-item danger">
            <div class="summary-value">{{ profile.alert_summary.by_level?.danger || 0 }}</div>
            <div class="summary-label">高危预警</div>
          </div>
        </div>
      </div>

      <!-- 类型分布 -->
      <div class="type-section">
        <h4>预警类型分布</h4>
        <div class="type-bars">
          <div class="type-bar-item">
            <span class="bar-label">问卷</span>
            <div class="bar-track">
              <div 
                class="bar-fill questionnaire" 
                :style="{ width: getTypePercentage('questionnaire') + '%' }"
              ></div>
            </div>
            <span class="bar-value">{{ profile.alert_summary.by_type?.questionnaire || 0 }}</span>
          </div>
          <div class="type-bar-item">
            <span class="bar-label">情绪</span>
            <div class="bar-track">
              <div 
                class="bar-fill emotion" 
                :style="{ width: getTypePercentage('emotion') + '%' }"
              ></div>
            </div>
            <span class="bar-value">{{ profile.alert_summary.by_type?.emotion || 0 }}</span>
          </div>
          <div class="type-bar-item">
            <span class="bar-label">对话</span>
            <div class="bar-track">
              <div 
                class="bar-fill conversation" 
                :style="{ width: getTypePercentage('conversation') + '%' }"
              ></div>
            </div>
            <span class="bar-value">{{ profile.alert_summary.by_type?.conversation || 0 }}</span>
          </div>
        </div>
      </div>

      <!-- 情绪趋势 -->
      <div class="emotion-section" v-if="profile.emotion_trend?.length > 0">
        <h4>情绪趋势（最近30天）</h4>
        <div class="emotion-list">
          <div 
            v-for="(emotion, index) in profile.emotion_trend.slice(-10)" 
            :key="index"
            class="emotion-item"
          >
            <span class="emotion-date">{{ emotion.date }}</span>
            <span class="emotion-badge" :class="emotion.type">{{ emotion.emotion }}</span>
          </div>
        </div>
      </div>

      <!-- 问卷历史 -->
      <div class="questionnaire-section" v-if="profile.questionnaire_history?.length > 0">
        <h4>问卷历史</h4>
        <el-table :data="profile.questionnaire_history" size="small">
          <el-table-column label="日期" width="120">
            <template #default="{ row }">
              {{ formatDate(row.date) }}
            </template>
          </el-table-column>
          <el-table-column label="问卷类型" prop="template_code" width="120" />
          <el-table-column label="得分" prop="score" width="80" />
          <el-table-column label="等级" width="100">
            <template #default="{ row }">
              <el-tag :type="getResultLevelType(row.result_level)" size="small">
                {{ row.result_level }}
              </el-tag>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <!-- 最近预警 -->
      <div class="recent-alerts-section" v-if="profile.recent_alerts?.length > 0">
        <h4>最近预警</h4>
        <div class="recent-list">
          <div 
            v-for="alert in profile.recent_alerts" 
            :key="alert.id"
            class="recent-item"
          >
            <el-tag :type="getLevelType(alert.level)" size="small" effect="dark">
              {{ getLevelText(alert.level) }}
            </el-tag>
            <span class="recent-title">{{ alert.title }}</span>
            <span class="recent-date">{{ formatDate(alert.created_at) }}</span>
          </div>
        </div>
      </div>
    </div>

    <div v-else class="empty-state">
      <el-empty description="暂无用户画像数据" />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useAdminAlertStore } from '@/stores/adminAlert'

const props = defineProps({
  userId: {
    type: String,
    required: true
  }
})

const store = useAdminAlertStore()
const profile = ref(null)
const isLoading = ref(false)

const getRiskClass = (risk) => {
  const map = {
    '高风险': 'danger',
    '中高风险': 'warning',
    '中风险': 'info',
    '低风险': 'success'
  }
  return map[risk] || 'info'
}

const getTypePercentage = (type) => {
  if (!profile.value?.alert_summary?.by_type) return 0
  const total = profile.value.alert_summary.total || 1
  const count = profile.value.alert_summary.by_type[type] || 0
  return Math.round((count / total) * 100)
}

const getLevelType = (level) => {
  const map = { danger: 'danger', warning: 'warning', info: 'info' }
  return map[level] || 'info'
}

const getLevelText = (level) => {
  const map = { danger: '高危', warning: '中危', info: '低危' }
  return map[level] || level
}

const getResultLevelType = (level) => {
  const map = {
    'severe': 'danger',
    'moderate': 'warning',
    'mild': 'info',
    'none': 'success'
  }
  return map[level] || 'info'
}

const formatDate = (date) => {
  if (!date) return '-'
  return new Date(date).toLocaleDateString('zh-CN')
}

const loadProfile = async () => {
  isLoading.value = true
  try {
    profile.value = await store.getUserProfile(props.userId, 30)
  } finally {
    isLoading.value = false
  }
}

onMounted(() => {
  loadProfile()
})
</script>

<style scoped>
.user-alert-profile {
  padding: 20px 0;
}

.user-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 24px;
  padding-bottom: 20px;
  border-bottom: 1px solid #ebeef5;
}

.user-avatar {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  font-weight: 600;
}

.user-meta {
  flex: 1;
}

.user-meta h3 {
  font-size: 20px;
  font-weight: 600;
  color: #303133;
  margin: 0 0 4px 0;
}

.user-meta p {
  font-size: 14px;
  color: #606266;
  margin: 0;
}

.user-id {
  font-size: 12px !important;
  color: #909399 !important;
  margin-top: 4px;
}

.risk-badge {
  padding: 8px 16px;
  border-radius: 20px;
  font-size: 14px;
  font-weight: 600;
}

.risk-badge.danger {
  background: #fef0f0;
  color: #f56c6c;
}

.risk-badge.warning {
  background: #fdf6ec;
  color: #e6a23c;
}

.risk-badge.info {
  background: #f4f4f5;
  color: #909399;
}

.risk-badge.success {
  background: #f0f9eb;
  color: #67c23a;
}

.summary-section,
.type-section,
.emotion-section,
.questionnaire-section,
.recent-alerts-section {
  margin-bottom: 24px;
}

.summary-section h4,
.type-section h4,
.emotion-section h4,
.questionnaire-section h4,
.recent-alerts-section h4 {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  margin: 0 0 16px 0;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}

.summary-item {
  text-align: center;
  padding: 16px;
  background: #f5f7fa;
  border-radius: 8px;
}

.summary-item.warning .summary-value {
  color: #e6a23c;
}

.summary-item.danger .summary-value {
  color: #f56c6c;
}

.summary-value {
  font-size: 28px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 4px;
}

.summary-label {
  font-size: 14px;
  color: #606266;
}

.type-bars {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.type-bar-item {
  display: flex;
  align-items: center;
  gap: 12px;
}

.bar-label {
  width: 60px;
  font-size: 14px;
  color: #606266;
}

.bar-track {
  flex: 1;
  height: 20px;
  background: #ebeef5;
  border-radius: 10px;
  overflow: hidden;
}

.bar-fill {
  height: 100%;
  border-radius: 10px;
  transition: width 0.3s ease;
}

.bar-fill.questionnaire {
  background: #409eff;
}

.bar-fill.emotion {
  background: #67c23a;
}

.bar-fill.conversation {
  background: #e6a23c;
}

.bar-value {
  width: 40px;
  text-align: right;
  font-size: 14px;
  color: #606266;
}

.emotion-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.emotion-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: #f5f7fa;
  border-radius: 8px;
}

.emotion-date {
  font-size: 12px;
  color: #909399;
}

.emotion-badge {
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
}

.emotion-badge.negative {
  background: #fef0f0;
  color: #f56c6c;
}

.emotion-badge.positive {
  background: #f0f9eb;
  color: #67c23a;
}

.recent-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.recent-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: #f5f7fa;
  border-radius: 8px;
}

.recent-title {
  flex: 1;
  font-size: 14px;
  color: #303133;
}

.recent-date {
  font-size: 12px;
  color: #909399;
}

.empty-state {
  padding: 40px 0;
}

@media (max-width: 768px) {
  .summary-grid {
    grid-template-columns: 1fr;
  }
  
  .user-header {
    flex-direction: column;
    text-align: center;
  }
  
  .recent-item {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
