<template>
  <div class="sidebar">
    <div class="sidebar-header">
      <div class="logo">
        <div class="logo-icon">
          <span class="logo-dot"></span>
          <span class="logo-line"></span>
        </div>
        <h1 class="logo-text">MindGarden</h1>
      </div>
      <p class="logo-subtitle">[CBT+中医情绪理论]</p>
    </div>
    
    <div class="sidebar-menu">
      <!-- 首页 -->
      <div 
        class="menu-item" 
        :class="{ active: activeItem === 'home' }" 
        @click="navigateTo('/')"
      >
        <i class="menu-icon home-icon"></i>
        <span class="menu-text">首页</span>
      </div>
      
      <!-- 对话记录下拉菜单 -->
      <div 
        class="menu-item dropdown" 
        :class="{ active: activeItem === 'history' }" 
        @click="toggleHistoryDropdown"
      >
        <i class="menu-icon favorite-icon"></i>
        <span class="menu-text">对话记录</span>
        <ArrowDown v-if="historyDropdownOpen" class="menu-icon dropdown-icon" />
        <ArrowUp v-else class="menu-icon dropdown-icon" />
        
        <!-- 下拉菜单内容 -->
        <div v-if="historyDropdownOpen" class="dropdown-menu">
          <div v-if="conversationHistory.length === 0" class="dropdown-empty">
            暂无对话记录
          </div>
          <div 
            v-for="(conversation, index) in conversationHistory" 
            :key="index"
            class="dropdown-item"
            :class="{ active: activeConversationId === conversation.id }"
          >
            <div class="dropdown-item-content" @click.stop="loadConversation(conversation)">
              <div class="dropdown-item-header">
                <span class="dropdown-item-title">{{ conversation.title || `对话 ${index + 1}` }}</span>
                <span class="dropdown-item-time">{{ formatTime(conversation.timestamp) }}</span>
              </div>
              <div class="dropdown-item-meta">
                <span class="dropdown-item-emotion">{{ conversation.emotion }}</span>
                <span class="dropdown-item-cognition">{{ conversation.cognitionType }}</span>
              </div>
            </div>
            <div class="dropdown-item-menu">
              <button 
                class="menu-button" 
                @click.stop="toggleConversationMenu(conversation.id)"
                :class="{ active: activeMenuId === conversation.id }"
              >
                <More class="menu-dots" />
              </button>
              <div 
                v-if="activeMenuId === conversation.id" 
                class="conversation-menu"
              >

                <div class="menu-item" @click.stop="pinConversation(conversation)">
                  <span class="menu-icon">📌</span>
                  <span>{{ conversation.pinned ? '取消置顶' : '置顶' }}</span>
                </div>

                <div class="menu-item delete" @click.stop="deleteConversation(conversation.id)">
                  <span class="menu-icon">🗑️</span>
                  <span>删除</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 预警提醒 -->
      <div 
        class="menu-item" 
        :class="{ active: activeItem === 'alerts' }" 
        @click="navigateTo('/alerts')"
      >
        <i class="menu-icon chart-icon"></i>
        <span class="menu-text">预警提醒</span>
        <el-badge 
          v-if="unacknowledgedAlertCount > 0" 
          :value="unacknowledgedAlertCount" 
          class="menu-badge"
        />
      </div>
      
      <!-- 情绪报告 -->
      <div 
        class="menu-item" 
        :class="{ active: activeItem === 'reports' }" 
        @click="navigateTo('/reports')"
      >
        <i class="menu-icon chart-icon"></i>
        <span class="menu-text">情绪报告</span>
      </div>
      
      <!-- 情绪记录 -->
      <div 
        class="menu-item" 
        :class="{ active: activeItem === 'mood' }" 
        @click="navigateTo('/mood')"
      >
        <i class="menu-icon chart-icon"></i>
        <span class="menu-text">情绪记录</span>
        <el-badge 
          v-if="emotionHasRemind" 
          is-dot 
          class="menu-badge"
        />
      </div>
        <!-- 问卷自查 -->
      <div 
        class="menu-item" 
        :class="{ active: activeItem === 'questionnaire' }" 
        @click="navigateTo('/questionnaire')"
      >
        <i class="menu-icon chart-icon"></i>
        <span class="menu-text">问卷自查</span>
        <el-badge 
          v-if="questionnaireDueCount > 0" 
          :value="questionnaireDueCount" 
          class="menu-badge"
        />
      </div>
      <!-- 多智能体测试对话 -->
      <div 
        class="menu-item" 
        :class="{ active: activeItem === 'multi-agent' }" 
        @click="navigateTo('multi-agent')"
      >
        <i class="menu-icon chart-icon"></i>
        <span class="menu-text">多智能体测试对话</span>
      </div>

    </div>
    
    <div class="sidebar-footer">    
      <div class="user-info">
        <div class="user-avatar" @click="openAvatarUpload">
          <img v-if="user.avatar" :src="user.avatar" alt="用户头像" class="avatar-image">
          <span v-else class="avatar-placeholder">{{ user.name ? user.name.charAt(0) : '小' }}</span>
        </div>
        <span class="user-name">{{ user.name ? user.name : '小小' }}</span>
        <div class="user-ellipsis" @click="toggleUserMenu">
          <span>...</span>
        </div>
        
        <!-- 用户菜单 -->
        <div v-if="userMenuOpen" class="user-menu">
          <div class="user-menu-item" @click="navigateTo('/user/profile')">
            <span>用户信息</span>
          </div>
          <div class="user-menu-item" @click="navigateTo('/user/settings')">
            <span>设置</span>
          </div>
          <div class="user-menu-divider"></div>
          <div class="user-menu-item" @click="logout">
            <span>退出账号</span>
          </div>
        </div>
        
        <!-- 头像上传输入 -->
        <input type="file" ref="avatarInput" accept="image/*" style="display: none" @change="handleAvatarUpload">
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ArrowUp, ArrowDown, More } from '@element-plus/icons-vue'
import { useQuestionnaireStore } from '@/stores/questionnaire'
import { useEmotionStore } from '@/stores/emotion'
import { useAlertStore } from '@/stores/alert'

