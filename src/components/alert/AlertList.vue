<template>
  <div class="alert-list">
    <div v-if="isLoading" class="loading-state">
      <div class="loading-content">
        <el-icon class="loading-icon is-loading"><Loading /></el-icon>
        <p class="loading-text">正在加载预警数据...</p>
      </div>
    </div>
    
    <div v-else-if="filteredAlerts.length === 0" class="empty-state">
      <el-empty 
        :description="emptyText"
        :image-size="120"
      >
        <template #image>
          <div class="empty-icon">🔔</div>
        </template>
      </el-empty>
    </div>
    
    <div v-else class="alert-items">
      <AlertCard
        v-for="alert in paginatedAlerts"
        :key="alert.id"
        :alert="alert"
        @click="handleCardClick"
        @acknowledge="handleAcknowledge"
        @detail="handleDetail"
      />
      
      <!-- 分页 -->
      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :total="filteredAlerts.length"
          :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useAlertStore } from '@/stores/alert'
import { Loading } from '@element-plus/icons-vue'
import AlertCard from './AlertCard.vue'

const alertStore = useAlertStore()

const props = defineProps({
  isLoading: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['card-click', 'acknowledge', 'detail'])

const currentPage = ref(1)
const pageSize = ref(10)

const filteredAlerts = computed(() => alertStore.filteredAlerts)

const paginatedAlerts = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return filteredAlerts.value.slice(start, end)
})

const emptyText = computed(() => {
  if (alertStore.selectedDate) {
    return `${alertStore.selectedDate} 暂无预警信息`
  }
  if (alertStore.filters.type !== 'all' || alertStore.filters.level !== 'all' || alertStore.filters.status !== 'all') {
    return '没有符合筛选条件的预警'
  }
  return '暂无预警信息'
})

const handleCardClick = (alert) => {
  emit('card-click', alert)
}

const handleAcknowledge = (alertId) => {
  emit('acknowledge', alertId)
}

const handleDetail = (alert) => {
  emit('detail', alert)
}

const handleSizeChange = (size) => {
  pageSize.value = size
  currentPage.value = 1
}

const handleCurrentChange = (page) => {
  currentPage.value = page
}
</script>

<style scoped>
.alert-list {
  width: 100%;
}

.loading-state {
  padding: 60px 20px;
  display: flex;
  justify-content: center;
  align-items: center;
}

.loading-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}

.loading-icon {
  font-size: 40px;
  color: #667eea;
}

.loading-text {
  font-size: 14px;
  color: #666;
  margin: 0;
}

.is-loading {
  animation: rotating 2s linear infinite;
}

@keyframes rotating {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

.empty-state {
  padding: 60px 20px;
  text-align: center;
}

.empty-icon {
  font-size: 64px;
  opacity: 0.3;
  margin-bottom: 16px;
}

.alert-items {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.pagination-wrapper {
  margin-top: 24px;
  padding-top: 16px;
  border-top: 1px solid rgba(0, 0, 0, 0.05);
  display: flex;
  justify-content: center;
}
</style>
