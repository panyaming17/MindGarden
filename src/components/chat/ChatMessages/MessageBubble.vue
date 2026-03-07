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
            <el-tooltip content="复制" placement="bottom" :effect="'dark'" :offset="[0, 5]">
              <el-icon class="action-icon" size="16"><CopyDocument /></el-icon>
            </el-tooltip>
            <el-tooltip content="重新生成" placement="bottom" :effect="'dark'" :offset="[0, 5]">
              <el-icon class="action-icon" size="16"><RefreshRight /></el-icon>
            </el-tooltip>
            <el-tooltip content="点赞" placement="bottom" :effect="'dark'" :offset="[0, 5]">
              <img src="/src/assets/icons/ThumbsUp.svg" class="action-icon" alt="点赞" />
            </el-tooltip>
            <el-tooltip content="点踩" placement="bottom" :effect="'dark'" :offset="[0, 5]">
              <img src="/src/assets/icons/ThumbsDown.svg" class="action-icon" alt="点踩" />
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
      <!-- 消息内容和时间 -->
      <div class="message-content-wrapper">
        <!-- 消息内容 -->
        <div class="message-content">
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
import { computed } from 'vue'
import { CopyDocument, RefreshRight } from '@element-plus/icons-vue'

const props = defineProps({
  message: {
    type: Object,
    required: true
  },
  currentRole: {
    type: String,
    default: '记录师'
  }
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
  if (props.message.type === 'system') {
    switch(props.currentRole) {
      case '记录师': return `${base} recorder-avatar`
      case '分析师': return `${base} analyst-avatar`
      case '调理师': return `${base} recorder-avatar`
      default: return `${base} recorder-avatar`
    }
  }
  return `${base} ${props.message.role}-avatar`
})

const getAvatarText = computed(() => {
  if (props.message.type === 'user') {
    const userInfo = getUserInfo()
    return userInfo.name.charAt(0) || '我'
  }
  if (props.message.type === 'system') {
    switch(props.currentRole) {
      case '记录师': return '记'
      case '分析师': return '分'
      case '调理师': return '调'
      default: return 'AI'
    }
  }
  switch(props.message.role) {
    case '记录师': return '记'
    case '分析师': return '分'
    case '调理师': return '调'
    default: return 'AI'
  }
})

const getAvatarImage = computed(() => {
  // 使用 assets 目录下的图片作为头像
  if (props.message.type === 'assistant' || props.message.type === 'system') {
    return '/src/assets/agent-avatar.png'
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
  if (props.message.type === 'system') return props.currentRole
  return props.message.role
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