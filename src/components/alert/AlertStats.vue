<template>
  <div class="alert-stats">
    <div class="stat-card total">
      <div class="stat-icon">🔔</div>
      <div class="stat-content">
        <div class="stat-value">{{ stats.total }}</div>
        <div class="stat-label">全部预警</div>
      </div>
    </div>
    
    <div class="stat-card unacknowledged">
      <div class="stat-icon">⏳</div>
      <div class="stat-content">
        <div class="stat-value">{{ stats.unacknowledged }}</div>
        <div class="stat-label">待处理</div>
      </div>
    </div>
    
    <div class="stat-card acknowledged">
      <div class="stat-icon">✅</div>
      <div class="stat-content">
        <div class="stat-value">{{ stats.acknowledged }}</div>
        <div class="stat-label">已处理</div>
      </div>
    </div>
    
    <div class="stat-card danger">
      <div class="stat-icon">🚨</div>
      <div class="stat-content">
        <div class="stat-value">{{ stats.dangerCount }}</div>
        <div class="stat-label">危险预警</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useAlertStore } from '@/stores/alert'

const alertStore = useAlertStore()

const stats = computed(() => alertStore.stats)
</script>

<style scoped>
.alert-stats {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}

.stat-card {
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(10px);
  border-radius: 16px;
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 16px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.5);
  transition: all 0.3s ease;
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
}

.stat-icon {
  font-size: 32px;
  width: 56px;
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;
}

.stat-card.total .stat-icon {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.stat-card.unacknowledged .stat-icon {
  background: linear-gradient(135deg, #f39c12 0%, #f1c40f 100%);
}

.stat-card.acknowledged .stat-icon {
  background: linear-gradient(135deg, #27ae60 0%, #2ecc71 100%);
}

.stat-card.danger .stat-icon {
  background: linear-gradient(135deg, #e74c3c 0%, #c0392b 100%);
}

.stat-content {
  flex: 1;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: #2c3e50;
  line-height: 1;
  margin-bottom: 4px;
}

.stat-label {
  font-size: 14px;
  color: #7f8c8d;
}

@media (max-width: 768px) {
  .alert-stats {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
