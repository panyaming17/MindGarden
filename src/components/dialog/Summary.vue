<template>
  <div class="summary">
    <div class="summary-header">
      <h3 class="summary-title">总结确认</h3>
      <p class="summary-subtitle">请确认你的对话信息和设定目标</p>
    </div>
    
    <div class="summary-content">
      <div class="summary-section">
        <h4 class="section-title">📋 对话交流</h4>
        <div class="section-content">
          <div class="summary-item">
            <span class="item-label">交流内容：</span>
            <span class="item-value">已完成初步对话交流</span>
          </div>
          <div class="summary-item">
            <span class="item-label">对话轮次：</span>
            <span class="item-value">3 轮对话</span>
          </div>
        </div>
      </div>
      
      <div class="summary-section">
        <h4 class="section-title">😊 情绪选择</h4>
        <div class="section-content">
          <div class="summary-item">
            <span class="item-label">当前情绪：</span>
            <span class="item-value emotion-tag">平静 😌</span>
          </div>
          <div class="summary-item">
            <span class="item-label">情绪描述：</span>
            <span class="item-value">内心平和，情绪稳定</span>
          </div>
        </div>
      </div>
      
      <div class="summary-section">
        <h4 class="section-title">🎯 目标设定</h4>
        <div class="section-content">
          <div class="summary-item">
            <span class="item-label">主要目标：</span>
            <span class="item-value">学习情绪管理技巧，提升自我认知</span>
          </div>
          <div class="summary-item">
            <span class="item-label">期望时间：</span>
            <span class="item-value">一个月内</span>
          </div>
          <div class="summary-item">
            <span class="item-label">优先级：</span>
            <span class="item-value priority-medium">中优先级 🟡</span>
          </div>
        </div>
      </div>
    </div>
    
    <div class="summary-actions">
      <button class="action-button secondary" @click="goBack">返回修改</button>
      <button class="action-button primary" @click="confirm">
        <span>✓ 确认创建</span>
      </button>
    </div>
  </div>
</template>

<script>
export default {
  name: 'Summary',
  methods: {
    goBack() {
      this.$emit('prev-step')
    },
    confirm() {
      this.$emit('confirm')
      alert('对话创建成功！')
    }
  }
}
</script>

<style scoped>
.summary {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.summary-header {
  text-align: center;
  margin-bottom: 30px;
  padding-bottom: 20px;
  border-bottom: 2px solid #E0E0E0;
}

.summary-title {
  font-size: 24px;
  color: #333;
  margin: 0 0 10px 0;
}

.summary-subtitle {
  font-size: 14px;
  color: #999;
  margin: 0;
}

.summary-content {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.summary-section {
  background-color: #F9F9F9;
  border-radius: 8px;
  padding: 20px;
}

.section-title {
  font-size: 16px;
  color: #333;
  margin: 0 0 15px 0;
}

.section-content {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.summary-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 0;
  border-bottom: 1px solid #E0E0E0;
}

.summary-item:last-child {
  border-bottom: none;
}

.item-label {
  font-size: 14px;
  color: #666;
}

.item-value {
  font-size: 14px;
  font-weight: 500;
  color: #333;
}

.emotion-tag {
  background-color: rgba(76, 175, 80, 0.1);
  color: #4CAF50;
  padding: 4px 12px;
  border-radius: 12px;
  font-weight: 500;
}

.priority-medium {
  color: #FFA500;
}

.summary-actions {
  display: flex;
  justify-content: center;
  gap: 15px;
  margin-top: 20px;
}

.action-button {
  padding: 12px 32px;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
}

.action-button.secondary {
  background-color: white;
  color: #666;
  border: 1px solid #E0E0E0;
}

.action-button.secondary:hover {
  background-color: #F5F5F5;
}

.action-button.primary {
  background-color: #4CAF50;
  color: white;
}

.action-button.primary:hover {
  background-color: #45a049;
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(76, 175, 80, 0.3);
}
</style>