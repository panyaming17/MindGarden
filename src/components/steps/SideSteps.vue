<template>
  <div class="side-steps">
    <div 
      v-for="(step, index) in steps" 
      :key="step.id"
      class="step-item"
      :class="{ 'active': step.id === currentStep, 'completed': step.id < currentStep }"
      @click="handleStepClick(step.id)"
    >
      <div class="step-icon">{{ step.icon }}</div>
      <div class="step-info">
        <div class="step-title">{{ step.title }}</div>
        <div class="step-description">{{ step.description }}</div>
      </div>
      <div class="step-arrow" v-if="step.id < steps.length">→</div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'SideSteps',
  props: {
    steps: {
      type: Array,
      default: () => []
    },
    currentStep: {
      type: Number,
      default: 1
    }
  },
  methods: {
    handleStepClick(stepId) {
      this.$emit('step-change', stepId)
    }
  }
}
</script>

<style scoped>
.side-steps {
  width: 250px;
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.step-item {
  display: flex;
  align-items: center;
  padding: 15px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
  position: relative;
}

.step-item:hover {
  background-color: rgba(76, 175, 80, 0.05);
}

.step-item.active {
  background-color: rgba(76, 175, 80, 0.1);
  border-left: 3px solid #4CAF50;
}

.step-item.completed {
  opacity: 0.6;
}

.step-icon {
  font-size: 24px;
  margin-right: 15px;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #F5F5F5;
  border-radius: 50%;
}

.step-item.active .step-icon {
  background-color: #4CAF50;
}

.step-info {
  flex: 1;
}

.step-title {
  font-size: 16px;
  font-weight: 500;
  color: #333;
  margin-bottom: 5px;
}

.step-item.active .step-title {
  color: #4CAF50;
}

.step-description {
  font-size: 12px;
  color: #999;
}

.step-arrow {
  font-size: 20px;
  color: #E0E0E0;
  margin-left: 10px;
}

.step-item.active .step-arrow {
  color: #4CAF50;
}
</style>