export default {
  name: 'Sidebar',
  components: {
    ArrowUp,
    ArrowDown,
    More
  },
  emits: ['load-conversation', 'user-updated', 'select-function'],
  setup(props, { emit }) {
    const router = useRouter()
    const questionnaireStore = useQuestionnaireStore()
    const emotionStore = useEmotionStore()
    const alertStore = useAlertStore()
    const historyDropdownOpen = ref(false)
    const conversationHistory = ref([])
    const user = ref({ name: '', avatar: '' })
    const userMenuOpen = ref(false)
    const avatarInput = ref(null)
    
    // 问卷待测数量
    const questionnaireDueCount = computed(() => questionnaireStore.dueCount)
    
    // 情绪记录提醒
    const emotionHasRemind = computed(() => emotionStore.hasRemind)
    
    // 未确认预警数量
    const unacknowledgedAlertCount = computed(() => alertStore.unacknowledgedCount)
    
    // 计算当前路由
    const currentRoute = computed(() => router.currentRoute.value.path)
    
    // 当前激活的菜单项
    const activeItem = ref('')
    // 当前激活的对话记录ID
    const activeConversationId = ref(null)
    // 当前激活的菜单ID
    const activeMenuId = ref(null)
    
    // 监听路由变化，更新激活状态
    watch(() => currentRoute.value, (newRoute) => {
      updateActiveItem(newRoute)
    })
    
    // 更新激活的菜单项
    const updateActiveItem = (route) => {
      switch (route) {
        case '/':
          activeItem.value = 'home'
          break
        case '/alerts':
          activeItem.value = 'alerts'
          break
        case '/reports':
          activeItem.value = 'reports'
          break
        case '/mood':
          activeItem.value = 'mood'
          break
        case '/multi-agent-test':
          activeItem.value = 'multi-agent'
          break
        case '/questionnaire':
          activeItem.value = 'questionnaire'
          break
        default:
          activeItem.value = ''
      }
    }
    
    // 初始化激活状态
    onMounted(() => {
      loadUserData()
      updateActiveItem(currentRoute.value)
    })
    
    // 模拟用户数据
    const mockUser = {
      name: '用户',
      avatar: ''
    }
    
    // 模拟对话记录数据
    const mockConversationHistory = [
      {
        id: 1,
        title: '工作压力大',
        timestamp: new Date('2026-02-19T10:30:00'),
        emotion: '焦虑',
        cognitionType: '过度担忧',
        messages: [
          {
            id: 1,
            type: 'user',
            content: '最近工作压力很大，感觉喘不过气来',
            timestamp: new Date('2026-02-19T10:30:00')
          },
          {
            id: 2,
            type: 'assistant',
            role: '记录师',
            content: '我理解你的感受，工作压力确实会让人感到疲惫。你能具体说说是什么让你感到压力吗？',
            timestamp: new Date('2026-02-19T10:31:00')
          }
        ],
        currentPhase: 'recorder',
        activeStep: 0,
        currentRole: '记录师'
      },
      {
        id: 2,
        title: '人际关系问题',
        timestamp: new Date('2026-02-18T15:45:00'),
        emotion: '沮丧',
        cognitionType: '自我否定',
        messages: [
          {
            id: 1,
            type: 'user',
            content: '我和朋友吵架了，感觉很难过',
            timestamp: new Date('2026-02-18T15:45:00')
          },
          {
            id: 2,
            type: 'assistant',
            role: '记录师',
            content: '吵架确实会让人感到难过，特别是和朋友之间。能告诉我发生了什么吗？',
            timestamp: new Date('2026-02-18T15:46:00')
          }
        ],
        currentPhase: 'recorder',
        activeStep: 0,
        currentRole: '记录师'
      },
      {
        id: 3,
        title: '健康担忧',
        timestamp: new Date('2026-02-17T09:15:00'),
        emotion: '恐惧',
        cognitionType: '灾难化思维',
        messages: [
          {
            id: 1,
            type: 'user',
            content: '最近总是担心自己的健康问题',
            timestamp: new Date('2026-02-17T09:15:00')
          },
          {
            id: 2,
            type: 'assistant',
            role: '记录师',
            content: '健康担忧是很常见的，特别是当我们感到压力时。你具体在担心什么健康问题呢？',
            timestamp: new Date('2026-02-17T09:16:00')
          }
        ],
        currentPhase: 'recorder',
        activeStep: 0,
        currentRole: '记录师'
      }
    ]
    
    // 加载用户数据
    const loadUserData = () => {
      // 从本地存储加载用户数据
      const storedUser = localStorage.getItem('user')
      console.log('Stored user:', storedUser)
      if (storedUser) {
        try {
          const parsedUser = JSON.parse(storedUser)
          console.log('Parsed user:', parsedUser)
          // 检查用户对象的属性，使用username或name
          const userName = parsedUser.username || parsedUser.name
          console.log('Parsed user name:', userName)
          // 构建用户对象，确保有name属性
          user.value = {
            name: userName,
            avatar: parsedUser.avatar || ''
          }
          console.log('Loaded user:', user.value)
          console.log('User name after assignment:', user.value.name)
        } catch (error) {
          console.error('Failed to parse user data:', error)
          user.value = mockUser
        }
      } else {
        // 使用默认用户数据
        user.value = mockUser
        console.log('Using mock user:', user.value)
        console.log('Mock user name:', user.value.name)
      }
    }
    
    // API基础URL
    const API_BASE_URL = 'http://localhost:8000/api/v1/chat'
    
    // 加载对话记录
    const loadConversationHistory = async () => {
      try {
        // 从本地存储获取用户数据
        const storedUser = localStorage.getItem('user')
        if (!storedUser) {
          console.error('用户未登录')
          return
        }
        
        const userData = JSON.parse(storedUser)
        const userId = userData.id
        
        if (!userId) {
          console.error('用户ID不存在')
          return
        }
        
        // 调用API获取会话列表
        const response = await fetch(`${API_BASE_URL}/sessions`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ user_id: userId })
        })
        
        if (!response.ok) {
          throw new Error('获取会话列表失败')
        }
        
        const data = await response.json()
        console.log('会话列表响应:', data)
        
        // 转换API返回的数据格式
        conversationHistory.value = data.sessions.map(session => ({
          id: session.session_id,
          title: session.title,
          timestamp: new Date(session.created_at),
          emotion: session.emotional_response || '未知',
          cognitionType: session.thinking_traps ? session.thinking_traps.join(', ') : '无',
          lastMessage: session.last_message || '无消息'
        }))
        console.log("会话记录列表：",conversationHistory)
      } catch (error) {
        console.error('加载对话记录失败:', error)
        // 使用模拟数据
        conversationHistory.value = mockConversationHistory
      }
    }
    
    // 切换历史记录下拉菜单
    const toggleHistoryDropdown = () => {
      historyDropdownOpen.value = !historyDropdownOpen.value
      if (historyDropdownOpen.value) {
        loadConversationHistory()
        // 触发选择功能事件，设置为历史记录
        emit('select-function', 'history')
        // 更新激活状态
        activeItem.value = 'history'
      }
    }
    
    // 加载对话
    const loadConversation = async (conversation) => {
      try {
        console.log('加载对话:', conversation)
        
        // 从本地存储获取用户数据
        const storedUser = localStorage.getItem('user')
        if (!storedUser) {
          console.error('用户未登录')
          return
        }
        
        const userData = JSON.parse(storedUser)
        const userId = userData.id
        
        if (!userId) {
          console.error('用户ID不存在')
          return
        }
        
        // 调用API获取会话对话记录
        const response = await fetch(`${API_BASE_URL}/history`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            user_id: userId,
            session_id: conversation.id
          })
        })
        
        if (!response.ok) {
          throw new Error('获取对话记录失败')
        }
        
        const data = await response.json()
        console.log('对话记录响应:', data)
        
        // 转换API返回的消息格式
        const messages = data.dialogues.map(dialogue => ({
          id: dialogue.id,
          type: dialogue.role === 'user' ? 'user' : 'assistant',
          role: dialogue.role === 'user' ? 'user' : '小园',
          content: dialogue.content,
          timestamp: dialogue.created_at,
          hint: dialogue.role === 'assistant' ? '由AI生成对话内容，仅供参考' : undefined
        }))
        
        // 构建完整的对话对象
        const fullConversation = {
          ...conversation,
          messages: messages
        }
        
        // 打印对话内容到控制台
        console.log('对话内容:', fullConversation)
        console.log('对话消息:', messages)
        
        // 缓存对话内容到本地存储
        const conversationCache = JSON.parse(localStorage.getItem('conversationCache') || '{}')
        conversationCache[conversation.id] = fullConversation
        localStorage.setItem('conversationCache', JSON.stringify(conversationCache))
        console.log('对话内容已缓存:', conversation.id)
        
        // 触发事件，将对话数据传递给父组件
        emit('load-conversation', fullConversation)
        // 更新激活状态
        activeItem.value = 'history'
        // 更新当前激活的对话记录ID
        activeConversationId.value = conversation.id
        
      } catch (error) {
        console.error('加载对话失败:', error)
        // 尝试从缓存中加载对话内容
        const conversationCache = JSON.parse(localStorage.getItem('conversationCache') || '{}')
        const cachedConversation = conversationCache[conversation.id]
        
        if (cachedConversation) {
          console.log('从缓存中加载对话内容:', conversation.id)
          emit('load-conversation', cachedConversation)
        } else {
          // 直接使用传入的对话数据（可能没有消息）
          console.log('使用传入的对话数据:', conversation.id)
          emit('load-conversation', conversation)
        }
        
        // 更新激活状态
        activeItem.value = 'history'
        // 更新当前激活的对话记录ID
        activeConversationId.value = conversation.id
      }
    }
    
    // 格式化时间
    const formatTime = (timestamp) => {
      if (!timestamp) return ''
      const date = new Date(timestamp)
      return date.toLocaleString('zh-CN', {
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
      })
    }
    
    // 切换对话菜单
    const toggleConversationMenu = (conversationId) => {
      if (activeMenuId.value === conversationId) {
        activeMenuId.value = null
      } else {
        activeMenuId.value = conversationId
      }
    }
    
    // 重命名对话
    const renameConversation = (conversation) => {
      const newTitle = prompt('请输入新的对话标题:', conversation.title || `对话 ${conversationHistory.value.indexOf(conversation) + 1}`)
      if (newTitle && newTitle.trim()) {
        const index = conversationHistory.value.findIndex(c => c.id === conversation.id)
        if (index !== -1) {
          conversationHistory.value[index].title = newTitle.trim()
          console.log('对话已重命名:', newTitle.trim())
        }
      }
      activeMenuId.value = null
    }
    
    // 置顶对话
    const pinConversation = (conversation) => {
      const index = conversationHistory.value.findIndex(c => c.id === conversation.id)
      if (index !== -1) {
        conversationHistory.value[index].pinned = !conversationHistory.value[index].pinned
        // 重新排序，置顶的对话排在前面
        conversationHistory.value.sort((a, b) => {
          if (a.pinned && !b.pinned) return -1
          if (!a.pinned && b.pinned) return 1
          return new Date(b.timestamp) - new Date(a.timestamp)
        })
        console.log(`${conversation.title || `对话 ${index + 1}`}${conversationHistory.value[index].pinned ? '已置顶' : '已取消置顶'}`)
      }
      activeMenuId.value = null
    }
    
    // 分享对话
    const shareConversation = (conversation) => {
      // 这里可以实现分享功能，例如生成分享链接或复制到剪贴板
      console.log('分享对话:', conversation.title || `对话 ${conversationHistory.value.indexOf(conversation) + 1}`)
      alert('分享功能已触发，实际项目中可实现生成分享链接或复制到剪贴板')
      activeMenuId.value = null
    }
    
    // 删除对话
    const deleteConversation = async (conversationId) => {
      if (confirm('确定要删除这条对话记录吗？')) {
        try {
          // 从本地存储获取用户数据
          const storedUser = localStorage.getItem('user')
          if (!storedUser) {
            console.error('用户未登录')
            alert('用户未登录，无法删除对话记录')
            return
          }
          
          const userData = JSON.parse(storedUser)
          const userId = userData.id
          
          if (!userId) {
            console.error('用户ID不存在')
            alert('用户ID不存在，无法删除对话记录')
            return
          }
          
          console.log('用户id:', userId)
          console.log('对话id:', conversationId)
          
          // 调用API删除对话记录
          const response = await fetch('/api/v1/chat/delete-session', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json'
            },
            body: JSON.stringify({
              user_id: userId,
              session_id: conversationId
            })
          })
          
          if (response.ok) {
            const data = await response.json()
            console.log('对话删除成功:', data.message)
            
            // 从本地状态中删除
            const index = conversationHistory.value.findIndex(c => c.id === conversationId)
            if (index !== -1) {
              const deletedConversation = conversationHistory.value[index]
              conversationHistory.value.splice(index, 1)
              // 从缓存中删除
              const conversationCache = JSON.parse(localStorage.getItem('conversationCache') || '{}')
              delete conversationCache[conversationId]
              localStorage.setItem('conversationCache', JSON.stringify(conversationCache))
              console.log('对话已从本地删除:', deletedConversation.title || `对话 ${index + 1}`)
            }
          } else {
            const errorData = await response.json()
            console.error('删除对话失败:', errorData.detail || '未知错误')
            alert(`删除失败: ${errorData.detail || '未知错误'}`)
          }
        } catch (error) {
          console.error('删除对话时发生错误:', error)
          alert('删除对话时发生错误，请稍后重试')
        }
      }
      activeMenuId.value = null
    }
    
    // 导航到指定路径（改为触发事件）
    const navigateTo = (path) => {
      // 触发选择功能事件，而不是路由跳转
      let functionName = ''
      switch (path) {
        case '/':
          functionName = 'home'
          break
        case '/alerts':
          functionName = 'alerts'
          break
        case '/reports':
          functionName = 'reports'
          break
        case '/mood':
          functionName = 'mood'
          break
        case '/questionnaire':
          functionName = 'questionnaire'
          break
        case '/multi-agent-test':
        case 'multi-agent':
          functionName = 'multi-agent'
          break
        default:
          functionName = 'home'
      }
      emit('select-function', functionName)
      // 更新激活状态
      activeItem.value = functionName
    }
    
    // 切换用户菜单
    const toggleUserMenu = () => {
      userMenuOpen.value = !userMenuOpen.value
    }
    
    // 打开头像上传
    const openAvatarUpload = () => {
      avatarInput.value.click()
    }
    
    // 处理头像上传
    const handleAvatarUpload = (event) => {
      const file = event.target.files[0]
      if (file) {
        // 实际项目中，这里应该上传文件到服务器
        // 这里使用本地URL模拟
        const reader = new FileReader()
        reader.onload = (e) => {
          user.value.avatar = e.target.result
          // 保存到本地存储
          localStorage.setItem('user', JSON.stringify(user.value))
          emit('user-updated', user.value)
        }
        reader.readAsDataURL(file)
      }
    }
    
    // 退出登录
    const logout = () => {
      // 实际项目中，这里应该调用API注销用户
      localStorage.removeItem('access_token')
      localStorage.removeItem('user')
      user.value = { name: '', avatar: '' }
      userMenuOpen.value = false
      router.push('/login')
    }
    
    // 初始化
    onMounted(() => {
      loadUserData()
      // 检查待测问卷
      questionnaireStore.checkDueQuestionnaires()
      // 检查情绪记录提醒
      emotionStore.checkRemind()
      // 加载预警列表
      alertStore.fetchAlerts()
      // 连接预警WebSocket
      const user = JSON.parse(localStorage.getItem('user') || '{}')
      if (user.id) {
        alertStore.connectWebSocket(user.id)
      }
    })
    
    // 监听路由变化，确保登录后更新用户信息
    watch(() => router.currentRoute.value, () => {
      loadUserData()
    })
    
    return {
      historyDropdownOpen,
      conversationHistory,
      user,
      userMenuOpen,
      avatarInput,
      currentRoute,
      activeItem,
      activeConversationId,
      activeMenuId,
      toggleHistoryDropdown,
      loadConversation,
      formatTime,
      navigateTo,
      toggleUserMenu,
      openAvatarUpload,
      handleAvatarUpload,
      logout,
      toggleConversationMenu,
      renameConversation,
      pinConversation,
      shareConversation,
      deleteConversation,
      questionnaireDueCount,
      emotionHasRemind,
      unacknowledgedAlertCount
    }
  }
}
</script>

