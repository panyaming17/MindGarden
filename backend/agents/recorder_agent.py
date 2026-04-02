# recorder_agent.py
import joblib
import os
import json
from sentence_transformers import SentenceTransformer
from backend.agents.base_agent import BaseAgent
from backend.repositories.record_repository_new import RecordRepository
from backend.core.llm_service import LLMService
from typing import Optional, Tuple, Dict, Any
from backend.core.database import SessionReportDB, SessionLocal
print("RecordRepository imported from:", RecordRepository.__module__)
class RecorderAgent(BaseAgent):
    # 类变量，所有实例共享
    _models_loaded = False
    _encoder = None
    _intensity_model = None
    _hedonic_model = None
    _tension_model = None
    _complexity_model = None
    _le_hedonic = None
    _le_tension = None
    _le_complexity = None

    def __init__(self, agent_name: str = "recorder_agent", llm_service: Optional[LLMService] = None):
        super().__init__(agent_name)
        self.repository = RecordRepository()
        self.llm_service = llm_service
        self._init_prompts()
        self.active_sessions = {}
        # 用于跟踪每个会话的对话计数和待分析对话
        self.session_dialogue_buffer = {}  # {session_id: {"count": 0, "dialogues": []}}

        # 初始化时加载模型
        if not RecorderAgent._models_loaded:
            try:
                self._load_models()
                RecorderAgent._models_loaded = True
                print("记录师智能体模型加载成功")
            except Exception as e:
                print(f"记录师智能体模型加载失败: {e}")

    def _load_models(self):
        """加载模型（只执行一次）"""
        try:
            RecorderAgent._encoder = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
            current_dir = os.path.dirname(os.path.abspath(__file__))
            model_dir = os.path.join(current_dir, "..", "checkpoints", "models")
            model_dir = os.path.abspath(model_dir)
            RecorderAgent._intensity_model = joblib.load(os.path.join(model_dir, "latest_intensity_model.pkl"))
            RecorderAgent._hedonic_model = joblib.load(os.path.join(model_dir, "latest_hedonic_model.pkl"))
            RecorderAgent._tension_model = joblib.load(os.path.join(model_dir, "latest_tension_model.pkl"))
            RecorderAgent._complexity_model = joblib.load(os.path.join(model_dir, "latest_complexity_model.pkl"))
            RecorderAgent._le_hedonic = joblib.load(os.path.join(model_dir, "le_hedonic.pkl"))
            RecorderAgent._le_tension = joblib.load(os.path.join(model_dir, "le_tension.pkl"))
            RecorderAgent._le_complexity = joblib.load(os.path.join(model_dir, "le_complexity.pkl"))
        except Exception as e:
            # 如果加载失败，抛出异常，让上层知道
            raise

    def predict_four_dim(self, text: str) -> Dict[str, Any]:
        """调用四维模型预测"""
        # 如果模型未加载成功，使用fallback
        if not RecorderAgent._models_loaded:
            return self._fallback_predict(text)

        try:
            emb = RecorderAgent._encoder.encode([text])
            intensity = float(RecorderAgent._intensity_model.predict(emb)[0])
            hedonic = RecorderAgent._le_hedonic.inverse_transform(RecorderAgent._hedonic_model.predict(emb))[0]
            tension = RecorderAgent._le_tension.inverse_transform(RecorderAgent._tension_model.predict(emb))[0]
            complexity = RecorderAgent._le_complexity.inverse_transform(RecorderAgent._complexity_model.predict(emb))[0]
            return {
                "intensity": round(intensity, 2),
                "hedonic": hedonic,
                "tension": tension,
                "complexity": complexity
            }
        except Exception as e:
            return self._fallback_predict(text)

    def _fallback_predict(self, text: str) -> Dict[str, Any]:
        """简单规则后备，确保测试流程可以继续"""
        if "紧张" in text or "焦虑" in text or "害怕" in text:
            return {"intensity": 7.5, "hedonic": "负性", "tension": "高", "complexity": "简单"}
        if "开心" in text or "高兴" in text:
            return {"intensity": 6.0, "hedonic": "正性", "tension": "低", "complexity": "简单"}
        return {"intensity": 3.0, "hedonic": "中性", "tension": "低", "complexity": "简单"}

    def _init_prompts(self):
        self.system_prompt = """你是一个高效的语义筛选助手。你的任务是判断用户输入是否包含需要专业心理咨询师关注的内容。请仅回答“是”或“否”，不要输出其他任何内容。
        请判断以下用户发言是否包含：
        1) 对自我、他人或未来的负面评价、担忧、恐惧、自责等（例如“我太差了”、“他肯定讨厌我”）。
        2) 具体的事件或行为描述（例如“昨天和同事吵架了”、“最近总失眠”）。
        3) 情绪表达（愤怒、悲伤、焦虑等）或身体症状（胸闷、手抖等）。
        只回答“是”或“否”。
        发言：{text}"""

    def quick_screen(self, text: str, use_llm: bool = True) -> Tuple[bool, Dict[str, Any]]:
        dim = self.predict_four_dim(text)
        if dim["intensity"] >= 4 or dim["tension"] == "高" or dim["complexity"] == "复杂":
            return True, dim

        if use_llm and self.llm_service:
            try:
                prompt = self.system_prompt.format(text=text)
                response = self.llm_service.chat_completion(
                    messages=[
                        {"role": "system", "content": self.system_prompt},
                        {"role": "user", "content": text}
                    ],
                    temperature=0,
                    max_tokens=5
                )
                answer = response.choices[0].message.content.strip()
                return answer == "是", dim
            except Exception as e:
                print(f"LLM 筛选失败: {e}")
        return False, dim

    def save_dialogue(self, user_id: str, content: str, role: str, four_dim: dict, is_valuable: bool, session_id: Optional[str] = None):
        try:
            self.repository.save_dialogue(
                user_id=user_id,
                role=role,
                content=content,
                # four_dim_intensity=four_dim.get("intensity"),
                # four_dim_hedonic=four_dim.get("hedonic"),
                # four_dim_tension=four_dim.get("tension"),
                # four_dim_complexity=four_dim.get("complexity"),
                four_dim=four_dim,
                is_valuable=is_valuable,
                session_id=session_id
            )
        except Exception as e:
            print(f"保存对话失败: {e}")

    def recorder_process(self, user_input: str, user_id: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        is_valuable, dim = self.quick_screen(user_input)
        self.save_dialogue(user_id, user_input, "user", dim, is_valuable, session_id)
        return {
            "user_id": user_id,
            "input": user_input,
            "four_dim": dim,
            "is_valuable": is_valuable
        }

    async def generate_record_report(self, user_id: str, session_id: str,
                                     dialogue_history: list) -> dict:
        """生成记录报告

        基于对话历史提取关键信息，生成记录报告。
        """
        if not self.llm_service:
            raise Exception("LLM服务未初始化")

        # 只提取用户对话用于情绪统计
        user_dialogues = [d for d in dialogue_history if d.get("role") == "user"]

        # 构建提示词
        prompt = f"""基于以下用户对话历史，生成一份记录报告。

用户对话历史：
{json.dumps(user_dialogues, ensure_ascii=False, indent=2)}

请生成记录报告，注意以下要求：
1. situations: 情境列表，描述"你"所处的情景（用"你"作为主语，不要出现"来访者""咨询师"等词，只描述用户的情景）
2. emotions: 情绪及占比列表，格式为[["情绪名", 占比], ...]，占比总和为1，基于对话中情绪出现频率统计
3. automatic_thoughts: CBT自动化思维列表（如灾难化思维、全或无思维、心理过滤等标准化CBT思维陷阱类型）
4. physical_symptoms: 身体症状列表
5. behaviors: 行为表现列表
6. duration: 持续时间描述
7. context: 背景信息（用"你"作为主语）

请严格按照以下JSON格式返回：
{{
  "situations": [
    {{
      "description": "你面临求职面试的压力",
      "time": "2026-03-28T20:00:00Z",
      "related": ["焦虑", "恐惧"]
    }}
  ],
  "emotions": [["焦虑", 0.6], ["恐惧", 0.3], ["沮丧", 0.1]],
  "automatic_thoughts": ["灾难化思维", "全或无思维"],
  "physical_symptoms": ["呼吸急促", "失眠"],
  "behaviors": ["回避面试准备", "反复检查简历"],
  "duration": "持续时间",
  "context": "你正在经历求职压力，表现出焦虑情绪"
}}
"""

        # 调用LLM
        response = await self.llm_service.chat_completion(
            messages=[
                {"role": "system", "content": "你是一位专业的心理咨询记录师。请基于用户对话提取关键信息，生成记录报告。注意：所有描述都用'你'作为主语，不要出现'来访者'等词。"},
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
            print(f"解析记录报告失败: {e}, 内容: {content if 'content' in locals() else 'N/A'}")
            # 返回默认报告结构
            report = {
                "situations": [],
                "emotions": [],
                "automatic_thoughts": [],
                "physical_symptoms": [],
                "behaviors": [],
                "duration": "",
                "context": ""
            }
        return report

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        user_input = input_data.get("message", input_data.get("user_input", ""))
        user_id = input_data.get("user_id", "")
        session_id = input_data.get("session_id", None)
        if not user_input or not user_id:
            return {
                "status": "error",
                "message": "缺少必要的输入参数"
            }
        try:
            result = self.recorder_process(user_input, user_id, session_id)
            
            # 三句触发逻辑：累积对话，每3句调用LLM分析
            if session_id:
                await self._accumulate_and_analyze(user_id, session_id, user_input, result)
            
            return {
                "intensity": result["four_dim"]["intensity"],
                "hedonic": result["four_dim"]["hedonic"],
                "tension": result["four_dim"]["tension"],
                "complexity": result["four_dim"]["complexity"],
                "is_valuable": result["is_valuable"]
            }
        except Exception as e:
            print(f"记录师处理失败: {e}")
            return {
                "intensity": 0.0,
                "hedonic": "中性",
                "tension": "低",
                "complexity": "简单",
                "is_valuable": False
            }
    
    async def _accumulate_and_analyze(self, user_id: str, session_id: str, user_input: str, result: Dict[str, Any]):
        """累积对话，每3句调用LLM分析并增量更新记录报告"""
        # 初始化会话缓冲区
        if session_id not in self.session_dialogue_buffer:
            self.session_dialogue_buffer[session_id] = {
                "count": 0,
                "dialogues": [],
                "user_id": user_id
            }
        
        buffer = self.session_dialogue_buffer[session_id]
        buffer["count"] += 1
        buffer["dialogues"].append({
            "role": "user",
            "content": user_input,
            "four_dim": result["four_dim"]
        })
        
        # 每3句触发一次分析
        if buffer["count"] >= 3:
            await self._update_record_report_incrementally(session_id, buffer)
            # 重置计数器，但保留已分析的对话
            buffer["count"] = 0
    
    async def _update_record_report_incrementally(self, session_id: str, buffer: Dict):
        """增量更新记录报告"""
        if not self.llm_service:
            return

        try:
            # 构建提示词，只分析新的3句话
            dialogues_to_analyze = buffer["dialogues"][-3:]

            # 只提取用户对话
            user_dialogues = [d for d in dialogues_to_analyze if d.get("role") == "user"]

            prompt = f"""基于以下用户对话，提取记录报告所需的信息。

用户对话内容：
{json.dumps(user_dialogues, ensure_ascii=False, indent=2)}

请提取以下信息并返回JSON格式：
1. situations: 情境列表（描述"你"所处的情景，用"你"作为主语）
2. emotions: 情绪及占比列表，格式为[["情绪名", 占比], ...]
3. automatic_thoughts: CBT自动化思维列表（如灾难化思维、全或无思维等标准化类型）
4. physical_symptoms: 身体症状列表
5. behaviors: 行为表现列表

注意：
- 这是增量分析，只需要返回这3句话中提取的信息
- 所有描述都用"你"作为主语，不要出现"来访者"等词
- emotions需要统计各情绪占比，总和为1

返回格式：
{{
  "situations": [{{"description": "你面临...", "related": ["焦虑", "恐惧"]}}],
  "emotions": [["焦虑", 0.6], ["恐惧", 0.4]],
  "automatic_thoughts": ["灾难化思维", "全或无思维"],
  "physical_symptoms": ["呼吸急促"],
  "behaviors": ["回避行为"]
}}
"""

            response = await self.llm_service.chat_completion(
                messages=[
                    {"role": "system", "content": "你是一位专业的心理咨询记录师。请提取用户对话中的关键信息。注意：所有描述都用'你'作为主语，不要出现'来访者'等词。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=800
            )

            # 解析JSON
            try:
                content = response["choices"][0]["message"]["content"]
                if "```json" in content:
                    start = content.find("```json") + 7
                    end = content.find("```", start)
                    content = content[start:end].strip()

                new_data = json.loads(content)
            except (json.JSONDecodeError, KeyError) as e:
                print(f"解析增量记录报告失败: {e}")
                new_data = {
                    "situations": [],
                    "emotions": [],
                    "automatic_thoughts": [],
                    "physical_symptoms": [],
                    "behaviors": []
                }

            # 合并到现有的记录报告中
            await self._merge_record_report(buffer["user_id"], session_id, new_data)
            
        except Exception as e:
            print(f"增量更新记录报告失败: {e}")
    
    async def _merge_record_report(self, user_id: str, session_id: str, new_data: Dict):
        """合并新的分析数据到记录报告"""
        db = SessionLocal()
        try:
            # 查询是否已存在记录报告
            existing_report = db.query(SessionReportDB).filter(
                SessionReportDB.user_id == user_id,
                SessionReportDB.session_id == session_id
            ).first()
            
            if existing_report and existing_report.record_report_json:
                # 合并数据
                existing_data = existing_report.record_report_json
                for key in ["situations", "emotions", "automatic_thoughts", "physical_symptoms", "behaviors"]:
                    if key in new_data and new_data[key]:
                        if key not in existing_data:
                            existing_data[key] = []
                        existing_data[key].extend(new_data[key])
                existing_report.record_report_json = existing_data
            else:
                # 创建新的记录报告
                new_report = SessionReportDB(
                    user_id=user_id,
                    session_id=session_id,
                    record_report_json=new_data,
                    analysis_report_json={},
                    treatment_report_json={}
                )
                db.add(new_report)
            
            db.commit()
        except Exception as e:
            print(f"合并记录报告失败: {e}")
            db.rollback()
        finally:
            db.close()
    
    async def finalize_record_report(self, user_id: str, session_id: str, force_regenerate: bool = True) -> Dict:
        """最终确定记录报告（当调用/end-session时）

        如果还有未分析的对话（不足3句），先分析剩余内容，然后补充duration和context。
        默认强制重新生成记录报告（force_regenerate=True），确保使用最新的提示词逻辑。
        """
        buffer = self.session_dialogue_buffer.get(session_id, {"count": 0, "dialogues": []})

        # 如果还有未分析的对话
        if buffer["count"] > 0 and buffer["dialogues"]:
            await self._update_record_report_incrementally(session_id, buffer)

        # 从所有对话历史生成记录报告（强制重新生成）
        print(f"DEBUG: 正在生成记录报告（强制重新生成={force_regenerate}）")
        from backend.core.database import DialogueDB, SessionLocal
        db = SessionLocal()
        try:
            dialogues = db.query(DialogueDB).filter(
                DialogueDB.user_id == user_id,
                DialogueDB.session_id == session_id
            ).order_by(DialogueDB.created_at.asc()).all()

            # 构建对话历史
            dialogue_history = []
            for d in dialogues:
                dialogue_history.append({
                    "role": d.role,
                    "content": d.content,
                    "created_at": d.created_at.isoformat() if d.created_at else None
                })

            # 生成记录报告
            record_data = await self.generate_record_report(user_id, session_id, dialogue_history)

            # 保存到数据库
            report = db.query(SessionReportDB).filter(
                SessionReportDB.user_id == user_id,
                SessionReportDB.session_id == session_id
            ).first()

            if report:
                report.record_report_json = record_data
            else:
                new_report = SessionReportDB(
                    user_id=user_id,
                    session_id=session_id,
                    record_report_json=record_data,
                    analysis_report_json={},
                    treatment_report_json={}
                )
                db.add(new_report)
            db.commit()

            # 补充duration和context（如果为空）
            if self.llm_service and (not record_data.get("duration") or not record_data.get("context")):
                try:
                    prompt = f"""基于以下记录报告内容，生成duration（持续时间描述）和context（背景信息）。

记录报告内容：
{json.dumps(record_data, ensure_ascii=False, indent=2)}

请返回JSON格式：
{{
  "duration": "持续时间描述（如'两周'、'三天'等）",
  "context": "背景信息/上下文描述"
}}
"""
                    response = await self.llm_service.chat_completion(
                        messages=[
                            {"role": "system", "content": "你是一位专业的心理咨询记录师。"},
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

                    supplement = json.loads(content)
                    if not record_data.get("duration"):
                        record_data["duration"] = supplement.get("duration", "")
                    if not record_data.get("context"):
                        record_data["context"] = supplement.get("context", "")

                    # 更新数据库
                    report = db.query(SessionReportDB).filter(
                        SessionReportDB.user_id == user_id,
                        SessionReportDB.session_id == session_id
                    ).first()
                    if report:
                        report.record_report_json = record_data
                        db.commit()
                except Exception as e:
                    print(f"补充duration和context失败: {e}")

            # 清理缓冲区
            if session_id in self.session_dialogue_buffer:
                del self.session_dialogue_buffer[session_id]

            return record_data

        except Exception as e:
            print(f"最终确定记录报告失败: {e}")
            import traceback
            traceback.print_exc()
            return {}
        finally:
            db.close()