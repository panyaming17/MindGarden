<template>
  <div class="goal-setting">
    <div class="goal-header">
      <h3 class="goal-title">目标设定</h3>
      <p class="goal-subtitle">设定你想要达成的情绪管理目标</p>
    </div>
    
    <div class="goal-form">
      <div class="form-group">
        <label class="form-label">主要目标</label>
        <textarea 
          v-model="mainGoal"
          class="form-textarea"
          placeholder="请描述你想要达成的情绪管理目标..."
          rows="3"
        ></textarea>
      </div>
      
      <div class="form-group">
        <label class="form-label">期望时间</label>
        <select v-model="timeframe" class="form-select">
          <option value="week">一周内</option>
          <option value="month">一个月内</option>
          <option value="quarter">三个月内</option>
          <option value="half-year">半年内</option>
          <option value="year">一年内</option>
        </select>
      </div>
      
      <div class="form-group">
        <label class="form-label">优先级</label>
        <div class="priority-options">
          <div 
            v-for="priority in priorities" 
            :key="priority.value"
            class="priority-item"
            :class="{ 'selected': selectedPriority === priority.value }"
            @click="selectPriority(priority.value)"
          >
            <div class="priority-icon">{{ priority.icon }}</div>
            <div class="priority-text">{{ priority.label }}</div>
          </div>
        </div>
      </div>
      
      <div class="form-group">
        <label class="form-label">备注说明</label>
        <textarea 
          v-model="notes"
          class="form-textarea"
          placeholder="可以添加一些额外的说明或备注..."
          rows="2"
        ></textarea>
      </div>
    </div>
    
    <div class="goal-summary" v-if="mainGoal">
      <h4 class="summary-title">目标概览</h4>
      <div class="summary-content">
        <div class="summary-item">
          <span class="summary-label">主要目标：</span>
          <span class="summary-value">{{ mainGoal }}</span>
        </div>
        <div class="summary-item">
          <span class="summary-label">期望时间：</span>
          <span class="summary-value">{{ getTimeframeLabel() }}</span>
        </div>
        <div class="summary-item">
          <span class="summary-label">优先级：</span>
          <span class="summary-value">{{ getPriorityLabel() }}</span>
        </div>
      </div>
    </div>
    
    <div class="goal-actions">
      <button class="action-button secondary" @click="goBack">上一步</button>
      <button class="action-button primary" @click="goNext">下一步</button>
    </div>
  </div>
</template>

<script>
export default {
  name: 'GoalSetting',
  data() {
    return {
      mainGoal: '',
      timeframe: 'month',
      selectedPriority: 'medium',
      notes: '',
      priorities: [
        { value: 'high', label: '高优先级', icon: '🔴' },
        { value: 'medium', label: '中优先级', icon: '🟡' },
        { value: 'low', label: '低优先级', icon: '🟢' }
      ]
    }
  },
  methods: {
    selectPriority(priority) {
      this.selectedPriority = priority
    },
    getTimeframeLabel() {
      const labels = {
        week: '一周内',
        month: '一个月内',
        quarter: '三个月内',
        'half-year': '半年内',
        year: '一年内'
      }
      return labels[this.timeframe] || ''
    },
    getPriorityLabel() {
      const priority = this.priorities.find(p => p.value === this.selectedPriority)
      return priority ? priority.label : ''
    },
    goBack() {
      this.$emit('prev-step')
    },
    goNext() {
      if (!this.mainGoal.trim()) {
        alert('请先设定主要目标')
        return
      }
      this.$emit('next-step')
    }
  }
}
</script>

<style scoped>
.goal-setting {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.goal-header {
  text-align: center;
  margin-bottom: 30px;
}

.goal-title {
  font-size: 24px;
  color: #333;
  margin: 0 0 10px 0;
}

.goal-subtitle {
  font-size: 14px;
  color: #999;
  margin: 0;
}

.goal-form {
  flex: 1;
  overflow-y: auto;
}

.form-group {
  margin-bottom: 25px;
}

.form-label {
  display: block;
  font-size: 14px;
  font-weight: 500;
  color: #333;
  margin-bottom: 8px;
}

.form-textarea {
  width: 100%;
  border: 1px solid #E0E0E0;
  border-radius: 8px;
  padding: 12px;
  font-size: 14px;
  resize: none;
  font-family: inherit;
  outline: none;
  transition: border-color 0.3s ease;
}

.form-textarea:focus {
  border-color: #4CAF50;
}

.form-select {
  width: 100%;
  border: 1px solid #E0E0E0;
  border-radius: 8px;
  padding: 12px;
  font-size: 14px;
  font-family: inherit;
  outline: none;
  background-color: white;
  cursor: pointer;
  transition: border-color 0.3s ease;
}

.form-select:focus {
  border-color: #4CAF50;
}

.priority-options {
  display: flex;
  gap: 15px;
}

.priority-item {
  flex: 1;
  border: 2px solid #E0E0E0;
  border-radius: 8px;
  padding: 15px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s ease;
}

.priority-item:hover {
  border-color: #4CAF50;
  background-color: rgba(76, 175, 80, 0.05);
}

.priority-item.selected {
  border-color: #4CAF50;
  background-color: rgba(76, 175, 80, 0.1);
}

.priority-icon {
  font-size: 32px;
  margin-bottom: 8px;
}

.priority-text {
  font-size: 14px;
  font-weight: 500;
  color: #333;
}

.goal-summary {
  background-color: #F5F5F5;
  padding: 20px;
  border-radius: 8px;
  margin-bottom: 20px;
}

.summary-title {
  font-size: 16px;
  color: #333;
  margin: 0 0 15px 0;
}

.summary-content {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.summary-item {
  display: flex;
  justify-content: space-between;
  padding: 10px 0;
  border-bottom: 1px solid #E0E0E0;
}

.summary-item:last-child {
  border-bottom: none;
}

.summary-label {
  font-size: 14px;
  color: #666;
}

.summary-value {
  font-size: 14px;
  font-weight: 500;
  color: #333;
}

.goal-actions {
  display: flex;
  justify-content: center;
  gap: 15px;
  margin-top: auto;
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