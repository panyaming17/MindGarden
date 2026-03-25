<template>
  <div class="chat-container">
    <!-- 外层1：StepsState 组件 -->
    <StepsState :activeStep="activeStep">
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
            :is-testing="isTesting"
            :placeholder="inputPlaceholder"
            @send-message="sendMessage"
            @start-new-chat="startNewChat"
            @end-chat="endChat"
            @start-test="startTest"
            @pause-test="pauseTest"
          />
        </div>
      </div>
    </StepsState>
  </div> 
  
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch, nextTick } from 'vue'
import ChatMessages from '../chat/ChatMessages/ChatMessages.vue'
import ChatInput from './ChatInput.vue'
import StepsState from '../chat/StepsState.vue'
import { Loading } from '@element-plus/icons-vue'

// API基础URL
const API_BASE_URL = 'http://localhost:8000 '

// 组件属性
const props = defineProps({
  // 外部传入的对话数据
  conversationData: {
    type: Object,
    default: null
  }
})

// 响应式数据
const messages = ref([])
const currentRole = ref('记录师')
const isAnalyzing = ref(false)
const isProcessing = ref(false)
const isTesting = ref(false)
const connectionStatus = ref('connected')
const activeStep = ref(0) // 0: 记录, 1: 分析, 2: 建议
const chatContentRef = ref(null)

// 存储所有的 setTimeout ID
const timeoutIds = ref([])

// 添加定时器并存储ID
const addTimeout = (callback, delay) => {
  const id = setTimeout(callback, delay)
  timeoutIds.value.push(id)
  return id
}

// 清除所有定时器
const clearAllTimeouts = () => {
  timeoutIds.value.forEach(id => clearTimeout(id))
  timeoutIds.value = []
}

// 监听对话数据变化
watch(() => props.conversationData, (newData) => {
  if (newData) {
    loadConversationData(newData)
  }
}, { immediate: true })

// 加载对话数据
const loadConversationData = (conversation) => {
  if (conversation && conversation.messages) {
    messages.value = conversation.messages
    // 根据对话数据设置当前角色和步骤
    if (conversation.currentPhase) {
      sessionData.currentPhase = conversation.currentPhase
    }
    if (conversation.activeStep !== undefined) {
      activeStep.value = conversation.activeStep
    }
    if (conversation.currentRole) {
      currentRole.value = conversation.currentRole
    }
    // 滚动到底部
    nextTick(() => {
      scrollToBottom()
    })
  }
}

// 滚动到最底部
const scrollToBottom = async () => {
  await nextTick()
  if (chatContentRef.value) {
    chatContentRef.value.scrollTop = chatContentRef.value.scrollHeight
  }
}

// 监听消息变化，自动滚动到底部
watch(() => messages.value.length, () => {
  scrollToBottom()
})

// 组件挂载时滚动到底部
onMounted(() => {
  scrollToBottom()
})

// 会话数据
const sessionData = reactive({
  sessionId: null,
  recordId: null,
  reportId: null,
  currentPhase: 'recorder' // recorder, analyst, therapist
})

// 计算属性
const inputPlaceholder = computed(() => {
  if (isAnalyzing.value || isProcessing.value) return '系统正在处理...'
  return '请输入内容...'
})

const analyzingText = computed(() => {
  switch (sessionData.currentPhase) {
    case 'analyst':
      return '分析师正在分析中...'
    case 'therapist':
      return '调理师正在生成疏导方案...'
    default:
      return '系统正在处理...'
  }
})

// 发送消息
const sendMessage = async (content) => {
  // 1. 添加用户消息
  const userMsg = {
    id: Date.now(),
    type: 'user',
    content,
    timestamp: new Date()
  }
  messages.value.push(userMsg)
  
  // 2. 根据当前阶段处理
  switch (sessionData.currentPhase) {
    case 'recorder':
      await handleRecorderConversation(content)
      break
    case 'analyst':
      // 分析阶段不需要用户输入，自动处理
      break
    case 'therapist':
      // 调理阶段不需要用户输入，自动处理
      break
  }
}

