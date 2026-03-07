<template>
  <div class="report-card analysis-report">
    <h3 class="report-title">🔍 双通路分析报告</h3>
    <div class="meta-info">
      <span>分析ID: {{ report.report_id }}</span>
      <span>关联记录: {{ report.record_id }}</span>
      <span>置信度: {{ (report.confidence_score * 100).toFixed(0) }}%</span>
    </div>

    <!-- CBT 分析 -->
    <div class="section">
      <h4>🧠 CBT 认知分析</h4>
      <div v-if="report.cbt_analysis.distortions_detected?.length">
        <div v-for="(dist, idx) in report.cbt_analysis.distortions_detected" :key="idx" class="distortion-item">
          <strong>{{ dist.distortion_type }}</strong>：{{ dist.matched_thought }}
          <div class="challenge" v-if="dist.challenge_question">💡 挑战提问：{{ dist.challenge_question }}</div>
        </div>
      </div>
      <p v-else>未检测到明显认知扭曲。</p>
      <p class="summary">{{ report.cbt_analysis.summary }}</p>
    </div>

    <!-- 中医情志分析 -->
    <div class="section">
      <h4>🌿 中医情志分析</h4>
      <div class="tcm-dominant">
        <span class="tag emotion">{{ report.tcm_analysis.dominant_emotion.type }}</span>
        主导情志，强度 {{ report.tcm_analysis.dominant_emotion.intensity }}/10，
        影响脏腑：{{ report.tcm_analysis.dominant_emotion.affected_zang }}
      </div>
      <div v-if="report.tcm_analysis.inhibiting_emotion" class="tcm-relation">
        相胜关系：<span class="tag inhibiting">{{ report.tcm_analysis.inhibiting_emotion }}</span> 胜
        <span class="tag emotion">{{ report.tcm_analysis.dominant_emotion.type }}</span>
      </div>
      <div v-if="report.tcm_analysis.secondary_emotions?.length" class="tcm-secondary">
        次要情绪：
        <span v-for="(em, idx) in report.tcm_analysis.secondary_emotions" :key="idx" class="tag secondary">
          {{ em.type }}({{ em.intensity }})
        </span>
      </div>
    </div>

    <!-- 综合框架 -->
    <div class="section">
      <h4>📋 综合干预框架</h4>
      <p>{{ report.integrated_framework }}</p>
      <div class="priority-badge" :class="report.priority">
        {{ report.priority === 'CBT优先' ? '🧠 认知优先' : report.priority === '情志优先' ? '🌿 情志优先' : '⚖️ 双通路并重' }}
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'AnalysisReport',
  props: {
    report: { type: Object, required: true }
  }
}
</script>

<style scoped>
.report-card { /* 同记录报告样式，略 */ }
.tag {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 0.9rem;
  margin: 0 4px;
}
.tag.emotion {
  background: #f39c12;
  color: white;
}
.tag.inhibiting {
  background: #3498db;
  color: white;
}
.tag.secondary {
  background: #bdc3c7;
  color: #2c3e50;
}
.distortion-item {
  background: #f8f9fa;
  padding: 10px;
  border-radius: 6px;
  margin-bottom: 8px;
}
.challenge {
  color: #e67e22;
  margin-top: 5px;
  font-size: 0.95rem;
}
.summary {
  font-style: italic;
  color: #34495e;
  margin-top: 10px;
}
.priority-badge {
  display: inline-block;
  padding: 4px 12px;
  border-radius: 20px;
  background: #ecf0f1;
  font-weight: bold;
  margin-top: 10px;
}
.priority-badge.CBT优先 { background: #d4edda; color: #155724; }
.priority-badge.情志优先 { background: #d1ecf1; color: #0c5460; }
.priority-badge.并重 { background: #fff3cd; color: #856404; }
</style>