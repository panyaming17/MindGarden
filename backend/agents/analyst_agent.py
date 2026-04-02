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
  "title": "会话标题（基于会话核心情景内容生成的简洁标题，不超过15字）",

  "basic_info": {
    "age": null,
    "gender": null,
    "occupation": null, 
    "main_issues": [] # 主要问题列表（如‘工作压力’，‘关系问题’）
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
        "timestamp": "2026-03-25T10:05:00Z（可以提取用户描述发生的时间，也可以通过询问用户确认）", 
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
                "title": "新会话",
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
            # 确保title字段存在
            if "title" not in updated_archive:
                updated_archive["title"] = current_archive.get("title", "会话")
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
        """构建干预建议 JSON"""
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

    async def _save_realtime_insight(self, user_id: str, session_id: str, 
                                    archive: Dict[str, Any], four_dim: Dict[str, Any],
                                    dialogue_id: Optional[int] = None):
        """实时保存分析洞察数据（包括四维数据增量更新）"""
        try:
            # 从档案中提取认知分析数据
            cognitive_patterns = archive.get("cognitive_patterns", {})
            emotional_timeline = archive.get("emotional_timeline", {})
            
            # 构建洞察数据
            insight_data = {
                "common_automatic_thoughts": cognitive_patterns.get("common_automatic_thoughts", []),
                "thinking_traps": cognitive_patterns.get("thinking_traps", []),
                "core_beliefs": cognitive_patterns.get("core_beliefs", []),
                "cognitive_mappings": [],  # 暂时为空，后续可以通过 LLM 生成
                "tcm_dominant_emotion": None,  # 暂时为空，后续可以通过 LLM 生成
                "tcm_related_organs": [],
                "tcm_qi_dynamics": None,
                "tcm_interpretation": None,
                "cbt_perspective": None,
                "tcm_perspective": None,
                "emotional_trend": emotional_timeline.get("summary", "")
            }
            
            # 保存到数据库（原有的认知分析字段）
            self.repository.save_analysis_insight(
                user_id=user_id,
                session_id=session_id,
                insight_data=insight_data,
                dialogue_id=dialogue_id
            )
            
            # 新增：增量更新四维数据统计
            intensity = four_dim.get("intensity")
            hedonic = four_dim.get("hedonic")
            tension = four_dim.get("tension")
            
            self.repository.update_four_dim_statistics(
                user_id=user_id,
                session_id=session_id,
                dialogue_id=dialogue_id,
                intensity_value=intensity,
                hedonic_label=hedonic,
                tension_label=tension
            )
            
            # 新增：每 2 轮对话调用一次 LLM 分析复杂度
            # 获取当前会话的对话数量
            recent_dialogues = self.repository.get_recent_dialogues(user_id, limit=100, session_id=session_id)
            user_dialogues_count = len([d for d in recent_dialogues if d.get("role") == "user"])
            
            if user_dialogues_count % 2 == 0:  # 每 2 轮对话
                await self._update_complexity_analysis(user_id, session_id, dialogue_id, recent_dialogues)
            
            print(f"DEBUG: 实时保存分析洞察成功，用户 ID: {user_id}, 会话 ID: {session_id}, 对话 ID: {dialogue_id}")
        except Exception as e:
            print(f"ERROR: _save_realtime_insight 失败：{e}")
            import traceback
            traceback.print_exc()
            raise e
    
    async def _update_complexity_analysis(self, user_id: str, session_id: str,
                                         dialogue_id: int, dialogue_history: List[Dict[str, Any]]):
        """
        更新复杂度分析（每 2 轮对话调用一次 LLM）
        
        :param user_id: 用户 ID
        :param session_id: 会话 ID
        :param dialogue_id: 触发更新的对话 ID
        :param dialogue_history: 对话历史列表
        """
        if not self.llm_service:
            return
        
        try:
            # 只提取用户对话
            user_dialogues = [d for d in dialogue_history if d.get("role") == "user"]
            all_user_content = "\n".join([d.get("content", "") for d in user_dialogues])
            
            prompt = f"""分析以下用户对话中的情绪，映射到中医七种情志（喜、怒、忧、思、悲、恐、惊），并计算各情志占比。

用户对话内容：
{all_user_content}

请分析：
1. 识别对话中涉及的所有情志类型（喜、怒、忧、思、悲、恐、惊）
2. 计算各情志的占比（总和为 1）
3. 如果只涉及一种情志，标记为"简单"；如果涉及多种，标记为"复杂"

请返回 JSON 格式：
{{
  "complexity_type": "简单"或"复杂",
  "emotions": {{
    "忧": 0.6,
    "思": 0.4
  }}
}}
"""
            response = await self.llm_service.chat_completion(
                messages=[
                    {"role": "system", "content": "你是一位中医情志分析专家。请将用户情绪映射到中医七种情志（喜、怒、忧、思、悲、恐、惊）。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=300
            )
            
            content = response["choices"][0]["message"]["content"]
            if "```json" in content:
                start = content.find("```json") + 7
                end = content.find("```", start)
                content = content[start:end].strip()
            
            result = json.loads(content)
            complexity_type = result.get("complexity_type", "简单")
            emotions = result.get("emotions", {})
            
            # 转换为标准格式
            complexity_analysis = {
                "type": complexity_type,
                "emotions": [{"emotion": k, "value": v} for k, v in emotions.items()]
            }
            
            # 增量保存到数据库
            self.repository.update_complexity_analysis(
                user_id=user_id,
                session_id=session_id,
                dialogue_id=dialogue_id,
                complexity_analysis=complexity_analysis
            )
            
            print(f"DEBUG: 复杂度分析更新成功，用户 ID: {user_id}, 会话 ID: {session_id}")
            
        except Exception as e:
            print(f"ERROR: _update_complexity_analysis 失败：{e}")
            # 不影响主流程

    async def _generate_complete_insight(self, user_id: str, session_id: str,
                                        archive: Dict[str, Any], dialogue_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """生成完整的分析洞察（包括认知映射和中医分析）"""
        if not self.llm_service:
            raise Exception("LLM 服务未初始化")
        
        try:
            # 准备对话内容
            user_dialogues = [d for d in dialogue_history if d.get("role") == "user"]
            user_contents = [d.get("content", "") for d in user_dialogues]
            user_dialogues_text = "\n".join([f"- {content}" for content in user_contents])
            
            # 准备档案数据
            archive_data = archive.get("archive_json", archive)
            
            prompt = f"""基于以下用户对话和档案信息，生成完整的分析洞察。

用户对话内容：
{user_dialogues_text}

用户档案：
{json.dumps(archive_data, ensure_ascii=False, indent=2)}

请生成以下分析洞察：

1. cognitive_mappings（认知映射关系）：
   建立情景 -> 自动化思维 -> 情绪 -> 核心信念的映射关系
   格式：[{{"situation": "情景描述", "automatic_thought": "自动化思维", "emotion": "情绪", "core_belief": "核心信念"}}]

2. tcm_analysis（中医分析）：
   - dominant_emotion: 主导情志（从喜、怒、忧、思、悲、恐、惊中选择）
   - related_organs: 相关脏腑列表
   - qi_dynamics: 气机动态描述
   - tcm_interpretation: 中医解读，体现投射关系：场景 -> 情志 -> 脏腑 -> 气机

3. causes（原因分析）：
   - cbt_perspective: CBT 视角分析
   - tcm_perspective: 中医视角分析

4. emotional_trend: 情绪趋势总结

请返回 JSON 格式：
{{
  "cognitive_mappings": [
    {{
      "situation": "面试场景",
      "automatic_thought": "我会失败",
      "emotion": "恐惧",
      "core_belief": "我不够好"
    }}
  ],
  "tcm_dominant_emotion": "忧",
  "tcm_related_organs": ["肺", "脾"],
  "tcm_qi_dynamics": "肺气郁结，气机不畅",
  "tcm_interpretation": "因求职事宜引发忧思，伤及肺脾，导致肺气郁结，气机不畅",
  "cbt_perspective": "从 CBT 视角分析...",
  "tcm_perspective": "从中医视角分析...",
  "emotional_trend": "用户情绪呈现...趋势"
}}
"""
            
            response = await self.llm_service.chat_completion(
                messages=[
                    {"role": "system", "content": "你是一位专业的心理咨询分析师，精通 CBT 和中医理论。请分析用户对话，建立认知映射关系，并进行中医情志脏腑投射分析。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1500
            )
            
            content = response["choices"][0]["message"]["content"]
            if "```json" in content:
                start = content.find("```json") + 7
                end = content.find("```", start)
                content = content[start:end].strip()
            
            result = json.loads(content)
            
            # 构建完整的洞察数据
            complete_insight = {
                "cognitive_mappings": result.get("cognitive_mappings", []),
                "tcm_dominant_emotion": result.get("tcm_dominant_emotion"),
                "tcm_related_organs": result.get("tcm_related_organs", []),
                "tcm_qi_dynamics": result.get("tcm_qi_dynamics"),
                "tcm_interpretation": result.get("tcm_interpretation"),
                "cbt_perspective": result.get("cbt_perspective"),
                "tcm_perspective": result.get("tcm_perspective"),
                "emotional_trend": result.get("emotional_trend")
            }
            
            return complete_insight
            
        except Exception as e:
            print(f"ERROR: _generate_complete_insight 失败：{e}")
            import traceback
            traceback.print_exc()
            # 返回默认数据
            return {
                "cognitive_mappings": [],
                "tcm_dominant_emotion": None,
                "tcm_related_organs": [],
                "tcm_qi_dynamics": None,
                "tcm_interpretation": None,
                "cbt_perspective": None,
                "tcm_perspective": None,
                "emotional_trend": ""
            }

    async def save_complete_insight(self, user_id: str, session_id: str, dialogue_history: List[Dict[str, Any]]):
        """生成并保存完整的分析洞察（可定期调用）"""
        try:
            # 获取当前档案
            archive_record = self.repository.get_user_archive(user_id, session_id)
            if not archive_record:
                print(f"WARNING: 用户档案不存在，无法生成完整洞察，用户 ID: {user_id}, 会话 ID: {session_id}")
                return
            
            # 生成完整洞察
            complete_insight = await self._generate_complete_insight(
                user_id=user_id,
                session_id=session_id,
                archive=archive_record,
                dialogue_history=dialogue_history
            )
            
            # 保存到数据库
            self.repository.save_analysis_insight(
                user_id=user_id,
                session_id=session_id,
                insight_data=complete_insight,
                dialogue_id=None  # 不是由特定对话触发
            )
            
            print(f"DEBUG: 完整分析洞察保存成功，用户 ID: {user_id}, 会话 ID: {session_id}")
        except Exception as e:
            print(f"ERROR: save_complete_insight 失败：{e}")
            import traceback
            traceback.print_exc()

    async def analyze_process(self, user_id: str, user_input: str, four_dim: Dict[str, Any], dialogue_id: int = None, session_id: str = None) -> Dict[str, Any]:
        """处理分析的主入口"""
        # 1. 获取当前档案
        try:
            archive_record = self.repository.get_user_archive(user_id, session_id)
            if not archive_record:
                # 没有档案，需要基于历史对话生成初始档案
                # 获取用户所有历史对话（最多 50 条，避免超长）
                histories = self.repository.get_recent_dialogues(user_id, limit=50, session_id=session_id)
                archive = await self._generate_initial_archive(user_id, histories)
                # 添加会话 ID 到档案
                archive["session_id"] = session_id
                # 保存初始档案
                self.repository.save_user_archive(user_id, session_id, archive, version=1)
            else:
                # 从档案记录中提取 archive_json
                archive_data = archive_record.get("archive_json", {})
                # 增量更新档案
                updated_archive = await self._update_archive(archive_record, user_input, four_dim)
                # 确保会话 ID 存在
                updated_archive["session_id"] = session_id
                # 保存更新后的档案（版本号 +1）
                version = archive_record.get("version", 0) + 1
                self.repository.save_user_archive(user_id, session_id, updated_archive, version=version)
                archive = updated_archive
        except Exception as e:
            # 如果保存失败，使用默认档案
            current_time = datetime.utcnow().isoformat()
            archive = {
                "session_id": session_id,
                "user_id": user_id,
                "created_at": current_time,
                "updated_at": current_time,
                "title": "新会话",
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

        # 2. 匹配策略
        strategy = self._match_strategy(four_dim)
        if not strategy:
            # 如果没有匹配到，使用默认策略
            strategy = {
                "fusion_mode": "cbt_main_tcm_aux",
                "strategy_content": "【CBT 核心】试着把你的想法写下来，然后问自己：这个想法有证据吗？\n【中医辅助】可以做几次深呼吸，让身体放松。",
                "cbt_techniques": "认知重构",
                "tcm_methods": "调息放松"
            }

        # 3. 构建建议
        advice = self._build_advice(archive, strategy, four_dim)

        # 4. 保存建议
        self.repository.save_advice(user_id, advice, dialogue_id, session_id)

        # 5. 实时保存分析洞察
        try:
            await self._save_realtime_insight(user_id, session_id, archive, four_dim, dialogue_id)
        except Exception as e:
            print(f"ERROR: 实时保存分析洞察失败：{e}")
            # 不影响主流程，继续执行

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
        if not self.llm_service:
            print("ERROR: 分析师智能体 - LLM服务未初始化")
            # 返回默认回复
            return "{\"session_id\": \"\", \"user_id\": \"\", \"created_at\": \"2026-03-27T00:00:00Z\", \"updated_at\": \"2026-03-27T00:00:00Z\", \"title\": \"新会话\", \"basic_info\": {\"age\": null, \"gender\": null, \"occupation\": null, \"main_issues\": []}, \"emotional_timeline\": {\"summary\": \"\", \"trends\": {\"intensity\": \"\", \"hedonic\": \"\", \"tension\": \"\", \"complexity\": \"\"}, \"key_events\": []}, \"cognitive_patterns\": {\"common_automatic_thoughts\": [], \"thinking_traps\": [], \"core_beliefs\": []}, \"situations\": [], \"intervention_history\": [], \"current_focus\": \"\", \"summary\": \"\"}"
        
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
    
    async def generate_analysis_report(self, user_id: str, session_id: str,
                                       archive_data: dict, dialogue_history: list) -> dict:
        """生成分析报告
        
        基于用户认知档案和对话历史，生成分析报告。
        """
        if not self.llm_service:
            raise Exception("LLM服务未初始化")
        
        # 构建提示词
        prompt = f"""基于以下用户认知档案和对话历史，生成一份分析报告。

用户认知档案：
{json.dumps(archive_data, ensure_ascii=False, indent=2)}

对话历史：
{json.dumps(dialogue_history, ensure_ascii=False, indent=2)}

请生成分析报告，包含以下字段：
- four_dim_summary: 四维情绪总结（avg_intensity平均强度、hedonic_distribution快感度分布、tension_distribution紧张度分布、complexity_distribution复杂度分布）
- emotional_timeline: 情绪时间线（timestamps时间戳列表、intensity强度变化、hedonic快感度变化、tension紧张度变化、complexity复杂度变化）
- cognitive_analysis: 认知分析（common_automatic_thoughts常见自动思维、thinking_traps思维陷阱、core_beliefs核心信念）
- tcm_analysis: 中医情志分析（dominant_emotion主导情志、related_organs相关脏腑、qi_dynamics气机动态、tcm_interpretation中医解读）
- causes: 原因分析（cbt_perspective CBT视角、tcm_perspective中医视角）
- trends: 趋势总结描述

请严格按照以下JSON格式返回：
{{
  "four_dim_summary": {{
    "avg_intensity": 6.5,
    "hedonic_distribution": {{"正性": 0, "中性": 0.1, "负性": 0.9}},
    "tension_distribution": {{"低": 0.2, "中": 0.5, "高": 0.3}},
    "complexity_distribution": {{"简单": 0.8, "复杂": 0.2}}
  }},
  "emotional_timeline": {{
    "timestamps": ["2026-03-28T10:00:00Z", "2026-03-28T10:05:00Z"],
    "intensity": [5.2, 6.8],
    "hedonic": ["负性", "负性"],
    "tension": ["中", "高"],
    "complexity": ["简单", "复杂"]
  }},
  "cognitive_analysis": {{
    "common_automatic_thoughts": ["思维1", "思维2"],
    "thinking_traps": ["陷阱1", "陷阱2"],
    "core_beliefs": ["信念1", "信念2"]
  }},
  "tcm_analysis": {{
    "dominant_emotion": "恐",
    "related_organs": ["肾"],
    "qi_dynamics": "气下",
    "tcm_interpretation": "中医解读内容"
  }},
  "causes": {{
    "cbt_perspective": "CBT视角分析",
    "tcm_perspective": "中医视角分析"
  }},
  "trends": "趋势总结描述"
}}
"""

        # 调用LLM
        response = await self.llm_service.chat_completion(
            messages=[
                {"role": "system", "content": "你是一位专业的心理咨询分析师。请基于用户认知档案和对话历史生成详细的分析报告。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=1500
        )

        # 解析JSON
        try:
            content = response["choices"][0]["message"]["content"]
            if "```json" in content:
                start = content.find("```json") + 7
                end = content.find("```", start)
                content = content[start:end].strip()

            report = json.loads(content)
        except (json.JSONDecodeError, KeyError) as e:
            print(f"解析分析报告失败: {e}, 内容: {content if 'content' in locals() else 'N/A'}")
            # 返回基于已构建数据的报告
            report = analysis_report

        return report
    
    async def generate_analysis_report_from_archive(self, user_id: str, session_id: str,
                                                    archive_data: dict, four_dim_data: dict,
                                                    dialogue_history: list = None) -> dict:
        """基于用户档案和四维数据生成分析报告

        从用户档案获取认知分析、中医分析等内容，结合四维数据生成完整的分析报告。
        建立认知映射关系：情景 -> 自动化思维 -> 情绪 -> core_beliefs
        """
        if not self.llm_service:
            raise Exception("LLM服务未初始化")

        # 计算四维统计
        intensity_values = four_dim_data.get("intensity_values", [])  # 格式: [{"value": 6.5, "timestamp": "..."}, ...]
        hedonic_values = four_dim_data.get("hedonic_values", [])  # 格式: [{"label": "负性", "value": 3}, ...]
        tension_values = four_dim_data.get("tension_values", [])  # 格式: [{"label": "低", "value": 5}, ...]
        complexity_values = four_dim_data.get("complexity_values", {})  # 格式: {"type": "复杂", "emotions": [...]}

        # 提取时间戳和强度值
        timestamps = [item.get("timestamp", "") for item in intensity_values]
        intensity_list = [item.get("value", 0) for item in intensity_values]

        # 构建分析报告基础结构
        analysis_report = {
            "four_dim_summary": {
                "intensity_values": intensity_values,
                "hedonic_distribution": hedonic_values,
                "tension_distribution": tension_values,
                "complexity_analysis": complexity_values
            },
            "emotional_timeline": {
                "timestamps": timestamps,
                "intensity": intensity_list,
                "hedonic": hedonic_values,
                "tension": tension_values,
                "complexity": complexity_values
            },
            "cognitive_analysis": {
                "mappings": [],
                "common_automatic_thoughts": [],
                "thinking_traps": [],
                "core_beliefs": []
            },
            "tcm_analysis": {
                "dominant_emotion": "",
                "related_organs": [],
                "qi_dynamics": "",
                "tcm_interpretation": ""
            },
            "causes": {
                "cbt_perspective": "",
                "tcm_perspective": ""
            },
            "trends": ""
        }

        # 使用LLM生成完整的分析报告
        try:
            # 准备用户对话内容
            user_contents = []
            if dialogue_history:
                user_contents = [d.get("content", "") for d in dialogue_history if d.get("role") == "user"]

            user_dialogues_text = "\n".join([f"- {content}" for content in user_contents])

            prompt = f"""基于以下用户对话和档案信息，生成完整的分析报告。

用户对话内容：
{user_dialogues_text}

用户档案：
{json.dumps(archive_data, ensure_ascii=False, indent=2)}

四维数据：
- 强度值：{intensity_values}
- 快感度统计：{hedonic_values}
- 紧张度统计：{tension_values}
- 复杂度分析：{complexity_values}

请生成分析报告，包含以下内容：

1. cognitive_analysis（认知分析）：
   - mappings: 认知映射关系列表，每个映射包含：
     * situation: 情景（用户对话中的具体场景或内容）
     * automatic_thought: 自动化思维（单一种CBT思维陷阱类型，如灾难化思维、全或无思维、心理过滤等）
     * emotion: 情绪
     * core_belief: 导致的核心信念
   - common_automatic_thoughts: 常见的自动思维列表
   - thinking_traps: 思维陷阱列表（标准化CBT类型）
   - core_beliefs: 核心信念列表

2. tcm_analysis（中医分析）：
   - dominant_emotion: 主导情志（从喜、怒、忧、思、悲、恐、惊中选择）
   - related_organs: 相关脏腑列表
   - qi_dynamics: 气机动态描述
   - tcm_interpretation: 中医解读，需要体现投射关系：场景 -> 情志 -> 脏腑 -> 气机
     例如：因求职事宜 -> 忧 -> 肺 -> 肺气郁结，气机不畅

3. causes（原因分析）：
   - cbt_perspective: CBT视角分析
   - tcm_perspective: 中医视角分析

4. trends: 情绪趋势总结

请返回JSON格式：
{{
  "cognitive_analysis": {{
    "mappings": [
      {{
        "situation": "面试场景",
        "automatic_thought": "灾难化思维",
        "emotion": "恐惧",
        "core_belief": "我不够好"
      }}
    ],
    "common_automatic_thoughts": ["我会失败", "我做不到"],
    "thinking_traps": ["灾难化思维", "全或无思维"],
    "core_beliefs": ["我不够好", "我无能"]
  }},
  "tcm_analysis": {{
    "dominant_emotion": "忧",
    "related_organs": ["肺", "脾"],
    "qi_dynamics": "肺气郁结，气机不畅",
    "tcm_interpretation": "因求职事宜引发忧思，伤及肺脾，导致肺气郁结，气机不畅"
  }},
  "causes": {{
    "cbt_perspective": "从CBT视角分析...",
    "tcm_perspective": "从中医视角分析..."
  }},
  "trends": "用户情绪呈现...趋势"
}}
"""

            response = await self.llm_service.chat_completion(
                messages=[
                    {"role": "system", "content": "你是一位专业的心理咨询分析师，精通CBT和中医理论。请分析用户对话，建立认知映射关系，并进行中医情志脏腑投射分析。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1500
            )

            content = response["choices"][0]["message"]["content"]
            if "```json" in content:
                start = content.find("```json") + 7
                end = content.find("```", start)
                content = content[start:end].strip()

            result = json.loads(content)

            # 更新分析报告
            analysis_report["cognitive_analysis"] = result.get("cognitive_analysis", {
                "mappings": [],
                "common_automatic_thoughts": [],
                "thinking_traps": [],
                "core_beliefs": []
            })
            analysis_report["tcm_analysis"] = result.get("tcm_analysis", {
                "dominant_emotion": "",
                "related_organs": [],
                "qi_dynamics": "",
                "tcm_interpretation": ""
            })
            analysis_report["causes"] = result.get("causes", {
                "cbt_perspective": "",
                "tcm_perspective": ""
            })
            analysis_report["trends"] = result.get("trends", "")

        except Exception as e:
            print(f"生成分析报告失败: {e}")
            import traceback
            traceback.print_exc()

        return analysis_report