// 自动生成患者消息
const generatePatientMessage = async (messageType = 'greeting') => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/dialogue/patient`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        message_type: messageType,
        patient_id: 'test_patient'
      })
    })
    
    if (!response.ok) {
      throw new Error('获取患者消息失败')
    }
    
    const data = await response.json()
    return data.response
  } catch (error) {
    console.error('生成患者消息失败:', error)
    // 返回默认消息
    return '我最近感觉很不好，总是觉得很沮丧，对什么都提不起兴趣。'
  }
}

// 自动发送患者消息
const autoSendPatientMessage = async (messageType = 'greeting') => {
  const patientMessage = await generatePatientMessage(messageType)
  await sendMessage(patientMessage)
  
  // 等待一段时间后自动发送后续消息
  addTimeout(async () => {
    if (sessionData.currentPhase === 'recorder') {
      await autoSendPatientMessage('response_to_analysis')
    }
  }, 3000)
}

// 处理记录师对话
const handleRecorderConversation = async (content) => {
  isProcessing.value = true  // 记录师对话处理中
  try {
    const response = await fetch(`${API_BASE_URL}/recorder/converse`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        user_input: content,
        session_id: sessionData.sessionId
      })
    })
    
    if (!response.ok) {
      throw new Error('对话失败')
    }
    
    const data = await response.json()
    
    // 保存会话ID
    if (data.session_id) {
      sessionData.sessionId = data.session_id
    }
    
    // 添加记录师回复
    const recorderMsg = {
      id: Date.now() + 1,
      type: 'assistant',
      role: '记录师',
      content: data.llm_response,
      hint: '由AI生成对话内容，仅供参考。',
      timestamp: new Date()
    }
    messages.value.push(recorderMsg)
    
    // 检查是否需要触发分析
    if (data.next_action === 'trigger_analyst' && data.record_id) {
      sessionData.recordId = data.record_id
      await triggerAnalysis()
    }
  } catch (error) {
    console.error('对话失败:', error)
    // 添加错误消息
    const errorMsg = {
      id: Date.now() + 1,
      type: 'system',
      content: '对话失败，请重试。',
      timestamp: new Date()
    }
    messages.value.push(errorMsg)
  } finally {
    isProcessing.value = false
  }
}

// 触发分析
const triggerAnalysis = async () => {
  activeStep.value = 1
  sessionData.currentPhase = 'analyst'
  currentRole.value = '分析师'
  isAnalyzing.value = true
  
  try {
    // 请求分析
    const analyzeResponse = await fetch(`${API_BASE_URL}/analyst/analyze`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        record_id: sessionData.recordId,
        priority: 'high'
      })
    })
    
    if (!analyzeResponse.ok) {
      throw new Error('分析请求失败')
    }
    
    const analyzeData = await analyzeResponse.json()
    
    // 检查分析状态
    if (analyzeData.status === 'completed' && analyzeData.report_id) {
      sessionData.reportId = analyzeData.report_id
      await getAnalysisReport()
    } else {
      // 模拟分析完成（实际项目中可能需要轮询或等待回调）
      addTimeout(async () => {
        // 假设分析完成，获取报告
        await getAnalysisReport()
      }, 3000)
    }
  } catch (error) {
    console.error('分析失败:', error)
    // 添加错误消息
    const errorMsg = {
      id: Date.now() + 1,
      type: 'system',
      content: '分析失败，请重试。',
      timestamp: new Date()
    }
    messages.value.push(errorMsg)
    isAnalyzing.value = false
  }
}

// 获取分析报告
const getAnalysisReport = async () => {
  try {
    const reportResponse = await fetch(`${API_BASE_URL}/analyst/report/${sessionData.reportId}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json'
      }
    })
    
    if (!reportResponse.ok) {
      throw new Error('获取报告失败')
    }
    
    const reportData = await reportResponse.json()
    
    // 添加分析师报告
    const analystMsg = {
      id: Date.now() + 1,
      type: 'assistant',
      role: '分析师',
      content: `分析报告：\n\n认知行为分析：${reportData.content.cbt_summary}\n\n中医情志分析：${reportData.content.tcm_summary}`,
      hint: '由AI生成分析报告，仅供参考。',
      timestamp: new Date()
    }
    messages.value.push(analystMsg)
    
    // 延迟发送患者对分析结果的响应
    addTimeout(async () => {
      const patientResponse = await generatePatientMessage('response_to_analysis')
      const userMsg = {
        id: Date.now(),
        type: 'user',
        content: patientResponse,
        timestamp: new Date()
      }
      messages.value.push(userMsg)
      
      // 触发调理师生成疏导方案
      await generateTherapyPlan()
    }, 2000)
  } catch (error) {
    console.error('获取报告失败:', error)
    // 添加错误消息
    const errorMsg = {
      id: Date.now() + 1,
      type: 'system',
      content: '获取报告失败，请重试。',
      timestamp: new Date()
    }
    messages.value.push(errorMsg)
    isAnalyzing.value = false
  }
}

