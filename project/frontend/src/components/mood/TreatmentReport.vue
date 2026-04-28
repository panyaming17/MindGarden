<template>
  <div class="treatment-report">
    <!-- 总体建议 -->
    <div v-if="data?.summary" class="summary-section">
      <div class="summary-card">
        <div class="summary-icon">💡</div>
        <div class="summary-content">
          <h3 class="summary-title">总体建议</h3>
          <p class="summary-text">{{ data.summary }}</p>
        </div>
      </div>
    </div>

    <!-- 融合策略 -->
    <div v-if="data?.fusion_strategies?.length" class="strategies-section">
      <h3 class="section-title">🔄 融合策略</h3>
      <div class="strategies-list">
        <div 
          v-for="(strategy, index) in data.fusion_strategies" 
          :key="index"
          class="strategy-card"
        >
          <div class="strategy-header">
            <span class="strategy-time">{{ formatTime(strategy.time) }}</span>
            <span class="strategy-mode">{{ formatFusionMode(strategy.fusion_mode) }}</span>
          </div>
          <div class="strategy-content">{{ strategy.key_points }}</div>
        </div>
      </div>
    </div>

    <!-- CBT作业 -->
    <div v-if="data?.cbt_homework?.length" class="homework-section">
      <h3 class="section-title">📝 CBT作业</h3>
      <div class="homework-list">
        <div 
          v-for="(homework, index) in data.cbt_homework" 
          :key="index"
          class="homework-card"
          :class="{ 'completed': isHomeworkCompleted('cbt', index) }"
        >
          <div class="homework-header">
            <div class="homework-checkbox" @click="toggleHomework('cbt', index)">
              <span v-if="isHomeworkCompleted('cbt', index)" class="check-icon">✓</span>
            </div>
            <h4 class="homework-name">{{ homework.title || homework.name }}</h4>
            <div class="homework-actions">
              <el-tooltip content="收藏" placement="top">
                <el-icon 
                  class="action-icon"
                  :class="{ 'active': isFavorited('cbt', index) }"
                  @click="toggleFavorite('cbt', index, homework)"
                >
                  <Star />
                </el-icon>
              </el-tooltip>
              <el-tooltip content="设置提醒" placement="top">
                <el-icon 
                  class="action-icon"
                  @click="openReminderModal('cbt', index, homework)"
                >
                  <Clock />
                </el-icon>
              </el-tooltip>
            </div>
          </div>
          <p class="homework-description">{{ homework.description }}</p>
          <div class="homework-meta">
            <span class="meta-item">
              <el-icon><Timer /></el-icon>
              {{ homework.frequency }}
            </span>
            <span v-if="homework.duration" class="meta-item">
              <el-icon><Calendar /></el-icon>
              {{ homework.duration }}
            </span>
          </div>
        </div>
      </div>
    </div>

    <!-- 中医调理 -->
    <div v-if="data?.tcm_practices?.length" class="practices-section">
      <h3 class="section-title">🌱 中医调理</h3>
      <div class="practices-list">
        <div 
          v-for="(practice, index) in data.tcm_practices" 
          :key="index"
          class="practice-card"
          :class="{ 'completed': isHomeworkCompleted('tcm', index) }"
        >
          <div class="practice-header">
            <div class="practice-checkbox" @click="toggleHomework('tcm', index)">
              <span v-if="isHomeworkCompleted('tcm', index)" class="check-icon">✓</span>
            </div>
            <!-- 兼容字符串和对象两种格式 -->
            <h4 class="practice-name">{{ typeof practice === 'string' ? practice : (practice.name || practice) }}</h4>
          </div>
          <!-- 如果是对象格式，显示描述和频率 -->
          <template v-if="typeof practice === 'object'">
            <p class="practice-description">{{ practice.description }}</p>
            <div v-if="practice.purpose" class="practice-purpose">
              <span class="purpose-label">目的：</span>
              <span class="purpose-text">{{ practice.purpose }}</span>
            </div>
            <div v-if="practice.frequency" class="practice-meta">
              <span class="meta-item">
                <el-icon><Timer /></el-icon>
                {{ practice.frequency }}
              </span>
            </div>
          </template>
        </div>
      </div>
    </div>

    <!-- 生活建议 -->
    <div v-if="data?.recommendations?.length" class="recommendations-section">
      <h3 class="section-title">💡 生活建议</h3>
      <div class="recommendations-list">
        <div 
          v-for="(recommendation, index) in data.recommendations" 
          :key="index"
          class="recommendation-item"
        >
          <span class="recommendation-number">{{ index + 1 }}</span>
          <span class="recommendation-text">{{ recommendation }}</span>
        </div>
      </div>
    </div>

    <!-- 下一步 -->
    <div v-if="data?.next_steps" class="next-steps-section">
      <h3 class="section-title">🎯 下一步</h3>
      <div class="next-steps-card">
        <div v-if="data.next_steps.suggestion" class="next-step-item">
          <span class="step-label">建议：</span>
          <span class="step-content">{{ data.next_steps.suggestion }}</span>
        </div>
        <div v-if="data.next_steps.follow_up" class="next-step-item">
          <span class="step-label">跟进：</span>
          <span class="step-content">{{ data.next_steps.follow_up }}</span>
        </div>
      </div>
    </div>

    <!-- 导出按钮 -->
    <div class="export-section">
      <h3 class="section-title">📤 导出报告</h3>
      <div class="export-buttons">
        <el-button type="success" @click="exportImage" :loading="exportingImage">
          <el-icon><Picture /></el-icon>
          导出图片
        </el-button>
      </div>
    </div>

    <!-- 提醒设置弹窗 -->
    <el-dialog
      v-model="reminderModal.visible"
      title="设置提醒"
      width="400px"
    >
      <div class="reminder-form">
        <p class="reminder-item">{{ reminderModal.item?.name }}</p>
        <el-form :model="reminderModal.form" label-width="80px">
          <el-form-item label="提醒时间">
            <el-time-picker
              v-model="reminderModal.form.time"
              format="HH:mm"
              placeholder="选择时间"
            />
          </el-form-item>
          <el-form-item label="重复">
            <el-select v-model="reminderModal.form.repeat" placeholder="选择重复方式">
              <el-option label="每天" value="daily" />
              <el-option label="工作日" value="weekday" />
              <el-option label="周末" value="weekend" />
              <el-option label="不重复" value="none" />
            </el-select>
          </el-form-item>
        </el-form>
      </div>
      <template #footer>
        <el-button @click="reminderModal.visible = false">取消</el-button>
        <el-button type="primary" @click="saveReminder">确定</el-button>
      </template>
    </el-dialog>

    <!-- 无数据提示 -->
    <div v-if="!hasData" class="no-data">
      <div class="no-data-icon">💊</div>
      <p>暂无调理建议</p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { Star, Clock, Timer, Calendar, Picture } from '@element-plus/icons-vue'
