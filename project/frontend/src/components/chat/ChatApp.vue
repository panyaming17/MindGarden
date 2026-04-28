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
            @withdraw="handleWithdraw"
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
            ref="chatInputRef"
            :is-loading="isProcessing"
            :is-disabled="isInputDisabled"
            :placeholder="inputPlaceholder"
            @send-message="sendMessage"
            @start-new-chat="startNewChat"
            @end-chat="endChat"
          />
        </div>
    </div>
  </div>

  <!-- 新对话确认对话框 -->
  <div v-if="showNewChatDialog" class="dialog-overlay" @click.self="cancelDialog">
    <div class="dialog-container" @click.stop>
      <div class="dialog-header">
        <h3>创建新对话</h3>
      </div>
      <div class="dialog-body">
        <p>当前对话尚未结束，请选择如何处理：</p>
      </div>
      <div class="dialog-actions">
        <button class="btn-cancel" @click="cancelDialog">取消</button>
        <button class="btn-discard" @click="handleDialogChoice('discard')">不保存</button>
        <button class="btn-save" @click="handleDialogChoice('save')">保存并创建新对话</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, nextTick, onMounted, onUnmounted } from 'vue'
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
      // console.log('Token即将过期，剩余时间:', Math.floor(timeLeft / 60000), '分钟')
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
  'end-chat',
  'chat-ended',
  'report-ready',
  'navigate-to-reports'
])

// 响应式数据
const messages = ref([])
const currentRole = ref('小园')
const isProcessing = ref(false)
const inputPlaceholder = ref('请输入内容...')
const chatContentRef = ref(null)
const chatInputRef = ref(null)
const title = ref('小园')
const isInputDisabled = ref(false)

// 用于截断正在进行的请求
let currentAbortController = null

// 会话数据
const sessionData = ref({
  sessionId: null,
  sessionTitle: null
})

// 本地存储键名（只存 sessionId，不存消息）
const CURRENT_SESSION_ID_KEY = 'currentSessionId'

// 保存当前会话ID到localStorage
const saveCurrentSessionId = () => {
  if (sessionData.value.sessionId) {
    localStorage.setItem(CURRENT_SESSION_ID_KEY, sessionData.value.sessionId)
    // console.log('已保存会话ID:', sessionData.value.sessionId)
  }
}

// 获取当前会话ID
const getCurrentSessionId = () => {
  return localStorage.getItem(CURRENT_SESSION_ID_KEY)
}

// 清除当前会话ID
const clearCurrentSessionId = () => {
  localStorage.removeItem(CURRENT_SESSION_ID_KEY)
  // console.log('已清除会话ID')
}

// 从后端恢复会话（通过 sessionId 获取会话详情）
const restoreSessionFromBackend = async (sessionId) => {
  try {
    // console.log('[先导语] restoreSessionFromBackend 被调用:', sessionId)
    
    const response = await fetch(`${API_BASE_URL}/session/${sessionId}`)
    
    if (!response.ok) {
      // 会话不存在，清除本地缓存
      // console.log('[先导语] 会话不存在，清除本地缓存')
      clearCurrentSessionId()
      return false
    }
    
    const sessionDetail = await response.json()
    // console.log('[先导语] 会话详情:', sessionDetail)
    // console.log('[先导语] 会话状态:', sessionDetail.status)
    // console.log('[先导语] 消息数量:', sessionDetail.messages?.length || 0)
    
    // 检查会话状态是否可以恢复（draft 或 active）
    // 只有 ended 状态的会话才需要清除缓存
    if (sessionDetail.status === 'ended' || sessionDetail.status === 'ending') {
      // 已结束的会话不能恢复，清除缓存
      // console.log('会话已结束，清除缓存')
      clearCurrentSessionId()
      return false
    }
    
    // 恢复会话数据
    sessionData.value.sessionId = sessionDetail.session_id
    sessionData.value.sessionTitle = sessionDetail.title
    sessionData.value.userId = sessionDetail.user_id
    title.value = sessionDetail.title || '小园'
    
    // 恢复消息列表
    if (sessionDetail.messages && sessionDetail.messages.length > 0) {
      messages.value = sessionDetail.messages.map(msg => ({
        id: msg.id,
        type: msg.role === 'user' ? 'user' : 'assistant',
        role: msg.role === 'user' ? 'user' : '小园',
        content: msg.content,
        timestamp: msg.timestamp,
        four_dim: msg.four_dim
      }))
    } else {
      // 没有消息，获取后端先导语
      // console.log('[先导语] 恢复会话无消息，获取后端先导语')
      await loadAndShowOpening(sessionDetail.user_id, sessionDetail.session_id)
    }
    
    // 保存会话ID到缓存（确保锁定）
    saveCurrentSessionId()
    
    // console.log('已从后端恢复会话:', sessionId, '状态:', sessionDetail.status)
    return true
  } catch (error) {
    console.error('恢复会话失败:', error)
    clearCurrentSessionId()
    return false
  }
}