// 生成疏导方案
const generateTherapyPlan = async () => {
  activeStep.value = 2
  sessionData.currentPhase = 'therapist'
  currentRole.value = '调理师'
  
  try {
    const therapyResponse = await fetch(`${API_BASE_URL}/therapist/generate-plan`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        report_id: sessionData.reportId,
        user_preference: 'balanced'
      })
    })
    
    if (!therapyResponse.ok) {
      throw new Error('生成疏导方案失败')
    }
    
    const therapyData = await therapyResponse.json()
    
    // 添加调理师疏导方案
    const therapistMsg = {
      id: Date.now() + 1,
      type: 'assistant',
      role: '调理师',
      content: `疏导方案：\n\n${therapyData.therapy_plan}\n\n${therapyData.therapist_summary}`,
      hint: '由AI生成疏导方案，仅供参考。',
      timestamp: new Date()
    }
    messages.value.push(therapistMsg)
    
    // 获取策略模板
    await getTherapyStrategies()
    
    // 延迟发送患者对调理方案的响应
    addTimeout(async () => {
      const patientResponse = await generatePatientMessage('response_to_suggestion')
      const userMsg = {
        id: Date.now(),
        type: 'user',
        content: patientResponse,
        timestamp: new Date()
      }
      messages.value.push(userMsg)
      
      // 延迟发送患者的后续问题
      addTimeout(async () => {
        const patientFollowUp = await generatePatientMessage('follow_up')
        const followUpMsg = {
          id: Date.now(),
          type: 'user',
          content: patientFollowUp,
          timestamp: new Date()
        }
        messages.value.push(followUpMsg)
      }, 3000)
    }, 2000)
  } catch (error) {
    console.error('生成疏导方案失败:', error)
    // 添加错误消息
    const errorMsg = {
      id: Date.now() + 1,
      type: 'system',
      content: '生成疏导方案失败，请重试。',
      timestamp: new Date()
    }
    messages.value.push(errorMsg)
  } finally {
    isAnalyzing.value = false
  }
}

// 获取策略模板
const getTherapyStrategies = async () => {
  try {
    const strategiesResponse = await fetch(`${API_BASE_URL}/therapist/strategies`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json'
      }
    })
    
    if (!strategiesResponse.ok) {
      throw new Error('获取策略模板失败')
    }
    
    const strategiesData = await strategiesResponse.json()
    
    // 添加策略模板消息
    const strategiesMsg = {
      id: Date.now() + 1,
      type: 'assistant',
      role: '调理师',
      content: `可选干预策略：\n\n认知行为策略：${strategiesData.cbt_strategies.join('、')}\n\n中医策略：${strategiesData.tcm_strategies.join('、')}\n\n综合方法：${strategiesData.integrated_approaches.join('、')}`,
      hint: '由AI生成策略建议，仅供参考。',
      timestamp: new Date()
    }
    messages.value.push(strategiesMsg)
  } catch (error) {
    console.error('获取策略模板失败:', error)
    // 策略模板获取失败不影响主流程，仅记录错误
  }
}

// 处理消息点击
const handleMessageClick = (message) => {
  console.log('Message clicked:', message)
}

// 开始新对话
const startNewChat = () => {
  messages.value = []
  currentRole.value = '记录师'
  activeStep.value = 0
  
  // 重置会话数据
  sessionData.sessionId = null
  sessionData.recordId = null
  sessionData.reportId = null
  sessionData.currentPhase = 'recorder'
  
  // 初始化欢迎消息
  const welcomeMsg = {
    id: Date.now(),
    type: 'assistant',
    role: '记录师',
    content: '你好，我是记录师。请问你最近有什么情绪困扰需要倾诉吗？',
    hint: '由AI生成对话内容，仅供参考。',
    timestamp: new Date()
  }
  messages.value.push(welcomeMsg)
}

// 开始测试
const startTest = async () => {
  try {
    isProcessing.value = true
    
    // 检查session_id是否存在，不存在则先创建会话
    if (!sessionData.sessionId) {
      // 创建会话
      try {
        const createSessionResponse = await fetch(`${API_BASE_URL}/api/v1/conversations/create`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            type: 'multi-agent'
          })
        })
        
        if (!createSessionResponse.ok) {
          throw new Error('创建会话失败')
        }
        
        const sessionDataResponse = await createSessionResponse.json()
        sessionData.sessionId = sessionDataResponse.session_id
        console.log('会话创建成功:', sessionDataResponse)
      } catch (sessionError) {
        console.error('创建会话失败:', sessionError)
        alert('创建会话失败，请重试')
        isProcessing.value = false
        return
      }
    }
    
    isTesting.value = true
    
    // 调用后端API开始测试
    const response = await fetch(`${API_BASE_URL}/api/v1/conversations/start-test`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        session_id: sessionData.sessionId
      })
    })
    
    if (!response.ok) {
      throw new Error('开始测试失败')
    }
    
    const data = await response.json()
    console.log('开始测试成功:', data)
    
    // 开始自动发送患者消息
    autoSendPatientMessage('greeting')
    
    // 显示成功消息
    alert('测试已成功开始')
  } catch (error) {
    console.error('开始测试失败:', error)
    alert('开始测试失败，请重试')
    isTesting.value = false
  } finally {
    isProcessing.value = false
  }
}

