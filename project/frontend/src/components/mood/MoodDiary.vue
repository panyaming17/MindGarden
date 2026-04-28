<template>
  <div class="mood-diary">
    <h2 class="page-title">情绪日记</h2>
    
    <div class="diary-content">
      <!-- 当天日期卡片 -->
      <div class="date-card">
        <h3 class="card-title">情绪日历 今日情绪记录</h3>
        <div class="current-date">
          {{ formatCurrentDate() }}
        </div>
        <div class="mood-form">
          <div class="form-group">
            <label>情绪选择（下拉选择表情）</label>
            <el-select v-model="moodForm.mood_label" placeholder="请选择情绪" class="w-full">
              <el-option label="喜 😊" value="喜" />
              <el-option label="怒 😠" value="怒" />
              <el-option label="忧 😟" value="忧" />
              <el-option label="思 😔" value="思" />
              <el-option label="悲 😢" value="悲" />
              <el-option label="恐 😨" value="恐" />
              <el-option label="惊 😰" value="惊" />
            </el-select>
          </div>
          
          <div class="form-group">
            <label>情绪标签，输入框</label>
            <el-input 
              v-model="moodForm.signature_text" 
              placeholder="输入情绪标签..."
            />
          </div>
          
          <el-button 
            type="primary" 
            @click="saveMoodEntry"
            :loading="isSaving"
          >
            保存记录
          </el-button>
        </div>
      </div>
      
      <!-- 缩小的日历 -->
      <div class="calendar-side">
        <h3 class="calendar-title">情绪日历</h3>
        <MoodCalendar 
          :calendar-data="calendarData" 
          @date-click="handleDateClick"
        />
        
        <!-- 浮窗显示当天的心情标签和情绪表情 -->
        <el-popover
          v-model:visible="popoverVisible"
          :width="200"
          trigger="manual"
          :placement="'top'"
          :popper-options="{ offset: [0, 10] }"
        >
          <template #default>
            <div class="mood-popover">
              <div class="popover-date">{{ popoverDate }}</div>
              <div class="popover-mood">
                <span class="mood-label">{{ popoverMood.label }}</span>
                <span class="mood-emoji">{{ popoverMood.emoji }}</span>
              </div>
              <div class="popover-signature" v-if="popoverMood.signature">{{ popoverMood.signature }}</div>
            </div>
          </template>
        </el-popover>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import MoodCalendar from './MoodCalendar.vue'
import MoodTrend from './MoodTrend.vue'
import { moodApi } from '@/utils/api'

// 响应式数据
const calendarData = ref({ days: [] })
const trendData = ref({ dates: [], intensities: [], labels: [] })
const selectedDate = ref(new Date().toISOString().split('T')[0])
const isSaving = ref(false)
const isLoading = ref(false)

// 情绪表情选项
const emojis = [
  { icon: '😊', value: 'happy' },
  { icon: '😐', value: 'calm' },
  { icon: '😰', value: 'anxious' },
  { icon: '😔', value: 'depressed' },
  { icon: '😠', value: 'angry' },
  { icon: '😨', value: 'fearful' },
  { icon: '😫', value: 'stressed' }
]

// 情绪记录表单
const moodForm = reactive({
  mood_label: '',
  emoji: '',
  signature_text: '',
  four_dim_intensity: 5,
  four_dim_hedonic: '中性',
  four_dim_tension: '中',
  four_dim_complexity: '中等'
})

// 浮窗相关数据
const popoverVisible = ref(false)
const popoverDate = ref('')
const popoverMood = ref({ label: '', emoji: '', signature: '' })

// 格式化当前日期
const formatCurrentDate = () => {
  const date = new Date()
  const day = date.getDate()
  const month = date.getMonth() + 1
  return `${day}/${month}`
}

// 处理日期点击
const handleDateClick = (date) => {
  selectedDate.value = date
  // 加载该日期的情绪记录
  loadMoodEntry(date)
  
  // 显示浮窗
  showMoodPopover(date)
}

// 显示情绪浮窗
const showMoodPopover = (date) => {
  // 从日历数据中查找该日期的情绪记录
  const entry = calendarData.value.days.find(item => item.date === date)
  if (entry) {
    popoverDate.value = date
    popoverMood.value = {
      label: entry.mood_label || '无',
      emoji: getEmojiByMood(entry.mood_label) || '😐',
      signature: entry.signature || ''
    }
    popoverVisible.value = true
    
    // 3秒后自动关闭浮窗
    setTimeout(() => {
      popoverVisible.value = false
    }, 3000)
  }
}

// 根据情绪标签获取对应的表情
const getEmojiByMood = (mood) => {
  const moodEmojiMap = {
    '开心': '😊',
    '平静': '😐',
    '焦虑': '😰',
    '抑郁': '😔',
    '愤怒': '😠',
    '恐惧': '😨',
    '压力': '😫'
  }
  return moodEmojiMap[mood] || '😐'
}

