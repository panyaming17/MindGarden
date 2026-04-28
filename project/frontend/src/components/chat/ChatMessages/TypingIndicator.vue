<template>
  <div class="typing-indicator">
    <div class="avatar">{{ roleAvatar }}</div>
    <div class="typing-content">
      <div class="role-name">{{ roleName }}</div>
      <div class="typing-dots">
        <span></span>
        <span></span>
        <span></span>
      </div>
    </div>
  </div>
</template>

<script setup>
const props = defineProps({
  role: {
    type: String,
    default: '记录师'
  }
})

const roleAvatar = computed(() => {
  switch(props.role) {
    case '记录师': return '记'
    case '分析师': return '分'
    case '调理师': return '调'
    default: return 'AI'
  }
})

const roleName = computed(() => `${props.role}正在分析中...`)
</script>

<style scoped>
.typing-indicator {
  display: flex;
  align-items: center;
  margin: 16px;
  animation: fadeIn 0.3s;
}

.avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 14px;
  font-weight: bold;
  margin-right: 12px;
}

.typing-content {
  background: white;
  padding: 12px 16px;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.role-name {
  font-size: 12px;
  color: #666;
  margin-bottom: 4px;
}

.typing-dots {
  display: flex;
  gap: 4px;
}

.typing-dots span {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #ccc;
  animation: bounce 1.4s infinite ease-in-out both;
}

.typing-dots span:nth-child(1) {
  animation-delay: -0.32s;
}

.typing-dots span:nth-child(2) {
  animation-delay: -0.16s;
}

@keyframes bounce {
  0%, 80%, 100% {
    transform: scale(0);
  }
  40% {
    transform: scale(1);
  }
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>