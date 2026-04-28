<template>
  <div class="record-report">
    <!-- 关键信息卡片 -->
    <div class="info-cards">
      <!-- 情绪词云 -->
      <div v-if="parsedEmotions.length" class="info-card emotions-card">
        <h3 class="card-title">😊 情绪感受</h3>
        <div class="emotion-wordcloud-container">
          <div 
            v-for="(emotion, index) in parsedEmotions" 
            :key="index"
            class="emotion-word"
            :style="getEmotionWordStyle(emotion, index)"
            :title="`${emotion.name}: 权重 ${emotion.weight.toFixed(2)}`"
          >
            {{ emotion.name }}
          </div>
        </div>
      </div>

      <!-- 身体症状 -->
      <div v-if="data?.physical_symptoms?.length" class="info-card symptoms-card">
        <h3 class="card-title">🧘 身体症状</h3>
        <div class="symptom-list">
          <div v-for="(symptom, index) in data.physical_symptoms" :key="index" class="symptom-item">
            <span class="symptom-dot"></span>
            <span>{{ symptom }}</span>
          </div>
        </div>
      </div>

      <!-- 行为表现 -->
      <div v-if="data?.behaviors?.length" class="info-card behaviors-card">
        <h3 class="card-title">⚙️ 行为表现</h3>
        <div class="behavior-list">
          <div v-for="(behavior, index) in data.behaviors" :key="index" class="behavior-item">
            <span class="behavior-icon">✓</span>
            <span>{{ behavior }}</span>
          </div>
        </div>
      </div>

      <!-- 思维陷阱 -->
      <div v-if="data?.automatic_thoughts?.length" class="info-card thoughts-card">
        <h3 class="card-title">💭 思维陷阱</h3>
        <div class="thought-list">
          <div v-for="(thought, index) in data.automatic_thoughts" :key="index" class="thought-item">
            <span class="thought-icon">⚠️</span>
            <span>{{ thought }}</span>
          </div>
        </div>
        <div v-if="data?.dominant_thinking_trap" class="dominant-trap">
          <span class="dominant-label">主导模式：</span>
          <span class="dominant-value">{{ data.dominant_thinking_trap }}</span>
        </div>
      </div>
    </div>

    <!-- 时间线 -->
    <div v-if="data?.situations?.length" class="timeline-section">
      <h3 class="section-title">📌 关键情境时间线</h3>
      <div class="timeline">
        <div 
          v-for="(situation, index) in sortedSituations" 
          :key="index"
          class="timeline-item"
        >
          <div class="timeline-marker">
            <div class="timeline-dot"></div>
            <div v-if="index < sortedSituations.length - 1" class="timeline-line"></div>
          </div>
          <div class="timeline-content">
            <div class="timeline-time">{{ formatTime(situation.time) }}</div>
            <div class="timeline-description">{{ situation.description }}</div>
            <div v-if="situation.related?.length" class="timeline-related">
              <span class="related-label">相关：</span>
              <span 
                v-for="(item, idx) in situation.related" 
                :key="idx"
                class="related-tag"
              >
                {{ item }}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 对话概况 -->
    <div v-if="data?.duration || data?.context" class="summary-section">
      <h3 class="section-title">📋 对话概况</h3>
      <div class="summary-cards">
        <div v-if="data.duration" class="summary-card">
          <div class="summary-icon">⏱️</div>
          <div class="summary-content">
            <div class="summary-label">持续时间</div>
            <div class="summary-value">{{ data.duration }}</div>
          </div>
        </div>
        <div v-if="data.context" class="summary-card full-width">
          <div class="summary-icon">📝</div>
          <div class="summary-content">
            <div class="summary-label">背景信息</div>
            <div class="summary-text">{{ data.context }}</div>
          </div>
        </div>
      </div>
    </div>

    <!-- 无数据提示 -->
    <div v-if="!hasData" class="no-data">
      <div class="no-data-icon">📝</div>
      <p>暂无记录数据</p>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  data: {
    type: Object,
    default: () => ({})
  }
})

