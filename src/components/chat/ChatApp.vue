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
            :is-loading="isProcessing"
            @message-click="handleMessageClick"
            @copy="handleMessageCopy"
            @regenerate="handleMessageRegenerate"
            @feedback="handleMessageFeedback"
          />
          <!-- 加载动画 -->
          <div v-if="isProcessing" class="loading-message">
            <div class="message-container assistant">
              <div class="avatar-section">
                <div class="avatar xiaoxiao-avatar">
                  <img src="/src/assets/agent-avatar.png" alt="小园" />
                </div>
                <div class="role-name">小园</div>
              </div>
              <div class="loading-content">
                <img src="/src/assets/run1.png" alt="加载中" class="loading-robot" />
                <span class="loading-text">思考中...</span>
              </div>
            </div>
          </div>
        </div>
        
        <!-- 输入框组件固定在底部（仅在首页显示） -->
        <div v-if="activeFunction === 'home'" class="chat-input-fixed">
          <ChatInput 
            :is-loading="isProcessing"
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
import { ref, watch, nextTick } from 'vue'
import ChatMessages from './ChatMessages/ChatMessages.vue'
import ChatInput from './ChatInput.vue'
import { Position } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

// API基础URL
const API_BASE_URL = 'http://localhost:8000/api/v1/chat'

// 检查登录状态
const checkLoginStatus = () => {
  const userData = localStorage.getItem('user')
  const tokenExpiry = localStorage.getItem('token_expiry')
  
  if (!userData) {
    ElMessage.error('用户未登录，请先登录')
    return false
  }
  
  // 检查token是否过期
  if (tokenExpiry) {
    const expiryTime = parseInt(tokenExpiry)
    const now = Date.now()
    
    if (now > expiryTime) {
      ElMessage.error('登录已过期，请重新登录')
      // 清除登录信息
      localStorage.removeItem('user')
      localStorage.removeItem('access_token')
      localStorage.removeItem('token_expiry')
      // 可以在这里添加跳转到登录页的逻辑
      return false
    }
    
    // 如果token即将过期（30分钟内），给出提示
    const timeLeft = expiryTime - now
    if (timeLeft < 30 * 60 * 1000) {
      console.log('Token即将过期，剩余时间:', Math.floor(timeLeft / 60000), '分钟')
    }
  }
  
  return true
}

// 组件属性
const props = defineProps({
  conversationData: {
    type: Object,
    default: null
  },
  activeFunction: {
    type: String,
    default: 'home'
  }
})

// 组件事件
const emit = defineEmits([
  'end-chat'
])

// 响应式数据
const messages = ref([])
const currentRole = ref('小园')
const isProcessing = ref(false)
const inputPlaceholder = ref('请输入内容...')
const chatContentRef = ref(null)
const title = ref('小园')

// 会话数据
const sessionData = ref({
  sessionId: null,
  sessionTitle: null
})

// 本地存储键名
const CURRENT_SESSION_KEY = 'currentSession'

// 保存当前会话到localStorage
const saveCurrentSession = () => {
  const sessionToSave = {
    sessionId: sessionData.value.sessionId,
    sessionTitle: sessionData.value.sessionTitle,
    messages: messages.value,
    timestamp: new Date().toISOString()
  }
  localStorage.setItem(CURRENT_SESSION_KEY, JSON.stringify(sessionToSave))
  console.log('当前会话已保存到localStorage')
}

// 从localStorage恢复会话
const restoreCurrentSession = () => {
  const savedSession = localStorage.getItem(CURRENT_SESSION_KEY)
  if (savedSession) {
    try {
      const sessionData = JSON.parse(savedSession)
      // 检查会话是否在24小时内
      const sessionTime = new Date(sessionData.timestamp)
      const now = new Date()
      const hoursDiff = (now - sessionTime) / (1000 * 60 * 60)
      
      if (hoursDiff < 24 && sessionData.messages && sessionData.messages.length > 0) {
        // 恢复会话数据
        sessionData.value.sessionId = sessionData.sessionId
        sessionData.value.sessionTitle = sessionData.sessionTitle
        messages.value = sessionData.messages
        console.log('已从localStorage恢复会话:', sessionData.sessionId)
        return true
      } else {
        // 会话过期，清除
        localStorage.removeItem(CURRENT_SESSION_KEY)
      }
    } catch (error) {
      console.error('恢复会话失败:', error)
      localStorage.removeItem(CURRENT_SESSION_KEY)
    }
  }
  return false
}

// 清除当前会话
const clearCurrentSession = () => {
  localStorage.removeItem(CURRENT_SESSION_KEY)
  console.log('当前会话已从localStorage清除')
}

