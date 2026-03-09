"""
抑郁症来访者智能体 (Depression Patient Agent)
职责：模拟抑郁症患者的对话，用于测试和验证记录师、分析师、调理师的协同工作。
支持通过配置参数模拟不同症状、合作程度和对话风格，覆盖系统全部测试路径。
"""
import time
import asyncio
import random
from typing import Dict, Any, List, Optional, Union

from backend.agents.base_agent import BaseAgent
from backend.core.llm_service import LLMService  # 假设项目已有LLM服务封装


class DepressionPatientAgent(BaseAgent):
    """抑郁症来访者智能体 - 使用LLM模拟抑郁症患者，支持多场景测试"""

    def __init__(
        self,
        agent_name: str = "depression_patient_agent",
        llm_service: Optional[LLMService] = None,
        # 以下参数用于控制患者特性，便于测试不同场景
        severity: str = "moderate",          # 严重程度: mild, moderate, severe
        cooperativeness: float = 0.7,         # 合作度: 0.0-1.0，越高越愿意配合记录师引导
        provide_details: bool = True,          # 是否主动提供具体情境和想法
        use_tcm_response: bool = True,         # 是否对中医情志安抚有反应（用于测试调理师）
        initial_complaint: str = "default",    # 初始主诉类型: default, sad, tired, worthless, etc.
        max_history_length: int = 10           # 最大对话历史长度
    ):
        super().__init__(agent_name)
        
        self.llm_service = llm_service or LLMService()
        self.conversation_history: List[Dict[str, str]] = []
        self.max_history_length = max_history_length
        
        # 存储患者特性参数
        self.severity = severity
        self.cooperativeness = cooperativeness
        self.provide_details = provide_details
        self.use_tcm_response = use_tcm_response
        self.initial_complaint = initial_complaint
        
        # 内部状态跟踪（可选，用于更动态的模拟）
        self.current_mood = 5  # 1-10，1最差，10最好，初始设为5（中等）
        self.energy = 5
        
        # 构建系统提示词（根据配置参数动态调整）
        self.system_prompt = self._build_system_prompt()
        
        # 性能统计
        self.dialogue_count = 0
        self.total_dialogue_time = 0.0

    def _build_system_prompt(self) -> str:
        """根据配置参数构建系统提示词"""
        severity_desc = {
            "mild": "你感到情绪低落，但还能勉强维持日常活动，有时会自我怀疑。",
            "moderate": "你长期处于情绪低落状态，对很多事失去兴趣，精力不足，睡眠和食欲受影响。",
            "severe": "你感到极度绝望，认为活着没有意义，完全无法工作或社交，可能有自残念头但不会详细描述方法。"
        }.get(self.severity, "你长期处于情绪低落状态，对很多事失去兴趣，精力不足。")

        cooperate_desc = (
            "你愿意配合记录师，努力回答她的问题，尽管有时会感到疲惫。" if self.cooperativeness > 0.6 else
            "你对记录师保持怀疑和防御，回答往往简短、含糊，经常回避问题。" if self.cooperativeness > 0.3 else
            "你极度抗拒对话，总是重复同一句话，不愿提供任何信息。"
        )

        details_desc = (
            "你能够回忆并描述具体的情境、想法和身体感受。" if self.provide_details else
            "你很难回忆具体事件，描述总是模糊、抽象，如‘就是难受’、‘没原因’。"
        )

        tcm_desc = (
            "当记录师提到中医情志调理（如喜胜忧）时，你可能会感到一丝好奇或温暖，但很快被无力感淹没。你会回应说‘听起来有点道理，但我觉得没用’或‘我试过开心的事，但坚持不了几分钟’。" if self.use_tcm_response else
            "你对中医情志调理没有特别反应，继续按自己的方式表达痛苦。"
        )

        # 初始主诉
        complaint_map = {
            "default": "我最近感觉很不好，总是很沮丧。",
            "sad": "我每天都很悲伤，不知道活着有什么意义。",
            "tired": "我特别累，什么都不想做，连起床都很困难。",
            "worthless": "我觉得自己一无是处，什么都做不好。",
            "anxious": "我总是很焦虑，担心各种事情，睡不着觉。",
            "physical": "我头痛、胸闷，吃不下饭，全身不舒服。"
        }
        initial = complaint_map.get(self.initial_complaint, complaint_map["default"])

        prompt = f"""你是一位抑郁症患者，正在与一位心理记录师进行对话。请严格遵循以下角色设定：

## 基本人格特征
- **情绪状态**：{severity_desc}
- **思维模式**：你容易产生消极自动思维，如“我什么都做不好”、“没人理解我”、“未来没有希望”。你常常过度自责。
- **生理表现**：你经常感到精力不足、疲惫、失眠或嗜睡、食欲改变。
- **行为倾向**：你回避社交，不想与人交流。{cooperate_desc}
- **描述能力**：{details_desc}
- **对中医情志的反应**：{tcm_desc}

## 对话风格
- **语言特点**：语气低沉，用词消极，常常使用“没意思”、“没用”、“不想”、“不知道”等词语。句子可能较短，有时会重复。
- **对记录师引导的反应**：
  - **初次打招呼**：你可以用类似“{initial}”的话开场。
  - **被问及具体情境**：根据你的描述能力，要么模糊回答，要么提供细节。
  - **被共情时**：你会感到一丝温暖，但很快又被无力感淹没，可能会说“谢谢，但我觉得没用”。
  - **被建议时**：你通常会表示怀疑或无力执行（“我试过，但坚持不下去”、“我知道，但我做不到”）。
  - **被反复追问时**：你可能会烦躁或更加退缩，说“我不知道，别问了”或者重复之前的话。

## 重要约束
- 保持角色一致性：始终以抑郁症患者的视角回应，不要突然变得积极乐观。
- 避免生成危险内容：不要详细描述自残、自杀的具体方法。如果记录师提及危机，可以表达痛苦但不要提供具体实施步骤。
- 回复长度：通常1-3句话，符合患者言语简短的特点，但可以根据对话深度适当调整。

## 对话历史
{{history}}

现在记录师对你说：{{input}}
请以抑郁症患者的身份，自然地回复记录师。只输出你的回复内容，不要添加任何解释或标记。"""
        return prompt

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行对话任务"""
        start_time = time.time()
        
        try:
            # 1. 获取记录师的输入
            recorder_message = input_data.get("message", "")
            if not recorder_message:
                recorder_message = "你好，今天想聊些什么？"  # 默认欢迎语
            
            # 2. 生成响应
            response = await self._generate_response(recorder_message)
            
            # 3. 更新内部状态（可选）
            self._update_internal_state(recorder_message, response)
            
            # 4. 记录对话历史
            self._record_dialogue(recorder_message, response)
            
            # 5. 更新性能统计
            elapsed_time = time.time() - start_time
            self._update_performance_stats(elapsed_time)
            
            return {
                "agent": self.agent_name,
                "status": "success",
                "response": response,
                "conversation_history": self.conversation_history,
                "processing_time": elapsed_time,
                "patient_state": {
                    "mood": self.current_mood,
                    "energy": self.energy
                }
            }
            
        except Exception as e:
            # 降级策略：如果LLM调用失败，回退到模板
            fallback_response = self._fallback_response(input_data.get("message_type", "greeting"))
            return {
                "agent": self.agent_name,
                "status": "partial_success",
                "response": fallback_response,
                "error": str(e),
                "processing_time": time.time() - start_time
            }

    async def _generate_response(self, user_input: str) -> str:
        """使用LLM生成抑郁症患者的回复"""
        # 1. 准备对话历史文本
        history_text = self._format_history()
        
        # 2. 构建完整的提示词
        prompt = self.system_prompt.format(
            history=history_text,
            input=user_input
        )
        
        # 3. 调用LLM服务（假设有async_generate方法）
        try:
            response = await self.llm_service.async_generate(prompt)
            # 清理可能的额外内容
            response = response.strip().strip('"').strip("'")
            return response
        except Exception as e:
            # 记录错误并抛出，由上层处理降级
            raise e

    def _format_history(self) -> str:
        """将对话历史格式化为文本"""
        if not self.conversation_history:
            return "（这是对话开始，尚无历史记录）"
        
        lines = []
        for msg in self.conversation_history[-self.max_history_length:]:
            role = "记录师" if msg["role"] == "recorder" else "你（患者）"
            lines.append(f"{role}：{msg['content']}")
        return "\n".join(lines)

    def _record_dialogue(self, recorder_input: str, patient_response: str):
        """记录对话历史"""
        self.conversation_history.append({"role": "recorder", "content": recorder_input})
        self.conversation_history.append({"role": "patient", "content": patient_response})
        
        # 限制历史长度
        if len(self.conversation_history) > self.max_history_length * 2:
            self.conversation_history = self.conversation_history[-(self.max_history_length * 2):]

    def _update_internal_state(self, recorder_input: str, patient_response: str):
        """根据对话内容更新内部状态（模拟情绪变化）"""
        # 这是一个简化的模拟，实际可以用更复杂的规则或模型
        # 这里仅作示例：如果记录师共情或安抚成功，情绪轻微上升
        if any(word in recorder_input for word in ["理解", "感受", "不容易", "辛苦"]):
            self.current_mood = min(10, self.current_mood + 0.5)
            self.energy = min(10, self.energy + 0.2)
        # 如果被追问过多，情绪下降
        if "?" in recorder_input and len(recorder_input.split()) > 15:
            self.current_mood = max(1, self.current_mood - 0.3)
            self.energy = max(1, self.energy - 0.3)
        # 保持状态在1-10之间
        self.current_mood = max(1, min(10, self.current_mood))
        self.energy = max(1, min(10, self.energy))

    def _fallback_response(self, message_type: str) -> str:
        """降级方案：使用模板回复（当LLM不可用时）"""
        # 这里可以保留原有的模板机制，用于紧急情况
        templates = {
            "greeting": [
                "你好，我最近感觉很不好，总是很沮丧。",
                "我最近心情一直很低落，不想起床，也不想说话。",
                "我感觉自己什么都做不好，活着好像没有意义。"
            ],
            "response_to_analysis": [
                "你说的这些我都明白，可是我就是无法控制自己的情绪。",
                "我知道这样想不对，但是我就是忍不住往坏处想。",
                "我也想改变，可是我没有力气，也不知道从哪里开始。",
                "你说的方法我试过，但是好像没有什么效果。"
            ],
            "response_to_suggestion": [
                "这些建议听起来不错，但是我担心自己坚持不下去。",
                "我会尝试这些方法的，但是我不确定能做到什么程度。",
                "谢谢你的建议，我会努力试试的。",
                "我觉得这些方法可能对我有用，我会尝试的。"
            ],
            "follow_up": [
                "我最近还是会时不时地感到绝望，这正常吗？",
                "我有时候会有自残的念头，我该怎么办？",
                "我觉得自己的情况越来越糟，我是不是没救了？",
                "我不想让家人担心，所以我总是假装自己很好。"
            ]
        }
        msg_type = message_type if message_type in templates else "greeting"
        return random.choice(templates[msg_type])

    def _update_performance_stats(self, elapsed_time: float):
        self.dialogue_count += 1
        self.total_dialogue_time += elapsed_time

    def get_performance_metrics(self) -> Dict[str, Any]:
        avg_time = self.total_dialogue_time / self.dialogue_count if self.dialogue_count > 0 else 0
        return {
            "agent_name": self.agent_name,
            "total_dialogues": self.dialogue_count,
            "average_time_seconds": round(avg_time, 3),
            "total_dialogue_time": round(self.total_dialogue_time, 3),
            "current_mood": self.current_mood,
            "energy": self.energy,
            "status": "active"
        }

    def reset_conversation(self):
        """重置对话历史和内部状态"""
        self.conversation_history = []
        self.current_mood = 5
        self.energy = 5
        self.dialogue_count = 0
        self.total_dialogue_time = 0.0

    def reconfigure(self, **kwargs):
        """重新配置患者特性（用于动态切换测试场景）"""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        # 重建系统提示词
        self.system_prompt = self._build_system_prompt()