// 从后端获取当前活跃会话
const getActiveSessionFromBackend = async (userId) => {
  try {
    const response = await fetch(`${API_BASE_URL}/active-session/${userId}`)
    
    if (!response.ok) {
      return null
    }
    
    const result = await response.json()
    
    if (result.has_active_session && result.session) {
      // console.log('从后端获取到活跃会话:', result.session.session_id, '状态:', result.session.status)
      return result.session
    }
    
    return null
  } catch (error) {
    // console.error('获取活跃会话失败:', error)
    return null
  }
}

// 创建新会话并锁定
const createAndLockSession = async () => {
  try {
    const userData = localStorage.getItem('user')
    if (!userData) {
      console.log('用户未登录，不创建会话')
      return false
    }
    
    const user = JSON.parse(userData)
    
    const response = await fetch(`${API_BASE_URL}/new-session`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_id: user.id })
    })
    
    if (!response.ok) {
      throw new Error('创建会话失败')
    }
    
    const result = await response.json()
    
    // 锁定会话ID
    sessionData.value.sessionId = result.session_id
    sessionData.value.sessionTitle = result.session_title
    sessionData.value.userId = user.id
    title.value = result.session_title || '小园'
    
    // 保存会话ID到 localStorage
    saveCurrentSessionId()
    
    // console.log('已创建并锁定会话:', result.session_id)
    return true
  } catch (error) {
    console.error('创建会话失败:', error)
    return false
  }
}

// 初始化首页会话
const initHomeSession = async () => {
  console.log('开始初始化首页会话...')
  
  // 获取用户信息
  const userData = localStorage.getItem('user')
  if (!userData) {
    console.log('用户未登录，不初始化会话')
    addWelcomeMessage()
    return
  }
  
  const user = JSON.parse(userData)
  
  // 步骤1: 先从后端获取当前活跃会话（这是最权威的来源）
  const activeSession = await getActiveSessionFromBackend(user.id)
  
  if (activeSession) {
    // 后端有活跃会话，直接使用
    sessionData.value.sessionId = activeSession.session_id
    sessionData.value.sessionTitle = activeSession.title
    sessionData.value.userId = activeSession.user_id
    title.value = activeSession.title || '小园'
    
    // 保存会话ID到缓存
    saveCurrentSessionId()
    
    // 获取会话详情（包括消息）
    const restored = await restoreSessionFromBackend(activeSession.session_id)
    if (restored) {
      // console.log('已恢复后端活跃会话:', activeSession.session_id)
      return
    }
  }
  
  // 步骤2: 后端没有活跃会话，检查本地缓存
  const cachedSessionId = getCurrentSessionId()
  // console.log('缓存的会话ID:', cachedSessionId)
  
  if (cachedSessionId) {
    // 尝试从后端恢复缓存的会话
    // console.log('尝试从后端恢复缓存会话:', cachedSessionId)
    const restored = await restoreSessionFromBackend(cachedSessionId)
    if (restored) {
      console.log('会话恢复成功')
      return
    }
    console.log('会话恢复失败，将创建新会话')
  }
  
  // 步骤3: 没有可恢复的会话，创建新会话
  console.log('创建新会话...')
  const created = await createAndLockSession()
  
  // 获取先导语（回访用户显示历史跟进，首次用户显示默认欢迎）
  await loadAndShowOpening(user.id, sessionData.value.sessionId)
  console.log('首页初始化完成')
}

// 组件挂载时初始化会话
onMounted(async () => {
  // 检查登录状态
  if (!checkLoginStatus()) {
    return
  }
  
  // 只有在没有对话数据且在首页时才初始化会话
  if (!props.conversationData && props.activeFunction === 'home') {
    try {
      await initHomeSession()
    } catch (error) {
      console.error('初始化会话失败:', error)
      // 即使初始化失败，也显示欢迎消息
      addWelcomeMessage()
    }
  }
})