import html2canvas from 'html2canvas'

const props = defineProps({
  data: {
    type: Object,
    default: () => ({})
  },
  sessionId: {
    type: String,
    default: ''
  }
})

// 响应式数据
const exportingImage = ref(false)
const reminderModal = ref({
  visible: false,
  type: '',
  index: 0,
  item: null,
  form: {
    time: null,
    repeat: 'daily'
  }
})

// 本地存储键
const STORAGE_KEY = `treatment_${props.sessionId}`

// 从本地存储加载状态
const loadStorageData = () => {
  const stored = localStorage.getItem(STORAGE_KEY)
  if (stored) {
    return JSON.parse(stored)
  }
  return {
    completed: { cbt: {}, tcm: {} },
    favorites: { cbt: {}, tcm: {} },
    reminders: []
  }
}

const storageData = ref(loadStorageData())

// 保存到本地存储
const saveStorageData = () => {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(storageData.value))
}

// 是否有数据
const hasData = computed(() => {
  return props.data && (
    props.data.summary ||
    props.data.fusion_strategies?.length ||
    props.data.cbt_homework?.length ||
    props.data.tcm_practices?.length ||
    props.data.recommendations?.length ||
    props.data.next_steps
  )
})

// 检查作业是否完成
const isHomeworkCompleted = (type, index) => {
  return storageData.value.completed[type][index] || false
}

// 切换作业完成状态
const toggleHomework = (type, index) => {
  storageData.value.completed[type][index] = !isHomeworkCompleted(type, index)
  saveStorageData()
  
  if (isHomeworkCompleted(type, index)) {
    ElMessage.success('已完成！继续保持！')
  }
}

// 检查是否已收藏
const isFavorited = (type, index) => {
  return storageData.value.favorites[type][index] || false
}

// 切换收藏状态
const toggleFavorite = (type, index, item) => {
  storageData.value.favorites[type][index] = !isFavorited(type, index)
  saveStorageData()
  
  if (isFavorited(type, index)) {
    ElMessage.success('已添加到收藏')
  } else {
    ElMessage.info('已取消收藏')
  }
}

// 打开提醒弹窗
const openReminderModal = (type, index, item) => {
  reminderModal.value = {
    visible: true,
    type,
    index,
    item,
    form: {
      time: null,
      repeat: 'daily'
    }
  }
}

