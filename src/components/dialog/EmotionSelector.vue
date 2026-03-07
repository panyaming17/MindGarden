<template>
  <div class="emotion-selector">
    <div class="emotion-header">
      <h3 class="emotion-title">情绪选择</h3>
      <p class="emotion-subtitle">请选择你当前的情绪状态</p>
    </div>
    
    <div class="emotion-grid">
      <div 
        v-for="emotion in emotions" 
        :key="emotion.id"
        class="emotion-item"
        :class="{ 'selected': selectedEmotion === emotion.id }"
        @click="selectEmotion(emotion.id)"
      >
        <div class="emotion-icon">{{ emotion.icon }}</div>
        <div class="emotion-name">{{ emotion.name }}</div>
        <div class="emotion-description">{{ emotion.description }}</div>
      </div>
    </div>
    
    <div class="emotion-detail" v-if="selectedEmotion">
      <h4 class="detail-title">情绪详情</h4>
      <p class="detail-text">{{ getSelectedEmotionDetail() }}</p>
    </div>
    
    <div class="emotion-actions">
      <button class="action-button secondary" @click="goBack">上一步</button>
      <button class="action-button primary" @click="goNext">下一步</button>
    </div>
  </div>
</template>

<script>
export default {
  name: 'EmotionSelector',
  data() {
    return {
      selectedEmotion: null,
      emotions: [
        { id: 1, name: '开心', icon: '😊', description: '心情愉快，充满正能量' },
        { id: 2, name: '平静', icon: '😌', description: '内心平和，情绪稳定' },
        { id: 3, name: '焦虑', icon: '😰', description: '感到不安，有些担忧' },
        { id: 4, name: '悲伤', icon: '😢', description: '情绪低落，心情沉重' },
        { id: 5, name: '愤怒', icon: '😠', description: '情绪激动，感到生气' },
        { id: 6, name: '疲惫', icon: '😴', description: '精神不振，感到疲倦' }
      ]
    }
  },
  methods: {
    selectEmotion(emotionId) {
      this.selectedEmotion = emotionId
    },
    getSelectedEmotionDetail() {
      const emotion = this.emotions.find(e => e.id === this.selectedEmotion)
      return emotion ? emotion.description : ''
    },
    goBack() {
      this.$emit('prev-step')
    },
    goNext() {
      if (this.selectedEmotion) {
        this.$emit('next-step')
      } else {
        alert('请先选择一个情绪')
      }
    }
  }
}
</script>

<style scoped>
.emotion-selector {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.emotion-header {
  text-align: center;
  margin-bottom: 30px;
}

.emotion-title {
  font-size: 24px;
  color: #333;
  margin: 0 0 10px 0;
}

.emotion-subtitle {
  font-size: 14px;
  color: #999;
  margin: 0;
}

.emotion-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
  margin-bottom: 30px;
}

.emotion-item {
  background-color: white;
  border: 2px solid #E0E0E0;
  border-radius: 12px;
  padding: 20px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s ease;
}

.emotion-item:hover {
  border-color: #4CAF50;
  transform: translateY(-4px);
  box-shadow: 0 4px 12px rgba(76, 175, 80, 0.2);
}

.emotion-item.selected {
  border-color: #4CAF50;
  background-color: rgba(76, 175, 80, 0.05);
}

.emotion-icon {
  font-size: 48px;
  margin-bottom: 10px;
}

.emotion-name {
  font-size: 16px;
  font-weight: 500;
  color: #333;
  margin-bottom: 5px;
}

.emotion-description {
  font-size: 12px;
  color: #999;
}

.emotion-detail {
  background-color: #F5F5F5;
  padding: 20px;
  border-radius: 8px;
  margin-bottom: 30px;
}

.detail-title {
  font-size: 16px;
  color: #333;
  margin: 0 0 10px 0;
}

.detail-text {
  font-size: 14px;
  color: #666;
  margin: 0;
}

.emotion-actions {
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