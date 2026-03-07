<template>
  <div class="steps-container">
    <!-- 顶部居中的步骤条 -->
    <div class="top-steps">
        <el-steps style="max-width: 600px" :active="activeStep" finish-status="success" simple>
            <el-step title="记录" />
            <el-step title="分析" />
            <el-step title="建议" />
        </el-steps>
    </div>
  
    <div class="steps-content">
      <div class="left-steps-section">
        <!-- 左侧居中的步骤条 -->
        <div class="left-steps">
          <div class="step-item" v-for="(step, index) in steps" :key="index">
            <div class="step-header">
              <div class="step-icon" :class="{ 'completed': index < activeStep, 'current': index === activeStep }">
                <el-icon v-if="index < activeStep"><Check /></el-icon>
                <span v-else>{{ index + 1 }}</span>
              </div>
              <div class="step-title">
                {{ step.title }}
                <span v-if="index < activeStep" class="step-status">{{ step.completedText }}</span>
                <span v-else-if="index === activeStep" class="step-status current">{{ step.currentText }}</span>
              </div>
            </div>
            <div class="step-description">{{ step.description }}</div>
            <el-button 
              v-if="index < activeStep" 
              type="primary" 
              size="small" 
              class="view-button"
              @click="handleViewReport(index)"
            >
              查看
            </el-button>
          </div>
        </div>
      </div>
      
      <div class="main-content-section">
        <!-- 默认插槽：用于渲染聊天内容 -->
        <slot></slot>
        
        <!-- 报告查看区域 -->
        <div v-if="showReport" class="report-viewer">
          <h3>{{ currentReportTitle }}</h3>
          <div class="report-content">
            <!-- 这里将显示相应的报告内容 -->
            <p>报告内容将在此显示...</p>
          </div>
          <el-button type="primary" @click="closeReport">关闭</el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { Edit, Picture, UploadFilled, Check } from '@element-plus/icons-vue'

const props = defineProps({
  activeStep: {
    type: Number,
    default: 0
  }
})

// 步骤数据
const steps = [
  {
    title: '记录报告',
    completedText: '已生成',
    currentText: '生成中',
    description: '您可以点击查看记录师记录的报告。'
  },
  {
    title: '分析报告',
    completedText: '已生成',
    currentText: '生成中',
    description: '您可以点击查看分析师的分析报告。'
  },
  {
    title: '调理建议',
    completedText: '已生成',
    currentText: '生成中',
    description: '您可以点击查看调理师的调理建议。'
  }
]

// 报告查看状态
const showReport = ref(false)
const currentReportIndex = ref(-1)

// 当前报告标题
const currentReportTitle = computed(() => {
  if (currentReportIndex.value >= 0 && currentReportIndex.value < steps.length) {
    return steps[currentReportIndex.value].title
  }
  return ''
})

// 处理查看报告
const handleViewReport = (index) => {
  currentReportIndex.value = index
  showReport.value = true
}

// 关闭报告
const closeReport = () => {
  showReport.value = false
  currentReportIndex.value = -1
}
</script>

<style scoped>
.steps-container {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  padding: 5px 0;
  position: relative;
  z-index: 1000;
  background: transparent !important;
}

/* 主内容区域 */
.main-content-section {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
}

/* 顶部居中的步骤条 */
.top-steps {
  display: flex;
  justify-content: center;
  width: 100%;
  margin-bottom: 40px;
}

/* 确保步骤条有足够的宽度 */
.top-steps :deep(.el-steps) {
  min-width: 400px;
  width: 100%;
  max-width: 600px;
}

/* 增加步骤之间的间距 */
.top-steps :deep(.el-step) {
  flex: 1;
  text-align: center;
}

/* 增加步骤主要内容区域的间距 */
.top-steps :deep(.el-step__main) {
  margin: 0 25px;
  min-width: 100px;
}

/* 确保步骤标题不被压缩 */
.top-steps :deep(.el-step__title) {
  white-space: nowrap;
  overflow: visible;
  padding: 0 15px;
  font-size: 16px;
}

/* 主要内容区域 - 两列布局 */
.steps-content {
  display: flex;
  flex: 1;
  min-height: 0;
  padding: 0 20px;
  gap: 120px;
}

/* 左侧步骤条区域 */
.left-steps-section {
  flex: 0 0 200px;
  padding-top: 150px;
}

/* 左侧步骤条 */
.left-steps {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 50px;
}

/* 步骤项 */
.step-item {
  position: relative;
  padding-left: 40px;
}

/* 步骤项之间的连线 */
.step-item:not(:last-child)::after {
  content: '';
  position: absolute;
  left: 19px;
  top: 30px;
  bottom: -50px;
  width: 2px;
  background-color: #e0e0e0;
}

/* 步骤头部 */
.step-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}

/* 步骤图标 */
.step-icon {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background-color: #f0f0f0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  color: #999;
  position: absolute;
  left: 0;
  top: 0;
  z-index: 1;
}

/* 已完成的步骤图标 */
.step-icon.completed {
  background-color: #43e97b;
  color: white;
}

/* 当前步骤图标 */
.step-icon.current {
  background-color: #667eea;
  color: white;
}

/* 步骤标题 */
.step-title {
  font-size: 16px;
  font-weight: bold;
  color: #333;
  display: flex;
  align-items: center;
  gap: 8px;
}

/* 步骤状态 */
.step-status {
  font-size: 14px;
  font-weight: normal;
  color: #666;
}

/* 当前步骤状态 */
.step-status.current {
  color: #667eea;
}

/* 步骤描述 */
.step-description {
  font-size: 14px;
  color: #666;
  line-height: 1.4;
  margin-bottom: 12px;
}

/* 查看按钮 */
.view-button {
  font-size: 14px;
  padding: 4px 12px;
}

/* 右侧主内容区域（聊天内容） */
.main-content-section {
  flex: 1;
  max-width: 1000px;
  display: flex;
  justify-content: center;
}

/* 报告查看区域 */
.report-viewer {
  margin-top: 20px;
  padding: 20px;
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  width: 100%;
  max-width: 800px;
}

.report-content {
  margin: 20px 0;
  padding: 20px;
  background-color: #f9f9f9;
  border-radius: 4px;
  min-height: 200px;
}

/* 透明背景样式 */
.top-steps :deep(.el-steps),
.left-steps :deep(.el-steps) {
  background-color: transparent !important;
  background: none !important;
}

.top-steps :deep(.el-step),
.left-steps :deep(.el-step) {
  background-color: transparent !important;
}

.top-steps :deep(.el-step__head),
.left-steps :deep(.el-step__head) {
  background-color: transparent !important;
}

.top-steps :deep(.el-step__main),
.left-steps :deep(.el-step__main) {
  background-color: transparent !important;
}

.top-steps :deep(.el-step__title),
.left-steps :deep(.el-step__title) {
  background-color: transparent !important;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .steps-content {
    flex-direction: column;
    gap: 20px;
  }
  
  .left-steps-section {
    flex: none;
    order: 2;
    padding-top: 20px;
  }
  
  .main-content-section {
    order: 1;
  }
  
  .left-steps {
    flex-direction: row;
    flex-wrap: wrap;
    gap: 20px;
  }
  
  .step-item {
    flex: 1;
    min-width: 200px;
    padding-left: 40px;
  }
  
  .step-item:not(:last-child)::after {
    display: none;
  }
}
</style>