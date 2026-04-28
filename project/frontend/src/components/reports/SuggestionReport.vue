<template>
  <div class="report-card suggestion-report">
    <h3 class="report-title">💡 个性化疏导方案</h3>
    <div class="meta-info">
      <span>方案ID: {{ report.suggestion_id }}</span>
      <span>基于分析: {{ report.report_id }}</span>
    </div>

    <div class="section">
      <h4>🎯 聚焦问题</h4>
      <ul>
        <li v-for="(issue, idx) in report.target_issues" :key="idx">{{ issue }}</li>
      </ul>
    </div>

    <div class="section">
      <h4>⚡ 核心理念</h4>
      <div class="principles">
        <span v-for="(principle, idx) in report.core_principles" :key="idx" class="principle-tag">
          {{ principle }}
        </span>
      </div>
    </div>

    <div class="section">
      <h4>📅 每日建议</h4>
      <div v-for="(item, idx) in report.daily_suggestions" :key="idx" class="suggestion-item" :class="item.type">
        <div class="suggestion-header">
          <span class="suggestion-title">{{ item.title }}</span>
          <span class="suggestion-duration">{{ item.duration }}分钟</span>
          <span class="suggestion-type" :class="item.type">{{ item.type }}</span>
        </div>
        <p class="suggestion-desc">{{ item.description }}</p>
      </div>
    </div>

    <div class="section" v-if="report.emergency_tips?.length">
      <h4>🚨 紧急应对</h4>
      <ul>
        <li v-for="(tip, idx) in report.emergency_tips" :key="idx">{{ tip }}</li>
      </ul>
    </div>

    <div class="encouragement">
      {{ report.encouragement }}
    </div>
  </div>
</template>

<script>
export default {
  name: 'SuggestionReport',
  props: {
    report: { type: Object, required: true }
  }
}
</script>

<style scoped>
.report-card { /* 基础样式 */ }
.principles {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.principle-tag {
  background: #f0f0f0;
  padding: 4px 10px;
  border-radius: 20px;
  font-size: 0.9rem;
  border: 1px solid #ddd;
}
.suggestion-item {
  background: #f9f9f9;
  border-radius: 8px;
  padding: 12px;
  margin-bottom: 12px;
  border-left: 4px solid #ccc;
}
.suggestion-item.认知 { border-left-color: #3498db; }
.suggestion-item.行为 { border-left-color: #2ecc71; }
.suggestion-item.情志 { border-left-color: #f39c12; }
.suggestion-item.身体 { border-left-color: #9b59b6; }
.suggestion-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}
.suggestion-title {
  font-weight: bold;
  font-size: 1.1rem;
}
.suggestion-duration {
  background: #ecf0f1;
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 0.8rem;
}
.suggestion-type {
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 0.8rem;
  color: white;
}
.suggestion-type.认知 { background: #3498db; }
.suggestion-type.行为 { background: #2ecc71; }
.suggestion-type.情志 { background: #f39c12; }
.suggestion-type.身体 { background: #9b59b6; }
.suggestion-desc {
  margin: 0;
  color: #2c3e50;
}
.encouragement {
  margin-top: 20px;
  padding: 15px;
  background: #fef9e7;
  border-radius: 8px;
  font-style: italic;
  text-align: center;
  color: #b9770e;
  border: 1px dashed #f1c40f;
}
</style>