// 情绪分类（正性/负性/中性）
const emotionCategories = {
  // 正性情绪 - 鲜艳颜色
  positive: ['开心', '满足', '好奇', '自信', '愉悦', '兴奋', '幸福', '感激', '希望', '乐观', 
             '平静', '放松', '温暖', '舒适', '安心', '期待', '喜悦', '快乐', '自豪', '感动',
             '满意', '欣慰', '振奋', '积极', '热情', '轻松', '惬意', '甜蜜', '温馨', '陶醉'],
  
  // 负性情绪 - 暗淡颜色
  negative: ['焦虑', '恐惧', '沮丧', '无助', '绝望', '愤怒', '悲伤', '担忧', '紧张', '压力',
             '痛苦', '烦恼', '郁闷', '烦躁', '失落', '孤独', '空虚', '疲惫', '崩溃', '绝望',
             '恐惧', '害怕', '不安', '焦虑', '抑郁', '自卑', '羞愧', '内疚', '怨恨', '嫉妒'],
  
  // 中性情绪 - 平淡颜色
  neutral: ['思考', '疑惑', '平淡', '冷静', '客观', '理性', '专注', '认真', '沉思', '观察',
            '等待', '犹豫', '迟疑', '麻木', '茫然', '困惑', '迷茫', '无所谓', '一般', '正常']
}

// 情绪颜色配置
const emotionColorSchemes = {
  positive: {
    colors: ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD', '#98D8C8', '#F7DC6F', '#BB8FCE', '#85C1E9'],
    bgColors: ['#FFF0F0', '#E8F8F5', '#EBF5FB', '#F0FDF4', '#FEFBF3', '#FAF0FF', '#F0FFFF', '#FEF9E7', '#F9F0FD', '#F4F9FC']
  },
  negative: {
    colors: ['#95A5A6', '#7F8C8D', '#616161', '#555555', '#424242', '#78909C', '#607D8B', '#546E7A', '#455A64', '#37474F'],
    bgColors: ['#F5F5F5', '#EEEEEE', '#E0E0E0', '#ECEFF1', '#CFD8DC', '#ECEFF1', '#ECEFF1', '#ECEFF1', '#ECEFF1', '#ECEFF1']
  },
  neutral: {
    colors: ['#90A4AE', '#78909C', '#607D8B', '#5D6D7E', '#7F8C8D', '#95A5A6', '#ABB2B9', '#99A3A4', '#869295', '#808B96'],
    bgColors: ['#F5F7FA', '#F8F9FA', '#FAFAFA', '#F4F6F7', '#F8F9FA', '#F5F5F5', '#F8F9FA', '#F8F9FA', '#F8F9FA', '#F8F9FA']
  }
}

// 获取情绪分类
const getEmotionCategory = (emotionName) => {
  if (emotionCategories.positive.includes(emotionName)) return 'positive'
  if (emotionCategories.negative.includes(emotionName)) return 'negative'
  return 'neutral'
}

// 解析情绪数据（支持多种格式）
const parsedEmotions = computed(() => {
  if (!props.data?.emotions) return []
  
  return props.data.emotions.map(item => {
    if (Array.isArray(item)) {
      return { name: item[0], weight: item[1] || 0.5, intensity: Math.round((item[1] || 0.5) * 10), description: '' }
    } else if (typeof item === 'string') {
      return { name: item, weight: 0.5, intensity: 5, description: '' }
    } else if (typeof item === 'object') {
      const name = item.type || item.name || item.emotion || ''
      const intensity = item.intensity || Math.round((item.weight || 0.5) * 10)
      const weight = item.weight || (item.intensity ? item.intensity / 10 : 0.5)
      return { 
        name, 
        weight, 
        intensity,
        description: item.description || ''
      }
    }
    return { name: String(item), weight: 0.5, intensity: 5, description: '' }
  }).sort((a, b) => b.weight - a.weight)
})

