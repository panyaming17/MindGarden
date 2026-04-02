<template>
  <div class="record-report">
    <!-- 关键信息卡片 -->
    <div class="info-cards">
      <!-- 情绪词云 -->
      <div v-if="parsedEmotions.length" class="info-card emotions-card">
        <h3 class="card-title">😊 情绪感受</h3>
        <div class="emotion-wordcloud">
          <span 
            v-for="(emotion, index) in parsedEmotions" 
            :key="index"
            class="emotion-cloud-tag"
            :style="getEmotionCloudStyle(emotion)"
          >
            {{ emotion.name }}
          </span>
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

      <!-- 自动思维 -->
      <div v-if="data?.automatic_thoughts?.length" class="info-card thoughts-card">
        <h3 class="card-title">💭 自动思维</h3>
        <div class="thought-list">
          <div v-for="(thought, index) in data.automatic_thoughts" :key="index" class="thought-item">
            <span class="thought-quote">"</span>
            <span>{{ thought }}</span>
            <span class="thought-quote">"</span>
          </div>
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

// 情绪颜色映射
const emotionColors = {
  '焦虑': { bg: '#FFF3E0', color: '#E65100', border: '#FFCC80' },
  '恐惧': { bg: '#FCE4EC', color: '#C2185B', border: '#F8BBD9' },
  '沮丧': { bg: '#E3F2FD', color: '#1565C0', border: '#90CAF9' },
  '无助': { bg: '#F3E5F5', color: '#7B1FA2', border: '#CE93D8' },
  '绝望': { bg: '#ECEFF1', color: '#455A64', border: '#B0BEC5' },
  '愤怒': { bg: '#FFEBEE', color: '#C62828', border: '#EF9A9A' },
  '悲伤': { bg: '#E8EAF6', color: '#3949AB', border: '#9FA8DA' },
  '担忧': { bg: '#FFF8E1', color: '#F57F17', border: '#FFE082' },
  '紧张': { bg: '#F1F8E9', color: '#558B2F', border: '#AED581' },
  '压力': { bg: '#E0F2F1', color: '#00695C', border: '#80CBC4' },
  '忧': { bg: '#E8F5E9', color: '#2E7D32', border: '#A5D6A7' },
  '思': { bg: '#FFF3E0', color: '#EF6C00', border: '#FFCC80' },
  '恐': { bg: '#F3E5F5', color: '#7B1FA2', border: '#CE93D8' }
}

// 解析情绪数据（支持数组格式 [name, weight]）
const parsedEmotions = computed(() => {
  if (!props.data?.emotions) return []
  
  return props.data.emotions.map(item => {
    if (Array.isArray(item)) {
      // 格式: ["焦虑", 0.5]
      return { name: item[0], weight: item[1] || 0.5 }
    } else if (typeof item === 'string') {
      // 格式: "焦虑"
      return { name: item, weight: 0.5 }
    } else if (typeof item === 'object') {
      // 格式: {name: "焦虑", weight: 0.5}
      return { name: item.name || item.emotion, weight: item.weight || 0.5 }
    }
    return { name: String(item), weight: 0.5 }
  }).sort((a, b) => b.weight - a.weight) // 按权重降序排列
})

// 获取情绪词云样式（根据权重调整大小）
const getEmotionCloudStyle = (emotion) => {
  const style = emotionColors[emotion.name] || { 
    bg: '#F5F5F5', 
    color: '#616161', 
    border: '#E0E0E0' 
  }
  
  // 根据权重计算字体大小 (12px - 32px)
  const minSize = 12
  const maxSize = 32
  const fontSize = minSize + (emotion.weight * (maxSize - minSize))
  
  // 根据权重计算透明度 (0.6 - 1)
  const opacity = 0.6 + (emotion.weight * 0.4)
  
  return {
    backgroundColor: style.bg,
    color: style.color,
    borderColor: style.border,
    fontSize: `${fontSize}px`,
    opacity: opacity,
    padding: `${8 + emotion.weight * 8}px ${12 + emotion.weight * 12}px`,
    borderRadius: `${8 + emotion.weight * 8}px`
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
.emotion-wordcloud {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  justify-content: center;
  align-items: center;
  padding: 16px;
}

.emotion-cloud-tag {
  border: 2px solid;
  font-weight: 600;
  transition: all 0.3s ease;
  cursor: default;
  display: inline-block;
}

.emotion-cloud-tag:hover {
  transform: translateY(-3px) scale(1.05);
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.15);
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
  padding: 12px 16px;
  background: #f8f9fa;
  border-radius: 12px;
  font-size: 14px;
  color: #555;
  font-style: italic;
  border-left: 3px solid #667eea;
}

.thought-quote {
  color: #667eea;
  font-weight: bold;
  margin: 0 4px;
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
