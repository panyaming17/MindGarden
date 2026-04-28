<template>
  <div :class="['message-bubble', message.type, message.role]">
    <!-- AI消息：头像在左侧 -->
    <div v-if="message.type === 'assistant' || message.type === 'system'" class="message-container assistant">
      <!-- 头像部分：头像和名称 -->
      <div class="avatar-section">
        <div class="avatar" :class="getAvatarClass">
          <img v-if="getAvatarImage" :src="getAvatarImage" :alt="displayRole" />
          <span v-else>{{ getAvatarText }}</span>
        </div>
        <div class="role-name">{{ displayRole }}</div>
      </div>
      
      <!-- 消息内容和时间 -->
      <div class="message-content-wrapper">
        <!-- 消息内容 -->
        <div class="message-content">
          <p>
            {{ message.content }}
            <!-- 提示文字（如"由AI生成对话内容，仅供参考"） -->
            <span v-if="message.hint" class="message-hint">
              {{ message.hint }}
            </span>
          </p>
        </div>
        
        <!-- 操作按钮和时间戳容器 -->
        <div class="message-footer">
          <!-- 操作按钮：复制、重新生成、点赞、点踩 -->
          <div class="message-actions">
            <el-tooltip content="复制" placement="bottom" effect="dark" :offset="5">
              <el-icon class="action-icon" size="16" @click="copyMessage"><CopyDocument /></el-icon>
            </el-tooltip>
            <el-tooltip content="重新生成" placement="bottom" effect="dark" :offset="5">
              <el-icon class="action-icon" size="16" @click="regenerateMessage"><RefreshRight /></el-icon>
            </el-tooltip>
            <el-tooltip content="点赞" placement="bottom" effect="dark" :offset="5">
              <img 
                src="/src/assets/icons/ThumbsUp.svg" 
                class="action-icon" 
                :class="{ 'active': feedbackType === 'like' }"
                alt="点赞" 
                @click="handleFeedback('like')"
              />
            </el-tooltip>
            <el-tooltip content="点踩" placement="bottom" effect="dark" :offset="5">
              <img 
                src="/src/assets/icons/ThumbsDown.svg" 
                class="action-icon" 
                :class="{ 'active': feedbackType === 'dislike' }"
                alt="点踩" 
                @click="handleFeedback('dislike')"
              />
            </el-tooltip>
          </div>
          
          <!-- 时间戳：在气泡右下角 -->
          <div class="timestamp">
            {{ formatTime(message.timestamp) }}
          </div>
        </div>
      </div>
    </div>
    
    <!-- 用户消息：头像在右侧 -->
    <div v-else class="message-container user">
      <!-- 撤回按钮（在消息左侧） -->
      <div v-if="canWithdraw" class="withdraw-btn-wrapper">
        <el-tooltip content="撤回" placement="top" effect="dark" :offset="5">
          <div class="withdraw-btn" @click="withdrawMessage">
            <el-icon size="16"><Back /></el-icon>
          </div>
        </el-tooltip>
      </div>
      
      <!-- 消息内容和时间 -->
      <div class="message-content-wrapper">
        <!-- 消息内容 -->
        <div class="message-content user">
          <p>{{ message.content }}</p>
          
          <!-- 提示文字（如"由A生成对话内容"） -->
          <div v-if="message.hint" class="message-hint">
            {{ message.hint }}
          </div>
        </div>
        
        <!-- 时间戳：在气泡左下角 -->
        <div class="timestamp user-timestamp">
          {{ formatTime(message.timestamp) }}
        </div>
      </div>
      
      <!-- 头像部分：头像和名称 -->
      <div class="avatar-section user-avatar-section">
        <div class="avatar" :class="getAvatarClass">
          <img v-if="getAvatarImage" :src="getAvatarImage" :alt="displayRole" />
          <span v-else>{{ getAvatarText }}</span>
        </div>
        <div class="role-name">{{ displayRole }}</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { CopyDocument, RefreshRight, Back } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

