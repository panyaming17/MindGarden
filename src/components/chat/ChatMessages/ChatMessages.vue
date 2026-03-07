<template>
  <div class="chat-messages">
    <MessageBubble 
      v-for="(message, index) in messages" 
      :key="index"
      :message="message"
      :current-role="currentRole"
    />
    <TypingIndicator v-if="isTyping" />
  </div>
</template>

<script setup>
import { ref, defineProps } from 'vue'
import MessageBubble from './MessageBubble.vue'
import TypingIndicator from './TypingIndicator.vue'

const props = defineProps({
  messages: {
    type: Array,
    default: () => []
  },
  currentRole: {
    type: String,
    default: '记录师'
  }
})

const { currentRole } = props

const isTyping = ref(false)
</script>

<style scoped>
.chat-messages {
  width: 100%;
  background-color: transparent;
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-height: 0;
}

.chat-messages::-webkit-scrollbar {
  width: 4px;
}

.chat-messages::-webkit-scrollbar-track {
  background: rgba(241, 241, 241, 0.5);
  border-radius: 3px;
}

.chat-messages::-webkit-scrollbar-thumb {
  background: rgba(193, 193, 193, 0.5);
  border-radius: 3px;
}

.chat-messages::-webkit-scrollbar-thumb:hover {
  background: rgba(161, 161, 161, 0.7);
}

/* 父组件穿透选择器，确保 MessageBubble 组件的样式正确应用 */
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
</style>