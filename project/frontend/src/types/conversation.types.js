// 对话状态定义
export const conversationStatus = {
  ACTIVE: 'active',
  COMPLETED: 'completed',
  ARCHIVED: 'archived'
}

// 对话数据结构类
export class Conversation {
  constructor({
    id,
    title,
    messages = [],
    status = conversationStatus.ACTIVE,
    createdAt = new Date(),
    updatedAt = new Date(),
    currentRole = '记录师'
  }) {
    this.id = id
    this.title = title
    this.messages = messages
    this.status = status
    this.createdAt = createdAt
    this.updatedAt = updatedAt
    this.currentRole = currentRole
  }
}

// 验证对话数据结构
export function validateConversation(conversation) {
  return (
    typeof conversation.id !== 'undefined' &&
    typeof conversation.title === 'string' &&
    Array.isArray(conversation.messages) &&
    Object.values(conversationStatus).includes(conversation.status) &&
    conversation.createdAt instanceof Date &&
    conversation.updatedAt instanceof Date
  )
}

// 创建新对话
export function createConversation(title, initialMessages = []) {
  return new Conversation({
    id: Date.now(),
    title,
    messages: initialMessages
  })
}

// 更新对话
export function updateConversation(conversation, updates) {
  return new Conversation({
    ...conversation,
    ...updates,
    updatedAt: new Date()
  })
}