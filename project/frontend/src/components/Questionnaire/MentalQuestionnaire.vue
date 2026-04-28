<template>
  <div class="mental-questionnaire">
    <!-- 顶部标题区 -->
    <div class="questionnaire-header">
      <div class="title-icon">🧠</div>
      <h2 class="title">情绪小测</h2>
      <p class="subtitle">花2分钟了解你的情绪状态，我们会严格保密</p>
      
      <!-- 进度条 -->
      <div class="progress-container">
        <div 
          class="progress-bar" 
          :style="{ width: `${progressPercent}%` }"
        ></div>
        <span class="progress-text">{{ currentIndex + 1 }}/{{ totalQuestions }}</span><span>{{progressPercent}}%</span>
      </div>
    </div>

    <!-- 问卷内容区 -->
    <div class="question-content" v-if="!finished">
      <!-- 当前题目 -->
      <div class="question-card">
        <div class="question-number">第 {{ currentIndex + 1 }} 题</div>
        <div class="question-text">{{ currentQuestion.text }}</div>
        
        <!-- 选项列表 -->
        <div class="options-list">
          <div 
            v-for="(option, idx) in currentQuestion.options" 
            :key="idx"
            class="option-item"
            :class="{ active: selectedOption === idx }"
            @click="selectOption(idx)"
          >
            <div class="option-radio" :class="{ checked: selectedOption === idx }">
              {{ selectedOption === idx ? '✓' : '' }}
            </div>
            <div class="option-text">
              {{ option.label }}
              <span class="option-desc">({{ option.desc }})</span>
            </div>
          </div>
        </div>
        
        <!-- 操作按钮 -->
        <div class="btn-group">
          <el-button 
            type="text" 
            @click="prevQuestion"
            :disabled="currentIndex === 0"
          >
            上一题
          </el-button>
          <el-button 
            type="primary" 
            @click="nextQuestion"
            :disabled="selectedOption === null"
            class="next-btn"
          >
            {{ currentIndex === totalQuestions - 1 ? '完成测评' : '下一题' }}
          </el-button>
        </div>
      </div>
    </div>

    <!-- 结果展示区 -->
    <div class="result-content" v-else>
      <div class="result-card">
        <!-- 情绪图标 -->
        <div class="result-icon">
          <span v-if="totalScore <= 7">😊</span>
          <span v-else-if="totalScore <= 15">😐</span>
          <span v-else-if="totalScore <= 23">😟</span>
          <span v-else>😥</span>
        </div>
        
        <!-- 结果标题 -->
        <h3 class="result-title">{{ resultTitle }}</h3>
        
        <!-- 分数详情 -->
        <div class="score-details">
          <div class="score-item">
            <span class="label">PHQ-9（抑郁）得分：</span>
            <span class="value">{{ phq9Score }}/27</span>
            <span class="level">{{ phq9Level }}</span>
          </div>
          <div class="score-item">
            <span class="label">GAD-7（焦虑）得分：</span>
            <span class="value">{{ gad7Score }}/21</span>
            <span class="level">{{ gad7Level }}</span>
          </div>
          <div class="score-item total">
            <span class="label">综合得分：</span>
            <span class="value">{{ totalScore }}/48</span>
          </div>
        </div>
        
        <!-- 建议 -->
        <div class="suggestion">
          <h4>📝 给你的建议：</h4>
          <p>{{ suggestionText }}</p>
        </div>
        
        <!-- 提交按钮 -->
        <el-button 
          type="primary" 
          @click="submitResult"
          class="submit-btn"
        >
          提交测评结果
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { ElButton, ElMessage } from 'element-plus';


