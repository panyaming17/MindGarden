<template>
  <div 
    class="sidebar" 
    :class="{ 'collapsed': isCollapsed, 'resizing': isResizing, 'drawer-open': drawerOpen }"
    :style="{ width: isCollapsed ? collapsedWidth + 'px' : sidebarWidth + 'px' }"
  >
    <!-- 折叠/展开按钮 -->
    <div class="sidebar-toggle" @click="toggleSidebar" :title="isCollapsed ? '展开侧边栏' : '收起侧边栏'">
      <el-icon :size="20">
        <Fold v-if="!isCollapsed" />
        <Expand v-else />
      </el-icon>
    </div>

    <!-- 拖拽调整宽度的手柄 -->
    <div 
      class="resize-handle" 
      @mousedown="startResize"
      v-show="!isCollapsed"
      title="拖动调整宽度"
    ></div>

    <div class="sidebar-header">
      <div class="logo">
        <div class="logo-icon">
          <span class="logo-dot"></span>
          <span class="logo-line"></span>
        </div>
        <h1 class="logo-text" v-show="!isCollapsed">MindGarden</h1>
      </div>
      <p class="logo-subtitle" v-show="!isCollapsed">[CBT+中医情绪理论]</p>
    </div>
    
    <div class="sidebar-menu">
      <!-- 首页 -->
      <div 
        class="menu-item" 
        :class="{ active: activeItem === 'home' }" 
        @click="navigateTo('/')"
        :title="isCollapsed ? '首页' : ''"
      >
        <el-icon class="menu-icon" :size="20"><HomeFilled /></el-icon>
        <span class="menu-text" v-show="!isCollapsed">首页</span>
      </div>
      
      <!-- 对话记录下拉菜单 -->
      <div 
        class="menu-item dropdown" 
        :class="{ active: activeItem === 'history' }" 
        @click="toggleHistoryDropdown"
        :title="isCollapsed ? '对话记录' : ''"
      >
        <el-icon class="menu-icon" :size="20"><ChatDotRound /></el-icon>
        <span class="menu-text" v-show="!isCollapsed">对话记录</span>
        <el-icon v-if="!isCollapsed" class="dropdown-arrow" :class="{ 'is-open': historyDropdownOpen }" :size="14">
          <ArrowDown />
        </el-icon>
      </div>
      
      <!-- 下拉菜单内容 -->
      <div v-if="historyDropdownOpen && !isCollapsed" class="dropdown-menu">
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
              @click.stop="toggleConversationMenu(conversation.id, $event)"
              @mouseenter.stop="onMenuButtonEnter(conversation.id, $event)"
              @mouseleave.stop="onMenuButtonLeave"
              :class="{ active: activeMenuId === conversation.id }"
            >
              <el-icon class="menu-dots"><More /></el-icon>
            </button>
            <div
              v-if="activeMenuId === conversation.id"
              class="conversation-menu"
              :style="menuPositionStyle"
              @mouseenter.stop="onMenuPanelEnter"
              @mouseleave.stop="onMenuPanelLeave"
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
      
      <!-- 预警提醒 -->
      <div 
        class="menu-item" 
        :class="{ active: activeItem === 'alerts' }" 
        @click="navigateTo('/alerts')"
        :title="isCollapsed ? '预警提醒' : ''"
      >
        <el-icon class="menu-icon" :size="20"><BellFilled /></el-icon>
        <span class="menu-text" v-show="!isCollapsed">预警提醒</span>
        <el-badge 
          v-if="unacknowledgedAlertCount > 0 && !isCollapsed" 
          :value="unacknowledgedAlertCount" 
          class="menu-badge"
        />
        <el-badge 
          v-if="unacknowledgedAlertCount > 0 && isCollapsed" 
          is-dot 
          class="menu-badge-collapsed"
        />
      </div>
      
      <!-- 情绪报告 -->
      <div 
        class="menu-item" 
        :class="{ active: activeItem === 'reports' }" 
        @click="navigateTo('/reports')"
        :title="isCollapsed ? '情绪报告' : ''"
      >
        <el-icon class="menu-icon" :size="20"><DataLine /></el-icon>
        <span class="menu-text" v-show="!isCollapsed">情绪报告</span>
      </div>
      
      <!-- 情绪记录 -->
      <div 
        class="menu-item" 
        :class="{ active: activeItem === 'mood' }" 
        @click="navigateTo('/mood')"
        :title="isCollapsed ? '情绪记录' : ''"
      >
        <el-icon class="menu-icon" :size="20"><Calendar /></el-icon>
        <span class="menu-text" v-show="!isCollapsed">情绪记录</span>
        <el-badge 
          v-if="emotionHasRemind && !isCollapsed" 
          is-dot 
          class="menu-badge"
        />
        <el-badge 
          v-if="emotionHasRemind && isCollapsed" 
          is-dot 
          class="menu-badge-collapsed"
        />
      </div>
      
      <!-- 问卷自查 -->
      <div 
        class="menu-item" 
        :class="{ active: activeItem === 'questionnaire' }" 
        @click="navigateTo('/questionnaire')"
        :title="isCollapsed ? '问卷自查' : ''"
      >
        <el-icon class="menu-icon" :size="20"><Document /></el-icon>
        <span class="menu-text" v-show="!isCollapsed">问卷自查</span>
        <el-badge 
          v-if="questionnaireDueCount > 0 && !isCollapsed" 
          :value="questionnaireDueCount" 
          class="menu-badge"
        />
        <el-badge 
          v-if="questionnaireDueCount > 0 && isCollapsed" 
          is-dot 
          class="menu-badge-collapsed"
        />
      </div>
    </div>
    
    <div class="sidebar-footer">    
      <div class="user-info">
        <div class="user-avatar" @click="openAvatarUpload">
          <img v-if="user.avatar" :src="user.avatar" alt="用户头像" class="avatar-image">
          <span v-else class="avatar-placeholder">{{ user.name ? user.name.charAt(0) : '小' }}</span>
        </div>
        <div class="user-details" v-show="!isCollapsed">
          <span class="user-name">{{ user.name ? user.name : '小小' }}</span>
          <div class="user-ellipsis" @click="toggleUserMenu">
            <span>...</span>
          </div>
        </div>
        
        <!-- 用户菜单 -->
        <div v-if="userMenuOpen && !isCollapsed" class="user-menu">
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
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { 
  ArrowDown, More, 
  HomeFilled, ChatDotRound, BellFilled, 
  DataLine, Calendar, Document, 
  Connection, UserFilled,
  Fold, Expand
} from '@element-plus/icons-vue'
import { useQuestionnaireStore } from '@/stores/questionnaire'
import { useEmotionStore } from '@/stores/emotion'
import { useAlertStore } from '@/stores/alert'

