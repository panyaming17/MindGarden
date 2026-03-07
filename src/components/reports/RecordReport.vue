<template>
  <div class="report-card record-report">
    <h3 class="report-title">📝 情绪记录报告</h3>
    <div class="meta-info">
      <span>记录ID: {{ report.record_id }}</span>
      <span>时间: {{ formatDate(report.timestamp) }}</span>
    </div>

    <div class="section">
      <h4>情境描述</h4>
      <p>{{ report.situation }}</p>
    </div>

    <div class="section">
      <h4>自动思维</h4>
      <ul>
        <li v-for="(thought, idx) in report.automatic_thoughts" :key="idx">
          {{ thought }}
        </li>
      </ul>
    </div>

    <div class="section">
      <h4>情绪分析</h4>
      <div v-for="(emotion, idx) in report.emotions" :key="idx" class="emotion-item">
        <span class="emotion-type">{{ emotion.type }}</span>
        <span class="emotion-intensity">强度: {{ emotion.intensity }}/10</span>
        <span v-if="emotion.description" class="emotion-desc">({{ emotion.description }})</span>
      </div>
    </div>

    <div class="section" v-if="report.physical_sensations?.length">
      <h4>身体感受</h4>
      <ul>
        <li v-for="(sensation, idx) in report.physical_sensations" :key="idx">
          {{ sensation }}
        </li>
      </ul>
    </div>

    <div class="section" v-if="report.summary">
      <h4>简要总结</h4>
      <p>{{ report.summary }}</p>
    </div>
  </div>
</template>

<script>
export default {
  name: 'RecordReport',
  props: {
    report: {
      type: Object,
      required: true
    }
  },
  methods: {
    formatDate(timestamp) {
      return new Date(timestamp).toLocaleString('zh-CN')
    }
  }
}
</script>

<style scoped>
.report-card {
  background: white;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
  margin-bottom: 20px;
  font-family: 'Microsoft YaHei', sans-serif;
}
.report-title {
  font-size: 1.5rem;
  margin-bottom: 10px;
  color: #2c3e50;
  border-bottom: 2px solid #42b983;
  padding-bottom: 8px;
}
.meta-info {
  display: flex;
  justify-content: space-between;
  color: #7f8c8d;
  font-size: 0.9rem;
  margin-bottom: 20px;
}
.section {
  margin-bottom: 20px;
}
.section h4 {
  font-size: 1.2rem;
  color: #34495e;
  margin-bottom: 10px;
  border-left: 4px solid #3498db;
  padding-left: 8px;
}
.emotion-item {
  display: flex;
  align-items: baseline;
  gap: 10px;
  margin-bottom: 5px;
}
.emotion-type {
  font-weight: bold;
  color: #e67e22;
}
.emotion-intensity {
  color: #2ecc71;
}
.emotion-desc {
  color: #95a5a6;
  font-style: italic;
}
ul {
  margin: 0;
  padding-left: 20px;
}
li {
  line-height: 1.6;
}
</style>