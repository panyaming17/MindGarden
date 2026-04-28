<template>
  <div class="top-steps">
    <div 
      v-for="(step, index) in steps" 
      :key="index"
      class="step-item"
      :class="{ 'active': index + 1 === currentStep, 'completed': index + 1 < currentStep }"
    >
      <div class="step-number">{{ index + 1 }}</div>
      <div class="step-title">{{ step }}</div>
      <div class="step-line" v-if="index < steps.length - 1"></div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'TopSteps',
  props: {
    currentStep: {
      type: Number,
      default: 1
    },
    totalSteps: {
      type: Number,
      default: 4
    }
  },
  computed: {
    steps() {
      return ['记录师', '分析师', '调理师', '总结确认'].slice(0, this.totalSteps)
    }
  }
}
</script>

<style scoped>
.top-steps {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
  background-color: white;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.step-item {
  display: flex;
  align-items: center;
  position: relative;
}

.step-number {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background-color: #E0E0E0;
  color: #666;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  font-size: 14px;
  transition: all 0.3s ease;
}

.step-item.active .step-number {
  background-color: #4CAF50;
  color: white;
}

.step-item.completed .step-number {
  background-color: #4CAF50;
  color: white;
}

.step-title {
  margin: 0 15px;
  font-size: 14px;
  color: #666;
  transition: all 0.3s ease;
}

.step-item.active .step-title {
  color: #4CAF50;
  font-weight: 500;
}

.step-line {
  width: 60px;
  height: 2px;
  background-color: #E0E0E0;
  margin: 0 10px;
  transition: all 0.3s ease;
}

.step-item.completed .step-line,
.step-item.active .step-line {
  background-color: #4CAF50;
}
</style>