export default {
  name: 'Sidebar',
  components: {
    ArrowDown,
    More,
    HomeFilled,
    ChatDotRound,
    BellFilled,
    DataLine,
    Calendar,
    Document,
    Connection,
    UserFilled,
    Fold,
    Expand
  },
  emits: ['load-conversation', 'user-updated', 'select-function', 'width-change', 'collapse-change'],
  setup(props, { emit }) {
    const router = useRouter()
    const questionnaireStore = useQuestionnaireStore()
    const emotionStore = useEmotionStore()
    const alertStore = useAlertStore()
    
    // 侧边栏宽度控制
    const isCollapsed = ref(false)
    const sidebarWidth = ref(280) // 默认宽度
    const collapsedWidth = ref(64) // 收起后的宽度
    const minWidth = ref(200) // 最小宽度
    const maxWidth = ref(400) // 最大宽度
    const isResizing = ref(false)
    
    // 原始宽度（用于拖拽计算）
    let startX = 0
    let startWidth = 0
    
    // 展开/收起侧边栏
    const toggleSidebar = () => {
      isCollapsed.value = !isCollapsed.value
      // 保存状态到 localStorage
      localStorage.setItem('sidebarCollapsed', isCollapsed.value)
      // 通知父组件宽度变化
      const effectiveWidth = isCollapsed.value ? collapsedWidth.value : sidebarWidth.value
      emit('width-change', effectiveWidth)
      emit('collapse-change', isCollapsed.value)
    }
    
    // 开始拖拽调整宽度
    const startResize = (e) => {
      isResizing.value = true
      startX = e.clientX
      startWidth = sidebarWidth.value
      
      document.addEventListener('mousemove', onResize)
      document.addEventListener('mouseup', stopResize)
      document.body.style.cursor = 'ew-resize'
      document.body.style.userSelect = 'none'
    }
    
    // 拖拽中
    const onResize = (e) => {
      if (!isResizing.value) return
      
      const diff = e.clientX - startX
      let newWidth = startWidth + diff
      
      // 限制范围
      newWidth = Math.max(minWidth.value, Math.min(maxWidth.value, newWidth))
      
      sidebarWidth.value = newWidth
      emit('width-change', newWidth)
    }
    
    // 停止拖拽
    const stopResize = () => {
      isResizing.value = false
      document.removeEventListener('mousemove', onResize)
      document.removeEventListener('mouseup', stopResize)
      document.body.style.cursor = ''
      document.body.style.userSelect = ''
      
      // 保存宽度到 localStorage
      localStorage.setItem('sidebarWidth', sidebarWidth.value)
    }
    
    // 其他状态
    const historyDropdownOpen = ref(false)
    const conversationHistory = ref([])
    const user = ref({ name: '', avatar: '' })
    const userMenuOpen = ref(false)
    const avatarInput = ref(null)
    const drawerOpen = ref(false)  // 抽屉打开状态
    
    // 计算属性
    const questionnaireDueCount = computed(() => questionnaireStore.dueCount)
    const emotionHasRemind = computed(() => emotionStore.hasRemind)
    const unacknowledgedAlertCount = computed(() => alertStore.unacknowledgedCount)
    const currentRoute = computed(() => router.currentRoute.value.path)
    const activeItem = ref('')
    const activeConversationId = ref(null)
    const activeMenuId = ref(null)
    const menuPositionStyle = ref({})
    
    let hoverShowTimer = null
    let hideTimer = null
    const isHoveringMenu = ref(false)
    const hoveringConversationId = ref(null)
    
    // 监听路由变化
    watch(() => currentRoute.value, (newRoute) => {
      updateActiveItem(newRoute)
    })
    
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
        case '/questionnaire':
          activeItem.value = 'questionnaire'
          break
        default:
          activeItem.value = ''
      }
    }
    
    // 初始化
    onMounted(() => {
      loadUserData()
      updateActiveItem(currentRoute.value)
      
      // 从 localStorage 恢复侧边栏状态
      const savedCollapsed = localStorage.getItem('sidebarCollapsed')
      const savedWidth = localStorage.getItem('sidebarWidth')
      
      if (savedCollapsed !== null) {
        isCollapsed.value = savedCollapsed === 'true'
      }
      if (savedWidth) {
        const width = parseInt(savedWidth)
        if (width >= minWidth.value && width <= maxWidth.value) {
          sidebarWidth.value = width
        }
      }
      
      // 监听抽屉打开状态
      window.addEventListener('storage', handleStorageChange)
      checkDrawerState()
    })
    
    // 处理 localStorage 变化
    const handleStorageChange = (event) => {
      if (event.key === 'historyDrawerOpen') {
        drawerOpen.value = event.newValue === 'true'
      }
    }
    
    // 检查抽屉状态
    const checkDrawerState = () => {
      drawerOpen.value = localStorage.getItem('historyDrawerOpen') === 'true'
    }
    
    onUnmounted(() => {
      clearAllTimers()
      document.removeEventListener('mousemove', onResize)
      document.removeEventListener('mouseup', stopResize)
      window.removeEventListener('storage', handleStorageChange)
    })
    
    // 用户数据加载
    const loadUserData = () => {
      const storedUser = localStorage.getItem('user')
      if (storedUser) {
        try {
          const parsedUser = JSON.parse(storedUser)
          const userName = parsedUser.username || parsedUser.name
          user.value = {
            name: userName,
            avatar: parsedUser.avatar || ''
          }
        } catch (error) {
          user.value = { name: '用户', avatar: '' }
        }
      } else {
        user.value = { name: '用户', avatar: '' }
      }
    }
    
    // 对话记录相关方法
    const API_BASE_URL = 'http://localhost:8000/api/v1/chat'
    
    const loadConversationHistory = async () => {
      try {
        const storedUser = localStorage.getItem('user')
        if (!storedUser) return
        
        const userData = JSON.parse(storedUser)
        const userId = userData.id
        if (!userId) return
        
        const response = await fetch(`${API_BASE_URL}/sessions`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ user_id: userId })
        })
        
        if (!response.ok) throw new Error('获取会话列表失败')
        
        const data = await response.json()
        conversationHistory.value = data.sessions.map(session => ({
          id: session.session_id,
          title: session.title,
          timestamp: new Date(session.created_at),
          emotion: session.emotional_response || '未知',
          cognitionType: session.thinking_traps || '无',
          lastMessage: session.last_message || '无消息'
        }))
      } catch (error) {
        console.error('加载对话记录失败:', error)
        conversationHistory.value = []
      }
    }
    
    const toggleHistoryDropdown = () => {
      historyDropdownOpen.value = !historyDropdownOpen.value
      if (historyDropdownOpen.value) {
        loadConversationHistory()
        emit('select-function', 'history')
        activeItem.value = 'history'
      }
    }
    
    const loadConversation = async (conversation) => {
      try {
        const storedUser = localStorage.getItem('user')
        if (!storedUser) return
        
        const userData = JSON.parse(storedUser)
        const userId = userData.id
        if (!userId) return
        
        const response = await fetch(`${API_BASE_URL}/history`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            user_id: userId,
            session_id: conversation.id
          })
        })
        
        if (!response.ok) throw new Error('获取对话记录失败')
        
        const data = await response.json()
        const messages = data.dialogues.map(dialogue => ({
          id: dialogue.id,
          type: dialogue.role === 'user' ? 'user' : 'assistant',
          role: dialogue.role === 'user' ? 'user' : '小园',
          content: dialogue.content,
          timestamp: dialogue.created_at,
          hint: dialogue.role === 'assistant' ? '由AI生成对话内容，仅供参考' : undefined
        }))
        
        const fullConversation = {
          ...conversation,
          messages: messages
        }
        
        const conversationCache = JSON.parse(localStorage.getItem('conversationCache') || '{}')
        conversationCache[conversation.id] = fullConversation
        localStorage.setItem('conversationCache', JSON.stringify(conversationCache))
        
        emit('load-conversation', fullConversation)
        activeItem.value = 'history'
        activeConversationId.value = conversation.id
        
      } catch (error) {
        console.error('加载对话失败:', error)
        const conversationCache = JSON.parse(localStorage.getItem('conversationCache') || '{}')
        const cachedConversation = conversationCache[conversation.id]
        
        if (cachedConversation) {
          emit('load-conversation', cachedConversation)
        } else {
          emit('load-conversation', conversation)
        }
        
        activeItem.value = 'history'
        activeConversationId.value = conversation.id
      }
    }
    
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
    
    // 菜单控制方法
    const showMenu = (conversationId, event) => {
      activeMenuId.value = conversationId
      isHoveringMenu.value = false
      if (event && event.target) {
        const button = event.target.closest('.menu-button')
        if (button) {
          const rect = button.getBoundingClientRect()
          menuPositionStyle.value = {
            position: 'fixed',
            bottom: `${window.innerHeight - rect.top + 4}px`,
            right: `${window.innerWidth - rect.right + 5}px`,
            zIndex: 99999
          }
        }
      }
    }

    const hideMenu = () => {
      activeMenuId.value = null
      menuPositionStyle.value = {}
      isHoveringMenu.value = false
      hoveringConversationId.value = null
    }

    const clearAllTimers = () => {
      if (hoverShowTimer) {
        clearTimeout(hoverShowTimer)
        hoverShowTimer = null
      }
      if (hideTimer) {
        clearTimeout(hideTimer)
        hideTimer = null
      }
    }

    const toggleConversationMenu = (conversationId, event) => {
      clearAllTimers()
      if (activeMenuId.value === conversationId) {
        hideMenu()
      } else {
        showMenu(conversationId, event)
      }
    }

    const onMenuButtonEnter = (conversationId, event) => {
      clearAllTimers()
      hoveringConversationId.value = conversationId
      if (activeMenuId.value === conversationId) return
      hoverShowTimer = setTimeout(() => {
        showMenu(conversationId, event)
        hoverShowTimer = null
      }, 1000)
    }

    const onMenuButtonLeave = () => {
      if (hoverShowTimer) {
        clearTimeout(hoverShowTimer)
        hoverShowTimer = null
      }
      hoveringConversationId.value = null
      if (activeMenuId.value && !isHoveringMenu.value) {
        hideTimer = setTimeout(() => {
          if (!isHoveringMenu.value) {
            hideMenu()
          }
          hideTimer = null
        }, 200)
      }
    }

    const onMenuPanelEnter = () => {
      clearAllTimers()
      isHoveringMenu.value = true
    }

    const onMenuPanelLeave = () => {
      isHoveringMenu.value = false
      hideTimer = setTimeout(() => {
        if (!isHoveringMenu.value) {
          hideMenu()
        }
        hideTimer = null
      }, 100)
    }
    
    // 对话操作方法
    const pinConversation = (conversation) => {
      const index = conversationHistory.value.findIndex(c => c.id === conversation.id)
      if (index !== -1) {
        conversationHistory.value[index].pinned = !conversationHistory.value[index].pinned
        conversationHistory.value.sort((a, b) => {
          if (a.pinned && !b.pinned) return -1
          if (!a.pinned && b.pinned) return 1
          return new Date(b.timestamp) - new Date(a.timestamp)
        })
      }
      activeMenuId.value = null
    }
    
    const deleteConversation = async (conversationId) => {
      if (confirm('确定要删除这条对话记录吗？')) {
        try {
          const storedUser = localStorage.getItem('user')
          if (!storedUser) return
          
          const userData = JSON.parse(storedUser)
          const userId = userData.id
          if (!userId) return
          
          const response = await fetch('/api/v1/chat/delete-session', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              user_id: userId,
              session_id: conversationId
            })
          })
          
          if (response.ok) {
            const index = conversationHistory.value.findIndex(c => c.id === conversationId)
            if (index !== -1) {
              conversationHistory.value.splice(index, 1)
              const conversationCache = JSON.parse(localStorage.getItem('conversationCache') || '{}')
              delete conversationCache[conversationId]
              localStorage.setItem('conversationCache', JSON.stringify(conversationCache))
            }
          }
        } catch (error) {
          console.error('删除对话失败:', error)
        }
      }
      activeMenuId.value = null
    }
    
    // 导航
    const navigateTo = (path) => {
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
        default:
          functionName = 'home'
      }
      
      emit('select-function', functionName)
      activeItem.value = functionName
      
      if (path !== '/' && router.currentRoute.value.path !== path) {
        router.replace(path)
      }
    }
    
    // 用户菜单
    const toggleUserMenu = () => {
      userMenuOpen.value = !userMenuOpen.value
    }
    
    const openAvatarUpload = () => {
      avatarInput.value.click()
    }
    
    const handleAvatarUpload = (event) => {
      const file = event.target.files[0]
      if (file) {
        const reader = new FileReader()
        reader.onload = (e) => {
          user.value.avatar = e.target.result
          localStorage.setItem('user', JSON.stringify(user.value))
          emit('user-updated', user.value)
        }
        reader.readAsDataURL(file)
      }
    }
    
    const logout = () => {
      localStorage.removeItem('access_token')
      localStorage.removeItem('user')
      user.value = { name: '', avatar: '' }
      userMenuOpen.value = false
      router.push('/login')
    }
    
    // 初始化
    onMounted(() => {
      loadUserData()
      questionnaireStore.checkDueQuestionnaires()
      emotionStore.checkRemind()
      alertStore.fetchAlerts()
      const user = JSON.parse(localStorage.getItem('user') || '{}')
      if (user.id) {
        alertStore.connectWebSocket(user.id)
      }
    })

    watch(() => router.currentRoute.value, () => {
      loadUserData()
    })
    
    return {
      // 侧边栏控制
      isCollapsed,
      sidebarWidth,
      collapsedWidth,
      isResizing,
      toggleSidebar,
      startResize,
      
      // 其他状态
      historyDropdownOpen,
      conversationHistory,
      user,
      userMenuOpen,
      avatarInput,
      activeItem,
      activeConversationId,
      activeMenuId,
      menuPositionStyle,
      drawerOpen,
      
      // 方法
      toggleHistoryDropdown,
      loadConversation,
      formatTime,
      navigateTo,
      toggleUserMenu,
      openAvatarUpload,
      handleAvatarUpload,
      logout,
      toggleConversationMenu,
      onMenuButtonEnter,
      onMenuButtonLeave,
      onMenuPanelEnter,
      onMenuPanelLeave,
      pinConversation,
      deleteConversation,
      
      // 计算属性
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
  position: relative;
  transition: width 0.3s ease;
  overflow: hidden;
}

