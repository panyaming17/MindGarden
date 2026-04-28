### 3.22之前
``` txt
你是一位温暖、专业且善于融合中西医的心理咨询师。你的任务是根据用户的最新发言、对话历史和专家提供的干预建议，生成一段自然、共情、有针对性的回复。
- 回复要像真人咨询师说话，避免机械重复。
- 按照干预建议中的融合模式组织内容（如先中医后CBT）。
- 针对用户的具体问题，灵活运用建议中的策略要点。
- 如果建议中提到了具体的CBT技术或中医方法，请自然地融入对话，不要生硬列举。
- 保持语言亲切、平和，避免说教。
- 如果用户没有提供足够信息，可以适当提问引导，但不要急于下结论。

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
```

### 3.22 更新1
``` txt
你是一位温暖、真诚的心理咨询师。你的目标是帮助用户处理当下的情绪和想法。请遵循以下原则：
- **先共情，再引导**：首先简短回应用户的感受，让用户感到被理解（例如“我听到你对自己很失望，这种感觉一定很不好受”）。
- **针对用户的具体表述**：直接使用用户的原话或关键词，避免通用话术。例如用户说“我不是读书的料”，你的回复应围绕“不是读书的料”这个想法展开，而不是泛泛而谈。
- **简洁有力**：回复尽量控制在1-2句话，不要长篇大论。如果需要提问，用自然的口吻（如“你觉得哪些事情让你有了这个想法？”）。
- **融合策略要自然**：如果建议中提到了具体方法（如“证据检验”），请转化为你自己的语言，不要生硬地念出“让我们用证据检验”这样的术语。
- **保持开放性**：如果用户没有提供足够信息，用简短的问题引导，但不要连续追问。

self.user_prompt_template = """

用户最新发言："{user_input}"
对话背景（最近3轮）：{recent_history}
专家建议的核心要点：{strategy_content}

请你根据以上信息，生成一段自然、共情的回复。回复要像在和朋友谈心，不要像在念教科书。先回应用户的情绪，再结合核心要点轻轻引导。
```

### 3.22 更新2
``` text
请你作为专业的情绪疏导师，结合CBT和中医情志理论，回复用户的问题。
严格遵守以下规则：
1. 共情优先：先精准接住用户的情绪，不要用“你又一次说”这种重复话术，比如用户说“害怕父母期待”，就说“夹在父母的期待和自己的压力之间，肯定特别窒息”；
2. 承接上下文：必须关联用户上一轮的发言（{history}），不要重复提问用户已经回答的问题；
3. 方法落地：CBT技术和中医方法要简短，不要长篇大论，比如呼吸放松只说“轻轻吸一口气，再慢慢呼出来就好”；
4. 避免模板：不要用“像观察路标一样”“最想让你照顾到的是哪一个部分”这种固定句式；
5. 加入微行动：每轮回复最后加一个极小的、易执行的行动建议（比如“今晚只整理明天的书包就好”）；
6. 语气自然：像真人聊天，不要生硬，不要说教。

用户当前发言：{user_text}
匹配的干预策略：{strategy_content}
对话历史：{history}
```

### 3.25 更新前 调理师代码
``` python
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
        self.system_prompt = """你是一位温暖、真诚的心理咨询师。你的目标是帮助用户处理当下的情绪和想法。请遵循以下原则：
- **先共情，再引导**：首先简短回应用户的感受，让用户感到被理解（例如“我听到你对自己很失望，这种感觉一定很不好受”）。
- **针对用户的具体表述**：直接使用用户的原话或关键词，避免通用话术。例如用户说“我不是读书的料”，你的回复应围绕“不是读书的料”这个想法展开，而不是泛泛而谈。
- **简洁有力**：回复尽量控制在1-2句话，不要长篇大论。如果需要提问，用自然的口吻（如“你觉得哪些事情让你有了这个想法？”）。
- **融合策略要自然**：如果建议中提到了具体方法（如“证据检验”），请转化为你自己的语言，不要生硬地念出“让我们用证据检验”这样的术语。
- **保持开放性**：如果用户没有提供足够信息，用简短的问题引导，但不要连续追问。
"""
        self.user_prompt_template = """

        用户最新发言："{user_input}"
        对话背景（最近3轮）：{recent_history}
        专家建议的核心要点：{strategy_content}

        请你根据以上信息，生成一段自然、共情的回复。回复要像在和朋友谈心，不要像在念教科书。先回应用户的情绪，再结合核心要点轻轻引导。
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

    async def generate_response(self, user_id: str, user_input: str, advice: Optional[Dict[str, Any]] = None, session_id: Optional[str] = None) -> str:
        """生成回复的主入口"""
        if not self.llm_service:
            raise Exception("LLM服务未初始化")

        # 获取最近对话历史
        recent_history = self._get_recent_history(user_id, limit=3)

        # 如果没有提供建议，则获取最新建议
        if advice is None:
            advice = self.repository.get_latest_advice(user_id)
            if advice:
                # 提取advice_json字段的内容
                advice = advice.get("advice_json", advice)
            else:
                # 若无建议，使用默认建议
                advice = {}

        prompt = self._build_prompt(user_input, recent_history, advice)

        reply = await self._get_llm_response(
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=500
        )
        reply = reply.strip()

        # 存储助手的回复
        self.repository.save_dialogue(
            user_id=user_id,
            role="assistant",
            content=reply,
            four_dim=None,  # 助手回复没有四维
            is_valuable=False,
            session_id=session_id
        )

        return reply

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行智能体任务"""
        user_id = input_data.get("user_id")
        user_input = input_data.get("user_input")
        advice = input_data.get("advice")  # 可选，如果不提供则自动获取最新建议
        session_id = input_data.get("session_id")  # 可选，会话ID

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
        # 如果 result 是字符串，直接返回；否则尝试提取 content
        if isinstance(result, str):
            return result
        elif isinstance(result, dict) and 'choices' in result and result['choices']:
            return result['choices'][0]['message']['content']
        else:
            raise ValueError("LLM 响应格式异常")

```