// 添加欢迎消息（支持先导语）
const addWelcomeMessage = (openingPrompt = null) => {
  const welcomeContent = openingPrompt || '你好！我是小园，你的专属情绪陪伴助手。无论你此刻心情如何，我都在这里倾听你、陪伴你。你可以和我分享你的心事、困惑，或者只是随便聊聊。让我们一起探索情绪的奥秘，找到内心的平静与力量吧！'
  messages.value = [
    {
      id: 'welcome',
      type: 'assistant',
      role: '小园',
      content: welcomeContent,
      timestamp: new Date().toISOString(),
      hint: openingPrompt ? '由AI生成对话内容，仅供参考' : '由AI生成对话内容，仅供参考'
    }
  ]
}

// 获取会话先导语（回访用户触发）
const fetchSessionOpening = async (userId, sessionId) => {
  try {
    const url = `${API_BASE_URL}/session-opening`
    const requestBody = { user_id: userId, session_id: sessionId }
    
    // console.log('[先导语] 请求信息:')
    // console.log('  → URL:', url)
    // console.log('  → Body:', JSON.stringify(requestBody, null, 2))
    
    const response = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(requestBody)
    })
    
    // console.log('[先导语] 响应信息:')
    // console.log('  → Status:', response.status, response.statusText)
    
    if (!response.ok) {
      console.warn('⚠️ [先导语] 获取失败:', response.status, response.statusText)
      return null
    }
    
    const result = await response.json()
    // console.log('[先导语] 响应数据:')
    // console.log('  → result:', JSON.stringify(result, null, 2))
    // console.log('  → result.data:', JSON.stringify(result.data, null, 2))
    
    return result.data
  } catch (error) {
    console.error('❌ [先导语] 获取异常:')
    console.error('  → 错误信息:', error.message)
    console.error('  → 错误详情:', error)
    return null
  }
}

// 获取先导语并显示
const loadAndShowOpening = async (userId, sessionId) => {
  // console.log('[先导语] loadAndShowOpening 被调用')
  // console.log('  → userId:', userId)
  // console.log('  → sessionId:', sessionId)
  
  const opening = await fetchSessionOpening(userId, sessionId)
  
  // console.log('[先导语] fetchSessionOpening 返回:')
  // console.log('  → opening:', opening)
  
  if (opening && opening.opening_prompt) {
    // console.log('✅ [先导语] 使用后端返回的先导语')
    // console.log('  → opening_prompt:', opening.opening_prompt)
    // console.log('  → has_history:', opening.has_history)
    addWelcomeMessage(opening.opening_prompt)
  } else {
    // console.warn('⚠️ [先导语] 后端未返回先导语，显示默认欢迎语')
    // console.log('  → opening:', opening)
    // console.log('  → opening?.opening_prompt:', opening?.opening_prompt)
    addWelcomeMessage()
  }
}

// Toast 提示
const showToast = (message) => {
  // 使用简单的 alert 作为临时方案，后续可替换为更优雅的 Toast 组件
  // 也可以使用 Element Plus 的 ElMessage 或自定义 Toast 组件
  // console.log('Toast:', message)
  
  // 创建一个临时的 toast 元素
  const toast = document.createElement('div')
  toast.textContent = message
  toast.style.cssText = `
    position: fixed;
    top: 20px;
    left: 50%;
    transform: translateX(-50%);
    background: rgba(0, 0, 0, 0.8);
    color: white;
    padding: 12px 24px;
    border-radius: 8px;
    z-index: 9999;
    font-size: 14px;
    animation: fadeInOut 3s ease-in-out forwards;
  `
  document.body.appendChild(toast)
  
  // 添加动画样式（如果还没有的话）
  if (!document.getElementById('toast-styles')) {
    const style = document.createElement('style')
    style.id = 'toast-styles'
    style.textContent = `
      @keyframes fadeInOut {
        0% { opacity: 0; transform: translateX(-50%) translateY(-10px); }
        15% { opacity: 1; transform: translateX(-50%) translateY(0); }
        85% { opacity: 1; transform: translateX(-50%) translateY(0); }
        100% { opacity: 0; transform: translateX(-50%) translateY(-10px); }
      }
    `
    document.head.appendChild(style)
  }
  
  // 3秒后自动移除
  setTimeout(() => {
    if (toast.parentNode) {
      toast.parentNode.removeChild(toast)
    }
  }, 3000)
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
      // console.log('会话ID获取成功:', sessionData.value.sessionId)
    } else {
      // console.error('会话ID获取失败:', data)
      throw new Error('会话ID获取失败')
    }
    return data
  } catch (error) {
    console.error('创建会话失败:', error)
    throw error
  }
}

