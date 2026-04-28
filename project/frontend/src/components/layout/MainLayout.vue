<template>
  <div class="main-layout">
    <!-- 背景组件 -->
    <BackGround />
    
    <Sidebar 
      :style="{ width: effectiveWidth + 'px' }"
      @create-new="handleCreateNew" 
      @load-conversation="handleLoadConversation"
      @select-function="handleSelectFunction"
      @width-change="handleWidthChange"
      @collapse-change="handleCollapseChange"
    />
    <div 
      class="main-content-wrapper"
      :style="{ marginLeft: effectiveWidth + 'px' }"
    >
      <component 
        v-if="currentComponent"
        :is="currentComponent"
        :conversationData="selectedConversation"
        :activeFunction="activeFunction"
        @navigate-to-reports="handleNavigateToReports"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import Sidebar from '../base/Sidebar.vue'
// import BackGround from '../base/BackGround.vue'
import BackGround from '../base/BackGround.vue'
import ChatApp from '../chat/ChatApp.vue'
import EmotionRecordPage from '../emotion/EmotionRecordPage.vue'
import AlertPage from '../alert/AlertPage.vue'
import QuestionnairePage from '../Questionnaire/QuestionnairePage.vue'
import MoodReport from '../mood/MoodReport.vue'

// 定义组件名称
defineOptions({
  name: 'MainLayout'
})

const route = useRoute()

// 响应式数据
const selectedConversation = ref(null)

// 侧边栏宽度
const sidebarWidth = ref(280)
const collapsedWidth = ref(64)
const isCollapsed = ref(false)

// 计算实际宽度
const effectiveWidth = computed(() => {
  return isCollapsed.value ? collapsedWidth.value : sidebarWidth.value
})

// 从 localStorage 恢复或根据当前路由设置默认功能
const getInitialFunction = () => {
  // 优先根据当前路由判断
  const path = route.path
  if (path === '/alerts') return 'alerts'
  if (path === '/reports') return 'reports'
  if (path === '/mood') return 'mood'
  if (path === '/questionnaire') return 'questionnaire'
  if (path === '/') return 'home'
  
  // 否则尝试从 localStorage 恢复
  const saved = localStorage.getItem('activeFunction')
  return saved || 'home'
}

const activeFunction = ref(getInitialFunction())

// 计算当前应该显示的组件
const currentComponent = computed(() => {
  // 根据 activeFunction 决定显示哪个组件
  if (activeFunction.value === 'home' || activeFunction.value === 'history') {
    return ChatApp
  }
  // 情绪记录（mood 路由对应 emotion 组件）
  if (activeFunction.value === 'mood' || activeFunction.value === 'emotion') {
    return EmotionRecordPage
  }
  // 预警提醒
  if (activeFunction.value === 'alerts') {
    return AlertPage
  }
  // 问卷自查
  if (activeFunction.value === 'questionnaire') {
    return QuestionnairePage
  }
  // 情绪报告
  if (activeFunction.value === 'reports') {
    return MoodReport
  }
  // 默认显示 ChatApp
  return ChatApp
})

// 保存功能选择到 localStorage
const saveActiveFunction = (func) => {
  localStorage.setItem('activeFunction', func)
}

// 处理侧边栏宽度变化
const handleWidthChange = (width) => {
  // 如果宽度等于收起宽度，说明是收起状态
  if (width === collapsedWidth.value) {
    isCollapsed.value = true
  } else {
    isCollapsed.value = false
    sidebarWidth.value = width
  }
}

// 处理侧边栏收起/展开状态变化
const handleCollapseChange = (collapsed) => {
  isCollapsed.value = collapsed
}

// 页面加载时恢复状态
onMounted(() => {
  // 确保 activeFunction 与当前路由一致
  const path = route.path
  if (path === '/alerts') activeFunction.value = 'alerts'
  else if (path === '/reports') activeFunction.value = 'reports'
  else if (path === '/mood') activeFunction.value = 'mood'
  else if (path === '/questionnaire') activeFunction.value = 'questionnaire'
  else if (path === '/') activeFunction.value = 'home'
  
  // 从 localStorage 恢复侧边栏状态
  const savedCollapsed = localStorage.getItem('sidebarCollapsed')
  const savedWidth = localStorage.getItem('sidebarWidth')
  
  if (savedCollapsed !== null) {
    isCollapsed.value = savedCollapsed === 'true'
  }
  if (savedWidth) {
    const width = parseInt(savedWidth)
    if (width >= 200 && width <= 400) {
      sidebarWidth.value = width
    }
  }
})

// 事件处理函数
const handleCreateNew = () => {
  // 创建新对话时清空选中的对话
  selectedConversation.value = null
  activeFunction.value = 'home'
  saveActiveFunction('home')
}

const handleLoadConversation = (conversation) => {
  // 处理加载对话事件，将对话数据传递给MainContent
  selectedConversation.value = conversation
  activeFunction.value = 'history'
  saveActiveFunction('history')
}

const handleSelectFunction = (functionName) => {
  // 处理功能选项选择事件，更新激活的功能
  activeFunction.value = functionName
  saveActiveFunction(functionName)
  // 只有当切换到非历史记录功能时才清空选中的对话
  if (functionName !== 'history') {
    selectedConversation.value = null
  }
}

// 处理跳转到报告页面（从对话结束触发）
const handleNavigateToReports = (data) => {
  // console.log('MainLayout: 跳转到情绪报告', data)
  // 切换到报告视图
  activeFunction.value = 'reports'
  saveActiveFunction('reports')
  // 清除选中的对话
  selectedConversation.value = null
}
</script>

<style scoped>
.main-layout {
  display: flex;
  height: 100vh;
  overflow: hidden;
  position: relative;
}

/* 背景组件在最底层 */
.main-layout :deep(.background-container) {
  z-index: 0;
}

.main-layout :deep(.sidebar) {
  position: fixed;
  left: 0;
  top: 0;
  height: 100vh;
  z-index: 100;
  transition: z-index 0.3s ease;
}

/* 当有抽屉打开时，降低侧边栏的 z-index */
.main-layout :deep(.sidebar.drawer-open) {
  z-index: 1999;
}

.main-layout :deep(.main-content) {
  flex: 1;
  height: 100%;
  min-width: 0;
  overflow-y: auto;  /* 添加垂直滚动条 */
  transition: margin-left 0.3s ease;
}

.main-content-wrapper {
  flex: 1;
  height: 100%;
  min-width: 0;
  overflow-y: auto;  /* 添加垂直滚动条 */
  transition: margin-left 0.3s ease;
  position: relative;
  z-index: 1;
}

.empty-content {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  width: 100%;
}

/* 响应式调整 */
@media (max-width: 768px) {
  .main-layout {
    flex-direction: column;
  }
  
  .main-layout :deep(.sidebar) {
    position: relative;
    width: 100% !important;
    height: auto;
    max-height: 50vh;
  }
  
  .main-layout :deep(.main-content) {
    margin-left: 0 !important;
    height: 50%;
  }
}
</style>