// 暂停测试
const pauseTest = async () => {
  try {
    isProcessing.value = true
    
    // 清除所有定时器，停止前端自动消息发送
    clearAllTimeouts()
    
    // 调用后端API暂停测试
    const response = await fetch(`${API_BASE_URL}/api/v1/conversations/pause-test`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        session_id: sessionData.sessionId
      })
    })
    
    if (!response.ok) {
      throw new Error('暂停测试失败')
    }
    
    const data = await response.json()
    console.log('暂停测试成功:', data)
    
    // 显示成功消息
    alert('测试已成功暂停')
    isTesting.value = false
  } catch (error) {
    console.error('暂停测试失败:', error)
    alert('暂停测试失败，请重试')
  } finally {
    isProcessing.value = false
  }
}

// 结束对话
const endChat = async () => {
  // 检查是否有报告生成
  const hasReport = !!sessionData.reportId
  
  // 弹出确认对话框
  let confirmMessage = ''
  if (activeStep.value === 2) {
    // 建议阶段
    confirmMessage = '确定要结束对话吗？对话内容将被保存到对话记录中。'
  } else if (hasReport) {
    // 有报告生成
    confirmMessage = `确定要结束当前${activeStep.value === 0 ? '记录' : '分析'}阶段的对话吗？对话内容和报告将被保存到对话记录中。`
  } else {
    // 无报告生成
    confirmMessage = `确定要结束当前${activeStep.value === 0 ? '记录' : '分析'}阶段的对话吗？由于没有生成报告，本次对话将不会被保存。`
  }
  
  if (!confirm(confirmMessage)) {
    return
  }
  
  try {
    isProcessing.value = true
    
    // 清除所有定时器，停止异步操作
    clearAllTimeouts()
    
    // 调用后端API结束对话（即使API调用失败，也继续结束对话）
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/conversations/end`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          session_id: sessionData.sessionId,
          record_id: sessionData.recordId,
          report_id: sessionData.reportId,
          phase: sessionData.currentPhase,
          active_step: activeStep.value,
          save_conversation: hasReport
        })
      })
      
      if (!response.ok) {
        console.warn('后端API调用失败，但仍继续结束对话')
      } else {
        const data = await response.json()
        console.log('后端API调用成功:', data)
      }
    } catch (apiError) {
      console.warn('后端API调用出错，但仍继续结束对话:', apiError)
    }
    
    // 显示成功消息
    alert('对话已成功结束')
    
    // 重置测试状态
    isTesting.value = false
    
    // 开始新对话
    startNewChat()
  } catch (error) {
    console.error('结束对话失败:', error)
    alert('结束对话失败，请重试')
  } finally {
    isProcessing.value = false
  }
}

// 初始化示例数据
onMounted(() => {
  // 只有在没有从props传入对话数据时才初始化示例数据
  if (!props.conversationData) {
    // 首先添加记录师的欢迎消息
    messages.value = [
      {
        id: 1,
        type: 'assistant',
        role: '记录师',
        content: '你好，我是记录师。请问你最近有什么情绪困扰需要倾诉吗？',
        hint: '由AI生成对话内容，仅供参考。',
        timestamp: new Date()
      }
    ]
    // 移除自动发送患者消息的逻辑，改为由开始测试按钮触发
  }
})
</script>

<style scoped>
.chat-container {
  height: 100%;
  width: 100%;
  display: flex;
  flex-direction: column;
  background: transparent;
}

.chat-app {
  display: flex;
  flex-direction: column;
  height: 100%;
  width: 100%;
  /* 背景透明 */
  background: transparent;
}

/* 聊天内容区域 */
.chat-content {
  flex: 1;
  overflow-y: auto;
  margin-right: -8px;
  padding-right: 180px;
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
  /* margin-top: 20px; */
  /* padding-top: 20px; */
  margin-right: 180px;
  border-top: 1px solid rgba(238, 238, 238, 0.5);
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

/* 分析中状态提示 */
.analyzing-indicator {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 12px;
  margin: 10px 0;
  background-color: rgba(102, 126, 234, 0.1);
  border-radius: 8px;
  border: 1px solid rgba(102, 126, 234, 0.3);
  color: #667eea;
  font-size: 14px;
}

.analyzing-indicator .is-loading {
  animation: rotate 1s linear infinite;
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