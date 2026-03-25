<template>
  <div class="main-layout">
    <Sidebar 
      @create-new="handleCreateNew" 
      @load-conversation="handleLoadConversation"
      @select-function="handleSelectFunction"
    />
    <MainContent 
      :conversationData="selectedConversation"
      :activeFunction="activeFunction === 'history' ? 'home' : activeFunction"
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
  // 清空选中的对话，因为切换功能时可能需要显示不同内容
  selectedConversation.value = null
}
</script>

<style scoped>
.main-layout {
  display: flex;
  height: 100vh;
  overflow: hidden;

}

/* 确保侧边栏和主内容区域有正确的宽度分配 */
.sidebar {
  flex: 0 0 20%;
  min-width: 180px;
}

.main-content {
  flex: 0 0 80%;
}

/* 响应式调整 */
@media (max-width: 768px) {
  .main-layout {
    flex-direction: column;
  }
  
  .sidebar,
  .main-content {
    flex: 0 0 100%;
  }
}
</style>