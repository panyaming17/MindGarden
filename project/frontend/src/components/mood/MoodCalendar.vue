<template>
  <div class="mood-calendar">
    <div class="calendar-header">
      <el-button @click="previousMonth" size="small">
        <el-icon><ArrowLeft /></el-icon>
      </el-button>
      <h4>{{ currentYearMonth }}</h4>
      <el-button @click="nextMonth" size="small">
        <el-icon><ArrowRight /></el-icon>
      </el-button>
    </div>
    
    <div class="calendar-grid">
      <div class="weekday-header">
        <div v-for="day in weekdays" :key="day" class="weekday">{{ day }}</div>
      </div>
      <div class="days-grid">
        <!-- 上个月的日期 -->
        <div 
          v-for="day in prevMonthDays" 
          :key="`prev-${day}`" 
          class="day prev-month"
        >
          {{ day }}
        </div>
        
        <!-- 当月的日期 -->
        <div 
          v-for="day in currentMonthDays" 
          :key="`current-${day}`" 
          class="day current-month"
          :class="{
            'today': isToday(day),
            'has-entry': hasMoodEntry(day)
          }"
          @click="handleDayClick(day)"
        >
          <span class="day-number">{{ day }}</span>
          <span v-if="hasMoodEntry(day)" class="mood-indicator" :class="getMoodClass(day)"></span>
        </div>
        
        <!-- 下个月的日期 -->
        <div 
          v-for="day in nextMonthDays" 
          :key="`next-${day}`" 
          class="day next-month"
        >
          {{ day }}
        </div>
      </div>
    </div>
    
    <!-- 情绪图例 -->
    <div class="mood-legend">
      <h5>情绪图例</h5>
      <div class="legend-items">
        <div class="legend-item">
          <span class="legend-color happy"></span>
          <span>开心</span>
        </div>
        <div class="legend-item">
          <span class="legend-color calm"></span>
          <span>平静</span>
        </div>
        <div class="legend-item">
          <span class="legend-color anxious"></span>
          <span>焦虑</span>
        </div>
        <div class="legend-item">
          <span class="legend-color depressed"></span>
          <span>抑郁</span>
        </div>
        <div class="legend-item">
          <span class="legend-color angry"></span>
          <span>愤怒</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ArrowLeft, ArrowRight } from '@element-plus/icons-vue'

// 组件属性
const props = defineProps({
  calendarData: {
    type: Object,
    default: () => ({ days: [] })
  }
})

// 事件
const emit = defineEmits(['date-click'])

// 响应式数据
const currentDate = ref(new Date())
const weekdays = ['日', '一', '二', '三', '四', '五', '六']

// 计算属性
const currentYear = computed(() => currentDate.value.getFullYear())
const currentMonth = computed(() => currentDate.value.getMonth())
const currentYearMonth = computed(() => `${currentYear.value}年${currentMonth.value + 1}月`)

// 当月第一天
const firstDayOfMonth = computed(() => new Date(currentYear.value, currentMonth.value, 1))
// 当月最后一天
const lastDayOfMonth = computed(() => new Date(currentYear.value, currentMonth.value + 1, 0))
// 当月第一天是星期几（0-6，0表示星期日）
const firstDayWeekday = computed(() => firstDayOfMonth.value.getDay())
// 当月的天数
const daysInMonth = computed(() => lastDayOfMonth.value.getDate())

// 上个月的日期
const prevMonthDays = computed(() => {
  const days = []
  const prevMonthLastDay = new Date(currentYear.value, currentMonth.value, 0).getDate()
  for (let i = prevMonthLastDay - firstDayWeekday.value + 1; i <= prevMonthLastDay; i++) {
    days.push(i)
  }
  return days
})

// 当月的日期
const currentMonthDays = computed(() => {
  const days = []
  for (let i = 1; i <= daysInMonth.value; i++) {
    days.push(i)
  }
  return days
})

