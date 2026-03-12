<template>
  <div class="chat-input-container">
        <!-- 操作按钮 -->
    <div class="action-buttons">
      <button 
        @click="startNewChat"
        class="btn-new-chat"
        :disabled="isLoading"
      >
        新对话
      </button>
      <button 
        @click="startTest"
        class="btn-start-test"
        :disabled="isLoading || isTesting"
      >
        开始测试
      </button>
      <button 
        @click="pauseTest"
        class="btn-pause-test"
        :disabled="isLoading || !isTesting"
      >
        暂停测试
      </button>
      <button 
        @click="endCurrentChat"
        class="btn-end-chat"
        :disabled="isLoading"
      >
        结束对话
      </button>
    </div>
    <!-- 输入区域和发送按钮 -->
    <div class="input-with-send">
      <!-- 文本输入区域 -->
      <textarea
        ref="textareaRef"
        v-model="inputText"
        :placeholder="placeholder"
        :disabled="isLoading"
        @input="handleInput"
        @keydown.enter.exact.prevent="handleSend"
        class="message-input"
        rows="3"
      ></textarea>
      
      <!-- 字符计数器 -->
      <div class="char-counter">
        {{ charCount }}/10000
      </div>
      
      <!-- 发送按钮 -->
      <button
        @click="handleSend"
        :disabled="isLoading || !inputText.trim()"
        class="btn-send"
      >
        <span v-if="isLoading">
          <span class="loading-dots">分析中</span>
        </span>
        <el-icon v-else>
          <Position />
        </el-icon>
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, nextTick } from 'vue'
import { Position } from '@element-plus/icons-vue'

const emit = defineEmits(['send-message', 'start-new-chat', 'end-chat', 'start-test', 'pause-test'])

const props = defineProps({
  isLoading: Boolean,
  isTesting: {
    type: Boolean,
    default: false
  },
  placeholder: {
    type: String,
    default: '请输入内容...'
  }
})

const inputText = ref('')
const textareaRef = ref(null)

// 字符计数
const charCount = computed(() => inputText.value.length)

// 输入处理
const handleInput = () => {
  if (charCount.value > 10000) {
    inputText.value = inputText.value.slice(0, 10000)
  }
  
  // 自动调整高度
  nextTick(() => {
    if (textareaRef.value) {
      textareaRef.value.style.height = 'auto'
      textareaRef.value.style.height = Math.min(
        textareaRef.value.scrollHeight,
        200
      ) + 'px'
    }
  })
}

// 发送消息
const handleSend = () => {
  if (!inputText.value.trim() || props.isLoading) return
  
  emit('send-message', inputText.value.trim())
  inputText.value = ''
  
  // 重置文本框高度
  if (textareaRef.value) {
    textareaRef.value.style.height = 'auto'
  }
}

// 开始新对话
const startNewChat = () => {
  if (props.isLoading) return
  
  if (inputText.value.trim() && !confirm('开始新对话将清除当前输入，确定吗？')) {
    return
  }
  
  inputText.value = ''
  emit('start-new-chat')
}

// 结束对话
const endCurrentChat = () => {
  if (props.isLoading) return
  
  // 发送结束对话事件
  emit('end-chat')
}

// 开始测试
const startTest = () => {
  if (props.isLoading || props.isTesting) return
  
  // 发送开始测试事件
  emit('start-test')
}

// 暂停测试
const pauseTest = () => {
  if (props.isLoading || !props.isTesting) return
  
  // 发送暂停测试事件
  emit('pause-test')
}
</script>

<style scoped>
.chat-input-container {
  padding: 16px;
  background: transparent;
  border-top: 1px solid rgba(238, 238, 238, 0.5);
}

.char-counter {
  position: absolute;
  left: 16px;
  bottom: 12px;
  font-size: 12px;
  color: rgba(153, 153, 153, 0.8);
  pointer-events: none; /* 防止干扰输入 */
}

.input-with-send {
  position: relative;
  margin-bottom: 12px;
}

.message-input {
  width: 100%;
  padding: 12px 12px 32px 16px;
  border: 2px solid #A5D6A7;
  border-radius: 15px;
  resize: none;
  font-size: 14px;
  font-family: inherit;
  box-sizing: border-box;
  transition: border-color 0.3s;
  background-color: #FFFFFF;
  padding-right: 60px; /* 为右侧的发送按钮留出空间 */
}

.btn-send {
  position: absolute;
  right: 12px;
  bottom: 12px;
  background: linear-gradient(135deg, rgba(79, 172, 254, 0.9) 0%, rgba(0, 242, 254, 0.9) 100%);
  color: white;
  font-weight: bold;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 8px 16px;
  border-radius: 20px;
  border: none;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.3s;
}

.btn-send .el-icon {
  font-size: 16px;
}

.message-input:focus {
  outline: none;
  border-color: #81C784;
}

.message-input:disabled {
  background: #F9F9F9;
  cursor: not-allowed;
  border-color: #e0e0e0;
}

.action-buttons {
  display: flex;
  justify-content: flex-start;
  margin-bottom: 10px;
}

.btn-new-chat {
  padding: 8px 24px;
  border-radius: 20px;
  border: none;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.3s;
  background: #81C784;
  color: rgb(30, 30, 30);
}

.btn-new-chat:hover:not(:disabled) {
  background:#81C784;
}

.btn-start-test {
  padding: 8px 24px;
  border-radius: 20px;
  border: none;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.3s;
  background: #4FC3F7;
  color: rgb(30, 30, 30);
  margin-left: 10px;
}

.btn-start-test:hover:not(:disabled) {
  background: #29B6F6;
}

.btn-pause-test {
  padding: 8px 24px;
  border-radius: 20px;
  border: none;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.3s;
  background: #FFD54F;
  color: rgb(30, 30, 30);
  margin-left: 10px;
}

.btn-pause-test:hover:not(:disabled) {
  background: #FFC107;
}

.btn-end-chat {
  padding: 8px 24px;
  border-radius: 20px;
  border: none;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.3s;
  background: #FF8A80;
  color: rgb(30, 30, 30);
  margin-left: 10px;
}

.btn-end-chat:hover:not(:disabled) {
  background: #FF5252;
}

.btn-end-chat:disabled,
.btn-new-chat:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-send:hover:not(:disabled) {
  opacity: 0.9;
  transform: translateY(-1px);
}

.btn-send:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.loading-dots::after {
  content: '...';
  animation: dots 1.5s steps(4, end) infinite;
}

@keyframes dots {
  0%, 20% { content: ''; }
  40% { content: '.'; }
  60% { content: '..'; }
  80%, 100% { content: '...'; }
}
</style>