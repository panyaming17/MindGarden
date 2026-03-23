<template>
  <div class="mood-diary">
    <h2 class="page-title">情绪日记</h2>
    
    <!-- 日历视图 -->
    <div class="calendar-section">
      <h3>情绪日历</h3>
      <MoodCalendar 
        :calendar-data="calendarData" 
        @date-click="handleDateClick"
      />
    </div>
    
    <!-- 情绪记录表单 -->
    <div class="form-section">
      <h3>{{ selectedDate }} 情绪记录</h3>
      <div class="mood-form">
        <div class="form-group">
          <label>情绪标签</label>
          <el-select v-model="moodForm.mood_label" placeholder="请选择情绪" class="w-full">
            <el-option label="开心" value="开心" />
            <el-option label="平静" value="平静" />
            <el-option label="焦虑" value="焦虑" />
            <el-option label="抑郁" value="抑郁" />
            <el-option label="愤怒" value="愤怒" />
            <el-option label="恐惧" value="恐惧" />
            <el-option label="压力" value="压力" />
          </el-select>
        </div>
        
        <div class="form-group">
          <label>签名语句</label>
          <el-input 
            v-model="moodForm.signature_text" 
            type="textarea" 
            placeholder="记录今天的心情..."
            rows="3"
          />
        </div>
        
        <div class="form-group">
          <label>情绪强度</label>
          <el-slider 
            v-model="moodForm.four_dim_intensity" 
            :min="0" 
            :max="10" 
            :step="0.5"
            show-input
          />
        </div>
        
        <div class="form-row">
          <div class="form-group half">
            <label>快感度</label>
            <el-select v-model="moodForm.four_dim_hedonic" placeholder="请选择" class="w-full">
              <el-option label="正性" value="正性" />
              <el-option label="中性" value="中性" />
              <el-option label="负性" value="负性" />
            </el-select>
          </div>
          
          <div class="form-group half">
            <label>紧张度</label>
            <el-select v-model="moodForm.four_dim_tension" placeholder="请选择" class="w-full">
              <el-option label="低" value="低" />
              <el-option label="中" value="中" />
              <el-option label="高" value="高" />
            </el-select>
          </div>
        </div>
        
        <div class="form-row">
          <div class="form-group half">
            <label>复杂度</label>
            <el-select v-model="moodForm.four_dim_complexity" placeholder="请选择" class="w-full">
              <el-option label="简单" value="简单" />
              <el-option label="中等" value="中等" />
              <el-option label="复杂" value="复杂" />
            </el-select>
          </div>
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
    
    <!-- 情绪趋势 -->
    <div class="trend-section">
      <h3>情绪趋势</h3>
      <MoodTrend :trend-data="trendData" />
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

// 情绪记录表单
const moodForm = reactive({
  mood_label: '',
  signature_text: '',
  four_dim_intensity: 5,
  four_dim_hedonic: '中性',
  four_dim_tension: '中',
  four_dim_complexity: '中等'
})

// 处理日期点击
const handleDateClick = (date) => {
  selectedDate.value = date
  // 加载该日期的情绪记录
  loadMoodEntry(date)
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
      moodForm.signature_text = entry.signature
      // 这里可以添加其他字段的赋值
    } else {
      // 重置表单
      moodForm.mood_label = ''
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
  max-width: 1200px;
  margin: 0 auto;
}

.page-title {
  font-size: 24px;
  font-weight: 600;
  margin-bottom: 30px;
  color: #2c3e50;
  text-align: center;
}

.calendar-section,
.form-section,
.trend-section {
  background: white;
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 20px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.calendar-section h3,
.form-section h3,
.trend-section h3 {
  font-size: 18px;
  font-weight: 500;
  margin-bottom: 20px;
  color: #34495e;
  border-bottom: 2px solid #42b983;
  padding-bottom: 10px;
}

.mood-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-group label {
  font-size: 14px;
  font-weight: 500;
  color: #555;
}

.form-row {
  display: flex;
  gap: 16px;
}

.form-group.half {
  flex: 1;
}

.w-full {
  width: 100%;
}

@media (max-width: 768px) {
  .form-row {
    flex-direction: column;
  }
  
  .mood-diary {
    padding: 10px;
  }
}
</style>
