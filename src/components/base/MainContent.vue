<template>
  <div class="main-content">
    <BackGround />
    
    <!-- 首页/对话 -->
    <ChatApp v-if="activeFunction === 'home'" :conversationData="conversationData" />
    
    <!-- 预警提醒 -->
    <div v-else-if="activeFunction === 'alerts'" class="function-content">
      <h2>预警提醒</h2>
      <p>这里显示预警提醒内容</p>
    </div>
    
    <!-- 情绪报告 -->
    <div v-else-if="activeFunction === 'reports'" class="function-content">
      <h2>情绪报告</h2>
      <p>这里显示情绪报告内容</p>
    </div>
    <!-- 问卷自查 -->
     <div v-else-if="activeFunction === 'questionnaire'" class="questionnaire-content">
      <Questionnaire/>
    </div>
    <!-- 多智能体测试对话 -->
    <MultiAgentTest v-else-if="activeFunction === 'multi-agent'" />
  </div>
</template>

<script setup>
import { ref, defineProps, watch } from 'vue'
import BackGround from './BackGround.vue'
import ChatApp from '../chat/ChatApp.vue'
import MultiAgentTest from '../MultiAgentTest/MultiAgentTest.vue'
import Questionnaire from '../Questionnaire/MentalQuestionnaire.vue'

// 组件属性
const props = defineProps({
  // 外部传入的对话数据
  conversationData: {
    type: Object,
    default: null
  },
  // 当前激活的功能
  activeFunction: {
    type: String,
    default: 'home'
  }
})
</script>

<style scoped>
.main-content {
  background-color: #FEF3E2;
  position: relative;
  overflow: hidden;
  display: flex;
  min-width: 0;
  height: 100%;
  overflow-y: hidden;
}

/* 确保背景图在最底层 */
.background-container {
  z-index: 0;
}

/* 确保其他内容在背景图之上 */
.chat-container,
.function-content,
.questionnaire-content {
  position: relative;
  z-index: 1;
}

.greeting-section {
  z-index: 1;
  margin-bottom: 60px;
  text-align: center;
}

.greeting-text {
  font-size: 24px;
  color: #4CAF50;
  font-weight: 500;
  text-align: center;
  margin: 0;
}

.input-section {
  z-index: 1;
  width: 100%;
  max-width: 600px;
}

.input-container {
  background-color: white;
  border-radius: 8px;
  border: 1px solid #4CAF50;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.message-input {
  width: 100%;
  border: none;
  outline: none;
  padding: 20px;
  font-size: 16px;
  resize: none;
  min-height: 80px;
  font-family: inherit;
}

.message-input::placeholder {
  color: #999;
}

.input-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 20px 15px;
}

.character-count {
  font-size: 12px;
  color: #999;
}

.send-button {
  width: 30px;
  height: 30px;
  border-radius: 50%;
  background-color: #4CAF50;
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s ease;
}

.send-button:hover {
  background-color: #45a049;
  transform: scale(1.05);
}

.send-icon {
  color: white;
  font-size: 14px;
  font-weight: bold;
}

.conversation-ui {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 2;
  display: flex;
  flex-direction: column;
  background-color: #FEF3E2;
}

.top-bar {
  padding: 20px;
  display: flex;
  align-items: center;
}

.back-button {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background-color: white;
  color: #666;
  border: 1px solid #E0E0E0;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
}

.back-button:hover {
  background-color: #F5F5F5;
  color: #4CAF50;
  border-color: #4CAF50;
}

.back-icon {
  font-size: 18px;
}

.back-text {
  font-size: 14px;
}

.content-wrapper {
  display: flex;
  flex: 1;
  padding: 20px;
  gap: 20px;
}

.main-content-inner {
  flex: 1;
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  padding: 30px;
  /* overflow-y: auto; */
}
.function-content {
  position: relative;
  z-index: 1;
  max-width: 800px;
  margin: 40px auto;
  background-color: white;
  padding: 30px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.function-content h2 {
  color: #4CAF50;
  margin-bottom: 20px;
}

.function-content p {
  color: #666;
  line-height: 1.6;
}

.questionnaire-content {
  position: relative;
  z-index: 1;
  min-width: 1200px;
  padding: 10px;
  border-radius: 8px;

}

</style>