// 发送消息
const sendMessage = async (text, retryCount = 0) => {
  if (!text.trim()) return
  if (isInputDisabled.value) {
    showToast('当前会话已结束，请开始新对话')
    return
  }
  
  // 检查是否有会话ID
  if (!sessionData.value.sessionId) {
    showToast('会话未初始化，请刷新页面')
    return
  }
  
  const MAX_RETRIES = 3
  
  // 添加用户消息（仅在第一次发送时添加）
  let userMessage = null
  if (retryCount === 0) {
    userMessage = {
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
  
  // 创建 AbortController 用于截断请求
  const abortController = new AbortController()
  currentAbortController = abortController
  
  // 显示处理中状态
  isProcessing.value = true
  
  try {
    const userData = localStorage.getItem('user')
    const userId = userData ? JSON.parse(userData).id : null
    if (!userId) {
      ElMessage.error('用户未登录，请先登录')
      return
    }
    
    const response = await fetch(`${API_BASE_URL}/message`, { 
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        user_id: userId,
        session_id: sessionData.value.sessionId,
        message: text
      }),
      signal: abortController.signal
    })
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      throw new Error(errorData.detail || `发送消息失败 (${response.status})`)
    }
    
    const data = await response.json()
    
    // 打印响应数据，便于调试
    // console.log('后端响应数据:', da  ta)
    
    // 用后端返回的真实ID更新用户消息ID（用于撤回功能）
    if (userMessage && data.user_dialogue_id) {
      userMessage.id = String(data.user_dialogue_id)
    }
    
    // 添加智能体回复
    const assistantMessage = {
      id: data.assistant_dialogue_id ? String(data.assistant_dialogue_id) : (Date.now() + 1).toString(),
      type: 'assistant',
      role: '小园',
      content: data.response || data.reply || '我理解你的感受。',
      timestamp: new Date().toISOString(),
      hint: '由AI生成对话内容，仅供参考'
    }
    messages.value.push(assistantMessage)
    
    // 发送成功，清除重试计数和控制器
    retryCount = 0
    currentAbortController = null
    
  } catch (error) {
    // 如果是主动截断（abort），不显示错误提示
    if (error.name === 'AbortError') {
      console.log('请求已被截断')
      currentAbortController = null
      return
    }
    
    console.error('发送消息失败:', error)
    
    // 判断是否可重试
    if (retryCount < MAX_RETRIES) {
      // console.log(`正在重试... (${retryCount + 1}/${MAX_RETRIES})`)
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
    // 只有在没有被截断时才重置状态
    if (!abortController.signal.aborted) {
      isProcessing.value = false
      scrollToBottom()
    }
  }
}

// 开始新对话
const startNewChat = async () => {
  // 停止报告轮询
  stopReportPolling()
  
  // 检查当前是否有对话内容（除了欢迎消息）
  const hasConversation = messages.value.some(m => m.type === 'user')
  
  if (hasConversation && sessionData.value.sessionId) {
    // 有对话内容，弹出确认对话框
    showNewChatDialog.value = true
  } else {
    // 没有对话内容，直接删除当前空会话并创建新会话
    await deleteCurrentSessionAndCreateNew()
  }
}

// 删除当前空会话并创建新会话
const deleteCurrentSessionAndCreateNew = async () => {
  // 如果有会话ID，先删除
  if (sessionData.value.sessionId) {
    try {
      const userData = localStorage.getItem('user')
      const userId = userData ? JSON.parse(userData).id : null
      
      if (userId) {
        await fetch(`${API_BASE_URL}/delete-session`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            user_id: userId,
            session_id: sessionData.value.sessionId
          })
        })
        // console.log('已删除空会话:', sessionData.value.sessionId)
      }
    } catch (error) {
      console.error('删除会话失败:', error)
    }
  }
  
  // 创建新会话
  await createNewSessionAfterAction()
}