// 加载情绪记录
const loadMoodEntry = async (date) => {
  try {
    const user = JSON.parse(localStorage.getItem('user'))
    if (!user?.id) {
      ElMessage.error('用户未登录')
      return
    }
    
    // 这里可以调用API获取指定日期的情绪记录
    // 由于API设计中没有单独获取单个情绪记录的接口，我们暂时从日历数据中查找
    const entry = calendarData.value.days.find(item => item.date === date)
    if (entry) {
      moodForm.mood_label = entry.mood_label
      moodForm.emoji = entry.emoji || getEmojiByMood(entry.mood_label)
      moodForm.signature_text = entry.signature
      // 这里可以添加其他字段的赋值
    } else {
      // 重置表单
      moodForm.mood_label = ''
      moodForm.emoji = ''
      moodForm.signature_text = ''
      moodForm.four_dim_intensity = 5
      moodForm.four_dim_hedonic = '中性'
      moodForm.four_dim_tension = '中'
      moodForm.four_dim_complexity = '中等'
    }
  } catch (error) {
    ElMessage.error('加载情绪记录失败')
  }
}

// 保存情绪记录
const saveMoodEntry = async () => {
  if (!moodForm.mood_label) {
    ElMessage.warning('请选择情绪标签')
    return
  }
  
  isSaving.value = true
  try {
    const user = JSON.parse(localStorage.getItem('user'))
    if (!user?.id) {
      ElMessage.error('用户未登录')
      return
    }
    
    const data = {
      user_id: user.id,
      date: selectedDate.value,
      mood_label: moodForm.mood_label,
      emoji: moodForm.emoji || getEmojiByMood(moodForm.mood_label),
      signature_text: moodForm.signature_text,
      four_dim: {
        intensity: moodForm.four_dim_intensity,
        hedonic: moodForm.four_dim_hedonic,
        tension: moodForm.four_dim_tension,
        complexity: moodForm.four_dim_complexity
      }
    }
    
    // 调用 API
    await moodApi.saveEntry(data)
    
    ElMessage.success('情绪记录保存成功')
    
    // 更新日历数据
    await loadCalendarData()
  } catch (error) {
    ElMessage.error('保存失败，请重试')
  } finally {
    isSaving.value = false
  }
}

// 加载日历数据
const loadCalendarData = async () => {
  try {
    isLoading.value = true
    const user = JSON.parse(localStorage.getItem('user'))
    if (!user?.id) {
      ElMessage.error('用户未登录')
      return
    }
    
    const now = new Date()
    const year = now.getFullYear()
    const month = now.getMonth() + 1
    
    const data = await moodApi.getCalendar(user.id, year, month)
    calendarData.value = data
  } catch (error) {
    ElMessage.error('加载日历数据失败')
  } finally {
    isLoading.value = false
  }
}

// 加载情绪趋势数据
const loadMoodTrend = async () => {
  try {
    const user = JSON.parse(localStorage.getItem('user'))
    if (!user?.id) {
      ElMessage.error('用户未登录')
      return
    }
    
    // 获取最近7天的日期
    const endDate = new Date().toISOString().split('T')[0]
    const startDate = new Date(Date.now() - 6 * 24 * 60 * 60 * 1000).toISOString().split('T')[0]
    
    const data = await moodApi.getTrend(user.id, startDate, endDate)
    trendData.value = data
  } catch (error) {
    ElMessage.error('加载情绪趋势数据失败')
  }
}

// 组件挂载时
onMounted(async () => {
  // 加载日历数据
  await loadCalendarData()
  // 加载情绪趋势数据
  await loadMoodTrend()
  // 加载当前日期的情绪记录
  loadMoodEntry(selectedDate.value)
})
</script>

<style scoped>
.mood-diary {
  padding: 20px;
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.page-title {
  font-size: 20px;
  font-weight: 600;
  margin-bottom: 20px;
  color: #2c3e50;
}

.diary-content {
  flex: 1;
  display: flex;
  gap: 15px;
  overflow: hidden;
}

.date-card {
  flex: 1;
  background: white;
  border-radius: 12px;
  padding: 15px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.card-title {
  font-size: 18px;
  font-weight: 500;
  margin-bottom: 10px;
  color: #34495e;
  border-bottom: 2px solid #42b983;
  padding-bottom: 10px;
}

.current-date {
  font-size: 24px;
  font-weight: 600;
  color: #42b983;
  margin-bottom: 20px;
  text-align: center;
}

.mood-form {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 12px;
  overflow: hidden;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
  overflow: hidden;
}

.form-group label {
  font-size: 14px;
  font-weight: 500;
  color: #555;
}

.emoji-selector {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.emoji-item {
  font-size: 24px;
  cursor: pointer;
  padding: 8px;
  border-radius: 8px;
  transition: all 0.3s ease;
}

.emoji-item:hover {
  background: #f0f0f0;
  transform: scale(1.1);
}

.emoji-item.active {
  background: #e6f7ff;
  border: 2px solid #1890ff;
}

.calendar-side {
  width: 300px;
  background: white;
  border-radius: 12px;
  padding: 15px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-height: 300px;
}

.calendar-title {
  font-size: 18px;
  font-weight: 500;
  margin-bottom: 20px;
  color: #34495e;
  border-bottom: 2px solid #42b983;
  padding-bottom: 10px;
}

.mood-popover {
  padding: 12px;
}

.popover-date {
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 8px;
  color: #333;
}

.popover-mood {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.mood-label {
  font-size: 14px;
  color: #666;
}

.mood-emoji {
  font-size: 20px;
}

.popover-signature {
  font-size: 12px;
  color: #999;
  line-height: 1.4;
}

@media (max-width: 768px) {
  .diary-content {
    flex-direction: column;
  }
  
  .calendar-side {
    width: 100%;
  }
  
  .mood-diary {
    padding: 10px;
  }
}
</style>