// 保存提醒
const saveReminder = () => {
  const { type, index, item, form } = reminderModal.value
  
  if (!form.time) {
    ElMessage.warning('请选择提醒时间')
    return
  }
  
  const reminder = {
    id: Date.now(),
    type,
    index,
    name: item.name,
    time: form.time,
    repeat: form.repeat
  }
  
  storageData.value.reminders.push(reminder)
  saveStorageData()
  
  reminderModal.value.visible = false
  ElMessage.success('提醒设置成功')
  
  // TODO: 发送到后端
  // sendReminderToServer(reminder)
}

// 格式化时间
const formatTime = (timeString) => {
  if (!timeString) return '-'
  const date = new Date(timeString)
  return date.toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// 格式化融合模式
const formatFusionMode = (mode) => {
  const modeMap = {
    'cbt_tcm_integrated': 'CBT+中医融合',
    'cbt_first': 'CBT优先',
    'tcm_first': '中医优先',
    'cbt_only': '仅CBT',
    'tcm_only': '仅中医'
  }
  return modeMap[mode] || mode
}

// 导出图片
const exportImage = async () => {
  exportingImage.value = true
  
  try {
    const element = document.querySelector('.treatment-report')
    if (!element) {
      ElMessage.error('无法找到报告内容')
      return
    }

    // 获取报告元素的实际尺寸
    const reportWidth = element.scrollWidth
    const reportHeight = element.scrollHeight

    // 使用 html2canvas 截图
    const canvas = await html2canvas(element, {
      scale: 2,  // 提高分辨率
      useCORS: true,
      backgroundColor: '#ffffff',
      logging: false,
      windowWidth: reportWidth,
      windowHeight: reportHeight,
      imageTimeout: 0
    })

    // 转换为图片并下载
    const imgData = canvas.toDataURL('image/png', 1.0)
    const link = document.createElement('a')
    link.download = `调理报告_${new Date().toLocaleDateString()}.png`
    link.href = imgData
    link.click()
    
    ElMessage.success('图片导出成功！')
  } catch (error) {
    console.error('导出图片失败:', error)
    ElMessage.error('导出图片失败，请重试')
  } finally {
    exportingImage.value = false
  }
}
</script>

<style scoped>
.treatment-report {
  padding: 8px;
}

/* 总体建议 */
.summary-section {
  margin-bottom: 32px;
}

.summary-card {
  display: flex;
  align-items: flex-start;
  gap: 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 20px;
  padding: 24px;
  color: white;
  box-shadow: 0 8px 24px rgba(102, 126, 234, 0.3);
}

.summary-icon {
  font-size: 40px;
  flex-shrink: 0;
}

.summary-content {
  flex: 1;
}

.summary-title {
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 8px;
}

.summary-text {
  font-size: 15px;
  line-height: 1.7;
  opacity: 0.95;
  margin: 0;
}

/* 区块标题 */
.section-title {
  font-size: 18px;
  font-weight: 600;
  color: #2c3e50;
  margin-bottom: 20px;
  padding-bottom: 12px;
  border-bottom: 2px solid #e8e8e8;
  display: flex;
  align-items: center;
  gap: 8px;
}

/* 融合策略 */
.strategies-section {
  margin-bottom: 32px;
}

.strategies-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.strategy-card {
  background: rgba(255, 255, 255, 0.9);
  border-radius: 16px;
  padding: 20px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
  border: 1px solid rgba(0, 0, 0, 0.05);
  border-left: 4px solid #667eea;
}

.strategy-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.strategy-time {
  font-size: 13px;
  color: #95a5a6;
}

.strategy-mode {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}

.strategy-content {
  font-size: 14px;
  color: #555;
  line-height: 1.6;
}

/* CBT作业 */
.homework-section {
  margin-bottom: 32px;
}

.homework-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.homework-card {
  background: rgba(255, 255, 255, 0.9);
  border-radius: 16px;
  padding: 20px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
  border: 1px solid rgba(0, 0, 0, 0.05);
  transition: all 0.3s ease;
}

.homework-card.completed {
  background: linear-gradient(135deg, #E8F5E9 0%, #C8E6C9 100%);
  border-color: #81C784;
}

.homework-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.homework-checkbox {
  width: 24px;
  height: 24px;
  border: 2px solid #667eea;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s ease;
  flex-shrink: 0;
}

.homework-card.completed .homework-checkbox {
  background: #81C784;
  border-color: #81C784;
}

.check-icon {
  color: white;
  font-size: 14px;
  font-weight: bold;
}

.homework-name {
  flex: 1;
  font-size: 16px;
  font-weight: 600;
  color: #2c3e50;
  margin: 0;
}

.homework-card.completed .homework-name {
  text-decoration: line-through;
  color: #4CAF50;
}

.homework-actions {
  display: flex;
  gap: 8px;
}

.action-icon {
  font-size: 20px;
  color: #95a5a6;
  cursor: pointer;
  transition: all 0.2s ease;
  padding: 4px;
  border-radius: 6px;
}

.action-icon:hover {
  color: #667eea;
  background: rgba(102, 126, 234, 0.1);
}

.action-icon.active {
  color: #FFB74D;
}

.homework-description {
  font-size: 14px;
  color: #555;
  line-height: 1.6;
  margin-bottom: 12px;
  padding-left: 36px;
}

.homework-meta {
  display: flex;
  gap: 16px;
  padding-left: 36px;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: #7f8c8d;
}

/* 中医调理 */
.practices-section {
  margin-bottom: 32px;
}

.practices-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.practice-card {
  background: rgba(255, 255, 255, 0.9);
  border-radius: 16px;
  padding: 20px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
  border: 1px solid rgba(0, 0, 0, 0.05);
  transition: all 0.3s ease;
  border-left: 4px solid #81C784;
}

.practice-card.completed {
  background: linear-gradient(135deg, #E8F5E9 0%, #C8E6C9 100%);
}

.practice-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.practice-checkbox {
  width: 24px;
  height: 24px;
  border: 2px solid #81C784;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s ease;
  flex-shrink: 0;
}

.practice-card.completed .practice-checkbox {
  background: #81C784;
  border-color: #81C784;
}

.practice-name {
  flex: 1;
  font-size: 16px;
  font-weight: 600;
  color: #2c3e50;
  margin: 0;
}

.practice-card.completed .practice-name {
  text-decoration: line-through;
  color: #4CAF50;
}

.practice-actions {
  display: flex;
  gap: 8px;
}

.practice-description {
  font-size: 14px;
  color: #555;
  line-height: 1.6;
  margin-bottom: 8px;
  padding-left: 36px;
}

.practice-purpose {
  padding-left: 36px;
  margin-bottom: 8px;
}

.purpose-label {
  font-size: 13px;
  color: #7f8c8d;
}

.purpose-text {
  font-size: 13px;
  color: #4CAF50;
  font-weight: 500;
}

.practice-meta {
  display: flex;
  gap: 16px;
  padding-left: 36px;
}

/* 生活建议 */
.recommendations-section {
  margin-bottom: 32px;
}

.recommendations-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.recommendation-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 16px 20px;
  background: rgba(255, 255, 255, 0.9);
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  border: 1px solid rgba(0, 0, 0, 0.05);
}

.recommendation-number {
  width: 28px;
  height: 28px;
  background: linear-gradient(135deg, #FFB74D 0%, #FF9800 100%);
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  font-weight: 600;
  flex-shrink: 0;
}

.recommendation-text {
  flex: 1;
  font-size: 14px;
  color: #555;
  line-height: 1.6;
  padding-top: 4px;
}

/* 下一步 */
.next-steps-section {
  margin-bottom: 32px;
}

.next-steps-card {
  background: linear-gradient(135deg, #E3F2FD 0%, #BBDEFB 100%);
  border-radius: 16px;
  padding: 20px;
  border: 1px solid rgba(33, 150, 243, 0.2);
}

.next-step-item {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
}

.next-step-item:last-child {
  margin-bottom: 0;
}

.step-label {
  font-size: 14px;
  color: #1976D2;
  font-weight: 600;
  flex-shrink: 0;
}

.step-content {
  font-size: 14px;
  color: #555;
  line-height: 1.6;
}

/* 导出 */
.export-section {
  margin-bottom: 24px;
}

.export-buttons {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

/* 提醒弹窗 */
.reminder-form {
  padding: 20px 0;
}

.reminder-item {
  font-size: 16px;
  font-weight: 600;
  color: #667eea;
  margin-bottom: 20px;
  padding: 12px 16px;
  background: #f5f5f5;
  border-radius: 8px;
}

/* 无数据 */
.no-data {
  text-align: center;
  padding: 60px 20px;
  color: #95a5a6;
}

.no-data-icon {
  font-size: 48px;
  margin-bottom: 16px;
  opacity: 0.5;
}

/* 响应式 */
@media (max-width: 768px) {
  .summary-card {
    flex-direction: column;
    text-align: center;
  }

  .homework-meta,
  .practice-meta {
    flex-direction: column;
    gap: 8px;
  }

  .export-buttons {
    flex-direction: column;
  }

  .export-buttons .el-button {
    width: 100%;
  }
}
</style>
