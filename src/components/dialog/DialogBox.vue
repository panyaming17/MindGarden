<template>
  <div class="dialog-box">
    <div class="dialog-header">
      <h3 class="dialog-title">对话交流</h3>
      <p class="dialog-subtitle">与小园进行对话交流，了解你的情绪状态</p>
    </div>
    
    <div class="dialog-messages">
      <div 
        v-for="(message, index) in messages" 
        :key="index"
        class="message-item"
        :class="message.type"
      >
        <div class="message-avatar">
          <span class="avatar-text">{{ message.avatar }}</span>
        </div>
        <div class="message-content">
          <div class="message-text">{{ message.text }}</div>
          <div class="message-time">{{ message.time }}</div>
        </div>
      </div>
    </div>
    
    <div class="dialog-input">
      <textarea 
        v-model="inputMessage"
        class="input-textarea"
        placeholder="请输入你的想法或感受..."
        @keydown.enter.exact="sendMessage"
      ></textarea>
      <button class="send-button" @click="sendMessage">
        <span>发送</span>
      </button>
    </div>
  </div>
</template>

<script>
export default {
  name: 'DialogBox',
  data() {
    return {
      inputMessage: '',
      messages: [
        {
          type: 'ai',
          avatar: '园',
          text: '你好！我是小园，很高兴能和你交流。请告诉我你今天过得怎么样？有什么特别的事情想分享吗？',
          time: '刚刚'
        }
      ]
    }
  },
  methods: {
    sendMessage() {
      if (!this.inputMessage.trim()) return
      
      this.messages.push({
        type: 'user',
        avatar: '我',
        text: this.inputMessage,
        time: this.getCurrentTime()
      })
      
      this.inputMessage = ''
      
      setTimeout(() => {
        this.messages.push({
          type: 'ai',
          avatar: '园',
          text: '我理解你的感受。能告诉我更多关于这件事的细节吗？',
          time: '刚刚'
        })
      }, 1000)
    },
    getCurrentTime() {
      const now = new Date()
      const hours = now.getHours().toString().padStart(2, '0')
      const minutes = now.getMinutes().toString().padStart(2, '0')
      return `${hours}:${minutes}`
    }
  }
}
</script>

<style scoped>
.dialog-box {
  display: flex;
  flex-direction: column;
  height: 100%;
  background-color: transparent;
}

.dialog-header {
  text-align: center;
  margin-bottom: 30px;
  padding-bottom: 20px;
  border-bottom: 1px solid #E0E0E0;
}

.dialog-title {
  font-size: 24px;
  color: #333;
  margin: 0 0 10px 0;
}

.dialog-subtitle {
  font-size: 14px;
  color: #999;
  margin: 0;
}

.dialog-messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  background-color: #FAFAFA;
  border-radius: 8px;
  margin-bottom: 20px;
}

.message-item {
  display: flex;
  margin-bottom: 20px;
}

.message-item.user {
  flex-direction: row-reverse;
}

.message-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background-color: #4CAF50;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-weight: bold;
  font-size: 14px;
  margin: 0 15px;
  flex-shrink: 0;
}

.message-item.user .message-avatar {
  background-color: #2196F3;
}

.message-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
}

.message-item.user .message-content {
  align-items: flex-end;
}

.message-text {
  background-color: white;
  padding: 12px 16px;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  max-width: 70%;
  word-wrap: break-word;
}

.message-item.user .message-text {
  background-color: #2196F3;
  color: white;
}

.message-time {
  font-size: 12px;
  color: #999;
  margin-top: 5px;
}

.dialog-input {
  display: flex;
  gap: 10px;
}

.input-textarea {
  flex: 1;
  border: 1px solid #E0E0E0;
  border-radius: 8px;
  padding: 12px;
  font-size: 14px;
  resize: none;
  min-height: 80px;
  font-family: inherit;
  outline: none;
  transition: border-color 0.3s ease;
}

.input-textarea:focus {
  border-color: #4CAF50;
}

.send-button {
  padding: 12px 24px;
  background-color: #4CAF50;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
}

.send-button:hover {
  background-color: #45a049;
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(76, 175, 80, 0.3);
}
</style>