// 获取词云样式
const getEmotionWordStyle = (emotion, index) => {
  const category = getEmotionCategory(emotion.name)
  const scheme = emotionColorSchemes[category]
  
  // 根据权重计算字体大小 (14px - 36px)
  const minSize = 14
  const maxSize = 36
  const sizeRange = maxSize - minSize
  const fontSize = minSize + (emotion.weight * sizeRange)
  
  // 选择颜色（根据索引循环使用配色方案）
  const colorIndex = index % scheme.colors.length
  const textColor = scheme.colors[colorIndex]
  
  // 计算透明度（正性情绪更明显，负性情绪更暗淡）
  let opacity = 0.85
  if (category === 'positive') {
    opacity = 0.85 + (emotion.weight * 0.15)  // 0.85-1.0 鲜艳
  } else if (category === 'negative') {
    opacity = 0.5 + (emotion.weight * 0.25)   // 0.5-0.75 暗淡
  } else {
    opacity = 0.65 + (emotion.weight * 0.2)   // 0.65-0.85 平淡
  }
  
  // 随机旋转角度 (-15deg 到 15deg)
  const rotation = (Math.random() - 0.5) * 30
  
  // 随机位置偏移（创建词云效果）
  const translateX = (Math.random() - 0.5) * 20
  const translateY = (Math.random() - 0.5) * 20
  
  return {
    fontSize: `${fontSize}px`,
    fontWeight: emotion.weight > 0.7 ? '700' : emotion.weight > 0.4 ? '600' : '500',
    color: textColor,
    opacity: opacity,
    transform: `rotate(${rotation}deg) translate(${translateX}px, ${translateY}px)`,
    textShadow: category === 'positive' 
      ? `0 2px 8px rgba(255, 107, 107, ${opacity * 0.3})`
      : category === 'negative'
        ? `0 1px 4px rgba(0, 0, 0, ${opacity * 0.2})`
        : `0 1px 6px rgba(149, 165, 166, ${opacity * 0.2})`,
    animationDelay: `${index * 0.1}s`
  }
}

// 按时间排序的情境
const sortedSituations = computed(() => {
  if (!props.data?.situations) return []
  return [...props.data.situations].sort((a, b) => {
    return new Date(a.time) - new Date(b.time)
  })
})

// 是否有数据
const hasData = computed(() => {
  return props.data && (
    props.data.emotions?.length ||
    props.data.physical_symptoms?.length ||
    props.data.behaviors?.length ||
    props.data.automatic_thoughts?.length ||
    props.data.situations?.length ||
    props.data.duration ||
    props.data.context
  )
})

// 格式化时间
const formatTime = (timeString) => {
  if (!timeString) return '-'
  const date = new Date(timeString)
  return date.toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}
</script>

<style scoped>
.record-report {
  padding: 8px;
}

/* 信息卡片网格 */
.info-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 20px;
  margin-bottom: 32px;
}

.info-card {
  background: rgba(255, 255, 255, 0.9);
  border-radius: 16px;
  padding: 20px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
  border: 1px solid rgba(0, 0, 0, 0.05);
}

.card-title {
  font-size: 16px;
  font-weight: 600;
  color: #2c3e50;
  margin-bottom: 16px;
  display: flex;
  align-items: center;
  gap: 8px;
}