// 1. 定义问卷题库（PHQ-9 + GAD-7）
const questionnaireList = [
  // PHQ-9 抑郁量表
  {
    id: 'phq-1',
    type: 'phq9',
    text: '对做事提不起劲或没有兴趣',
    options: [
      { label: '完全没有', desc: '0天', score: 0 },
      { label: '有几天', desc: '1～4天', score: 1 },
      { label: '一半以上天数', desc: '5～9天', score: 2 },
      { label: '几乎每天', desc: '10～14天', score: 3 }
    ]
  },
  {
    id: 'phq-2',
    type: 'phq9',
    text: '感到心情低落、沮丧或绝望',
    options: [
      { label: '完全没有', desc: '0天', score: 0 },
      { label: '有几天', desc: '1～4天', score: 1 },
      { label: '一半以上天数', desc: '5～9天', score: 2 },
      { label: '几乎每天', desc: '10～14天', score: 3 }
    ]
  },
  {
    id: 'phq-3',
    type: 'phq9',
    text: '入睡困难、睡不安稳或睡眠过多',
    options: [
      { label: '完全没有', desc: '0天', score: 0 },
      { label: '有几天', desc: '1～4天', score: 1 },
      { label: '一半以上天数', desc: '5～9天', score: 2 },
      { label: '几乎每天', desc: '10～14天', score: 3 }
    ]
  },
  {
    id: 'phq-4',
    type: 'phq9',
    text: '感觉疲倦或没有活力',
    options: [
      { label: '完全没有', desc: '0天', score: 0 },
      { label: '有几天', desc: '1～4天', score: 1 },
      { label: '一半以上天数', desc: '5～9天', score: 2 },
      { label: '几乎每天', desc: '10～14天', score: 3 }
    ]
  },
  {
    id: 'phq-5',
    type: 'phq9',
    text: '食欲不振或吃太多',
    options: [
      { label: '完全没有', desc: '0天', score: 0 },
      { label: '有几天', desc: '1～4天', score: 1 },
      { label: '一半以上天数', desc: '5～9天', score: 2 },
      { label: '几乎每天', desc: '10～14天', score: 3 }
    ]
  },
  {
    id: 'phq-6',
    type: 'phq9',
    text: '觉得自己很糟，或觉得自己很失败，让自己或家人失望',
    options: [
      { label: '完全没有', desc: '0天', score: 0 },
      { label: '有几天', desc: '1～4天', score: 1 },
      { label: '一半以上天数', desc: '5～9天', score: 2 },
      { label: '几乎每天', desc: '10～14天', score: 3 }
    ]
  },
  {
    id: 'phq-7',
    type: 'phq9',
    text: '对事物专注有困难（例如阅读、看手机、看电视）',
    options: [
      { label: '完全没有', desc: '0天', score: 0 },
      { label: '有几天', desc: '1～4天', score: 1 },
      { label: '一半以上天数', desc: '5～9天', score: 2 },
      { label: '几乎每天', desc: '10～14天', score: 3 }
    ]
  },
  {
    id: 'phq-8',
    type: 'phq9',
    text: '动作或说话速度特别缓慢，或相反：烦躁、坐立不安',
    options: [
      { label: '完全没有', desc: '0天', score: 0 },
      { label: '有几天', desc: '1～4天', score: 1 },
      { label: '一半以上天数', desc: '5～9天', score: 2 },
      { label: '几乎每天', desc: '10～14天', score: 3 }
    ]
  },
  {
    id: 'phq-9',
    type: 'phq9',
    text: '有不如死掉或用某种方式伤害自己的念头',
    options: [
      { label: '完全没有', desc: '0天', score: 0 },
      { label: '有几天', desc: '1～4天', score: 1 },
      { label: '一半以上天数', desc: '5～9天', score: 2 },
      { label: '几乎每天', desc: '10～14天', score: 3 }
    ]
  },
  
  // GAD-7 焦虑量表
  {
    id: 'gad-1',
    type: 'gad7',
    text: '感觉紧张、焦虑或烦躁',
    options: [
      { label: '完全没有', desc: '0天', score: 0 },
      { label: '有几天', desc: '1～4天', score: 1 },
      { label: '一半以上天数', desc: '5～9天', score: 2 },
      { label: '几乎每天', desc: '10～14天', score: 3 }
    ]
  },
  {
    id: 'gad-2',
    type: 'gad7',
    text: '不能停止或控制担忧',
    options: [
      { label: '完全没有', desc: '0天', score: 0 },
      { label: '有几天', desc: '1～4天', score: 1 },
      { label: '一半以上天数', desc: '5～9天', score: 2 },
      { label: '几乎每天', desc: '10～14天', score: 3 }
    ]
  },
  {
    id: 'gad-3',
    type: 'gad7',
    text: '对各种事情过分担忧',
    options: [
      { label: '完全没有', desc: '0天', score: 0 },
      { label: '有几天', desc: '1～4天', score: 1 },
      { label: '一半以上天数', desc: '5～9天', score: 2 },
      { label: '几乎每天', desc: '10～14天', score: 3 }
    ]
  },
  {
    id: 'gad-4',
    type: 'gad7',
    text: '很难放松下来',
    options: [
      { label: '完全没有', desc: '0天', score: 0 },
      { label: '有几天', desc: '1～4天', score: 1 },
      { label: '一半以上天数', desc: '5～9天', score: 2 },
      { label: '几乎每天', desc: '10～14天', score: 3 }
    ]
  },
  {
    id: 'gad-5',
    type: 'gad7',
    text: '由于不安而无法静坐',
    options: [
      { label: '完全没有', desc: '0天', score: 0 },
      { label: '有几天', desc: '1～4天', score: 1 },
      { label: '一半以上天数', desc: '5～9天', score: 2 },
      { label: '几乎每天', desc: '10～14天', score: 3 }
    ]
  },
  {
    id: 'gad-6',
    type: 'gad7',
    text: '容易生气或发怒',
    options: [
      { label: '完全没有', desc: '0天', score: 0 },
      { label: '有几天', desc: '1～4天', score: 1 },
      { label: '一半以上天数', desc: '5～9天', score: 2 },
      { label: '几乎每天', desc: '10～14天', score: 3 }
    ]
  },
  {
    id: 'gad-7',
    type: 'gad7',
    text: '感到害怕，似乎有可怕的事情即将发生',
    options: [
      { label: '完全没有', desc: '0天', score: 0 },
      { label: '有几天', desc: '1～4天', score: 1 },
      { label: '一半以上天数', desc: '5～9天', score: 2 },
      { label: '几乎每天', desc: '10～14天', score: 3 }
    ]
  }
];

