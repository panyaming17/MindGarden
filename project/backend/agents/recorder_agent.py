# recorder_agent.py
import joblib
import os
import json
import uuid
from datetime import datetime
from backend.agents.base_agent import BaseAgent
from backend.repositories.record_repository import RecordRepository
from backend.core.llm_service import LLMService
from typing import Optional, Tuple, Dict, Any, List
from backend.core.database import SessionReportDB, SessionLocal
from backend.services.clinical_case_rag import get_clinical_case_rag

# 本地模型路径配置
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LOCAL_MODEL_PATH = os.path.join(
    PROJECT_ROOT, 
    "models", 
    "paraphrase-multilingual-MiniLM-L12-v2",
    "models--sentence-transformers--paraphrase-multilingual-MiniLM-L12-v2",
    "snapshots",
    "e8f8c211226b894fcb81acc59f3b34ba3efd5f42"
)

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
        self.session_dialogue_buffer = {}  # {session_id: {"count": 0, "dialogues": []}}
        self.clinical_rag = None
        # LLM 失败计数器（按用户维度）
        self.llm_failure_count = {}  # {user_id: count}
        # SVM 模型加载标志
        self._svm_models_loaded = False

    def _get_clinical_rag(self):
        """延迟加载临床案例RAG服务"""
        if self.clinical_rag is None:
            try:
                self.clinical_rag = get_clinical_case_rag()
                print("[记录师] 临床案例RAG服务加载成功")
            except Exception as e:
                print(f"[记录师] 临床案例RAG加载失败: {e}")
                self.clinical_rag = None
        return self.clinical_rag

    def _load_svm_models(self):
        """加载 SVM 模型作为备选方案（只执行一次）"""
        if self._svm_models_loaded:
            return
        
        try:
            from sentence_transformers import SentenceTransformer
            
            # 优先使用本地模型
            if os.path.exists(LOCAL_MODEL_PATH):
                print(f"[记录师] 使用本地模型：{LOCAL_MODEL_PATH}")
                RecorderAgent._encoder = SentenceTransformer(LOCAL_MODEL_PATH)
            else:
                print(f"本地模型不存在，从网络下载：{LOCAL_MODEL_PATH}")
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
            
            self._svm_models_loaded = True
            print("[记录师] SVM 备选模型加载成功")
        except Exception as e:
            print(f"[记录师] SVM 模型加载失败：{e}")
            raise

    def _predict_four_dim_with_svm(self, text: str) -> Dict[str, Any]:
        """使用 SVM 模型进行四维预测（备选方案）"""
        try:
            # 确保模型已加载
            if not self._svm_models_loaded:
                self._load_svm_models()
            
            # 文本向量化
            embedding = RecorderAgent._encoder.encode([text])[0]
            
            # 预测四维
            intensity = float(RecorderAgent._intensity_model.predict([embedding])[0])
            hedonic_pred = RecorderAgent._hedonic_model.predict([embedding])[0]
            tension_pred = RecorderAgent._tension_model.predict([embedding])[0]
            complexity_pred = RecorderAgent._complexity_model.predict([embedding])[0]
            
            # 标签映射
            hedonic = RecorderAgent._le_hedonic.inverse_transform([hedonic_pred])[0]
            tension = RecorderAgent._le_tension.inverse_transform([tension_pred])[0]
            complexity = RecorderAgent._le_complexity.inverse_transform([complexity_pred])[0]
            
            print(f"[记录师] 使用 SVM 模型预测：强度={intensity:.2f}, 快感={hedonic}, 紧张={tension}, 复杂度={complexity}")
            
            return {
                "intensity": round(intensity, 2),
                "hedonic": hedonic,
                "tension": tension,
                "complexity": complexity,
                "source": "svm"
            }
        except Exception as e:
            print(f"[记录师] SVM 预测失败：{e}")
            # SVM 也失败时，降级为规则预测
            return self._fallback_predict(text)
    
    def predict_four_dim(self, text: str, context_dialogues: List[Dict] = None, user_id: str = None) -> Dict[str, Any]:
        """
        四维情绪预测（带失败降级机制）
        
        预测优先级：
        1. 临床案例 RAG（主要方案）
        2. 规则预测（RAG 失败时）
        3. SVM 模型（LLM 连续失败 3 次后的备选方案）
        
        :param text: 用户输入文本
        :param context_dialogues: 对话上下文
        :param user_id: 用户 ID（用于失败计数）
        :return: 四维预测结果
        """
        # 策略 1: 使用临床案例 RAG 预测
        rag = self._get_clinical_rag()
        if rag:
            try:
                result = rag.predict_four_dim_from_cases(text, context_dialogues)
                return {
                    "intensity": result["intensity"],
                    "hedonic": result["hedonic"],
                    "tension": result["tension"],
                    "complexity": result["complexity"],
                    "rag_similar_cases": result.get("similar_cases", []),
                    "source": "rag"
                }
            except Exception as e:
                print(f"[记录师] RAG 预测失败，降级为规则预测：{e}")
        
        # RAG 失败，使用规则预测
        result = self._fallback_predict(text)
        result["source"] = "rule"
        return result

    def _fallback_predict(self, text: str) -> Dict[str, Any]:
        """简单规则后备预测"""
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

    def quick_screen(self, text: str, use_llm: bool = True, user_id: str = None) -> tuple:
        # 先进行四维预测
        dim = self.predict_four_dim(text, user_id=user_id)
        
        # 如果四维已经达到阈值，直接返回
        if dim["intensity"] >= 4 or dim["tension"] == "高" or dim["complexity"] == "复杂":
            return True, dim
        
        # 使用 LLM 进行二次筛选
        if use_llm and self.llm_service:
            try:
                prompt = self.system_prompt.format(text=text)
                response = self.llm_service.chat_completion(
                    messages=[{"role": "system", "content": self.system_prompt}, {"role": "user", "content": text}],
                    temperature=0, max_tokens=5
                )
                answer = response.choices[0].message.content.strip()
                
                # LLM 调用成功，重置失败计数
                if user_id and user_id in self.llm_failure_count:
                    self.llm_failure_count[user_id] = 0
                    print(f"[记录师] LLM 调用成功，重置用户 {user_id} 的失败计数")
                
                return answer == "是", dim
            except Exception as e:
                print(f"[记录师] LLM 筛选失败：{e}")
                
                # LLM 失败计数 +1
                if user_id:
                    if user_id not in self.llm_failure_count:
                        self.llm_failure_count[user_id] = 0
                    self.llm_failure_count[user_id] += 1
                    
                    print(f"[记录师] 用户 {user_id} LLM 失败次数：{self.llm_failure_count[user_id]}/3")
                    
                    # 连续失败 3 次，切换到 SVM 模式
                    if self.llm_failure_count[user_id] >= 3:
                        print(f"[记录师] ⚠️ 用户 {user_id} LLM 连续失败 3 次，切换到 SVM 备选模式")
                        # 使用 SVM 重新预测四维
                        svm_dim = self._predict_four_dim_with_svm(text)
                        # 根据 SVM 结果判断
                        if svm_dim["intensity"] >= 4 or svm_dim["tension"] == "高" or svm_dim["complexity"] == "复杂":
                            return True, svm_dim
                        return False, svm_dim
                
                return False, dim
        return False, dim

    def save_dialogue(self, user_id: str, content: str, role: str, four_dim: dict, is_valuable: bool, session_id: Optional[str] = None, stage: Optional[str] = None) -> Optional[int]:
        try:
            dialogue_id = self.repository.save_dialogue(
                user_id=user_id, role=role, content=content,
                four_dim=four_dim, is_valuable=is_valuable, session_id=session_id, stage=stage
            )
            return dialogue_id
        except Exception as e:
            print(f"[记录师] 保存对话失败：{e}")
            return None

    def recorder_process(self, user_input: str, user_id: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        # 获取最近对话上下文用于 RAG
        recent_context = self.repository.get_recent_dialogues(user_id, limit=6, session_id=session_id)
        dim = self.predict_four_dim(user_input, recent_context)
        is_valuable = dim["intensity"] >= 4 or dim["tension"] == "高" or dim["complexity"] == "复杂"
        
        # 计算当前阶段
        stage = self.determine_stage_v2(session_id, dim, user_input, user_id)
        
        # 保存对话记录（包含 stage）
        dialogue_id = self.save_dialogue(user_id, user_input, "user", dim, is_valuable, session_id, stage)

        # RAG索引：将用户消息添加到记忆RAG（原有逻辑保留）
        try:
            from backend.services.memory_rag_service import get_memory_rag_service, save_memory_rag_index
            rag_service = get_memory_rag_service()
            if rag_service and session_id:
                rag_service.add_chunks(
                    user_id=user_id, session_id=session_id,
                    dialogues=[{"role": "user", "content": user_input, "timestamp": "", "metadata": dim}]
                )
                save_memory_rag_index()
        except Exception as e:
            print(f"[RAG 索引] 添加失败：{e}")

        return {
            "user_id": user_id,
            "input": user_input,
            "four_dim": dim,
            "is_valuable": is_valuable,
            "dialogue_id": dialogue_id,
            "stage": stage
        }

    async def generate_record_report(self, user_id: str, session_id: str,
                                     dialogue_history: list) -> dict:
        """生成记录报告

        基于对话历史提取关键信息，生成记录报告。
        格式符合前端 RecordReport.vue 期望的结构。
        """
        if not self.llm_service:
            raise Exception("LLM服务未初始化")

        user_dialogues = [d for d in dialogue_history if d.get("role") == "user"]

        prompt = f"""基于以下用户对话历史，生成一份记录报告。

用户对话历史：
{json.dumps(user_dialogues, ensure_ascii=False, indent=2)}

请生成记录报告，注意以下要求：
1. situations: 情境时间线列表，描述"你"所处的情景，包含 time(ISO格式时间)、description(情境描述)、related(相关情绪列表)
2. emotions: 情绪列表，格式为 [{{"type": "情绪名", "intensity": 1-10, "description": "描述"}}]，intensity 根据对话中情绪强烈程度估算
3. automatic_thoughts: CBT思维陷阱类型列表（如"灾难化思维"、"全或无思维"、"心理过滤"、"过度概括"、"情绪化推理"等标准化类型），可添加多个
4. physical_symptoms: 身体症状列表
5. behaviors: 行为表现列表
6. duration: 持续时间描述（如"30分钟"、"1小时"）
7. context: 背景信息摘要（用"你"作为主语，描述整体情况）
8. primary_emotion: 主要情绪（字符串）
9. dominant_thinking_trap: 主导思维陷阱类型（从 automatic_thoughts 中选择最突出的一个）

请严格按照以下 JSON 格式返回：
{{
  "situations": [
    {{
      "time": "2026-03-28T20:00:00Z",
      "description": "你面临求职面试的压力",
      "related": ["焦虑", "恐惧"]
    }}
  ],
  "emotions": [
    {{ "type": "焦虑", "intensity": 8, "description": "对面试结果的担忧" }},
    {{ "type": "恐惧", "intensity": 7, "description": "对失败的害怕" }}
  ],
  "automatic_thoughts": ["灾难化思维", "全或无思维", "过度概括"],
  "physical_symptoms": ["呼吸急促", "失眠", "手心出汗"],
  "behaviors": ["回避面试准备", "反复检查简历"],
  "duration": "30分钟",
  "context": "你正在经历求职压力，对即将到来的面试感到焦虑和恐惧",
  "primary_emotion": "焦虑",
  "dominant_thinking_trap": "灾难化思维"
}}
"""

        response = await self.llm_service.chat_completion(
            messages=[
                {"role": "system", "content": "你是一位专业的心理咨询记录师。请基于用户对话提取关键信息，生成记录报告。注意：所有描述都用'你'作为主语，不要出现'来访者'等词。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=1500
        )

        try:
            content = response["choices"][0]["message"]["content"]
            if "```json" in content:
                start = content.find("```json") + 7
                end = content.find("```", start)
                content = content[start:end].strip()

            report = json.loads(content)
            
            report["record_id"] = f"record_{uuid.uuid4().hex[:8]}"
            report["session_id"] = session_id
            report["user_id"] = user_id
            report["timestamp"] = datetime.now().isoformat()
            
        except (json.JSONDecodeError, KeyError) as e:
            print(f"解析记录报告失败: {e}, 内容: {content if 'content' in locals() else 'N/A'}")
            report = {
                "record_id": f"record_{uuid.uuid4().hex[:8]}",
                "session_id": session_id,
                "user_id": user_id,
                "situations": [],
                "emotions": [],
                "automatic_thoughts": [],
                "physical_symptoms": [],
                "behaviors": [],
                "duration": "",
                "context": "",
                "primary_emotion": "",
                "dominant_thinking_trap": "",
                "timestamp": datetime.now().isoformat()
            }
        return report

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        user_input = input_data.get("message", input_data.get("user_input", ""))
        user_id = input_data.get("user_id", "")
        session_id = input_data.get("session_id", None)
        if not user_input or not user_id:
            return {"status": "error", "message": "缺少必要的输入参数"}
        try:
            result = self.recorder_process(user_input, user_id, session_id)
            # 三句触发逻辑保持不变
            if session_id:
                await self._accumulate_and_analyze(user_id, session_id, user_input, result)
            return {
                "intensity": result["four_dim"]["intensity"],
                "hedonic": result["four_dim"]["hedonic"],
                "tension": result["four_dim"]["tension"],
                "complexity": result["four_dim"]["complexity"],
                "dialogue_id": result.get("dialogue_id"),
                "stage": result["stage"]
            }
        except Exception as e:
            print(f"记录师处理失败: {e}")
            return {"intensity": 0.0, "hedonic": "中性", "tension": "低", "complexity": "简单", "stage": "S1_建立关系"}
    
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
            dialogues_to_analyze = buffer["dialogues"][-3:]
            user_dialogues = [d for d in dialogues_to_analyze if d.get("role") == "user"]

            prompt = f"""基于以下用户对话，提取记录报告所需的信息。

用户对话内容：
{json.dumps(user_dialogues, ensure_ascii=False, indent=2)}

请提取以下信息并返回 JSON 格式：
1. situations: 情境时间线列表，包含 time(ISO格式时间)、description(情境描述)、related(相关情绪列表)
2. emotions: 情绪列表，格式为 [{{"type": "情绪名", "intensity": 1-10, "description": "描述"}}]
3. automatic_thoughts: CBT思维陷阱类型列表（如"灾难化思维"、"全或无思维"、"心理过滤"、"过度概括"、"情绪化推理"等标准化类型），可添加多个
4. physical_symptoms: 身体症状列表
5. behaviors: 行为表现列表
6. primary_emotion: 主要情绪（字符串）
7. dominant_thinking_trap: 主导思维陷阱类型（从 automatic_thoughts 中选择最突出的一个）

注意：
- 这是增量分析，只需要返回这 3 句话中提取的信息
- 所有描述都用"你"作为主语
- intensity 根据对话中情绪强烈程度估算(1-10)

返回格式：
{{
  "situations": [{{"time": "2026-03-28T20:00:00Z", "description": "你面临...", "related": ["焦虑", "恐惧"]}}],
  "emotions": [{{"type": "焦虑", "intensity": 8, "description": "对...的担忧"}}],
  "automatic_thoughts": ["灾难化思维", "全或无思维"],
  "physical_symptoms": ["呼吸急促"],
  "behaviors": ["回避行为"],
  "primary_emotion": "焦虑",
  "dominant_thinking_trap": "灾难化思维"
}}
"""

            response = await self.llm_service.chat_completion(
                messages=[
                    {"role": "system", "content": "你是一位专业的心理咨询记录师。请提取用户对话中的关键信息。注意：所有描述都用'你'作为主语。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=800
            )

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

            await self._merge_record_report(buffer["user_id"], session_id, new_data)
            
        except Exception as e:
            print(f"增量更新记录报告失败: {e}")
    
    async def _merge_record_report(self, user_id: str, session_id: str, new_data: Dict):
        """合并新的分析数据到记录报告"""
        db = SessionLocal()
        try:
            existing_report = db.query(SessionReportDB).filter(
                SessionReportDB.user_id == user_id,
                SessionReportDB.session_id == session_id
            ).order_by(SessionReportDB.updated_at.desc(), SessionReportDB.id.desc()).first()
            
            if existing_report:
                if existing_report.record_report_json:
                    existing_data = existing_report.record_report_json
                else:
                    existing_data = {}
                
                for key in ["situations", "emotions", "automatic_thoughts", "physical_symptoms", "behaviors"]:
                    if key in new_data and new_data[key]:
                        if key not in existing_data:
                            existing_data[key] = []
                        existing_data[key].extend(new_data[key])
                
                if "emotions" in existing_data and existing_data["emotions"]:
                    emotion_intensities = {}
                    for emotion_item in existing_data["emotions"]:
                        if isinstance(emotion_item, dict):
                            emotion_name = emotion_item.get("type", "")
                            intensity = emotion_item.get("intensity", 5)
                            if emotion_name:
                                if emotion_name not in emotion_intensities:
                                    emotion_intensities[emotion_name] = []
                                emotion_intensities[emotion_name].append(intensity)
                        elif isinstance(emotion_item, list) and len(emotion_item) == 2:
                            emotion_name, ratio = emotion_item
                            intensity = round(ratio * 10)
                            if emotion_name:
                                if emotion_name not in emotion_intensities:
                                    emotion_intensities[emotion_name] = []
                                emotion_intensities[emotion_name].append(intensity)
                    
                    if emotion_intensities:
                        avg_intensities = {k: sum(v)/len(v) for k, v in emotion_intensities.items()}
                        existing_data["primary_emotion"] = max(avg_intensities, key=avg_intensities.get)
                
                if "automatic_thoughts" in existing_data and existing_data["automatic_thoughts"]:
                    from collections import Counter
                    thought_counts = Counter(existing_data["automatic_thoughts"])
                    if thought_counts:
                        dominant_thinking_trap = thought_counts.most_common(1)[0][0]
                        existing_data["dominant_thinking_trap"] = dominant_thinking_trap
                
                existing_report.record_report_json = existing_data
            else:
                print(f"WARNING: _merge_record_report 未找到 session_reports 记录，跳过合并。user_id={user_id}, session_id={session_id}")
                print(f"WARNING: 请确保在调用增量更新前已通过 end_session 创建记录")
            
            db.commit()
        except Exception as e:
            print(f"合并记录报告失败: {e}")
            db.rollback()
        finally:
            db.close()
    
    def determine_stage_v2(self, session_id: str, four_dim: dict, user_input: str, user_id: str) -> str:
        """六阶段判定逻辑"""
        round_count = self.repository.get_dialogue_count(session_id)
        
        archive_record = self.repository.get_user_archive(user_id, session_id)
        archive = archive_record.get("archive_json", {}) if archive_record else {}

        has_focus = bool(archive.get("current_focus"))
        cognitive_patterns = archive.get("cognitive_patterns", {})
        has_traps = bool(cognitive_patterns.get("thinking_traps"))
        intensity = four_dim.get("intensity", 0)

        # 检查是否已有干预建议
        has_intervention = self._session_has_intervention(session_id)

        if round_count <= 2:
            return "S1_建立关系"
        if self._user_asks_for_advice(user_input) or round_count >= 15:
            return "S6_总结巩固"
        if has_intervention:
            return "S5_干预中"
        if has_traps and intensity >= 4:
            return "S4_认知浮现"
        if has_focus and intensity >= 4:
            info_completeness = archive.get("info_completeness", 0.5)
            if info_completeness < 0.7:
                return "S3_深度探索"
            else:
                return "S4_认知浮现"
        return "S2_信息收集"

    def _session_has_intervention(self, session_id: str) -> bool:
        """检查本会话是否已给出干预建议"""
        advices = self.repository.get_advices_by_session(session_id)
        return len(advices) > 0

    def _user_asks_for_advice(self, text: str) -> bool:
        advice_keywords = ["我该怎么办", "怎么办", "怎么解决", "有什么方法", "我该怎么做",
                           "帮帮我", "怎么办才好", "有没有建议", "能给点建议", "求建议",
                           "我应该", "要怎么", "如何是好"]
        return any(kw in text for kw in advice_keywords)

    async def finalize_record_report(self, user_id: str, session_id: str, force_regenerate: bool = True) -> Dict:
        """最终确定记录报告（当调用/end-session时）

        如果还有未分析的对话（不足3句），先分析剩余内容，然后补充duration和context。
        默认强制重新生成记录报告（force_regenerate=True），确保使用最新的提示词逻辑。
        
        注意：此方法只更新现有记录，不创建新记录。调用方应确保在调用前已创建 session_reports 记录。
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

            # 保存到数据库 - 只更新现有记录，不创建新记录
            report = db.query(SessionReportDB).filter(
                SessionReportDB.user_id == user_id,
                SessionReportDB.session_id == session_id
            ).order_by(SessionReportDB.updated_at.desc(), SessionReportDB.id.desc()).first()

            if report:
                report.record_report_json = record_data
                db.commit()
                print(f"DEBUG: 已更新现有报告记录，ID: {report.id}")
            else:
                # 如果没有现有记录，记录警告但不创建新记录
                # 调用方应确保在调用前已创建记录
                print(f"WARNING: 未找到现有报告记录，跳过保存。用户ID: {user_id}, 会话ID: {session_id}")
                print(f"WARNING: 请确保在调用 finalize_record_report 前已创建 session_reports 记录")
                return record_data  # 返回生成的数据，但不保存到数据库

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

                    # 更新数据库 - 只更新现有记录
                    report = db.query(SessionReportDB).filter(
                        SessionReportDB.user_id == user_id,
                        SessionReportDB.session_id == session_id
                    ).order_by(SessionReportDB.updated_at.desc(), SessionReportDB.id.desc()).first()
                    if report:
                        report.record_report_json = record_data
                        db.commit()
                        print(f"DEBUG: 已更新报告记录的 duration 和 context，ID: {report.id}")
                    else:
                        print(f"WARNING: 补充 duration/context 时未找到现有报告记录")
                except Exception as e:
                    print(f"补充duration和context失败: {e}")

            # 清理缓冲区
            if session_id in self.session_dialogue_buffer:
                del self.session_dialogue_buffer[session_id]
            
            # 存储 primary_emotion 和 dominant_thinking_trap 到 chat_sessions 表
            from backend.core.database import ChatSessionDB
            from datetime import datetime
            chat_session = db.query(ChatSessionDB).filter(
                ChatSessionDB.session_id == session_id,
                ChatSessionDB.user_id == user_id
            ).first()
            
            if chat_session:
                # 提取 primary_emotion 和 dominant_thinking_trap
                primary_emotion = record_data.get("primary_emotion", "")
                dominant_thinking_trap = record_data.get("dominant_thinking_trap", "")
                
                # 存储到 chat_sessions 表
                chat_session.thinking_traps = dominant_thinking_trap if dominant_thinking_trap else None
                chat_session.emotional_response = primary_emotion if primary_emotion else None
                chat_session.status = 'ended'  # 设置状态为结束
                chat_session.updated_at = datetime.now()
                db.commit()
                print(f"DEBUG: 已存储 primary_emotion={primary_emotion} 和 dominant_thinking_trap={dominant_thinking_trap} 到 chat_sessions 表")
                print(f"DEBUG: 已将会话状态设置为 ended: {session_id}")
            else:
                print(f"WARNING: 未找到会话记录，无法存储数据: {session_id}")
            
            # 返回报告数据和报告ID（如果有）
            report_id = report.id if report else None
            return {"record_data": record_data, "report_id": report_id}

        except Exception as e:
            print(f"最终确定记录报告失败: {e}")
            import traceback
            traceback.print_exc()
            return {}
        finally:
            db.close()