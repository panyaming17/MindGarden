<template>
  <div class="chat-container">
    <!-- 标题 -->
     <div class="title-container">{{ title }}</div>
      <!-- 内层2：聊天区 -->
      <div class="chat-app">
        <!-- 聊天内容区域（可滚动） -->
        <div ref="chatContentRef" class="chat-content">
          <ChatMessages 
            :messages="messages"
            :current-role="currentRole"
            @message-click="handleMessageClick"
          />
          
          <!-- 分析中状态提示 -->
          <div v-if="isAnalyzing" class="analyzing-indicator">
            <el-icon class="is-loading"><Loading /></el-icon>
            <span>{{ analyzingText }}</span>
          </div>
        </div>
        
        <!-- 输入框组件固定在底部 -->
        <div class="chat-input-fixed">
          <ChatInput 
            :is-loading="isAnalyzing || isProcessing"
            :placeholder="inputPlaceholder"
            @send-message="sendMessage"
            @start-new-chat="startNewChat"
            @end-chat="endChat"
          />
        </div>
      </div>
  </div> 
  
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch, nextTick } from 'vue'
import ChatMessages from './ChatMessages/ChatMessages.vue'
import ChatInput from './ChatInput.vue'
import { Loading } from '@element-plus/icons-vue'

// API基础URL
const API_BASE_URL = 'http://localhost:8000/api/v1/chat'

// 响应式数据
const messages = ref([])
const currentRole = ref('小园')
const isAnalyzing = ref(false)
const isProcessing = ref(false)
const inputPlaceholder = ref('请输入内容...')
const analyzingText = ref('分析中...')
const chatContentRef = ref(null)
const title = ref('小园')

// 会话数据
const sessionData = reactive({
  sessionId: null,
  sessionTitle: null
})

// 组件挂载时添加欢迎消息
onMounted(() => {
  addWelcomeMessage()
  createNewSession()
})

// 添加欢迎消息
const addWelcomeMessage = () => {
  messages.value = [
    {
      id: 'welcome',
      type: 'assistant',
      role: '小园',
      content: '你好！我是小园，你的专属情绪陪伴助手。无论你此刻心情如何，我都在这里倾听你、陪伴你。你可以和我分享你的心事、困惑，或者只是随便聊聊。让我们一起探索情绪的奥秘，找到内心的平静与力量吧！',
      timestamp: new Date().toISOString(),
      hint: '由AI生成对话内容，仅供参考'
    }
  ]
}

// 创建新会话
const createNewSession = async () => {
  try {
    const userData = localStorage.getItem('user')
    const userId = userData ? JSON.parse(userData).id : null
    if (!userId) throw new Error('用户未登录')
    
    const response = await fetch(`${API_BASE_URL}/new-session`, { 
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_id: userId })
    })
    
    if (!response.ok) throw new Error('创建会话失败')
    const data = await response.json()
    
    // 验证会话ID和标题
    if (data.session_id && data.session_title) {
      sessionData.sessionId = data.session_id
      sessionData.sessionTitle = data.session_title
      console.log('会话ID和标题获取成功:', sessionData.sessionId, sessionData.sessionTitle)
    } else {
      console.error('会话ID或标题获取失败:', data)
      throw new Error('会话ID或标题获取失败')
    }
    return data
  } catch (error) {
    console.error('创建会话失败:', error)
    throw error
  }
}

// 发送消息
const sendMessage = async (text) => {
  if (!text.trim()) return
  
  // 添加用户消息
  const userMessage = {
    id: Date.now().toString(),
    type: 'user',
    role: 'user',
    content: text,
    timestamp: new Date().toISOString()
  }
  messages.value.push(userMessage)
  
  // 滚动到底部
  scrollToBottom()
  
  // 显示分析中状态
  isProcessing.value = true
  
  try {
    const userData = localStorage.getItem('user')
    const userId = userData ? JSON.parse(userData).id : null
    if (!userId) throw new Error('用户未登录')
    if (!sessionData.sessionId) throw new Error('会话ID不存在')
    
    const response = await fetch(`${API_BASE_URL}/message`, { 
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        user_id: userId,
        session_id: sessionData.sessionId,
        message: text
      })
    })
    
    if (!response.ok) throw new Error('发送消息失败')
    const data = await response.json()
    
    // 打印响应数据，便于调试
    console.log('后端响应数据:', data)
    
    // 添加智能体回复
    const assistantMessage = {
      id: (Date.now() + 1).toString(),
      type: 'assistant',
      role: '小园',
      content: data.response || data.reply || '我理解你的感受。',
      timestamp: new Date().toISOString(),
      hint: '由AI生成对话内容，仅供参考'
    }
    messages.value.push(assistantMessage)
    
  } catch (error) {
    console.error('发送消息失败:', error)
    // 添加错误消息
    const errorMessage = {
      id: (Date.now() + 2).toString(),
      type: 'assistant',
      role: '小园',
      content: '抱歉，我暂时无法回复你的消息。请稍后再试。',
      timestamp: new Date().toISOString()
    }
    messages.value.push(errorMessage)
  } finally {
    isProcessing.value = false
    scrollToBottom()
  }
}

