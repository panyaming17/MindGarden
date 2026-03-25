from typing import Dict, Any, Optional, List
from backend.agents.base_agent import BaseAgent
from backend.repositories.record_repository_new import RecordRepository
from backend.core.llm_service import LLMService
print("RecordRepository imported from:", RecordRepository.__module__)

class TherapistAgent(BaseAgent):
    """调理师智能体 - 负责生成自然回复"""

    def __init__(self, agent_name: str = "therapist_agent", llm_service: Optional[LLMService] = None):
        super().__init__(agent_name)
        self.repository = RecordRepository()
        self.llm_service = llm_service
        self._init_prompts()

    def _init_prompts(self):
        self.system_prompt = """你是一位温暖、真诚的心理咨询师。你的任务是帮助用户处理当下的情绪和想法。

【重要】你必须严格按照分析师提供的以下信息来构建回复：
- 当前核心议题
- 推荐的具体CBT技术
- 推荐的中医情志方法
- 融合模式（决定CBT与中医的先后顺序）

请遵循以下原则：
1. **先共情**：简短回应用户的感受，让用户感到被理解。
2. **再引导**：根据融合模式，自然地融入CBT和中医方法。不要机械列举术语，而是用口语化的方式表达。
3. **简洁有力**：回复控制在2-4句话，避免长篇大论。
4. **使用用户原话**：适当引用用户的关键词，让回复更贴心。
5. **开放结束**：用简短问题鼓励用户继续表达（如果需要）。

融合模式说明：
- cbt_main_tcm_aux：先CBT引导，再辅以中医建议
- tcm_first_then_cbt：先用中医方法平复，再进行CBT探讨
- parallel：两者交替或同时提及

请用自然、温暖的语言回复，像和朋友谈心一样，可以适当用些语气词，如，嗯、哦等。
"""

        self.user_prompt_template = """
用户最新发言："{user_input}"
对话背景（最近3轮）：
{recent_history}

【分析师建议】
- 核心议题：{current_focus}
- 自动化思维：{key_thoughts}
- 思维陷阱：{thinking_traps}
- 推荐CBT方法：{cbt_techniques}
- 推荐中医方法：{tcm_methods}
- 融合模式：{fusion_mode}

请根据以上信息生成回复。回复要像在和朋友谈心，先共情，再按融合模式自然融入具体方法，最后可用简短问题引导。
"""

    def _get_recent_history(self, user_id: str, limit: int = 3, session_id: Optional[str] = None) -> str:
        """获取最近几轮对话历史（用户+助手）"""
        histories = self.repository.get_recent_dialogues(user_id, limit=limit * 2, session_id=session_id)  # 获取足够条数
        history_str = ""
        for d in histories[-limit*2:]:
            role = "用户" if d["role"] == "user" else "助手"
            history_str += f"{role}: {d['content']}\n"
        return history_str.strip()

    def _build_prompt(self, user_input: str, recent_history: str, advice: Dict[str, Any]) -> str:
        """构建给LLM的提示词"""
        # 从advice中提取字段，提供默认值
        current_focus = advice.get("current_focus", "")
        key_thoughts = advice.get("key_thoughts", [])
        key_thoughts_str = "、".join(key_thoughts) if key_thoughts else "暂无"
        thinking_traps = advice.get("thinking_traps", [])
        thinking_traps_str = "、".join(thinking_traps) if thinking_traps else "暂无"
        cbt_techniques = advice.get("cbt_techniques", "")
        tcm_methods = advice.get("tcm_methods", "")
        fusion_mode = advice.get("fusion_mode", "cbt_main_tcm_aux")

        return self.user_prompt_template.format(
            user_input=user_input,
            recent_history=recent_history,
            current_focus=current_focus,
            key_thoughts=key_thoughts_str,
            thinking_traps=thinking_traps_str,
            cbt_techniques=cbt_techniques,
            tcm_methods=tcm_methods,
            fusion_mode=fusion_mode
        )

    async def generate_response(self, user_id: str, user_input: str, advice: Optional[Dict[str, Any]] = None, session_id: Optional[str] = None) -> str:
        """生成回复的主入口"""
        if not self.llm_service:
            raise Exception("LLM服务未初始化")

        # 获取最近对话历史
        print(f"DEBUG: 调理师智能体 - 获取用户最近的对话历史，用户ID: {user_id}, 会话ID: {session_id}")
        recent_history = self._get_recent_history(user_id, limit=3, session_id=session_id)
        print(f"DEBUG: 调理师智能体 - 最近对话历史: {recent_history}")

        # 如果没有提供建议，则获取最新建议
        print("DEBUG: 调理师智能体 - 获取分析师建议")
        if advice is None:
            advice = self.repository.get_latest_advice(user_id)
            if advice:
                # 提取advice_json字段的内容
                advice = advice.get("advice_json", advice)
                print(f"DEBUG: 调理师智能体 - 获取到最新建议: {advice}")
            else:
                # 若无建议，使用默认建议（空字典，提示词会使用默认值）
                advice = {}
                print("DEBUG: 调理师智能体 - 未获取到建议，使用默认建议")

        # 构建提示词
        print("DEBUG: 调理师智能体 - 构建提示词")
        prompt = self._build_prompt(user_input, recent_history, advice)
        print(f"DEBUG: 调理师智能体 - 提示词长度: {len(prompt)}")

        # 调用LLM
        print("DEBUG: 调理师智能体 - 调用LLM服务生成回复")
        reply = await self._get_llm_response(
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=500
        )
        reply = reply.strip()
        print(f"DEBUG: 调理师智能体 - LLM生成回复: {reply}")

        # 存储回复
        print("DEBUG: 调理师智能体 - 存储助手回复到数据库")
        self.repository.save_dialogue(
            user_id=user_id,
            role="assistant",
            content=reply,
            four_dim=None,
            is_valuable=False,
            session_id=session_id
        )
        print("DEBUG: 调理师智能体 - 回复存储成功")

        return reply

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行智能体任务"""
        user_id = input_data.get("user_id")
        user_input = input_data.get("user_input")
        advice = input_data.get("advice")  # 可选，如果不提供则自动获取最新建议
        session_id = input_data.get("session_id")

        if not user_id or not user_input:
            return {"status": "error", "message": "缺少必要参数"}

        try:
            reply = await self.generate_response(user_id, user_input, advice, session_id)
            return {"status": "success", "data": {"reply": reply}}
        except Exception as e:
            return {"status": "error", "message": f"生成回复失败: {str(e)}"}
    
    async def _get_llm_response(self, messages, temperature, max_tokens):
        result = await self.llm_service.chat_completion(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        if isinstance(result, str):
            return result
        elif isinstance(result, dict) and 'choices' in result and result['choices']:
            return result['choices'][0]['message']['content']
        else:
            raise ValueError("LLM 响应格式异常")