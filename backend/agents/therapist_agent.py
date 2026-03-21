from typing import Dict, Any, Optional, List
from backend.agents.base_agent import BaseAgent
from backend.repositories.record_repository import RecordRepository
from backend.core.llm_service import LLMService


class TherapistAgent(BaseAgent):
    """调理师智能体 - 负责生成自然回复"""

    def __init__(self, agent_name: str = "therapist_agent", llm_service: Optional[LLMService] = None):
        super().__init__(agent_name)
        self.repository = RecordRepository()
        self.llm_service = llm_service
        self._init_prompts()

    def _init_prompts(self):
        self.system_prompt = """你是一位温暖、专业且善于融合中西医的心理咨询师。你的任务是根据用户的最新发言、对话历史和专家提供的干预建议，生成一段自然、共情、有针对性的回复。
- 回复要像真人咨询师说话，避免机械重复。
- 按照干预建议中的融合模式组织内容（如先中医后CBT）。
- 针对用户的具体问题，灵活运用建议中的策略要点。
- 如果建议中提到了具体的CBT技术或中医方法，请自然地融入对话，不要生硬列举。
- 保持语言亲切、平和，避免说教。
- 如果用户没有提供足够信息，可以适当提问引导，但不要急于下结论。
"""

        self.user_prompt_template = """
用户历史发言（最近3轮）：
{recent_history}

用户最新发言："{user_input}"

专家干预建议：
- 当前核心议题：{current_focus}
- 融合模式：{fusion_mode}
- 策略要点：{strategy_content}
- 需要关注的自动化思维：{key_thoughts}

请生成回复。
"""

    def _get_recent_history(self, user_id: str, limit: int = 3) -> str:
        """获取最近几轮对话历史（用户+助手）"""
        histories = self.repository.get_recent_dialogues(user_id, limit=limit * 2)  # 获取足够条数
        # 按时间倒序，但我们需要正序的最近3轮（用户+助手交替）
        # 简单取最后几条
        history_str = ""
        for d in histories[-limit*2:]:
            role = "用户" if d["role"] == "user" else "助手"
            history_str += f"{role}: {d['content']}\n"
        return history_str.strip()

    def _build_prompt(self, user_input: str, recent_history: str, advice: Dict[str, Any]) -> str:
        """构建给LLM的提示词"""
        key_thoughts = advice.get("key_thoughts", [])
        key_thoughts_str = "、".join(key_thoughts) if key_thoughts else "暂无"
        return self.user_prompt_template.format(
            recent_history=recent_history,
            user_input=user_input,
            current_focus=advice.get("current_focus", "请继续倾诉"),
            fusion_mode=advice.get("fusion_mode", "cbt_main_tcm_aux"),
            strategy_content=advice.get("strategy_content", "请倾听用户的烦恼，给予温暖回应。"),
            key_thoughts=key_thoughts_str
        )

    def generate_response(self, user_id: str, user_input: str, advice: Optional[Dict[str, Any]] = None) -> str:
        """生成回复的主入口"""
        if not self.llm_service:
            raise Exception("LLM服务未初始化")

        # 获取最近对话历史
        recent_history = self._get_recent_history(user_id, limit=3)

        # 如果没有提供建议，则获取最新建议
        if advice is None:
            advice = self.repository.get_latest_advice(user_id)
            if not advice:
                # 若无建议，使用默认安慰话术
                return "我听到了你的诉说，愿意多和我聊聊吗？"

        prompt = self._build_prompt(user_input, recent_history, advice)

        response = self.llm_service.chat_completion(
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=500
        )
        reply = response.choices[0].message.content.strip()

        # 存储助手的回复
        self.repository.save_dialogue(
            user_id=user_id,
            role="assistant",
            content=reply,
            four_dim=None,  # 助手回复没有四维
            is_valuable=False
        )

        return reply

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行智能体任务"""
        user_id = input_data.get("user_id")
        user_input = input_data.get("user_input")
        advice = input_data.get("advice")  # 可选，如果不提供则自动获取最新建议

        if not user_id or not user_input:
            return {"status": "error", "message": "缺少必要参数"}

        try:
            reply = self.generate_response(user_id, user_input, advice)
            return {"status": "success", "data": {"reply": reply}}
        except Exception as e:
            return {"status": "error", "message": f"生成回复失败: {str(e)}"}