/* 情绪词云 */
.emotion-wordcloud-container {
  position: relative;
  min-height: 180px;
  padding: 24px;
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  align-items: center;
  gap: 16px;
  background: linear-gradient(135deg, #fafbfc 0%, #f5f7fa 100%);
  border-radius: 12px;
}

.emotion-word {
  display: inline-block;
  padding: 8px 16px;
  border-radius: 20px;
  cursor: default;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  white-space: nowrap;
  animation: wordFloatIn 0.6s ease-out forwards;
  opacity: 0;
  transform-origin: center center;
}

.emotion-word:hover {
  transform: scale(1.15) !important;
  z-index: 10;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
}

@keyframes wordFloatIn {
  from {
    opacity: 0;
    transform: translateY(20px) scale(0.8);
  }
  to {
    opacity: var(--final-opacity, 1);
    transform: translateY(0) scale(1);
  }
}

/* 症状列表 */
.symptom-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.symptom-item {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 14px;
  color: #555;
}

.symptom-dot {
  width: 8px;
  height: 8px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 50%;
  flex-shrink: 0;
}

/* 行为列表 */
.behavior-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.behavior-item {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 14px;
  color: #555;
}

.behavior-icon {
  width: 20px;
  height: 20px;
  background: linear-gradient(135deg, #81C784 0%, #4CAF50 100%);
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  flex-shrink: 0;
}

/* 思维列表 */
.thought-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.thought-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 16px;
  background: #fff8e1;
  border-radius: 12px;
  font-size: 14px;
  color: #e65100;
  font-weight: 500;
  border-left: 3px solid #ff9800;
}

.thought-icon {
  font-size: 16px;
  flex-shrink: 0;
}

.dominant-trap {
  margin-top: 16px;
  padding: 12px 16px;
  background: linear-gradient(135deg, #fff3e0 0%, #ffe0b2 100%);
  border-radius: 12px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.dominant-label {
  font-size: 13px;
  color: #666;
}

.dominant-value {
  font-size: 15px;
  font-weight: 600;
  color: #e65100;
}

/* 时间线 */
.timeline-section {
  margin-bottom: 32px;
}

.section-title {
  font-size: 18px;
  font-weight: 600;
  color: #2c3e50;
  margin-bottom: 20px;
  padding-bottom: 12px;
  border-bottom: 2px solid #e8e8e8;
}

.timeline {
  position: relative;
  padding-left: 32px;
}

.timeline-item {
  position: relative;
  padding-bottom: 24px;
}

.timeline-marker {
  position: absolute;
  left: -32px;
  top: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.timeline-dot {
  width: 16px;
  height: 16px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 50%;
  border: 3px solid white;
  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
  z-index: 1;
}

.timeline-line {
  width: 2px;
  flex: 1;
  background: linear-gradient(to bottom, #667eea, #764ba2);
  min-height: 60px;
  margin-top: 4px;
}

.timeline-content {
  background: rgba(255, 255, 255, 0.9);
  border-radius: 12px;
  padding: 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  border: 1px solid rgba(0, 0, 0, 0.05);
}

.timeline-time {
  font-size: 12px;
  color: #667eea;
  font-weight: 500;
  margin-bottom: 8px;
}

.timeline-description {
  font-size: 14px;
  color: #2c3e50;
  line-height: 1.6;
  margin-bottom: 8px;
}

.timeline-related {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;
  margin-top: 8px;
}

.related-label {
  font-size: 12px;
  color: #95a5a6;
}

.related-tag {
  padding: 4px 10px;
  background: #f0f0f0;
  border-radius: 12px;
  font-size: 12px;
  color: #666;
}

/* 概况部分 */
.summary-section {
  margin-bottom: 24px;
}

.summary-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 16px;
}

.summary-card {
  display: flex;
  align-items: flex-start;
  gap: 16px;
  background: rgba(255, 255, 255, 0.9);
  border-radius: 16px;
  padding: 20px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
  border: 1px solid rgba(0, 0, 0, 0.05);
}

.summary-card.full-width {
  grid-column: 1 / -1;
}

.summary-icon {
  font-size: 28px;
  flex-shrink: 0;
}

.summary-content {
  flex: 1;
}

.summary-label {
  font-size: 12px;
  color: #95a5a6;
  margin-bottom: 4px;
}

.summary-value {
  font-size: 16px;
  font-weight: 600;
  color: #2c3e50;
}

.summary-text {
  font-size: 14px;
  color: #555;
  line-height: 1.6;
}

/* 无数据 */
.no-data {
  text-align: center;
  padding: 60px 20px;
  color: #95a5a6;
}

.no-data-icon {
  font-size: 48px;
  margin-bottom: 16px;
  opacity: 0.5;
}

/* 响应式 */
@media (max-width: 768px) {
  .info-cards {
    grid-template-columns: 1fr;
  }

  .timeline {
    padding-left: 24px;
  }

  .timeline-marker {
    left: -24px;
  }

  .summary-cards {
    grid-template-columns: 1fr;
  }
}
</style>