// 开始新对话
const startNewChat = () => {
  messages.value = []
  addWelcomeMessage()
  createNewSession()
}

// 结束对话
const endChat = async () => {
  try {
    const userData = localStorage.getItem('user')
    const userId = userData ? JSON.parse(userData).id : null
    if (!userId) throw new Error('用户未登录')
    if (!sessionData.sessionId) throw new Error('会话ID不存在')
    
    const response = await fetch(`${API_BASE_URL}/end-session`, { 
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        user_id: userId,
        session_id: sessionData.sessionId
      })
    })
    
    if (!response.ok) throw new Error('结束会话失败')
    
    // 清空消息
    messages.value = []
    addWelcomeMessage()
    createNewSession()
    
  } catch (error) {
    console.error('结束会话失败:', error)
  }
}

// 滚动到底部
const scrollToBottom = () => {
  nextTick(() => {
    if (chatContentRef.value) {
      chatContentRef.value.scrollTop = chatContentRef.value.scrollHeight
    }
  })
}

// 处理消息点击
const handleMessageClick = (message) => {
  console.log('点击了消息:', message)
}

// 监听消息变化，自动滚动到底部
watch(messages, () => {
  scrollToBottom()
}, { deep: true })

</script>

<style scoped>
.chat-container {
  height: 100%;
  width: 100%;
  max-width: 800px;
  display: flex;
  flex-direction: column;
  background: transparent;
  margin: 0 auto;
}

/* 标题样式 */
.title-container {
  text-align: center;
  font-size: 24px;
  font-weight: bold;
  color: #4CAF50;
  margin: 20px 0;
  padding: 10px 0;
  border-bottom: 1px solid rgba(238, 238, 238, 0.5);
}

.chat-app {
  display: flex;
  flex-direction: column;
  flex: 1;
  width: 100%;
  /* 背景透明 */
  background: transparent;
  position: relative;
}

/* 聊天内容区域 */
.chat-content {
  flex: 1;
  overflow-y: auto;
  margin-right: -8px;
  padding-right: 16px;
  min-height: 0;
}

/* 聊天内容区域的滚动条样式 */
.chat-content::-webkit-scrollbar {
  width: 4px;
}

.chat-content::-webkit-scrollbar-track {
  background: rgba(241, 241, 241, 0.3);
  border-radius: 4px;
}

.chat-content::-webkit-scrollbar-thumb {
  background: rgba(1, 146, 28, 0.3);
  border-radius: 4px;
  transition: background 0.3s ease;
}

.chat-content::-webkit-scrollbar-thumb:hover {
  background: rgba(15, 158, 2, 0.6);
}

/* 输入框固定在底部 */
.chat-input-fixed {
  border-top: 1px solid rgba(238, 238, 238, 0.5);
  margin-right: 0;
  width: 100%;
  background: transparent;
}

/* 确保聊天内容区域占满可用空间 */
.chat-app {
  min-height: 500px;
}

/* 使用深度选择器强制覆盖子组件样式 */
.chat-app :deep(.chat-messages) {
  background-color: transparent !important;
}

.chat-app :deep(.chat-input-container) {
  background: transparent !important;
}


@keyframes rotate {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

/* 确保消息容器背景透明 */
.chat-app :deep(.message-bubble) {
  background: transparent !important;
}

.chat-app :deep(.message-container) {
  background: transparent !important;
}

.chat-app :deep(.avatar-section) {
  background: transparent !important;
}

.chat-app :deep(.user-avatar-section) {
  background: transparent !important;
}

.chat-app :deep(.message-content-wrapper) {
  background: transparent !important;
}

/* 保持消息内容气泡的样式 */
.chat-app :deep(.message-content) {
  background: rgba(255, 255, 255, 0.9) !important;
  box-shadow: 0 2px 8px rgba(0,0,0,0.05) !important;
  backdrop-filter: blur(10px) !important;
  border: 1px solid rgba(255, 255, 255, 0.2) !important;
}

.chat-app :deep(.message-content.user) {
  background: rgba(102, 126, 234, 0.1) !important;
  border: 1px solid rgba(102, 126, 234, 0.3) !important;
  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.1) !important;
}
</style>