// 创建新会话（在结束或删除旧会话后）
const createNewSessionAfterAction = async () => {
  // 重置消息列表
  messages.value = []
  
  // 清除会话ID缓存
  clearCurrentSessionId()
  
  // 重置会话数据
  sessionData.value = {
    sessionId: null,
    sessionTitle: null
  }
  
  // 创建新会话并锁定
  await createAndLockSession()
  
  // 获取先导语（回访用户显示历史跟进，首次用户显示默认欢迎）
  // 优先使用 sessionData 中已有的 userId（createAndLockSession 已设置）
  const userId = sessionData.value.userId
  // console.log('[先导语] createNewSessionAfterAction 调试信息:')
  // console.log('  → sessionData.value.userId:', userId)
  // console.log('  → sessionData.value.sessionId:', sessionData.value.sessionId)
  
  if (userId && sessionData.value.sessionId) {
    // console.log('[先导语] 调用 loadAndShowOpening')
    await loadAndShowOpening(userId, sessionData.value.sessionId)
  } else {
    console.warn('[先导语] userId 或 sessionId 为空，跳过获取先导语')
    console.log('  → 尝试从 localStorage 获取 userId')
    const userData = localStorage.getItem('user')
    const fallbackUserId = userData ? JSON.parse(userData).id : null
    // console.log('  → fallbackUserId:', fallbackUserId)
    if (fallbackUserId && sessionData.value.sessionId) {
      // console.log('[先导语] 使用 fallbackUserId 调用 loadAndShowOpening')
      await loadAndShowOpening(fallbackUserId, sessionData.value.sessionId)
    } else {
      console.warn('[先导语] 仍然无法获取 userId，显示默认欢迎语')
      addWelcomeMessage()
    }
  }
  
  // 重置标题
  title.value = '小园'
  
  // 启用输入框
  isInputDisabled.value = false
  
  console.log('已创建新会话')
}

// 确认对话框相关
const showNewChatDialog = ref(false)

// 处理对话框选择
const handleDialogChoice = async (choice) => {
  showNewChatDialog.value = false
  
  if (choice === 'save') {
    // 用户选择保存当前对话并创建新对话
    await saveAndCreateNew()
  } else if (choice === 'discard') {
    // 用户选择不保存，删除当前会话并创建新会话
    await discardAndCreateNew()
  }
}

// 保存当前会话并创建新会话
const saveAndCreateNew = async () => {
  try {
    const userData = localStorage.getItem('user')
    const userId = userData ? JSON.parse(userData).id : null
    if (!userId) throw new Error('用户未登录')
    if (!sessionData.value.sessionId) throw new Error('会话ID不存在')
    
    const currentSessionId = sessionData.value.sessionId
    
    // 调用 end-session API，skip_redirect=true 表示不跳转报告页面
    const response = await fetch(`${API_BASE_URL}/end-session`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        user_id: userId,
        session_id: currentSessionId,
        skip_redirect: true  // 不跳转报告页面
      })
    })
    
    if (!response.ok) throw new Error('结束会话失败')
    
    showToast('对话已保存，正在生成报告...')
    
    // 创建新会话
    await createNewSessionAfterAction()
    
  } catch (error) {
    console.error('保存会话失败:', error)
    showToast('保存会话失败: ' + error.message)
  }
}

// 不保存当前会话，删除并创建新会话
const discardAndCreateNew = async () => {
  try {
    const userData = localStorage.getItem('user')
    const userId = userData ? JSON.parse(userData).id : null
    if (!userId) throw new Error('用户未登录')
    if (!sessionData.value.sessionId) throw new Error('会话ID不存在')
    
    // 调用 delete-session API
    const response = await fetch(`${API_BASE_URL}/delete-session`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        user_id: userId,
        session_id: sessionData.value.sessionId
      })
    })
    
    if (!response.ok) throw new Error('删除会话失败')
    
    showToast('已创建新对话')
    
    // 创建新会话
    await createNewSessionAfterAction()
    
  } catch (error) {
    console.error('删除会话失败:', error)
    showToast('删除会话失败: ' + error.message)
  }
}

// 取消对话框
const cancelDialog = () => {
  showNewChatDialog.value = false
}