// 组件挂载时添加欢迎消息
nextTick(() => {
  // 检查登录状态
  if (!checkLoginStatus()) {
    return
  }
  
  // 只有在没有对话数据且在首页时才恢复或创建新会话
  if (!props.conversationData && props.activeFunction === 'home') {
    // 先尝试恢复会话
    const restored = restoreCurrentSession()
    if (!restored) {
      // 没有可恢复的会话，创建新会话
      addWelcomeMessage()
      createNewSession()
    }
  }
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
    
    if (!response) throw new Error('创建会话失败')
    const data = await response.json()
    
    // 验证会话ID
    if (data.session_id) {
      sessionData.value.sessionId = data.session_id
      // 不需要 session_title，使用默认值
      sessionData.value.sessionTitle = `会话 ${data.session_id.substring(0, 8)}`
      console.log('会话ID获取成功:', sessionData.value.sessionId)
    } else {
      console.error('会话ID获取失败:', data)
      throw new Error('会话ID获取失败')
    }
    return data
  } catch (error) {
    console.error('创建会话失败:', error)
    throw error
  }
}

// 发送消息（带重试机制）
const sendMessage = async (text, retryCount = 0) => {
  if (!text.trim()) return
  
  const MAX_RETRIES = 3
  
  // 添加用户消息（仅在第一次发送时添加）
  if (retryCount === 0) {
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
  }
  
  // 显示处理中状态
  isProcessing.value = true
  
  try {
    const userData = localStorage.getItem('user')
    const userId = userData ? JSON.parse(userData).id : null
    if (!userId) {
      ElMessage.error('用户未登录，请先登录')
      return
    }
    if (!sessionData.value.sessionId) {
      ElMessage.error('会话ID不存在，请刷新页面重试')
      return
    }
    
    const response = await fetch(`${API_BASE_URL}/message`, { 
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        user_id: userId,
        session_id: sessionData.value.sessionId,
        message: text
      })
    })
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      throw new Error(errorData.detail || `发送消息失败 (${response.status})`)
    }
    
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
    
    // 发送成功，清除重试计数
    retryCount = 0
    
  } catch (error) {
    console.error('发送消息失败:', error)
    
    // 判断是否可重试
    if (retryCount < MAX_RETRIES) {
      console.log(`正在重试... (${retryCount + 1}/${MAX_RETRIES})`)
      isProcessing.value = false
      
      // 显示重试提示
      ElMessage.warning(`网络连接失败，正在重试 (${retryCount + 1}/${MAX_RETRIES})...`)
      
      // 延迟1秒后重试
      await new Promise(resolve => setTimeout(resolve, 1000))
      return sendMessage(text, retryCount + 1)
    }
    
    // 重试次数用完，显示错误
    ElMessage.error('网络连接失败，请检查网络后重试')
    
    // 添加错误消息
    const errorMessage = {
      id: (Date.now() + 2).toString(),
      type: 'assistant',
      role: '小园',
      content: '抱歉，我暂时无法回复你的消息。请检查网络连接后重试。',
      timestamp: new Date().toISOString(),
      isError: true
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
  clearCurrentSession()
  addWelcomeMessage()
  createNewSession()
}

// 结束对话
const endChat = async () => {
  try {
    const userData = localStorage.getItem('user')
    const userId = userData ? JSON.parse(userData).id : null
    if (!userId) throw new Error('用户未登录')
    if (!sessionData.value.sessionId) throw new Error('会话ID不存在')
    
    const response = await fetch(`${API_BASE_URL}/end-session`, { 
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        user_id: userId,
        session_id: sessionData.value.sessionId
      })
    })
    
    if (!response.ok) throw new Error('结束会话失败')
    
    // 清空消息
    messages.value = []
    clearCurrentSession()
    addWelcomeMessage()
    createNewSession()
    
    // 触发结束对话事件
    emit('end-chat')
    
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

// 处理消息复制
const handleMessageCopy = (message) => {
  console.log('复制消息:', message)
}

// 处理重新生成消息
const handleMessageRegenerate = async (message) => {
  console.log('重新生成消息:', message)
  
  // 找到这条消息对应的用户消息
  const messageIndex = messages.value.findIndex(m => m.id === message.id)
  if (messageIndex === -1) return
  
  // 找到前一条用户消息
  let userMessage = null
  for (let i = messageIndex - 1; i >= 0; i--) {
    if (messages.value[i].type === 'user') {
      userMessage = messages.value[i]
      break
    }
  }
  
  if (!userMessage) {
    ElMessage.warning('无法找到对应的用户消息')
    return
  }
  
  // 删除当前AI回复及之后的消息
  messages.value = messages.value.slice(0, messageIndex)
  
  // 重新发送用户消息
  isProcessing.value = true
  
  try {
    const userData = localStorage.getItem('user')
    const userId = userData ? JSON.parse(userData).id : null
    if (!userId) throw new Error('用户未登录')
    if (!sessionData.value.sessionId) throw new Error('会话ID不存在')
    
    const response = await fetch(`${API_BASE_URL}/message`, { 
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        user_id: userId,
        session_id: sessionData.value.sessionId,
        message: userMessage.content
      })
    })
    
    if (!response.ok) throw new Error('重新生成失败')
    const data = await response.json()
    
    // 添加新的智能体回复
    const assistantMessage = {
      id: Date.now().toString(),
      type: 'assistant',
      role: '小园',
      content: data.response || data.reply || '我理解你的感受。',
      timestamp: new Date().toISOString(),
      hint: '由AI生成对话内容，仅供参考'
    }
    messages.value.push(assistantMessage)
    
    ElMessage.success('已重新生成回复')
    
  } catch (error) {
    console.error('重新生成失败:', error)
    ElMessage.error('重新生成失败，请稍后重试')
    
    // 恢复原来的消息
    messages.value.splice(messageIndex, 0, message)
  } finally {
    isProcessing.value = false
    scrollToBottom()
  }
}

