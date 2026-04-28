// 消息类型定义
export const messageTypes = {
  USER: 'user',
  ASSISTANT: 'assistant',
  SYSTEM: 'system'
}

// 角色类型定义
export const roles = {
  RECORDER: '记录师',
  ANALYST: '分析师',
  TREATMENT: '调理师'
}

// 消息数据结构类
export class Message {
  constructor({
    id,
    type,
    content,
    timestamp = new Date(),
    role,
    isTyping = false,
    isLoading = false
  }) {
    this.id = id
    this.type = type
    this.content = content
    this.timestamp = timestamp
    this.role = role
    this.isTyping = isTyping
    this.isLoading = isLoading
  }
}

// 验证消息数据结构
export function validateMessage(message) {
  return (
    typeof message.id !== 'undefined' &&
    Object.values(messageTypes).includes(message.type) &&
    typeof message.content === 'string' &&
    message.timestamp instanceof Date
  )
}

// 创建用户消息
export function createUserMessage(content) {
  return new Message({
    id: Date.now(),
    type: messageTypes.USER,
    content
  })
}

// 创建助理消息
export function createAssistantMessage(content, role = roles.XIAOXIAO) {
  return new Message({
    id: Date.now(),
    type: messageTypes.ASSISTANT,
    content,
    role
  })
}

// 创建系统消息
export function createSystemMessage(content) {
  return new Message({
    id: Date.now(),
    type: messageTypes.SYSTEM,
    content
  })
}

// 创建打字中消息
export function createTypingMessage(role = roles.XIAOXIAO) {
  return new Message({
    id: Date.now(),
    type: messageTypes.ASSISTANT,
    content: '',
    role,
    isTyping: true
  })
}

// 创建加载中消息
export function createLoadingMessage(role = roles.XIAOXIAO) {
  return new Message({
    id: Date.now(),
    type: messageTypes.ASSISTANT,
    content: '',
    role,
    isLoading: true
  })
}