// 结束对话
const endChat = async () => {
  if (messages.value.length <= 1) {
    // 如果只有欢迎消息或没有消息，直接清空不调用API
    clearCurrentSessionId()
    messages.value = []
    addWelcomeMessage()
    return
  }
  
  try {
    const userData = localStorage.getItem('user')
    const userId = userData ? JSON.parse(userData).id : null
    if (!userId) throw new Error('用户未登录')
    if (!sessionData.value.sessionId) throw new Error('会话ID不存在')
    
    const currentSessionId = sessionData.value.sessionId
    
    const response = await fetch(`${API_BASE_URL}/end-session`, { 
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        user_id: userId,
        session_id: currentSessionId
      })
    })
    
    if (!response.ok) throw new Error('结束会话失败')
    
    // 清除当前会话数据
    clearCurrentSessionId()
    
    // 弹出 Toast 提示
    showToast('对话已结束，正在跳转到报告页面...')
    
    // 将当前会话ID存入localStorage，供报告页面使用
    localStorage.setItem('pendingReportSessionId', currentSessionId)
    localStorage.setItem('pendingReportUserId', userId)
    
    // 立即通知父组件跳转到情绪报告页面
    emit('navigate-to-reports', {
      sessionId: currentSessionId,
      userId: userId
    })
    
    // 在后台继续轮询报告状态（用于更新报告页面的提示）
    startReportPolling(currentSessionId, userId)
    
  } catch (error) {
    console.error('结束会话失败:', error)
    alert('结束会话失败: ' + error.message)
  }
}

// 报告轮询相关变量和方法
const reportPollingTimer = ref(null)

