import json
import asyncio
from datetime import datetime
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

请用自然、温暖的语言回复，像和朋友谈心一样，可以适当用些语气词。
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
        recent_history = self._get_recent_history(user_id, limit=3, session_id=session_id)

        # 如果没有提供建议，则获取最新建议
        if advice is None:
            advice = self.repository.get_latest_advice(user_id)
            if advice:
                # 提取advice_json字段的内容
                advice = advice.get("advice_json", advice)
            else:
                # 若无建议，使用默认建议（空字典，提示词会使用默认值）
                advice = {}

        # 构建提示词
        prompt = self._build_prompt(user_input, recent_history, advice)

        # 调用LLM
        reply = await self._get_llm_response(
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=500
        )
        reply = reply.strip()

        # 存储回复
        self.repository.save_dialogue(
            user_id=user_id,
            role="assistant",
            content=reply,
            four_dim=None,
            is_valuable=False,
            session_id=session_id
        )

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
            "time": datetime.utcnow().isoformat(),
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
                    "time": datetime.utcnow().isoformat(),
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