<style scoped>
.sidebar {
  background-color: #F9E0C9;
  height: 100%;
  display: flex;
  flex-direction: column;
  box-shadow: 2px 0 10px rgba(0, 0, 0, 0.1);
}

.sidebar-header {
  padding: 0 20px 30px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.1);
}

.logo {
  display: flex;
  align-items: center;
  margin-bottom: 5px;
}

.logo-icon {
  width: 30px;
  height: 30px;
  margin-right: 10px;
  position: relative;
}

.logo-dot {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background-color: #4CAF50;
}

.logo-line {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%) rotate(45deg);
  width: 18px;
  height: 2px;
  background-color: #4CAF50;
}

.logo-text {
  font-size: 20px;
  font-weight: bold;
  color: #333;
  margin: 0;
}

.logo-subtitle {
  font-size: 12px;
  color: #666;
  margin: 0;
  padding-left: 40px;
}

.sidebar-menu {
  flex: 1;
  padding: 20px 0;
}

.menu-item {
  display: flex;
  align-items: center;
  padding: 12px 20px;
  cursor: pointer;
  transition: all 0.3s ease;
  color: #666;
}

/* .menu-item:hover {
  background-color: rgba(76, 175, 80, 0.1);
  color: #4CAF50;
} */

.menu-item.active {
  background-color: #4CAF50;
  color: white;
  font-weight: 500;
}