// 处理消息反馈
const handleMessageFeedback = (data) => {
  console.log('消息反馈:', data)
  const { message, type } = data
  
  if (type) {
    ElMessage.success(type === 'like' ? '感谢您的点赞！' : '感谢您的反馈，我们会继续改进')
  }
  
  // TODO: 可以将反馈发送到后端
  // sendFeedbackToServer(message.id, type)
}

// 监听消息变化，自动滚动到底部并保存会话
watch(messages, () => {
  scrollToBottom()
  // 自动保存会话（仅在首页且不是从对话记录加载时）
  if (props.activeFunction === 'home' && !props.conversationData && messages.value.length > 0) {
    saveCurrentSession()
  }
}, { deep: true })

// 监听对话数据变化
watch(() => props.conversationData, (newConversation) => {
  if (newConversation) {
    // 更新消息列表
    if (newConversation.messages && newConversation.messages.length > 0) {
      messages.value = newConversation.messages
      // 消息更新后，在下一个DOM更新周期检查渲染是否完成
      nextTick(() => {
        console.log('对话气泡渲染完成，消息数量:', messages.value.length)
        console.log('渲染的消息:', messages.value)
      })
    }
    
    // 更新标题
    if (newConversation.title) {
      title.value = newConversation.title
    }
    
    // 更新会话数据
    if (newConversation.id) {
      sessionData.value.sessionId = newConversation.id
    }
    
    scrollToBottom()
  }
}, { deep: true })

// 监听activeFunction变化，当切换到home时重置消息列表
watch(() => props.activeFunction, (newFunction) => {
  if (newFunction === 'home') {
    // 重置消息列表，添加欢迎消息
    addWelcomeMessage()
    // 创建新会话
    createNewSession()
    // 重置标题
    title.value = '小园'
    // 消息更新后，在下一个DOM更新周期检查渲染是否完成
    nextTick(() => {
      console.log('切换到首页，消息列表已重置')
    })
  }
})

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
  padding: 0 20px;
  box-sizing: border-box;
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

/* 输入框固定在底部 */
.chat-input-fixed {
  border-top: 1px solid rgba(238, 238, 238, 0.5);
  margin-right: 0;
  width: 100%;
  background: transparent;
}

/* 加载消息样式 */
.loading-message {
  margin: 16px 0;
  max-width: 92%;
  margin-right: auto;
}

.loading-message .message-container {
  display: flex;
  align-items: flex-start;
  gap: 12px;
}

.loading-message .avatar-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  min-width: 50px;
}

.loading-message .avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  border: 2px solid rgba(255, 255, 255, 0.2);
}

.loading-message .avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: 50%;
}

.loading-message .xiaoxiao-avatar {
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
}

.loading-message .role-name {
  font-size: 12px;
  color: rgba(102, 102, 102, 0.8);
  text-align: center;
}

.loading-content {
  display: flex;
  align-items: center;
  gap: 12px;
  background: rgba(255, 255, 255, 0.9);
  padding: 12px 16px;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.05);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.loading-robot {
  width: 40px;
  height: 40px;
  object-fit: contain;
  animation: bounce 1s ease-in-out infinite;
}

.loading-text {
  font-size: 14px;
  color: #666;
}

@keyframes bounce {
  0%, 100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-5px);
  }
}
</style>