.sidebar.collapsed {
  width: 64px;
}

.sidebar.resizing {
  transition: none;
  user-select: none;
}

/* 折叠按钮 */
.sidebar-toggle {
  position: absolute;
  top: 10px;
  right: 10px;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  border-radius: 6px;
  background: rgba(255, 255, 255, 0.5);
  transition: all 0.3s ease;
  z-index: 10;
}

.sidebar-toggle:hover {
  background: rgba(76, 175, 80, 0.2);
  color: #4CAF50;
}

/* 拖拽调整手柄 */
.resize-handle {
  position: absolute;
  top: 0;
  right: 0;
  width: 6px;
  height: 100%;
  cursor: ew-resize;
  background: transparent;
  z-index: 5;
}

/* 头部 */
.sidebar-header {
  padding: 20px 20px 30px;
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
  flex-shrink: 0;
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
  white-space: nowrap;
}

.logo-subtitle {
  font-size: 12px;
  color: #666;
  margin: 0;
  padding-left: 40px;
  white-space: nowrap;
}

/* 菜单 */
.sidebar-menu {
  flex: 1;
  padding: 20px 0;
  overflow-y: auto;
  overflow-x: hidden;
}

.sidebar-menu::-webkit-scrollbar {
  width: 4px;
}

.sidebar-menu::-webkit-scrollbar-track {
  background: rgba(0, 0, 0, 0.05);
}