// 下个月的日期
const nextMonthDays = computed(() => {
  const days = []
  const totalDays = prevMonthDays.value.length + currentMonthDays.value.length
  const remainingDays = 42 - totalDays // 6行7列
  for (let i = 1; i <= remainingDays; i++) {
    days.push(i)
  }
  return days
})

// 方法
const previousMonth = () => {
  currentDate.value = new Date(currentYear.value, currentMonth.value - 1, 1)
}

const nextMonth = () => {
  currentDate.value = new Date(currentYear.value, currentMonth.value + 1, 1)
}

const isToday = (day) => {
  const today = new Date()
  return today.getFullYear() === currentYear.value &&
         today.getMonth() === currentMonth.value &&
         today.getDate() === day
}

const hasMoodEntry = (day) => {
  const dateStr = `${currentYear.value}-${String(currentMonth.value + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`
  return props.calendarData.days.some(item => item.date === dateStr)
}

const getMoodClass = (day) => {
  const dateStr = `${currentYear.value}-${String(currentMonth.value + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`
  const entry = props.calendarData.days.find(item => item.date === dateStr)
  if (entry) {
    switch (entry.mood_label) {
      case '开心': return 'happy'
      case '平静': return 'calm'
      case '焦虑': return 'anxious'
      case '抑郁': return 'depressed'
      case '愤怒': return 'angry'
      case '恐惧': return 'fearful'
      case '压力': return 'stressed'
      default: return ''
    }
  }
  return ''
}

const handleDayClick = (day) => {
  const dateStr = `${currentYear.value}-${String(currentMonth.value + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`
  emit('date-click', dateStr)
}

// 组件挂载时
onMounted(() => {
  // 初始化当前月份
})
</script>

<style scoped>
.mood-calendar {
  width: 100%;
}

.calendar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}

.calendar-header h4 {
  margin: 0;
  font-size: 16px;
  font-weight: 500;
  color: #333;
}

.calendar-grid {
  width: 100%;
}

.weekday-header {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 8px;
  margin-bottom: 8px;
}

.weekday {
  text-align: center;
  font-size: 14px;
  font-weight: 500;
  color: #666;
  padding: 8px 0;
}

.days-grid {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 8px;
}

.day {
  position: relative;
  aspect-ratio: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.day:hover {
  background-color: #f0f0f0;
}

.day-number {
  font-size: 14px;
}

.prev-month, .next-month {
  color: #ccc;
}

.current-month {
  color: #333;
}

.today {
  background-color: #e3f2fd;
  font-weight: 500;
}

.has-entry {
  position: relative;
}

.mood-indicator {
  position: absolute;
  bottom: 4px;
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.mood-indicator.happy {
  background-color: #4caf50;
}

.mood-indicator.calm {
  background-color: #2196f3;
}

.mood-indicator.anxious {
  background-color: #ff9800;
}

.mood-indicator.depressed {
  background-color: #9c27b0;
}

.mood-indicator.angry {
  background-color: #f44336;
}

.mood-indicator.fearful {
  background-color: #607d8b;
}

.mood-indicator.stressed {
  background-color: #795548;
}

.mood-legend {
  margin-top: 20px;
  padding-top: 16px;
  border-top: 1px solid #e0e0e0;
}

.mood-legend h5 {
  margin: 0 0 12px 0;
  font-size: 14px;
  font-weight: 500;
  color: #666;
}

.legend-items {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: #666;
}

.legend-color {
  width: 12px;
  height: 12px;
  border-radius: 50%;
}

.legend-color.happy {
  background-color: #4caf50;
}

.legend-color.calm {
  background-color: #2196f3;
}

.legend-color.anxious {
  background-color: #ff9800;
}

.legend-color.depressed {
  background-color: #9c27b0;
}

.legend-color.angry {
  background-color: #f44336;
}

@media (max-width: 768px) {
  .day {
    font-size: 12px;
  }
  
  .legend-items {
    gap: 12px;
  }
}
</style>
