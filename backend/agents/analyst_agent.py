import json
from typing import Dict, Any, Optional, List
from datetime import datetime
import uuid

from backend.agents.base_agent import BaseAgent
from backend.repositories.record_repository import RecordRepository
from backend.core.llm_service import LLMService


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
  "user_id": "用户ID",
  "created_at": "时间戳",
  "basic_info": {"age": null, "gender": null, "occupation": null, "main_issues": []},
  "emotional_timeline": {
    "summary": "整体情绪趋势总结",
    "trends": {"intensity": "描述", "tension": "描述", "complexity": "描述", "hedonic": "描述"},
    "key_events": [{"timestamp": "时间", "event": "事件描述", "four_dim": {...}}]
  },
  "cognitive_patterns": {
    "common_automatic_thoughts": ["思维1", "思维2"],
    "thinking_traps": ["灾难化", "读心术"],
    "core_beliefs": ["核心信念1"]
  },
  "situations": [{"time": "时间", "description": "情境", "related_thoughts": ["想法"]}],
  "intervention_history": [{"timestamp": "时间", "strategy": "策略", "effect": "效果"}],
  "current_focus": "当前核心议题"
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
"""

    def _generate_initial_archive(self, user_id: str, dialogues: List[Dict[str, Any]]) -> Dict[str, Any]:
        """调用LLM生成初始档案（基于全部历史对话）"""
        if not self.llm_service:
            raise Exception("LLM服务未初始化")

        # 构建对话历史文本
        history_text = ""
        for d in dialogues:
            role = "用户" if d["role"] == "user" else "助手"
            history_text += f"{role}: {d['content']}\n"

        prompt = f"用户ID: {user_id}\n\n对话记录:\n{history_text}\n\n{self.system_prompt_init}"
        response = self.llm_service.chat_completion(
            messages=[
                {"role": "system", "content": "你是一位专业的心理咨询分析师。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=1500
        )
        content = response.choices[0].message.content
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
            archive = {
                "user_id": user_id,
                "created_at": datetime.utcnow().isoformat(),
                "basic_info": {},
                "emotional_timeline": {},
                "cognitive_patterns": {},
                "situations": [],
                "intervention_history": [],
                "current_focus": ""
            }
        return archive

    def _update_archive(self, current_archive: Dict[str, Any], user_input: str, four_dim: Dict[str, Any]) -> Dict[str, Any]:
        """调用LLM增量更新档案"""
        if not self.llm_service:
            raise Exception("LLM服务未初始化")

        prompt = self.user_prompt_template.format(
            archive_json=json.dumps(current_archive, ensure_ascii=False, indent=2),
            user_input=user_input,
            four_dim_json=json.dumps(four_dim, ensure_ascii=False)
        )
        response = self.llm_service.chat_completion(
            messages=[
                {"role": "system", "content": self.system_prompt_update},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
            max_tokens=1000
        )
        content = response.choices[0].message.content
        try:
            if "```json" in content:
                start = content.find("```json") + 7
                end = content.find("```", start)
                content = content[start:end].strip()
            updated_archive = json.loads(content)
            # 确保必填字段存在
            if "user_id" not in updated_archive:
                updated_archive["user_id"] = current_archive.get("user_id")
            if "created_at" not in updated_archive:
                updated_archive["created_at"] = current_archive.get("created_at", datetime.utcnow().isoformat())
            return updated_archive
        except json.JSONDecodeError:
            # 如果解析失败，返回原档案（不更新）
            return current_archive

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
        strategy = self.repository.find_strategy(
            intensity_level=intensity_level,
            hedonic=four_dim["hedonic"],
            tension=four_dim["tension"],
            complexity=four_dim["complexity"]
        )
        return strategy

    def _build_advice(self, archive: Dict[str, Any], strategy: Dict[str, Any], four_dim: Dict[str, Any]) -> Dict[str, Any]:
        """构建干预建议JSON"""
        # 提取最近几个自动化思维
        thoughts = archive.get("cognitive_patterns", {}).get("common_automatic_thoughts", [])[-3:]
        advice = {
            "timestamp": datetime.utcnow().isoformat(),
            "current_focus": archive.get("current_focus", ""),
            "four_dim": four_dim,
            "fusion_mode": strategy.get("fusion_mode", "cbt_main_tcm_aux"),
            "strategy_content": strategy.get("strategy_content", ""),
            "cbt_techniques": strategy.get("cbt_techniques", ""),
            "tcm_methods": strategy.get("tcm_methods", ""),
            "key_thoughts": thoughts,
            "suggested_technique": "认知重构" if "cbt" in strategy.get("fusion_mode", "") else "疏肝理气"
        }
        return advice

    def analyze_process(self, user_id: str, user_input: str, four_dim: Dict[str, Any], dialogue_id: int = None) -> Dict[str, Any]:
        """处理分析的主入口"""
        # 1. 获取当前档案
        archive = self.repository.get_user_archive(user_id)
        if not archive:
            # 没有档案，需要基于历史对话生成初始档案
            # 获取用户所有历史对话（最多50条，避免超长）
            histories = self.repository.get_recent_dialogues(user_id, limit=50)
            archive = self._generate_initial_archive(user_id, histories)
            # 保存初始档案
            self.repository.save_user_archive(user_id, archive, version=1)
        else:
            # 增量更新档案
            archive = self._update_archive(archive, user_input, four_dim)
            # 保存更新后的档案（版本号+1）
            version = archive.get("version", 0) + 1
            self.repository.save_user_archive(user_id, archive, version=version)

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
        self.repository.save_advice(user_id, advice, dialogue_id)

        return advice

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行智能体任务"""
        user_id = input_data.get("user_id")
        user_input = input_data.get("user_input")
        four_dim = input_data.get("four_dim")
        dialogue_id = input_data.get("dialogue_id")

        if not user_id or not user_input or not four_dim:
            return {"status": "error", "message": "缺少必要参数"}

        try:
            advice = self.analyze_process(user_id, user_input, four_dim, dialogue_id)
            return {"status": "success", "data": advice}
        except Exception as e:
            return {"status": "error", "message": f"分析失败: {str(e)}"}