.sidebar-menu::-webkit-scrollbar-thumb {
  background: rgba(76, 175, 80, 0.3);
  border-radius: 4px;
}

.menu-item {
  display: flex;
  align-items: center;
  padding: 12px 20px;
  cursor: pointer;
  transition: all 0.3s ease;
  color: #666;
  white-space: nowrap;
  position: relative;
}

.menu-item:hover {
  background-color: rgba(76, 175, 80, 0.1);
  color: #4CAF50;
}

.menu-item.active {
  background-color: #4CAF50;
  color: white;
  font-weight: 500;
}

.menu-icon {
  flex-shrink: 0;
  margin-right: 12px;
}

.menu-text {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* 下拉箭头 */
.dropdown-arrow {
  margin-left: auto;
  transition: transform 0.3s ease;
}

.dropdown-arrow.is-open {
  transform: rotate(180deg);
}

/* 下拉菜单 */
.dropdown-menu {
  background-color: rgba(255, 255, 255, 0.5);
  border-radius: 0 0 4px 4px;
  max-height: calc(100vh - 300px);
  overflow-y: auto;
}

.dropdown-menu::-webkit-scrollbar {
  width: 4px;
}

.dropdown-menu::-webkit-scrollbar-track {
  background: rgba(241, 241, 241, 0.3);
}

.dropdown-menu::-webkit-scrollbar-thumb {
  background: rgba(76, 175, 80, 0.3);
  border-radius: 4px;
}

.dropdown-item {
  padding: 12px 20px; 
  cursor: pointer;
  transition: all 0.3s ease;
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.dropdown-item:hover {
  background-color: rgba(76, 175, 80, 0.1);
}

.dropdown-item.active {
  background-color: rgba(76, 175, 80, 0.3);
}

.dropdown-item-content {
  flex: 1;
  min-width: 0;
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
  gap: 8px;
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

.dropdown-item-menu {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-left: 8px;
}

.menu-button {
  background: none;
  border: none;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 4px;
  opacity: 0.7;
  transition: all 0.3s ease;
}

.menu-button:hover {
  background-color: rgba(0, 0, 0, 0.05);
  opacity: 1;
}

.menu-dots {
  font-size: 16px;
  color: #666;
  transform: rotate(90deg);
}

.dropdown-item.active .menu-dots {
  color: white;
}

.menu-dots :deep(.el-icon) {
  font-size: 16px;
  transform: rotate(90deg);
}

.conversation-menu {
  position: fixed;
  background-color: white;
  border: 1px solid rgba(0, 0, 0, 0.1);
  border-radius: 6px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
  z-index: 99999;
  min-width: 90px;
  padding: 4px 0;
}

.conversation-menu .menu-item {
  padding: 8px 12px;
  font-size: 13px;
  white-space: nowrap;
  color: #333;
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

/* 角标 */
.menu-badge {
  margin-left: auto;
}

.menu-badge-collapsed {
  position: absolute;
  top: 8px;
  right: 8px;
}

.menu-badge :deep(.el-badge__content) {
  background-color: #f56c6c;
  border: none;
}

/* 底部 */
.sidebar-footer {
  padding: 20px;
  border-top: 1px solid rgba(0, 0, 0, 0.1);
  position: relative;
}

.user-info {
  display: flex;
  align-items: center;
  position: relative;
}

.user-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background-color: #4CAF50;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  border: 2px solid #4CAF50;
  cursor: pointer;
  transition: transform 0.3s ease;
}

.user-avatar:hover {
  transform: scale(1.05);
}

.avatar-placeholder {
  color: white;
  font-size: 16px;
  font-weight: bold;
}

.avatar-image {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  object-fit: cover;
}

.user-details {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-left: 10px;
  min-width: 0;
}

.user-name {
  font-size: 14px;
  color: #333;
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.user-ellipsis {
  font-size: 18px;
  color: #999;
  cursor: pointer;
  transition: color 0.3s ease;
  padding: 4px;
}

.user-ellipsis:hover {
  color: #4CAF50;
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

/* 收起状态的样式 */
.sidebar.collapsed .sidebar-toggle {
  position: static;
  margin: 10px auto;
}

.sidebar.collapsed .sidebar-header {
  padding: 10px;
  text-align: center;
}

.sidebar.collapsed .logo {
  justify-content: center;
}

.sidebar.collapsed .logo-text,
.sidebar.collapsed .logo-subtitle {
  display: none;
}

.sidebar.collapsed .menu-item {
  justify-content: center;
  padding: 12px;
}

.sidebar.collapsed .menu-icon {
  margin-right: 0;
}

.sidebar.collapsed .sidebar-footer {
  padding: 10px;
  justify-content: center;
}

.sidebar.collapsed .user-info {
  justify-content: center;
}
</style>
