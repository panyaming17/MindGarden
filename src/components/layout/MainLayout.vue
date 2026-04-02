<template>
  <div class="main-layout">
    <Sidebar 
      @create-new="handleCreateNew" 
      @load-conversation="handleLoadConversation"
      @select-function="handleSelectFunction"
    />
    <MainContent 
      :conversationData="selectedConversation"
      :activeFunction="activeFunction"
    />
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import Sidebar from '../base/Sidebar.vue'
import MainContent from '../base/MainContent.vue'

// 定义组件名称
defineOptions({
  name: 'MainLayout'
})

// 响应式数据
const selectedConversation = ref(null)
const activeFunction = ref('home') // 默认选中首页

// 事件处理函数
const handleCreateNew = () => {
  // 创建新对话时清空选中的对话
  selectedConversation.value = null
  activeFunction.value = 'home'
}

const handleLoadConversation = (conversation) => {
  // 处理加载对话事件，将对话数据传递给MainContent
  selectedConversation.value = conversation
  activeFunction.value = 'history'
}

const handleSelectFunction = (functionName) => {
  // 处理功能选项选择事件，更新激活的功能
  activeFunction.value = functionName
  // 只有当切换到非历史记录功能时才清空选中的对话
  if (functionName !== 'history') {
    selectedConversation.value = null
  }
}
</script>

<style scoped>
.main-layout {
  display: flex;
  height: 100vh;
  overflow: hidden;
  position: relative;
}

/* 确保侧边栏和主内容区域有正确的宽度分配 */
.sidebar {
  flex: 0 0 280px;
  min-width: 280px;
  max-width: 320px;
  height: 100%;
}

.main-content {
  flex: 1;
  height: 100%;
  min-width: 0;
}

/* 响应式调整 */
@media (max-width: 768px) {
  .main-layout {
    flex-direction: column;
  }
  
  .sidebar,
  .main-content {
    flex: 0 0 100%;
    height: 50%;
  }
}
</style>