<template>
  <div class="main-content">
    <BackGround />
    
    <!-- 首页/对话 -->
    <ChatApp v-if="activeFunction === 'home' || activeFunction === 'history'" :conversationData="conversationData" :activeFunction="activeFunction" @end-chat="handleEndChat" />
    
    <!-- 预警提醒 -->
    <div v-else-if="activeFunction === 'alerts'" class="alert-content">
      <AlertPage />
    </div>
    
    <!-- 情绪报告 -->
    <div v-else-if="activeFunction === 'reports'" class="function-content">
      <MoodReport />
    </div>
    <!-- 情绪记录 -->
    <div v-else-if="activeFunction === 'mood'" class="mood-content">
      <EmotionRecordPage />
    </div>
    <!-- 问卷自查 -->
    <div v-else-if="activeFunction === 'questionnaire'" class="questionnaire-content">
      <QuestionnairePage />
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
import MoodTrend from '../mood/MoodTrend.vue'
import MoodDiary from '../mood/MoodDiary.vue'
import MoodReport from '../mood/MoodReport.vue'
import QuestionnairePage from '../Questionnaire/QuestionnairePage.vue'
import EmotionRecordPage from '../emotion/EmotionRecordPage.vue'
import AlertPage from '../alert/AlertPage.vue'

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

// 处理结束对话事件
const handleEndChat = () => {
  console.log('结束对话事件触发')
  // 可以在这里添加额外的逻辑，比如更新会话列表等
}
</script>

<style scoped>
.main-content {
  background-color: #FEF3E2;
  position: relative;
  overflow-y: auto;
  overflow-x: hidden;
  display: flex;
  flex-direction: column;
  min-width: 0;
  height: 100%;
  flex: 1;
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
  width: 100%;
  height: 100%;
  margin: 0;
  background-color: transparent;
  padding: 0;
  border-radius: 0;
  box-shadow: none;
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
  width: 100%;
  height: 100%;
  overflow-y: auto;
  padding: 0;
  border-radius: 0;
}

.mood-content {
  position: relative;
  z-index: 1;
  width: 100%;
  height: 100%;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.mood-content .mood-trend {
  background: white;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  flex: 1;
  width: 20%;
  margin-bottom: 5px;
  min-height: 50%;
}

.mood-content .mood-diary {
  background: white;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  flex: 1;
  width: 100%;
  margin-top: 5px;
  min-height: 50%;
}

.alert-content {
  position: relative;
  z-index: 1;
  width: 100%;
  height: 100%;
  overflow-y: auto;
  padding: 0;
  border-radius: 0;
}

/* 滚动条样式 - 与项目其他滚动条风格统一 */
.main-content::-webkit-scrollbar {
  width: 4px;
}

.main-content::-webkit-scrollbar-track {
  background: rgba(241, 241, 241, 0.3);
  border-radius: 4px;
}

.main-content::-webkit-scrollbar-thumb {
  background: rgba(1, 146, 28, 0.3);
  border-radius: 4px;
  transition: background 0.3s ease;
}

.main-content::-webkit-scrollbar-thumb:hover {
  background: rgba(15, 158, 2, 0.6);
}

</style>