const props = defineProps({
  message: {
    type: Object,
    required: true
  },
  currentRole: {
    type: String,
    default: '小园'
  }
})

const emit = defineEmits(['copy', 'regenerate', 'feedback', 'withdraw'])

// 反馈类型（like/dislike）
const feedbackType = ref(null)

// 复制消息
const copyMessage = async () => {
  try {
    await navigator.clipboard.writeText(props.message.content)
    ElMessage.success('消息已复制到剪贴板')
    emit('copy', props.message)
  } catch (err) {
    console.error('复制失败:', err)
    ElMessage.error('复制失败，请手动复制')
  }
}

// 重新生成消息
const regenerateMessage = () => {
  emit('regenerate', props.message)
}

// 处理反馈（点赞/点踩）
const handleFeedback = (type) => {
  if (feedbackType.value === type) {
    // 取消反馈
    feedbackType.value = null
  } else {
    feedbackType.value = type
  }
  emit('feedback', { message: props.message, type: feedbackType.value })
}

// 撤回消息
const withdrawMessage = () => {
  emit('withdraw', props.message)
}

// 判断是否可以撤回（2分钟内）
const WITHDRAW_TIME_LIMIT = 2 * 60 * 1000 // 2分钟（毫秒）
const canWithdraw = computed(() => {
  if (props.message.type !== 'user') return false
  if (!props.message.timestamp) return false
  const messageTime = new Date(props.message.timestamp).getTime()
  const now = Date.now()
  return (now - messageTime) < WITHDRAW_TIME_LIMIT
})

// 从localStorage获取用户信息
const getUserInfo = () => {
  const storedUser = localStorage.getItem('user')
  if (storedUser) {
    try {
      const user = JSON.parse(storedUser)
      return {
        name: user.username || user.name || '用户',
        avatar: user.avatar || null
      }
    } catch (error) {
      console.error('Failed to parse user data:', error)
      return { name: '用户', avatar: null }
    }
  }
  return { name: '用户', avatar: null }
}

// 计算属性
const getAvatarClass = computed(() => {
  const base = 'avatar'
  if (props.message.type === 'user') return `${base} user-avatar`
  if (props.message.type === 'assistant' || props.message.type === 'system') return `${base} xiaoxiao-avatar`
  return base
})

const getAvatarText = computed(() => {
  if (props.message.type === 'user') {
    const userInfo = getUserInfo()
    return userInfo.name.charAt(0) || '我'
  }
  return '园'
})

const getAvatarImage = computed(() => {
  // 使用 assets 目录下的图片作为头像
  if (props.message.type === 'assistant' || props.message.type === 'system') {
    // 使用带hash的编译后文件名
    return '/assets/agent-avatar-B871T6O8.png'
  }
  // 用户头像
  const userInfo = getUserInfo()
  return userInfo.avatar || null
})

const displayRole = computed(() => {
  if (props.message.type === 'user') {
    const userInfo = getUserInfo()
    return userInfo.name || '用户'
  }
  // 智能体显示名称为"小园"
  return '小园'
})

// 格式化时间
const formatTime = (timestamp) => {
  return new Date(timestamp).toLocaleTimeString('zh-CN', {
    hour: '2-digit',
    minute: '2-digit'
  })
}
</script>

<style scoped>
/* 基础样式 */
.message-bubble {
  margin: 16px 0;
  max-width: 92%;
  background: transparent !important;
}

/* 用户消息靠右 */
.message-bubble.user {
  margin-left: auto;
  background: transparent !important;
}

/* AI消息靠左 */
.message-bubble.assistant {
  margin-right: auto;
  background: transparent !important;
}

/* 消息容器 */
.message-container {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  background: transparent !important;
}

/* AI消息容器：头像在左 */
.message-container.assistant {
  justify-content: flex-start;
  background: transparent !important;
}