const startReportPolling = (sessionId, userId) => {
  // 每2秒轮询一次报告状态
  reportPollingTimer.value = setInterval(async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/report-status/${sessionId}`)
      const result = await response.json()
      
      if (result.status === 'completed') {
        // 三份报告都完成了，停止轮询
        stopReportPolling()
        emit('report-ready', { sessionId, userId })
        
        // 更新消息显示
        messages.value = [{
          id: Date.now(),
          role: 'assistant',
          content: '报告已生成完成！请在右侧查看您的专属报告。',
          timestamp: new Date().toISOString(),
          isWelcome: false,
          isReportReady: true
        }]
      }
    } catch (error) {
      console.error('查询报告状态失败:', error)
    }
  }, 2000)
}

const stopReportPolling = () => {
  if (reportPollingTimer.value) {
    clearInterval(reportPollingTimer.value)
    reportPollingTimer.value = null
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
        message: userMessage.content,
        regenerate: true,
        assistant_dialogue_id: message.id
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
  // console.log('消息反馈:', data)  
  const { message, type } = data
  
  if (type) {
    ElMessage.success(type === 'like' ? '感谢您的点赞！' : '感谢您的反馈，我们会继续改进')
  }
  
  // TODO: 可以将反馈发送到后端
  // sendFeedbackToServer(message.id, type)
}

// 处理撤回消息
const handleWithdraw = async (message) => {
  console.log('撤回消息:', message)
  
  // 找到消息索引
  const messageIndex = messages.value.findIndex(m => m.id === message.id)
  if (messageIndex === -1) return
  
  // ====== 第一步：截断正在进行的请求 ======
  if (currentAbortController && isProcessing.value) {
    console.log('检测到正在生成的回复，正在截断...')
    currentAbortController.abort()
    currentAbortController = null
  }
  
  // 重置处理状态（恢复发送按钮）
  isProcessing.value = false
  
  // 获取用户信息
  const userData = localStorage.getItem('user')
  const userId = userData ? JSON.parse(userData).id : null
  // console.log('撤回参数:', { userId, sessionId: sessionData.value.sessionId, messageId: message.id, messageType: message.type })
  
  if (!userId) {
    ElMessage.error('用户未登录，请先登录')
    return
  }
  
  if (!sessionData.value.sessionId) {
    ElMessage.error('会话不存在')
    return
  }
  
  try {
    // ====== 第二步：调用后端撤回接口 ======
    const response = await fetch(`${API_BASE_URL}/withdraw-message`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        user_id: userId,
        session_id: sessionData.value.sessionId,
        message_id: message.id
      })
    })
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      
      // 处理特定错误情况
      if (response.status === 400 && errorData.detail?.includes('超过')) {
        ElMessage.warning(errorData.detail || '已超过2分钟，无法撤回该消息')
        return
      }
      
      throw new Error(errorData.detail || `撤回失败 (${response.status})`)
    }
    
    const result = await response.json()
    // console.log('撤回成功:', result)
    
  } catch (error) {
    console.error('撤回消息失败:', error)
    
    // 如果是时间限制错误，不执行前端撤回
    if (error.message?.includes('超过') || error.message?.includes('无法撤回')) {
      ElMessage.warning(error.message)
      return
    }
    
    // 其他错误：仍然允许前端撤回（降级处理）
    ElMessage.warning('后端同步失败，已在前端本地撤回')
  }
  
  // ====== 第三步：前端状态更新（无论后端成功与否都执行） ======
  
  // 将消息内容填入输入框
  if (chatInputRef.value) {
    chatInputRef.value.setInputText(message.content)
  }
  
  // 删除该消息及其后面的所有消息（前端同步）
  messages.value = messages.value.slice(0, messageIndex)
  
  // 滚动到底部
  scrollToBottom()
  
  ElMessage.success('消息已撤回，可在输入框中编辑后重新发送')
}

// 监听消息变化，自动滚动到底部并保存会话
watch(messages, () => {
  scrollToBottom()
  // 自动保存会话ID（仅在首页且不是从对话记录加载时）
  if (props.activeFunction === 'home' && !props.conversationData && messages.value.length > 0) {
    saveCurrentSessionId()
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
        // console.log('对话气泡渲染完成，消息数量:', messages.value.length)
        // console.log('渲染的消息:', messages.value)
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

// 监听activeFunction变化，当切换到home时恢复或显示欢迎消息（不创建新会话）
// 监听 activeFunction 变化
watch(() => props.activeFunction, async (newFunction, oldFunction) => {
  // console.log('activeFunction 变化:', oldFunction, '->', newFunction)
  
  if (newFunction === 'home') {
    // 获取用户信息
    const userData = localStorage.getItem('user')
    if (!userData) {
      console.log('用户未登录')
      addWelcomeMessage()
      return
    }
    
    const user = JSON.parse(userData)
    
    // 先从后端获取当前活跃会话
    const activeSession = await getActiveSessionFromBackend(user.id)
    
    if (activeSession) {
      // 后端有活跃会话，直接使用
      sessionData.value.sessionId = activeSession.session_id
      sessionData.value.sessionTitle = activeSession.title
      sessionData.value.userId = activeSession.user_id
      title.value = activeSession.title || '小园'
      saveCurrentSessionId()
      
      // 获取会话详情
      const restored = await restoreSessionFromBackend(activeSession.session_id)
      if (restored) {
        // console.log('切回首页，已恢复后端活跃会话:', activeSession.session_id)
        return
      }
    }
    
    // 后端没有活跃会话，检查本地缓存
    const cachedSessionId = getCurrentSessionId()
    
    if (cachedSessionId) {
      // 尝试从后端恢复会话
      const restored = await restoreSessionFromBackend(cachedSessionId)
      if (restored) {
        // console.log('切回首页，已恢复会话:', sessionData.value.sessionId)
        return
      }
      console.log('恢复失败，创建新会话')
    }
    
    // 没有可恢复的会话，创建新会话
    try {
      await createAndLockSession()
      await loadAndShowOpening(user.id, sessionData.value.sessionId)
      title.value = '小园'
    } catch (error) {
      console.error('创建新会话失败:', error)
      addWelcomeMessage()
    }
  }
  // 离开首页时不需要保存会话，因为会话数据都在后端
})

// 组件卸载时清理资源
onUnmounted(() => {
  stopReportPolling()
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
  z-index: 1;
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

/* 对话框样式 */
.dialog-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
}

.dialog-container {
  background: white;
  border-radius: 16px;
  padding: 24px;
  max-width: 400px;
  width: 90%;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
}

.dialog-header h3 {
  margin: 0 0 16px 0;
  font-size: 18px;
  color: #333;
}

.dialog-body p {
  margin: 0 0 20px 0;
  color: #666;
  font-size: 14px;
}

.dialog-actions {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.dialog-actions button {
  padding: 12px 20px;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-cancel {
  background: #f5f5f5;
  color: #666;
}

.btn-cancel:hover {
  background: #e0e0e0;
}

.btn-discard {
  background: #fff3e0;
  color: #e65100;
}

.btn-discard:hover {
  background: #ffe0b2;
}

.btn-save {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.btn-save:hover {
  opacity: 0.9;
  transform: translateY(-1px);
}
</style>