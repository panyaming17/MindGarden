// stores/chat.js
import { defineStore } from 'pinia'
import {
  messageTypes,
  roles,
  createUserMessage,
  createAssistantMessage,
  createSystemMessage,
  createTypingMessage
} from '../types/message.types'
import {
  conversationStatus,
  createConversation
} from '../types/conversation.types'

export const useChatStore = defineStore('chat', {
  state: () => ({
    conversations: [],
    currentConversation: null,
    aiRole: roles.XIAOXIAO,
    isAnalyzing: false
  }),
  
  getters: {
    currentMessages: (state) => {
      return state.currentConversation ? state.currentConversation.messages : []
    },
    
    hasActiveConversation: (state) => {
      return state.currentConversation !== null
    }
  },
  
  actions: {
    // 初始化对话
    initConversation() {
      const initialConversation = createConversation('新对话', [
        createSystemMessage('欢迎使用聊天助手，我是你的AI助手小小！')
      ])
      this.conversations.push(initialConversation)
      this.currentConversation = initialConversation
    },
    
    // 发送消息
    sendMessage(content) {
      if (!this.currentConversation) {
        this.initConversation()
      }
      
      // 添加用户消息
      const userMessage = createUserMessage(content)
      this.currentConversation.messages.push(userMessage)
      
      // 更新对话时间
      this.currentConversation.updatedAt = new Date()
      
      // 模拟AI回复
      setTimeout(() => {
        const typingMessage = createTypingMessage(this.aiRole)
        this.currentConversation.messages.push(typingMessage)
        
        // 移除打字状态并添加实际回复
        setTimeout(() => {
          const assistantMessage = createAssistantMessage(
            `我收到了你的消息：${content}`,
            this.aiRole
          )
          
          // 移除打字消息
          this.currentConversation.messages = this.currentConversation.messages.filter(
            msg => !msg.isTyping
          )
          
          // 添加回复消息
          this.currentConversation.messages.push(assistantMessage)
          this.currentConversation.updatedAt = new Date()
        }, 1000)
      }, 500)
    },
    
    // 切换角色
    switchRole(role) {
      if (Object.values(roles).includes(role)) {
        this.aiRole = role
        if (this.currentConversation) {
          this.currentConversation.currentRole = role
        }
      }
    },
    
    // 创建新对话
    createNewConversation(title) {
      const newConversation = createConversation(title || '新对话')
      this.conversations.push(newConversation)
      this.currentConversation = newConversation
    },
    
    // 切换对话
    switchConversation(conversationId) {
      const conversation = this.conversations.find(c => c.id === conversationId)
      if (conversation) {
        this.currentConversation = conversation
      }
    }
  }
})