// 2. 响应式数据
const currentIndex = ref(0); // 当前题目索引
const selectedOption = ref(null); // 当前选中的选项索引
const answers = ref([]); // 用户答案列表
const finished = ref(false); // 是否完成问卷

// 3. 计算属性
const totalQuestions = computed(() => questionnaireList.length);
const currentQuestion = computed(() => questionnaireList[currentIndex.value]);
const progressPercent = computed(() => {
  if (finished.value) return 100;
  return (currentIndex.value / totalQuestions.value) * 100;
});

// PHQ-9 得分
const phq9Score = computed(() => {
  return answers.value
    .filter(item => item.type === 'phq9')
    .reduce((sum, item) => sum + item.score, 0);
});

// GAD-7 得分
const gad7Score = computed(() => {
  return answers.value
    .filter(item => item.type === 'gad7')
    .reduce((sum, item) => sum + item.score, 0);
});

// 综合得分
const totalScore = computed(() => phq9Score.value + gad7Score.value);

// PHQ-9 严重程度
const phq9Level = computed(() => {
  const score = phq9Score.value;
  if (score <= 4) return '无抑郁';
  if (score <= 9) return '轻度抑郁';
  if (score <= 14) return '中度抑郁';
  if (score <= 19) return '中重度抑郁';
  return '重度抑郁';
});

// GAD-7 严重程度
const gad7Level = computed(() => {
  const score = gad7Score.value;
  if (score <= 4) return '无焦虑';
  if (score <= 9) return '轻度焦虑';
  if (score <= 14) return '中度焦虑';
  return '重度焦虑';
});