/* 用户消息容器：头像在右 */
.message-container.user {
  justify-content: flex-end;
  background: transparent !important;
}

/* 头像部分：头像和名称垂直排列 */
.avatar-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  background: transparent !important;
  padding: 4px;
  min-width: 50px;
}

/* 用户头像部分：确保头像在名称上面 */
.user-avatar-section {
  flex-direction: column;
  align-items: center;
  background: transparent !important;
}

/* 头像 */
.avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 16px;
  font-weight: bold;
  flex-shrink: 0;
  overflow: hidden;
  border: 2px solid rgba(255, 255, 255, 0.2);
  line-height: 40px;
  text-align: center;
}

/* 头像图片 */
.avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: 50%;
}

/* 角色名称 */
.role-name {
  font-size: 12px;
  color: rgba(102, 102, 102, 0.8);
  text-align: center;
  white-space: nowrap;
  background: transparent;
}

/* 消息内容包装器：内容和时间 */
.message-content-wrapper {
  display: flex;
  flex-direction: column;
  background: transparent !important;
  padding: 0;
  margin: 0;
  min-width: 0;
  width: fit-content;
  max-width: 100%;
}

/* 消息内容 */
.message-content {
  background: rgba(255, 255, 255, 0.9);
  padding: 12px 16px;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.05);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  min-width: 0;
  position: relative;
  word-wrap: break-word;
  overflow-wrap: break-word;
  white-space: normal;
  word-break: break-word;
  width: fit-content;
  max-width: 100%;
  min-width: 100px;
}

/* 用户消息内容 */
.message-content.user {
  background: rgba(102, 126, 234, 0.1);
  border: 1px solid rgba(102, 126, 234, 0.3);
  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.1);
  word-wrap: break-word;
  overflow-wrap: break-word;
  white-space: normal;
  word-break: break-word;
  width: fit-content;
  max-width: 100%;
  min-width: 10px;
}

/* 消息文本 */
.message-content p {
  margin: 0;
  line-height: 1.4;
  word-wrap: break-word;
  color: #333;
  background: transparent !important;
}

/* 角色标签 */
.role-tag {
  display: inline-block;
  padding: 2px 8px;
  background: transparent !important;
  border-radius: 10px;
  font-size: 12px;
  margin-bottom: 8px;
  color: rgba(102, 102, 102, 0.8);
}

/* 消息提示 */
.message-hint {
  margin-left: 8px;
  font-size: 12px;
  color: rgba(153, 153, 153, 0.8);
  background: transparent !important;
  font-style: italic;
}

/* 操作按钮和时间戳容器 */
.message-footer {
  margin-top: 8px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: transparent !important;
}

/* 操作按钮容器 */
.message-actions {
  margin-left: 4px;
  display: flex;
  align-items: center;
  gap: 12px;
  opacity: 0; 
  visibility: hidden;
  transition: all 0.3s ease;
  background: transparent !important;
}

/* 鼠标悬停时显示操作按钮 */
.message-content-wrapper:hover .message-actions {
  opacity: 1;
  visibility: visible;
}

/* 操作按钮样式 */
.action-icon {
  width: 16px;
  height: 16px;
  cursor: pointer;
  color: #303030;
  transition: all 0.2s ease;
  background: transparent !important;
  stroke-width: 1.5px;
}

.action-icon:hover {
  color: rgba(102, 126, 234, 0.8);
  transform: scale(1.1);
}

.action-icon.active {
  color: #4CAF50;
  transform: scale(1.1);
}

.action-icon.active img {
  filter: brightness(1.2);
}

/* 图片按钮样式 */
.action-icon img {
  width: 16px;
  height: 16px;
  background: transparent !important;
}

/* 确保操作按钮在消息气泡底部正确显示 */
.message-actions {
  flex-shrink: 0;
  align-self: flex-start;
}

