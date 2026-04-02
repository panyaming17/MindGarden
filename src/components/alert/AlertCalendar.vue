<template>
  <div class="alert-calendar">
    <div class="calendar-header">
      <el-button text size="small" @click="prevMonth">
        <el-icon><ArrowLeft /></el-icon>
      </el-button>
      <span class="calendar-title">{{ currentYear }}年{{ currentMonth }}月</span>
      <el-button text size="small" @click="nextMonth">
        <el-icon><ArrowRight /></el-icon>
      </el-button>
    </div>
    
    <div class="calendar-weekdays">
      <span v-for="day in weekdays" :key="day" class="weekday">{{ day }}</span>
    </div>
    
    <div class="calendar-days">
      <div
        v-for="(day, index) in calendarDays"
        :key="index"
        class="calendar-day"
        :class="{
          'other-month': !day.isCurrentMonth,
          'today': day.isToday,
          'selected': day.date === selectedDate,
          'has-alert': day.hasAlert
        }"
        @click="selectDate(day.date)"
      >
        <span class="day-number">{{ day.day }}</span>
        <div v-if="day.alertLevels.length > 0" class="alert-dots">
          <span
            v-for="level in day.alertLevels.slice(0, 3)"
            :key="level"
            class="alert-dot"
            :style="{ background: getLevelColor(level) }"
          ></span>
        </div>
      </div>
    </div>
    
    <div class="calendar-legend">
      <div class="legend-item">
        <span class="legend-dot" style="background: #3498db;"></span>
        <span>提示</span>
      </div>
      <div class="legend-item">
        <span class="legend-dot" style="background: #f39c12;"></span>
        <span>警告</span>
      </div>
      <div class="legend-item">
        <span class="legend-dot" style="background: #e74c3c;"></span>
        <span>危险</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { ArrowLeft, ArrowRight } from '@element-plus/icons-vue'
import { useAlertStore, alertLevelConfig } from '@/stores/alert'

const alertStore = useAlertStore()

const weekdays = ['日', '一', '二', '三', '四', '五', '六']

const currentDate = ref(new Date())
const selectedDate = computed(() => alertStore.selectedDate)

const currentYear = computed(() => currentDate.value.getFullYear())
const currentMonth = computed(() => currentDate.value.getMonth() + 1)

const calendarDays = computed(() => {
  const year = currentYear.value
  const month = currentMonth.value - 1
  
  const firstDay = new Date(year, month, 1)
  const lastDay = new Date(year, month + 1, 0)
  const prevLastDay = new Date(year, month, 0)
  
  const days = []
  const firstDayWeek = firstDay.getDay()
  
  // 上月日期
  for (let i = firstDayWeek - 1; i >= 0; i--) {
    const day = prevLastDay.getDate() - i
    const date = formatDate(new Date(year, month - 1, day))
    days.push({
      day,
      date,
      isCurrentMonth: false,
      isToday: false,
      hasAlert: !!alertStore.calendarData[date],
      alertLevels: alertStore.calendarData[date]?.levels || []
    })
  }
  
  // 当月日期
  const today = new Date()
  for (let i = 1; i <= lastDay.getDate(); i++) {
    const date = formatDate(new Date(year, month, i))
    const isToday = today.getFullYear() === year && 
                    today.getMonth() === month && 
                    today.getDate() === i
    days.push({
      day: i,
      date,
      isCurrentMonth: true,
      isToday,
      hasAlert: !!alertStore.calendarData[date],
      alertLevels: alertStore.calendarData[date]?.levels || []
    })
  }
  
  // 下月日期
  const remainingDays = 42 - days.length
  for (let i = 1; i <= remainingDays; i++) {
    const date = formatDate(new Date(year, month + 1, i))
    days.push({
      day: i,
      date,
      isCurrentMonth: false,
      isToday: false,
      hasAlert: !!alertStore.calendarData[date],
      alertLevels: alertStore.calendarData[date]?.levels || []
    })
  }
  
  return days
})

const formatDate = (date) => {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

const getLevelColor = (level) => {
  return alertLevelConfig[level]?.color || '#999'
}

const prevMonth = () => {
  currentDate.value = new Date(currentYear.value, currentMonth.value - 2, 1)
}

const nextMonth = () => {
  currentDate.value = new Date(currentYear.value, currentMonth.value, 1)
}

const selectDate = (date) => {
  if (selectedDate.value === date) {
    alertStore.setSelectedDate(null)
  } else {
    alertStore.setSelectedDate(date)
  }
}

// 监听月份变化，可以在这里加载对应月份的数据
watch(currentDate, () => {
  // 如果需要按月加载数据，可以在这里调用
  // alertStore.fetchAlertsByMonth(currentYear.value, currentMonth.value)
})
</script>

<style scoped>
.alert-calendar {
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(10px);
  border-radius: 16px;
  padding: 20px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.5);
}

.calendar-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.calendar-title {
  font-size: 16px;
  font-weight: 600;
  color: #2c3e50;
}

.calendar-weekdays {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 4px;
  margin-bottom: 8px;
}

.weekday {
  text-align: center;
  font-size: 12px;
  color: #999;
  padding: 8px 0;
}

.calendar-days {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 4px;
}

.calendar-day {
  aspect-ratio: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
  position: relative;
  padding: 4px;
}

.calendar-day:hover {
  background: rgba(102, 126, 234, 0.1);
}

.calendar-day.other-month {
  color: #ccc;
}

.calendar-day.today {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.calendar-day.today .day-number {
  color: white;
  font-weight: 600;
}

.calendar-day.selected {
  box-shadow: 0 0 0 2px #667eea;
}

.calendar-day.has-alert:not(.today) {
  background: rgba(255, 243, 224, 0.5);
}

.day-number {
  font-size: 14px;
  color: #333;
  line-height: 1;
}

.alert-dots {
  display: flex;
  gap: 2px;
  margin-top: 2px;
  height: 6px;
}

.alert-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
}

.calendar-legend {
  display: flex;
  justify-content: center;
  gap: 16px;
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid rgba(0, 0, 0, 0.05);
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #666;
}

.legend-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}
</style>