.menu-icon {
  width: 20px;
  height: 20px;
  margin-right: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* 菜单角标样式 */
.menu-badge {
  margin-left: auto;
}

.menu-badge :deep(.el-badge__content) {
  background-color: #f56c6c;
  border: none;
}

/* 下拉菜单图标 */
::v-deep .dropdown-icon {
  margin-left: auto;
  margin-right: 0;
  font-size: 16px;
  transition: transform 0.3s ease;
  color: inherit;
}

.home-icon:before {
  content: "🏠";
  font-size: 16px;
}

.favorite-icon:before {
  content: "⭐";
  font-size: 16px;
}

.store-icon:before {
  content: "📊";
  font-size: 16px;
}

.chart-icon:before {
  content: "📊";
  font-size: 16px;
}

.user-icon:before {
  content: "👤";
  font-size: 16px;
}

/* 下拉菜单样式 */
.dropdown {
  position: relative;
}



.dropdown-item {
  padding: 12px 20px; 
  cursor: pointer;
  transition: all 0.3s ease;
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
  position: relative;
  display: flex;
  justify-content: space-between;
  align-items: center;
  z-index: 1;
  overflow: visible;
}

.dropdown-item-content {
  flex: 1;
  cursor: pointer;
  min-width: 0;
}

.dropdown-item:hover {
  background-color: rgba(76, 175, 80, 0.1);
}

.dropdown-item.active {
  background-color: rgba(76, 175, 80, 0.5);
  color: white;
  font-weight: 500;
}

/* 菜单按钮样式 */

.dropdown-item.active ::v-deep .menu-dots {
  color: white;
}

/* 菜单按钮容器样式 */
.dropdown-item-menu {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  margin-left: 10px;
  width: 24px;
  height: 24px;
}

/* 菜单按钮样式 */
.menu-button {
  background: none;
  border: none;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 4px;
  transition: all 0.3s ease;
  opacity: 0.7;
  visibility: visible;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
}

.menu-button:hover {
  background-color: rgba(0, 0, 0, 0.05);
  opacity: 1;
}

/* 三点菜单图标样式 */
::v-deep .menu-dots {
  font-size: 16px;
  color: #666;
  line-height: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  transform: rotate(90deg);
  transition: all 0.3s ease;
}

.dropdown-item.active ::v-deep .menu-dots {
  color: white;
}

/* 对话菜单样式 */
.conversation-menu {
  position: absolute;
  top: 0; 
  right: 5px;
  background-color: white;
  border: 1px solid rgba(0, 0, 0, 0.1);
  border-radius: 4px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  z-index: 1000;
  max-width: 60px;
  margin: 0;
}

.conversation-menu .menu-item {
  padding: 4px 6px;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  font-size: 10px;
}

.conversation-menu .menu-item:hover {
  background-color: #f5f5f5;
}

.conversation-menu .menu-item.delete {
  color: #ff4d4f;
}

.conversation-menu .menu-item.delete:hover {
  background-color: rgba(255, 77, 79, 0.1);
}

.conversation-menu .menu-icon {
  font-size: 10px;
}

/* 滚动条样式 */
.dropdown-menu {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  background-color: #F9E0C9;
  border: 1px solid rgba(0, 0, 0, 0.1);
  border-top: none;
  border-radius: 0 0 4px 4px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  z-index: 1;
  max-height: calc(100vh - 180px);
  overflow-y: auto;
  transition: all 0.3s ease;
  overflow-x: visible;
}

.dropdown-menu:hover {
  overflow-y: auto;
}

/* 滚动条样式 */
.dropdown-menu::-webkit-scrollbar {
  width: 4px;
}

.dropdown-menu::-webkit-scrollbar-track {
  background: rgba(241, 241, 241, 0.3);
  border-radius: 4px;
}

.dropdown-menu::-webkit-scrollbar-thumb {
  background: rgba(1, 146, 28, 0.3);
  border-radius: 4px;
  transition: background 0.3s ease;
}

.dropdown-menu::-webkit-scrollbar-thumb:hover {
  background: rgba(15, 158, 2, 0.6);
}

.dropdown-item-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
}