/* 时间戳：在气泡右下角 */
.timestamp {
  font-size: 11px;
  color: rgba(153, 153, 153, 0.8);
  text-align: right;
  margin-top: 4px;
  padding-right: 4px;
  background: transparent !important;
}

/* 用户消息时间戳：在气泡左下角 */
.user-timestamp {
  text-align: left;
  padding-left: 4px;
  background: transparent !important;
}

/* 撤回按钮容器（在消息左侧） */
.withdraw-btn-wrapper {
  display: flex;
  align-items: flex-start;
  padding-top: 12px;
  opacity: 0;
  visibility: hidden;
  transition: all 0.3s ease;
  flex-shrink: 0;
}

/* 鼠标悬停时显示撤回按钮 */
.message-container.user:hover .withdraw-btn-wrapper {
  opacity: 1;
  visibility: visible;
}

/* 撤回按钮样式 */
.withdraw-btn {
  width: 24px;
  height: 24px;
  border-radius: 6px;
  border: 1.5px solid #999;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: #666;
  transition: all 0.2s ease;
  background: transparent;
}

.withdraw-btn:hover {
  color: rgba(102, 126, 234, 0.9);
  border-color: rgba(102, 126, 234, 0.9);
  transform: scale(1.1);
}

/* 头像样式 */
.user-avatar {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.xiaoxiao-avatar {
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
}

.recorder-avatar {
  background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
}

.analyst-avatar {
  background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
}

/* 确保背景透明（穿透选择器） */
:deep(.message-bubble) {
  background: transparent !important;
}

:deep(.message-container) {
  background: transparent !important;
}

:deep(.avatar-section) {
  background: transparent !important;
}

:deep(.user-avatar-section) {
  background: transparent !important;
}

:deep(.message-content-wrapper) {
  background: transparent !important;
}

:deep(.message-content) {
  background: rgba(255, 255, 255, 0.9) !important;
  box-shadow: 0 2px 8px rgba(0,0,0,0.05) !important;
  backdrop-filter: blur(10px) !important;
  border: 1px solid rgba(255, 255, 255, 0.2) !important;
}

:deep(.message-content.user) {
  background: rgba(102, 126, 234, 0.1) !important;
  border: 1px solid rgba(102, 126, 234, 0.3) !important;
  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.1) !important;
}

:deep(.timestamp) {
  background: transparent !important;
}

:deep(.user-timestamp) {
  background: transparent !important;
  text-align: left !important;
  padding-left: 4px !important;
  padding-right: 0 !important;
}

:deep(.role-name) {
  background: transparent !important;
}

:deep(.role-tag) {
  background: transparent !important;
}

:deep(.message-hint) {
  background: transparent !important;
}

:deep(.avatar img) {
  background: transparent !important;
}

:deep(.message-content p) {
  background: transparent !important;
}

/* 确保头像背景不透明 */
:deep(.user-avatar) {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
  color: white !important;
}

:deep(.xiaoxiao-avatar) {
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%) !important;
  color: white !important;
}

:deep(.recorder-avatar) {
  background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%) !important;
  color: white !important;
}

:deep(.analyst-avatar) {
  background: linear-gradient(135deg, #fa709a 0%, #fee140 100%) !important;
  color: white !important;
}

:deep(.avatar span) {
  background: transparent !important;
  color: white !important;
}

/* 响应式调整 */
@media (max-width: 768px) {
  .message-bubble {
    max-width: 90%;
    margin: 12px 0;
    background: transparent !important;
  }
  
  .avatar {
    width: 36px;
    height: 36px;
    font-size: 14px;
    line-height: 36px;
  }
  
  .role-name {
    font-size: 11px;
  }
  
  .timestamp {
    font-size: 10px;
  }
  
  .message-content {
    padding: 10px 14px;
  }
  
  .avatar-section {
    min-width: 40px;
    background: transparent !important;
  }
}
</style>