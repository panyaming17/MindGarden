import json
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional, List
from backend.agents.base_agent import BaseAgent
from backend.repositories.record_repository import RecordRepository
from backend.core.llm_service import LLMService
from backend.core.memory_manager import get_memory_manager, save_memory_manager, PsychologicalMemory
from backend.services.memory_rag_service import get_memory_rag_service, save_memory_rag_index
print("RecordRepository imported from:", RecordRepository.__module__)

class TherapistAgent(BaseAgent):
    """调理师智能体 - 负责生成自然回复"""

    def __init__(self, agent_name: str = "therapist_agent", llm_service: Optional[LLMService] = None):
        super().__init__(agent_name)
        self.repository = RecordRepository()
        self.llm_service = llm_service
        self.memory: Optional[PsychologicalMemory] = None
        self._init_prompts()

    def _init_prompts(self):
        self.system_prompt = """你是一位温暖、真诚的心理咨询师。你的任务是帮助用户处理当下的情绪和想法。

【重要】你必须严格按照分析师提供的以下信息来构建回复：
- 当前核心议题
- 推荐的具体CBT技术
- 推荐的中医情志方法
- 融合模式（当用户表现出强烈情绪时，需要决定CBT与中医的先后顺序）

【语言风格 - 极其重要】
1. **禁止机械套用固定句式**：不要每次都使用"听起来..."、"能和我聊聊..."等固定模式。每次回复的开头都应该不同。
2. **共情方式多样化**：共情不等于重复"听起来xxx"。可以用："你现在的感受我能理解"、"这事搁在谁身上都不好受"、"看得出来你挺不容易的"、"心慌的感觉确实挺折磨人的"等多种方式。
3. **提问方式多样化**：不要每次都问"能和我聊聊...吗？"。可以试试："当时是什么感觉？"、"后来呢？"、"你心里是怎么想的？"、"身体上有什么反应吗？"等。
4. **根据用户输入长度调整**：如果用户只说了很短的话（如"焦虑"），不要机械重复之前的回复，要从新角度回应，或者用更简洁的方式确认。
5. **禁止用其他国家的语言**：你只能用中文回复用户。如果用户用其他语言回复，你需要用中文回复。如果用户用中文回复，你需要用中文回复。

【回访会话处理 - 重要】
当用户在回访会话中回复你的开场白时，你需要根据其回复选择不同的策略：

策略A：用户表示"好多了/好转了/正向回复"
  → 第一步：肯定用户的进步（1句话）
  → 第二步：直接询问最近有没有其他情绪困扰或新话题
  → 注意：不要问"你是怎么做到的"，直接引导到新话题
  → 第三步：进入正常的 S1-S4 对话流程

策略B：用户表示"没有好转/更糟了/负向回复"
  → 第一步：共情用户的持续困扰（1句话）
  → 第二步：每次只追问 1 个细节问题（不要连续问多个）
     例如："具体什么时候感觉最难熬？" 或 "身体上还有什么反应吗？"
  → 第三步：等待用户回答后，再决定是否继续追问下一个细节
  → 第四步：如果用户表示不想继续讨论、或转移话题、或你已经问了 2-3 个问题
     → 温和地转向："那我们先放一放这些，最近有没有其他让你困扰的事情？"

【重要：用户转移话题时的处理】
如果用户在策略B的追问过程中表示不想讨论、或主动提起其他话题：
  → 立即停止追问上次议题的细节
  → 顺着用户提到的新话题继续
  → 不要强行拉回旧话题

策略C：用户回复模糊或中性
  → 温和地探索："能多说说吗？最近感觉怎么样？"
  → 根据用户的回答自然过渡到上述策略A或B

【记忆感知 - 极其重要】
你拥有对话记忆系统，必须严格遵守以下规则：
1. **已解决议题不再推荐对应方法**：如果记忆显示某个问题已缓解（如用户说"胸口不闷了"），绝对不要再推荐针对该问题的方法（如"按揉两胁"），而是转向当前活跃议题或引导下一步。
2. **用户拒绝的方法绝对不再使用**：如果记忆显示用户明确拒绝了某个方法（如说"我没有这些想法"），请立即切换到其他方法，绝对不要重复推荐被拒绝的方法。
3. **差异化回复 - 绝对不要重复**：根据对话进展调整回复，**绝对不要重复之前已经说过的完整回复内容**。每次回复都必须是新鲜、有针对性的。
4. **上下文连贯**：记住之前对话的关键信息，保持回复的连贯性，但不要机械重复之前的话。
5. **情绪变化感知**：如果用户情绪有好转趋势，给予肯定并引导进入下一阶段；如果情绪恶化，增加共情和支持。
6. **灵活调整方法**：如果用户表示某个方法不适用或不想使用，立即切换到其他CBT技术或中医方法，不要坚持原方案。
7. **针对最新输入**：每次回复必须针对用户的最新发言，不要重复回答已经回答过的问题。

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

请用自然、温暖的语言回复，像和朋友谈心一样，可以适当用些语气词。

【格式要求】直接输出回复内容，不要添加任何前缀（如"小园："、"回复："等），不要添加引号包裹。"""

        self.stage_prompts = {
            "S1_建立关系": """
【当前阶段：初次接触，建立信任】
- 只做两件事：如果有用户的表达感受，先简短共情（1句话） + 一个开放性问题，如果用户只是问好，就同样问好并邀请用户分享自己的感受
- 禁止使用任何CBT技术、中医方法、建议、作业
""",
            "S2_信息收集": """
【当前阶段：信息收集】
- 温和地询问用户的基本情况、困扰的大致方向
- 提问应聚焦于“什么”、“何时”、“多久”，用一个问题引导用户描述，不要连续问多个问题，尽量可以添加例子
- 不要深入探讨情绪细节，先建立全景
""",
            "S3_深度探索": """
【当前阶段：深度探索，浮现认知】
- 先共情，然后邀请用户描述具体情境、脑子里的念头、身体感觉等
- 用一个问题引导用户描述，不要连续问多个问题，尽量可以添加例子
- 此时不要给建议或方法，保持倾听姿态
""",
            "S4_认知浮现": """
【当前阶段：认知浮现】
- 用户已表达出明显的自动思维或思维陷阱
- 可以温和地反馈你的观察，但暂不进行强力干预
- 例如：“我注意到你提到了‘都是我的错’，这种想法让你感觉很沉重对吗？”
""",
            "S5_干预中": """
【当前阶段：认知重构与调理】
- 用户已充分表达，可以引入一个CBT技术或中医身体觉察练习
- 从advice中选择一项最匹配的技术，用提问方式融入
""",
            "S6_总结巩固": """
【当前阶段：总结与巩固】
- 用2-3句话总结今天的核心发现，肯定用户的觉察
- 给出一个极简的CBT作业或中医认知行为疗法的小练习
"""
        }

        self.user_prompt_template = """
【用户最新发言】"{user_input}"
{opening_context}
【关键指令 - 必须遵守】
1. **针对最新发言回复**：只根据用户的【最新发言】生成回复，不要重复之前轮次的回复内容
2. **不要重复自己**：你之前说过的话不要再说一遍，每次都要提供新鲜、有针对性的内容
3. **历史仅供参考**：下面的历史记录只是让你了解背景，不要重复历史中的回复

【历史对话摘要】（仅供参考，不要重复）
{recent_history}

{memory_context}

{rag_context}

{clinical_case_context}

{stage_instruction}

【分析师建议】
- 核心议题：{current_focus}
- 自动化思维：{key_thoughts}
- 思维陷阱：{thinking_traps}
- 推荐CBT方法：{cbt_techniques}
- 推荐中医方法：{tcm_methods}
- 融合模式：{fusion_mode}

【生成要求】
1. 只针对用户的【最新发言】进行回复
2. 绝对不要重复你之前已经说过的完整句子或段落
3. 如果记忆上下文中标注了"已解决的议题"，请不要再推荐针对该议题的方法
4. 如果用户明确拒绝了某个方法，请切换到其他方法
5. 回复要像在和朋友谈心，先共情，再按融合模式自然融入具体方法
6. **每次回复都必须是新鲜的、不同的内容**
7. **严格遵守当前阶段的回复约束**
8. 如果RAG检索到了相关历史记忆或临床案例，可以适当引用或关联这些内容，让对话更连贯

【最后一道指令——必须遵守】
在生成回复之前，请自查：
- 回复中是否包含比喻？（如“像...一样”、“仿佛”、“如同”）
- 回复中是否超过两句话？
- 回复中是否使用了任何心理描写或意象词汇（如“沉甸甸”、“轻飘飘”、“悬着”）？
如果有，请删除后重新生成。

现在，请输出你的回复：
"""

    def _get_stage_prompt_suffix(self, stage: str) -> str:
        return self.stage_prompts.get(stage, "")

    def _get_recent_history(self, user_id: str, limit: int = 3, session_id: Optional[str] = None) -> str:
        # 保持原有实现
        histories = self.repository.get_recent_dialogues(user_id, limit=limit * 2, session_id=session_id)
        if not histories:
            return "（无历史对话）"
        history_str = ""
        total = len(histories)
        for i, d in enumerate(histories):
            role = "用户" if d["role"] == "user" else "助手"
            if role == "助手":
                is_last_assistant = (i == total - 1)
                max_len = 20 if is_last_assistant else 30
                content = d["content"][:max_len] + "..." if len(d["content"]) > max_len else d["content"]
                if is_last_assistant and len(d["content"]) > max_len:
                    content += "（注意：这是你上一轮的回复开头，本次回复必须完全不同！）"
            else:
                content = d["content"][:60] + "..." if len(d["content"]) > 60 else d["content"]
            history_str += f"{role}: {content}\n"
        return history_str.strip()

    def _build_prompt(self, user_input: str, recent_history: str, advice: Dict[str, Any],
                      memory_context: str = "", stage: str = "S2_信息收集",
                      opening_context: str = "", rag_context: str = "", clinical_case_context: str = "") -> str:
        current_focus = advice.get("current_focus", "")
        key_thoughts = "、".join(advice.get("key_thoughts", [])) or "暂无"
        thinking_traps = "、".join(advice.get("thinking_traps", [])) or "暂无"
        cbt_techniques = advice.get("cbt_techniques", "")
        tcm_methods = advice.get("tcm_methods", "")
        fusion_mode = advice.get("fusion_mode", "cbt_main_tcm_aux")
        stage_instruction = self._get_stage_prompt_suffix(stage)

        return self.user_prompt_template.format(
            user_input=user_input,
            recent_history=recent_history,
            memory_context=memory_context,
            stage_instruction=stage_instruction,
            opening_context=opening_context,
            rag_context=rag_context,
            clinical_case_context=clinical_case_context,
            current_focus=current_focus,
            key_thoughts=key_thoughts,
            thinking_traps=thinking_traps,
            cbt_techniques=cbt_techniques,
            tcm_methods=tcm_methods,
            fusion_mode=fusion_mode
        )

    async def generate_response(self, user_id: str, user_input: str, advice: Optional[Dict[str, Any]] = None,
                                session_id: Optional[str] = None, regenerate: bool = False,
                                stage: str = "S2_信息收集", opening_context: str = "") -> str:
        if not self.llm_service:
            raise Exception("LLM服务未初始化")
        if self.memory is None:
            self.memory = get_memory_manager(self.llm_service)

        recent_history = self._get_recent_history(user_id, limit=3, session_id=session_id)

        if advice is None:
            advice = self.repository.get_latest_advice(user_id)
            if advice:
                advice = advice.get("advice_json", advice)
            else:
                advice = {}

        # 记忆上下文
        memory_context = self.memory.build_memory_enhanced_prompt(user_id, session_id, user_input, advice)

        # 用户历史记忆RAG
        rag_context = ""
        try:
            rag_service = get_memory_rag_service()
            if rag_service:
                rag_results = rag_service.search_relevant_memories(
                    user_id=user_id, query_text=user_input, top_k=5,
                    exclude_session_id=session_id, min_similarity=0.25
                )
                if rag_results:
                    parts = ["\n【RAG检索到的相关历史记忆】"]
                    for m in rag_results[:3]:
                        parts.append(f"  {m['role']}：{m['content'][:50]}...")
                    rag_context = "\n".join(parts)
        except Exception as e:
            print(f"[RAG检索] 失败: {e}")

        # 临床案例RAG上下文（从advice的four_dim中获取similar_cases）
        clinical_case_context = ""
        similar_cases = advice.get("four_dim", {}).get("similar_cases", [])
        if similar_cases:
            parts = ["\n【相似临床案例参考】（仅供参考，不要照搬回复）"]
            for i, case in enumerate(similar_cases[:3]):
                parts.append(f"  案例{i+1}（相似度{case.get('similarity', 0):.2f}）：")
                parts.append(f"    情境：{case.get('document', '')[:80]}...")
                parts.append(f"    思维陷阱：{case.get('metadata', {}).get('thinking_trap', '无')}")
                parts.append(f"    情志标签：{case.get('metadata', {}).get('emotion_labels', '无')}")
            clinical_case_context = "\n".join(parts)

        prompt = self._build_prompt(user_input, recent_history, advice, memory_context, stage,
                                    opening_context, rag_context, clinical_case_context)

        print("\n" + "="*80)
        print("【调理师生成回复】")
        print(f"  用户输入: {user_input[:50]}...")
        print(f"  当前阶段: {stage}")
        print(f"  临床案例数: {len(similar_cases)}")
        print("="*80)

        temperature = 0.9 if regenerate else 0.7
        reply = await self._get_llm_response(
            messages=[{"role": "system", "content": self.system_prompt}, {"role": "user", "content": prompt}],
            temperature=temperature, max_tokens=500
        )
        reply = reply.strip()
        import re
        reply = re.sub(r'^(小园|回复|助手|AI)[：:]\s*', '', reply)

        self.memory.add_user_message(user_id, session_id, user_input)
        self.memory.add_ai_message(user_id, session_id, reply, advice=advice)
        await self.memory.update_resolved_topics(user_id, session_id, user_input, reply)
        await self.memory.generate_summary(user_id, session_id)
        save_memory_manager()

        assistant_dialogue_id = self.repository.save_dialogue(
            user_id=user_id, role="assistant", content=reply,
            four_dim=None, is_valuable=False, session_id=session_id
        )

        # 助手回复加入记忆RAG
        try:
            rag_service = get_memory_rag_service()
            if rag_service and session_id:
                rag_service.add_chunks(
                    user_id=user_id, session_id=session_id,
                    dialogues=[{"role": "assistant", "content": reply, "timestamp": "", "metadata": {}}]
                )
                save_memory_rag_index()
        except Exception as e:
            print(f"[RAG索引] 添加失败: {e}")

        return reply, assistant_dialogue_id

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        user_id = input_data.get("user_id")
        user_input = input_data.get("user_input")
        advice = input_data.get("advice")
        session_id = input_data.get("session_id")
        regenerate = input_data.get("regenerate", False)
        stage = input_data.get("stage", "S2_信息收集")
        opening_context = input_data.get("opening_context", "")

        if not user_id or not user_input:
            return {"status": "error", "message": "缺少必要参数"}

        try:
            reply, assistant_dialogue_id = await self.generate_response(
                user_id, user_input, advice, session_id, regenerate, stage, opening_context
            )
            return {"status": "success", "data": {"reply": reply, "dialogue_id": assistant_dialogue_id}}
        except Exception as e:
            return {"status": "error", "message": f"生成回复失败: {str(e)}"}
    
    async def handle_session_opening(self, user_id: str, session_id: str) -> Dict[str, Any]:
        """
        处理会话开场逻辑
        
        Returns:
            {
                "has_history": bool,
                "opening_prompt": str,  # 直接发给用户的开场白
                "opening_for_llm": str  # 注入给LLM的上下文
            }
        """
        if self.memory is None:
            self.memory = get_memory_manager(self.llm_service)
        
        opening = self.memory.generate_session_opening(user_id, session_id)
        
        if not opening["has_history"]:
            return {
                "has_history": False,
                "opening_prompt": "你好呀，今天想和我聊点什么呢？",
                "opening_for_llm": "",
                "previous_issues": []
            }
        
        return {
            "has_history": True,
            "opening_prompt": opening["opening_prompt"],
            "opening_for_llm": opening["opening_for_llm"],
            "previous_issues": opening.get("previous_issues", []),
            "last_active_topics": opening.get("last_active_topics", []),
            "last_resolved_topics": opening.get("last_resolved_topics", [])
        }
    
    async def mark_issues_resolved(self, user_id: str, session_id: str, resolved_issues: List[str]) -> Dict[str, Any]:
        """
        用户回答议题已解决后，标记不再注入到后续prompt中
        
        Returns:
            {"status": "success", "marked_issues": List[str]}
        """
        if self.memory is None:
            self.memory = get_memory_manager(self.llm_service)
        
        self.memory.mark_previous_session_resolved(user_id, session_id, resolved_issues)
        
        return {
            "status": "success",
            "marked_issues": resolved_issues
        }
    
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
    
    async def generate_treatment_report(self, user_id: str, session_id: str,
                                        analysis_report: dict) -> dict:
        """生成调理报告

        基于分析师生成的分析报告（CBT分析和TCM分析），生成针对性的调理建议。
        优先级：1.使用本地模板生成基础调理报告 2.添加重试机制调用LLM

        Args:
            user_id: 用户ID
            session_id: 会话ID
            analysis_report: 分析报告，包含cognitive_analysis和tcm_analysis
        """
        print("DEBUG: 开始生成调理报告...")

        # 提取分析报告中的关键信息
        cognitive_analysis = analysis_report.get("cognitive_analysis", {})
        tcm_analysis = analysis_report.get("tcm_analysis", {})

        thinking_traps = cognitive_analysis.get("thinking_traps", [])
        core_beliefs = cognitive_analysis.get("core_beliefs", [])
        dominant_emotion = tcm_analysis.get("dominant_emotion", "")
        related_organs = tcm_analysis.get("related_organs", [])
        qi_dynamics = tcm_analysis.get("qi_dynamics", "")

        print(f"DEBUG: 思维陷阱: {thinking_traps}")
        print(f"DEBUG: 主导情志: {dominant_emotion}")
        print(f"DEBUG: 相关脏腑: {related_organs}")

        # 优先级1: 使用本地模板生成基础调理报告
        base_report = self._generate_base_treatment_report(
            thinking_traps=thinking_traps,
            core_beliefs=core_beliefs,
            dominant_emotion=dominant_emotion,
            related_organs=related_organs,
            qi_dynamics=qi_dynamics
        )
        print("DEBUG: 已生成基础调理报告")

        # 优先级2: 如果LLM服务可用，尝试用LLM优化报告（带重试机制）
        if self.llm_service:
            llm_report = await self._generate_treatment_report_with_retry(
                analysis_report=analysis_report,
                base_report=base_report,
                max_retries=3
            )
            if llm_report:
                print("DEBUG: 使用LLM优化后的调理报告")
                return llm_report
            else:
                print("DEBUG: LLM优化失败，使用基础调理报告")
                return base_report
        else:
            print("DEBUG: LLM服务未初始化，使用基础调理报告")
            return base_report

    def _generate_base_treatment_report(self, thinking_traps: List[str],
                                        core_beliefs: List[str],
                                        dominant_emotion: str,
                                        related_organs: List[str],
                                        qi_dynamics: str) -> dict:
        """使用本地模板生成基础调理报告

        根据分析结果中的关键信息，匹配本地模板生成基础调理建议。
        """
        # 根据思维陷阱匹配CBT作业
        cbt_homework = self._match_cbt_homework(thinking_traps, core_beliefs)

        # 根据主导情志和脏腑匹配中医实践
        tcm_practices = self._match_tcm_practices(dominant_emotion, related_organs, qi_dynamics)

        # 生成融合策略
        fusion_strategies = [{
            "time": datetime.now().isoformat(),
            "fusion_mode": "cbt_tcm_integrated",
            "key_points": f"针对{dominant_emotion}情志，结合CBT认知调整和{','.join(related_organs)}脏腑调理"
        }]

        # 生成报告摘要
        summary = f"针对{dominant_emotion}情志和{','.join(thinking_traps)}等思维陷阱的调理方案"

        # 生成总体建议
        recommendations = [
            f"关注{dominant_emotion}情志对身体的影响",
            "保持规律作息，避免过度劳累",
            "如症状持续，建议寻求专业帮助"
        ]

        return {
            "summary": summary,
            "fusion_strategies": fusion_strategies,
            "cbt_homework": cbt_homework,
            "tcm_practices": tcm_practices,
            "recommendations": recommendations,
            "next_steps": {
                "suggestion": "持续记录情绪和身体状况的变化",
                "follow_up": "一周后评估调理效果"
            }
        }

    def _match_cbt_homework(self, thinking_traps: List[str], core_beliefs: List[str]) -> List[dict]:
        """根据思维陷阱匹配CBT作业模板"""
        homework_templates = {
            "灾难化思维": {
                "name": "灾难化思维挑战记录",
                "description": "当出现'一定会失败'等想法时，记录下：1.触发事件 2.当时的想法 3.写下3个反驳证据",
                "frequency": "每天",
                "duration": "两周"
            },
            "全或无思维": {
                "name": "灰度思考练习",
                "description": "当出现'完全不行'等绝对化想法时，尝试用0-100%的尺度评估情况，寻找中间状态",
                "frequency": "每天",
                "duration": "持续进行"
            },
            "心理过滤": {
                "name": "积极事件记录",
                "description": "每天记录3件做得好的事情或积极的经历，无论多小都要记录",
                "frequency": "每天",
                "duration": "三周"
            },
            "情绪化推理": {
                "name": "情绪与事实区分练习",
                "description": "当感到'我觉得糟糕，所以情况一定很糟'时，分别列出情绪感受和客观事实",
                "frequency": "每天",
                "duration": "两周"
            },
            "应该陈述": {
                "name": "灵活期望练习",
                "description": "将'我应该...'改为'我可以...'或'我希望...'，记录使用新表达后的感受变化",
                "frequency": "每天",
                "duration": "持续进行"
            }
        }

        homework = []
        for trap in thinking_traps:
            if trap in homework_templates:
                homework.append(homework_templates[trap])

        # 如果没有匹配到，添加默认作业
        if not homework:
            homework.append({
                "name": "思维记录表",
                "description": "记录每天出现的自动化思维，分析其类型（灾难化/全或无/过滤等），并尝试寻找反证",
                "frequency": "每天",
                "duration": "持续进行"
            })

        return homework

    def _match_tcm_practices(self, dominant_emotion: str, related_organs: List[str],
                             qi_dynamics: str) -> List[dict]:
        """根据情志和脏腑匹配中医实践模板"""
        # 情志-脏腑-调理方法映射
        emotion_practices = {
            "忧": {
                "organs": ["肺"],
                "practices": [
                    {
                        "name": "太渊穴按摩",
                        "description": "按揉手腕横纹桡侧凹陷处的太渊穴，每次3-5分钟，补肺气",
                        "purpose": "补益肺气，缓解忧思",
                        "frequency": "每日2次"
                    },
                    {
                        "name": "百合银耳羹",
                        "description": "百合30g、银耳10g、冰糖适量，炖煮食用",
                        "purpose": "润肺养阴，宁心安神",
                        "frequency": "每周3-4次"
                    }
                ]
            },
            "思": {
                "organs": ["脾"],
                "practices": [
                    {
                        "name": "足三里穴按摩",
                        "description": "按揉膝盖下3寸、胫骨外侧1横指处的足三里穴，每次5分钟",
                        "purpose": "健脾益气，调和脾胃",
                        "frequency": "每日2次"
                    },
                    {
                        "name": "山药薏米粥",
                        "description": "山药50g、薏米30g、粳米100g煮粥",
                        "purpose": "健脾祛湿，益气养血",
                        "frequency": "每周4-5次"
                    }
                ]
            },
            "怒": {
                "organs": ["肝"],
                "practices": [
                    {
                        "name": "太冲穴按摩",
                        "description": "按揉足背第1、2跖骨结合部前方凹陷处的太冲穴，每次3-5分钟",
                        "purpose": "疏肝理气，平肝潜阳",
                        "frequency": "每日2次，生气时加按"
                    },
                    {
                        "name": "玫瑰花茶",
                        "description": "玫瑰花5-8朵，沸水冲泡代茶饮",
                        "purpose": "疏肝解郁，理气和中",
                        "frequency": "每日1-2次"
                    }
                ]
            },
            "恐": {
                "organs": ["肾"],
                "practices": [
                    {
                        "name": "涌泉穴按摩",
                        "description": "按揉足底前1/3凹陷处的涌泉穴，每次5-10分钟",
                        "purpose": "滋补肾气，宁心安神",
                        "frequency": "每晚睡前"
                    },
                    {
                        "name": "黑芝麻核桃粥",
                        "description": "黑芝麻20g、核桃仁15g、粳米100g煮粥",
                        "purpose": "补肾益精，养血安神",
                        "frequency": "每周3-4次"
                    }
                ]
            }
        }

        practices = []

        # 根据主导情志匹配
        if dominant_emotion in emotion_practices:
            practices.extend(emotion_practices[dominant_emotion]["practices"])

        # 根据相关脏腑补充
        organ_practices = {
            "心": {
                "name": "内关穴按摩",
                "description": "按揉腕横纹上2寸、两筋之间的内关穴，每次3-5分钟",
                "purpose": "宁心安神，理气止痛",
                "frequency": "每日2次，焦虑时加按"
            },
            "肝": {
                "name": "推胁肋",
                "description": "双手掌根从腋下沿胁肋向下推至腰部，每次10-15次",
                "purpose": "疏肝理气，解郁散结",
                "frequency": "每日1次"
            }
        }

        for organ in related_organs:
            if organ in organ_practices and organ not in [p.get("purpose", "") for p in practices]:
                practices.append(organ_practices[organ])

        # 如果气机不畅，添加呼吸练习
        if "郁" in qi_dynamics or "不畅" in qi_dynamics:
            practices.append({
                "name": "腹式呼吸练习",
                "description": "吸气时腹部鼓起（4秒）-屏息（2秒）-呼气时腹部收缩（6秒），重复10次",
                "purpose": "调畅气机，宁心安神",
                "frequency": "每日2次，焦虑时随时练习"
            })

        return practices

    async def _generate_treatment_report_with_retry(self, analysis_report: dict,
                                                    base_report: dict,
                                                    max_retries: int = 3) -> Optional[dict]:
        """带重试机制的LLM调理报告生成

        尝试多次调用LLM优化基础报告，如果都失败则返回None。
        """
        cognitive_analysis = analysis_report.get("cognitive_analysis", {})
        tcm_analysis = analysis_report.get("tcm_analysis", {})

        thinking_traps = cognitive_analysis.get("thinking_traps", [])
        core_beliefs = cognitive_analysis.get("core_beliefs", [])
        dominant_emotion = tcm_analysis.get("dominant_emotion", "")
        related_organs = tcm_analysis.get("related_organs", [])
        qi_dynamics = tcm_analysis.get("qi_dynamics", "")

        # 构建提示词
        prompt = f"""基于以下分析信息，优化调理报告。

核心问题：
- 主要思维陷阱：{', '.join(thinking_traps)}
- 核心信念：{', '.join(core_beliefs)}
- 主导情志：{dominant_emotion}
- 相关脏腑：{', '.join(related_organs)}
- 气机问题：{qi_dynamics}

基础调理报告：
{json.dumps(base_report, ensure_ascii=False, indent=2)}

请优化此报告，使建议更具体、更可操作。保持相同的JSON结构。

必须返回有效的JSON格式，包含以下字段：
- summary: 报告摘要
- fusion_strategies: 融合策略列表
- cbt_homework: CBT作业列表
- tcm_practices: 中医实践列表
- recommendations: 总体建议列表
- next_steps: 后续步骤
"""

        for attempt in range(max_retries):
            try:
                print(f"DEBUG: 第{attempt + 1}次尝试调用LLM...")

                response = await self.llm_service.chat_completion(
                    messages=[
                        {"role": "system", "content": "你是一位专业的心理咨询调理师。请优化调理报告，使其更具体、更可操作。必须返回有效的JSON格式。"},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3,
                    max_tokens=2000
                )

                # 解析JSON
                content = response["choices"][0]["message"]["content"]

                # 提取JSON
                if "```json" in content:
                    start = content.find("```json") + 7
                    end = content.find("```", start)
                    content = content[start:end].strip()
                elif "```" in content:
                    start = content.find("```") + 3
                    end = content.find("```", start)
                    content = content[start:end].strip()

                report = json.loads(content)

                # 验证必要字段
                required_fields = ["summary", "fusion_strategies", "cbt_homework",
                                   "tcm_practices", "recommendations", "next_steps"]
                if all(field in report for field in required_fields):
                    print(f"DEBUG: 第{attempt + 1}次尝试成功")
                    return report
                else:
                    print(f"DEBUG: 第{attempt + 1}次尝试返回的JSON缺少必要字段")

            except Exception as e:
                print(f"DEBUG: 第{attempt + 1}次尝试失败: {e}")

            # 等待后重试
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # 指数退避：1s, 2s, 4s
                print(f"DEBUG: 等待{wait_time}秒后重试...")
                await asyncio.sleep(wait_time)

        print(f"DEBUG: {max_retries}次尝试均失败")
        return None

    def _get_default_treatment_report(self) -> dict:
        """获取默认调理报告"""
        return {
            "summary": "基于分析报告生成的调理报告",
            "fusion_strategies": [
                {
                    "time": datetime.now().isoformat(),
                    "fusion_mode": "cbt_tcm_integrated",
                    "key_points": "结合CBT认知调整和中医情志调理"
                }
            ],
            "cbt_homework": [
                {
                    "name": "情绪日记",
                    "description": "每天记录情绪变化和触发事件",
                    "frequency": "每天",
                    "duration": "持续进行"
                }
            ],
            "tcm_practices": [
                {
                    "name": "呼吸调息",
                    "description": "每日进行深呼吸练习，调节气机",
                    "purpose": "宁心安神",
                    "frequency": "每日2次"
                }
            ],
            "recommendations": ["建议持续关注情绪变化", "必要时寻求专业帮助"],
            "next_steps": {
                "suggestion": "继续观察情绪变化",
                "follow_up": "定期评估"
            }
        }