.dropdown-item-title {
  font-size: 14px;
  font-weight: 500;
  color: #333;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 150px;
}

.dropdown-item-time {
  font-size: 12px;
  color: #999;
  white-space: nowrap;
}

.dropdown-item-meta {
  display: flex;
  gap: 12px;
  font-size: 12px;
}

.dropdown-item-emotion {
  color: #667eea;
  background-color: rgba(102, 126, 234, 0.1);
  padding: 2px 8px;
  border-radius: 10px;
}

.dropdown-item-cognition {
  color: #fa709a;
  background-color: rgba(250, 112, 154, 0.1);
  padding: 2px 8px;
  border-radius: 10px;
}

.dropdown-empty {
  padding: 20px;
  text-align: center;
  color: #999;
  font-size: 14px;
}

.sidebar-footer {
  padding: 20px;
  border-top: 1px solid rgba(0, 0, 0, 0.1);
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.user-info {
  display: flex;
  align-items: center;
}

.user-avatar {
  width: 30px;
  height: 30px;
  border-radius: 50%;
  background-color: #4CAF50;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 10px;
  border: 1px solid #4CAF50;
}

.avatar-placeholder {
  color: white;
  font-size: 14px;
  font-weight: bold;
}

.user-name {
  font-size: 14px;
  color: #333;
  margin-right: 10px;
}

.user-ellipsis {
  margin-left: 180px;
  font-size: 14px;
  color: #999;
  cursor: pointer;
  transition: color 0.3s ease;
}

.user-ellipsis:hover {
  color: #4CAF50;
}

.avatar-image {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  object-fit: cover;
}

.user-menu {
  position: absolute;
  bottom: 100%;
  right: 0;
  background-color: white;
  border: 1px solid rgba(0, 0, 0, 0.1);
  border-radius: 4px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  z-index: 100;
  min-width: 120px;
  margin-bottom: 10px;
}

.user-menu-item {
  padding: 10px 15px;
  cursor: pointer;
  transition: background-color 0.3s ease;
  font-size: 14px;
  color: #333;
}

.user-menu-item:hover {
  background-color: #f5f5f5;
}

.user-menu-divider {
  height: 1px;
  background-color: rgba(0, 0, 0, 0.1);
  margin: 5px 0;
}

.user-info {
  position: relative;
  display: flex;
  align-items: center;
}

.user-avatar {
  cursor: pointer;
  transition: transform 0.3s ease;
}

.user-avatar:hover {
  transform: scale(1.05);
}
</style>