// 结果标题
const resultTitle = computed(() => {
  if (totalScore.value <= 7) return '你的情绪状态很稳定👍';
  if (totalScore.value <= 15) return '你的情绪有轻微波动😐';
  if (totalScore.value <= 23) return '需要关注你的情绪状态😟';
  return '建议及时寻求专业帮助😥';
});

// 建议文本
const suggestionText = computed(() => {
  if (totalScore.value <= 7) {
    return '你的情绪状态整体良好，继续保持积极的生活方式，多和家人朋友沟通哦～';
  } else if (totalScore.value <= 15) {
    return '近期可能有一些小情绪，可以尝试通过运动、听音乐、散步等方式缓解，若持续不适可考虑聊聊。';
  } else if (totalScore.value <= 23) {
    return '你的情绪状态需要重视，建议进行专业的咨询性会谈，我们会为你匹配合适的咨询师。';
  } else {
    return '你的情绪状态显示较高风险，强烈建议立即联系专业心理医生或咨询师，寻求一对一的帮助。';
  }
});

// 4. 方法
// 选择选项
const selectOption = (idx) => {
  selectedOption.value = idx;
  // 轻动画反馈
  const optionEl = document.querySelector(`.option-item:nth-child(${idx + 1})`);
  if (optionEl) {
    optionEl.classList.add('selected-animation');
    setTimeout(() => {
      optionEl.classList.remove('selected-animation');
    }, 300);
  }
};

// 上一题
const prevQuestion = () => {
  if (currentIndex.value > 0) {
    currentIndex.value--;
    // 恢复上一题的选择
    const prevAnswer = answers.value.find(item => item.id === currentQuestion.value.id);
    selectedOption.value = prevAnswer ? prevAnswer.optionIdx : null;
  }
};

// 下一题/完成
const nextQuestion = () => {
  // 保存当前答案
  const currentAnswer = {
    id: currentQuestion.value.id,
    type: currentQuestion.value.type,
    text: currentQuestion.value.text,
    optionIdx: selectedOption.value,
    optionLabel: currentQuestion.value.options[selectedOption.value].label,
    score: currentQuestion.value.options[selectedOption.value].score
  };
  
  // 更新答案列表（替换已有答案或新增）
  const existingIdx = answers.value.findIndex(item => item.id === currentAnswer.id);
  if (existingIdx > -1) {
    answers.value[existingIdx] = currentAnswer;
  } else {
    answers.value.push(currentAnswer);
  }
  
  // 推进到下一题或完成
  if (currentIndex.value < totalQuestions.value - 1) {
    currentIndex.value++;
    selectedOption.value = null; // 重置选项
  } else {
      finished.value = true; // 完成问卷
  }
};

// 提交结果
const submitResult = () => {
  // 构造结构化数据（对接后端RecorderAgent）
  const resultData = {
    sessionId: `session_${Date.now()}`,
    phq9: {
      score: phq9Score.value,
      level: phq9Level.value,
      answers: answers.value.filter(item => item.type === 'phq9')
    },
    gad7: {
      score: gad7Score.value,
      level: gad7Level.value,
      answers: answers.value.filter(item => item.type === 'gad7')
    },
    totalScore: totalScore.value,
    needCounseling: totalScore.value >= 10, // 总分≥10建议咨询
    suggestion: suggestionText.value,
    submitTime: new Date().toISOString()
  };
  
  // 模拟提交到后端
  // console.log('提交的问卷结果：', resultData);
  
  // 提示用户
  ElMessage.success('测评结果已提交！我们会尽快为你跟进～');
  
  // 这里可以添加axios请求，把resultData发送到后端
  // axios.post('/api/v1/questionnaire/submit', resultData)
  //   .then(res => { ... })
  //   .catch(err => { ... });
};

// 初始化
onMounted(() => {
  selectedOption.value = null;
});
</script>

<style scoped>
.mental-questionnaire {
  max-width: 700px;
  margin: 20px auto;
  padding: 20px;
  font-family: "Microsoft YaHei", sans-serif;
}

/* 头部样式 */
.questionnaire-header {
  text-align: center;
  margin-bottom: 30px;
}

