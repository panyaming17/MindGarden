import json
from typing import Dict, Any, Optional, List
from datetime import datetime
import uuid

from backend.agents.base_agent import BaseAgent
from backend.repositories.record_repository_new import RecordRepository
from backend.core.llm_service import LLMService
print("RecordRepository imported from:", RecordRepository.__module__)

class AnalystAgent(BaseAgent):
    """分析师智能体 - 负责档案维护与策略匹配"""

    def __init__(self, agent_name: str = "analyst_agent", llm_service: Optional[LLMService] = None):
        super().__init__(agent_name)
        self.repository = RecordRepository()
        self.llm_service = llm_service
        self._init_prompts()

    def _init_prompts(self):
        """初始化提示词模板"""
        self.system_prompt_init = """你是一位专业的心理咨询分析师。你的任务是基于用户的完整对话历史，构建一份详细的用户认知档案。档案应包含以下内容（JSON格式）：
{
  "session_id": "会话ID",
  "user_id": "用户ID",
  "created_at": "2026-03-25T10:00:00Z",
  "updated_at": "2026-03-25T11:00:00Z",

  "basic_info": {
    "age": null,
    "gender": null,
    "occupation": null,
    "main_issues": []
  },

  "emotional_timeline": {
    "summary": "整体情绪趋势描述（由LLM生成）",
    "trends": {
      "intensity": "描述（如‘波动，近期升高’）",
      "hedonic": "描述（如‘始终负性’）",
      "tension": "描述（如‘由高转中’）",
      "complexity": "描述（如‘简单为主，偶有复杂’）"
    },
    "key_events": [
      {
        "timestamp": "2026-03-25T10:05:00Z",
        "event": "事件简述（如‘用户提到毕业求职困难’）",
        "description": "详细描述或用户原话",
        "four_dim": { "intensity": 6.0, "hedonic": "负性", "tension": "中", "complexity": "简单" }
      }
    ]
  },

  "cognitive_patterns": {
    "common_automatic_thoughts": [ "我没有找到工作", "我感觉自己配不上" ],
    "thinking_traps": [ "过度概括", "情绪化推理", "心理过滤", "低估自我" ],
    "core_beliefs": [ "我无能", "我不值得被认可" ]
  },

  "situations": [
    {
      "timestamp": "2026-03-25T10:10:00Z",
      "description": "情境描述（如‘投递简历后迟迟未收到回复’）",
      "related_thoughts": [ "我配不上" ],
      "emotional_response": "沮丧、无助"
    }
  ],

  "intervention_history": [
    {
      "timestamp": "2026-03-25T10:15:00Z",
      "strategy": "干预策略名称（如‘认知解离 + 降低期待’）",
      "effect": "用户反馈效果（如‘感觉没那么绝望了，但还是很担心’）"
    }
  ],

  "current_focus": "当前最核心的议题（如‘求职过程中的自我怀疑与匹配焦虑’）",

  "summary": "会话整体摘要（便于快速理解）"
}
请根据对话记录提取信息，确保真实准确。"""

        self.system_prompt_update = """你是一位专业的心理咨询分析师。现有用户的认知档案如下（JSON格式）。请根据用户的最新发言和情绪分析结果，**增量更新**档案。只修改或补充需要变化的字段，保持其他部分不变。输出更新后的完整档案（JSON格式）。"""

        self.user_prompt_template = """
当前用户的认知档案：
{archive_json}

用户最新发言："{user_input}"
情绪分析结果：{four_dim_json}

请基于这些信息，增量更新用户的认知档案。注意：
- 如果发言包含自动化思维，添加到 cognitive_patterns.common_automatic_thoughts（去重）。
- 如果识别出思维陷阱，添加到 cognitive_patterns.thinking_traps（去重）。
- 如果有重要事件，添加到 emotional_timeline.key_events。
- 更新 emotional_timeline.summary 和 trends 以反映最新状态。
- 更新 current_focus 为当前最核心的议题。
- 更新 updated_at 为当前时间。
- 确保所有字段都符合要求的结构。
"""

    async def _generate_initial_archive(self, user_id: str, dialogues: List[Dict[str, Any]]) -> Dict[str, Any]:
        """调用LLM生成初始档案（基于全部历史对话）"""
        if not self.llm_service:
            raise Exception("LLM服务未初始化")

        # 构建对话历史文本
        history_text = ""
        for d in dialogues:
            role = "用户" if d["role"] == "user" else "助手"
            history_text += f"{role}: {d['content']}\n"

        prompt = f"用户ID: {user_id}\n\n对话记录:\n{history_text}\n\n{self.system_prompt_init}"
        print(f"DEBUG: 分析师智能体 - 准备调用LLM生成初始档案，用户ID: {user_id}")
        content = await self._get_llm_response(
            messages=[
                {"role": "system", "content": "你是一位专业的心理咨询分析师。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=1500
        )
        print(f"DEBUG: 分析师智能体 - LLM调用成功，返回内容长度: {len(content)}")
        # 尝试提取JSON
        try:
            # 如果返回内容包含```json ... ```，则提取
            if "```json" in content:
                start = content.find("```json") + 7
                end = content.find("```", start)
                content = content[start:end].strip()
            archive = json.loads(content)
        except json.JSONDecodeError:
            # 如果解析失败，返回默认结构
            current_time = datetime.utcnow().isoformat()
            archive = {
                "session_id": "",
                "user_id": user_id,
                "created_at": current_time,
                "updated_at": current_time,
                "basic_info": {
                    "age": None,
                    "gender": None,
                    "occupation": None,
                    "main_issues": []
                },
                "emotional_timeline": {
                    "summary": "",
                    "trends": {
                        "intensity": "",
                        "hedonic": "",
                        "tension": "",
                        "complexity": ""
                    },
                    "key_events": []
                },
                "cognitive_patterns": {
                    "common_automatic_thoughts": [],
                    "thinking_traps": [],
                    "core_beliefs": []
                },
                "situations": [],
                "intervention_history": [],
                "current_focus": "",
                "summary": ""
            }
        return archive

    async def _update_archive(self, current_archive: Dict[str, Any], user_input: str, four_dim: Dict[str, Any]) -> Dict[str, Any]:
        """调用LLM增量更新档案"""
        if not self.llm_service:
            raise Exception("LLM服务未初始化")

        # 从 current_archive 中提取 archive_json 字段
        archive_data = current_archive.get("archive_json", current_archive)

        prompt = self.user_prompt_template.format(
            archive_json=json.dumps(archive_data, ensure_ascii=False, indent=2),
            user_input=user_input,
            four_dim_json=json.dumps(four_dim, ensure_ascii=False)
        )
        print(f"DEBUG: 分析师智能体 - 准备调用LLM增量更新档案")
        content = await self._get_llm_response(
            messages=[
                {"role": "system", "content": self.system_prompt_update},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
            max_tokens=1000
        )
        print(f"DEBUG: 分析师智能体 - LLM调用成功，返回内容长度: {len(content)}")
        try:
            if "```json" in content:
                start = content.find("```json") + 7
                end = content.find("```", start)
                content = content[start:end].strip()
            updated_archive = json.loads(content)
            # 确保必填字段存在
            if "session_id" not in updated_archive:
                updated_archive["session_id"] = current_archive.get("session_id", "")
            if "user_id" not in updated_archive:
                updated_archive["user_id"] = current_archive.get("user_id")
            if "created_at" not in updated_archive:
                updated_archive["created_at"] = current_archive.get("created_at", datetime.utcnow().isoformat())
            # 更新 updated_at 字段
            updated_archive["updated_at"] = datetime.utcnow().isoformat()
            # 确保其他必填字段存在
            if "basic_info" not in updated_archive:
                updated_archive["basic_info"] = {
                    "age": None,
                    "gender": None,
                    "occupation": None,
                    "main_issues": []
                }
            if "emotional_timeline" not in updated_archive:
                updated_archive["emotional_timeline"] = {
                    "summary": "",
                    "trends": {
                        "intensity": "",
                        "hedonic": "",
                        "tension": "",
                        "complexity": ""
                    },
                    "key_events": []
                }
            if "cognitive_patterns" not in updated_archive:
                updated_archive["cognitive_patterns"] = {
                    "common_automatic_thoughts": [],
                    "thinking_traps": [],
                    "core_beliefs": []
                }
            if "situations" not in updated_archive:
                updated_archive["situations"] = []
            if "intervention_history" not in updated_archive:
                updated_archive["intervention_history"] = []
            if "current_focus" not in updated_archive:
                updated_archive["current_focus"] = ""
            if "summary" not in updated_archive:
                updated_archive["summary"] = ""
            return updated_archive
        except json.JSONDecodeError:
            # 如果解析失败，返回原档案（不更新）
            return archive_data

    def _match_strategy(self, four_dim: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """从策略库匹配策略"""
        # 将连续强度转为等级
        def to_level(val):
            if val < 4:
                return "低"
            elif val < 7:
                return "中"
            else:
                return "高"
        intensity_level = to_level(four_dim["intensity"])
        print(f"DEBUG: 分析师智能体 - 尝试匹配策略，参数: intensity_level={intensity_level}, hedonic={four_dim['hedonic']}, tension={four_dim['tension']}, complexity={four_dim['complexity']}")
        strategy = self.repository.find_strategy(
            intensity_level=intensity_level,
            hedonic=four_dim["hedonic"],
            tension=four_dim["tension"],
            complexity=four_dim["complexity"]
        )
        if strategy:
            print(f"DEBUG: 分析师智能体 - 成功从数据库匹配到策略: {strategy}")
        else:
            print("DEBUG: 分析师智能体 - 未从数据库匹配到策略，将使用默认策略")
        return strategy

    def _build_advice(self, archive: Dict[str, Any], strategy: Dict[str, Any], four_dim: Dict[str, Any]) -> Dict[str, Any]:
        """构建干预建议JSON"""
        # 提取最近几个自动化思维
        thoughts = archive.get("cognitive_patterns", {}).get("common_automatic_thoughts", [])[-3:]
        # 提取思维陷阱
        thinking_traps = archive.get("cognitive_patterns", {}).get("thinking_traps", [])
        advice = {
            "timestamp": datetime.utcnow().isoformat(),
            "current_focus": archive.get("current_focus", ""),
            "four_dim": four_dim,
            "fusion_mode": strategy.get("fusion_mode", "cbt_main_tcm_aux"),
            "strategy_content": strategy.get("strategy_content", ""),
            "cbt_techniques": strategy.get("cbt_techniques", ""),
            "tcm_methods": strategy.get("tcm_methods", ""),
            "key_thoughts": thoughts,
            "thinking_traps": thinking_traps,
            "suggested_technique": "认知重构" if "cbt" in strategy.get("fusion_mode", "") else "疏肝理气"
        }
        return advice

    async def analyze_process(self, user_id: str, user_input: str, four_dim: Dict[str, Any], dialogue_id: int = None, session_id: str = None) -> Dict[str, Any]:
        """处理分析的主入口"""
        # 1. 获取当前档案
        archive_record = self.repository.get_user_archive(user_id, session_id)
        if not archive_record:
            # 没有档案，需要基于历史对话生成初始档案
            # 获取用户所有历史对话（最多50条，避免超长）
            histories = self.repository.get_recent_dialogues(user_id, limit=50, session_id=session_id)
            archive = await self._generate_initial_archive(user_id, histories)
            # 添加会话ID到档案
            archive["session_id"] = session_id
            # 保存初始档案
            self.repository.save_user_archive(user_id, session_id, archive, version=1)
        else:
            # 从档案记录中提取 archive_json
            archive_data = archive_record.get("archive_json", {})
            # 增量更新档案
            updated_archive = await self._update_archive(archive_record, user_input, four_dim)
            # 确保会话ID存在
            updated_archive["session_id"] = session_id
            # 保存更新后的档案（版本号+1）
            version = archive_record.get("version", 0) + 1
            self.repository.save_user_archive(user_id, session_id, updated_archive, version=version)
            archive = updated_archive

        # 2. 匹配策略
        strategy = self._match_strategy(four_dim)
        if not strategy:
            # 如果没有匹配到，使用默认策略
            strategy = {
                "fusion_mode": "cbt_main_tcm_aux",
                "strategy_content": "【CBT核心】试着把你的想法写下来，然后问自己：这个想法有证据吗？\n【中医辅助】可以做几次深呼吸，让身体放松。",
                "cbt_techniques": "认知重构",
                "tcm_methods": "调息放松"
            }

        # 3. 构建建议
        advice = self._build_advice(archive, strategy, four_dim)

        # 4. 保存建议
        self.repository.save_advice(user_id, advice, dialogue_id, session_id)

        return advice

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行智能体任务"""
        user_id = input_data.get("user_id")
        user_input = input_data.get("user_input")
        four_dim = input_data.get("four_dim")
        dialogue_id = input_data.get("dialogue_id")
        session_id = input_data.get("session_id")

        if not user_id or not user_input or not four_dim:
            return {"status": "error", "message": "缺少必要参数"}

        try:
            advice = await self.analyze_process(user_id, user_input, four_dim, dialogue_id, session_id)
            return {"status": "success", "data": advice}
        except Exception as e:
            return {"status": "error", "message": f"分析失败: {str(e)}"}
    
    async def _get_llm_response(self, messages, temperature, max_tokens):
        print(f"DEBUG: 分析师智能体 - 调用LLM服务，提供商: {self.llm_service.provider}")
        result = await self.llm_service.chat_completion(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            try_all_providers=False
        )
        print(f"DEBUG: 分析师智能体 - LLM服务返回结果: {result}")
        # 如果 result 是字符串，直接返回；否则尝试提取 content
        if isinstance(result, str):
            return result
        elif isinstance(result, dict) and 'choices' in result and result['choices']:
            return result['choices'][0]['message']['content']
        else:
            raise ValueError("LLM 响应格式异常")