.title-icon {
  font-size: 40px;
  margin-bottom: 10px;
}

.title {
  font-size: 24px;
  color: #333;
  margin: 10px 0;
}

.subtitle {
  color: #666;
  font-size: 14px;
  margin-bottom: 20px;
}

/* 进度条 */
.progress-container {
  width: 100%;
  height: 8px;
  background: #f0f0f0;
  border-radius: 4px;
  margin: 0 auto;
  position: relative;
}

.progress-bar {
  height: 100%;
  background: #409eff;
  border-radius: 4px;
  transition: width 0.3s ease;
}

.progress-text {
  position: absolute;
  right: 0;
  top: 10px;
  font-size: 12px;
  color: #999;
}

/* 题目卡片 */
.question-card {
  background: #FEF3E2;
  border-radius: 12px;
  padding: 30px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.10);
}

.question-number {
  font-size: 14px;
  color: #409eff;
  margin-bottom: 10px;
}

.question-text {
  font-size: 18px;
  color: #333;
  margin-bottom: 20px;
  line-height: 1.5;
}

/* 选项列表 */
.options-list {
  margin-bottom: 30px;
}

.option-item {
  display: flex;
  align-items: center;
  padding: 15px 20px;
  border: 1px solid #e6e6e6;
  border-radius: 8px;
  margin-bottom: 10px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.option-item:hover {
  border-color: #409eff;
  background: #f8f9ff;
}

.option-item.active {
  background: #e6f7ff;
  border-color: #409eff;
  color: #409eff;
}

.option-radio {
  width: 20px;
  height: 20px;
  border: 1px solid #ccc;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 15px;
  font-size: 12px;
}

.option-radio.checked {
  background: #409eff;
  border-color: #409eff;
  color: #fff;
}

.option-text {
  flex: 1;
  display: flex;
  justify-content: space-between;
}

.option-desc {
  color: #999;
  font-size: 14px;
  margin-left: 10px;
}

/* 按钮组 */
.btn-group {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.next-btn {
  padding: 10px 30px;
  border-radius: 8px;
}

/* 选中动画 */
.selected-animation {
  animation: selectFlash 0.3s ease;
}

@keyframes selectFlash {
  0% { background: #e6f7ff; }
  50% { background: #b3d9ff; }
  100% { background: #e6f7ff; }
}

/* 结果页面 */
.result-content {
  margin-top: 20px;
}

.result-card {
  background: #ffffff;
  border-radius: 12px;
  padding: 10px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.08);
  text-align: center;
}

.result-icon {
  font-size: 60px;
  margin-bottom: 20px;
}

.result-title {
  font-size: 22px;
  color: #333;
  margin-bottom: 30px;
}

/* 分数详情 */
.score-details {
  text-align: left;
  margin: 0 auto 30px;
  max-width: 400px;
  background: #f8f9fa;
  padding: 20px;
  border-radius: 8px;
}

.score-item {
  display: flex;
  justify-content: space-between;
  padding: 10px 0;
  border-bottom: 1px solid #eee;
}

.score-item.total {
  font-weight: bold;
  border-bottom: none;
  margin-top: 5px;
}

.score-item .label {
  color: #666;
}

.score-item .value {
  color: #333;
  font-weight: 500;
}

.score-item .level {
  color: #409eff;
  margin-left: 10px;
}

/* 建议 */
.suggestion {
  text-align: left;
  margin: 0 auto 30px;
  max-width: 400px;
  line-height: 1.6;
}

.suggestion h4 {
  font-size: 16px;
  margin-bottom: 10px;
  color: #333;
}

.suggestion p {
  color: #666;
  font-size: 15px;
}

.submit-btn {
  padding: 12px 40px;
  border-radius: 8px;
  font-size: 16px;
}

/* 响应式适配 */
@media (max-width: 768px) {
  .mental-questionnaire {
    padding: 10px;
  }
  
  .question-card {
    padding: 20px;
  }
  
  .result-card {
    padding: 20px;
  }
  
  .score-details {
    padding: 15px;
  }
}
</style>