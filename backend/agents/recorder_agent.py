# recorder_agent.py
import joblib
import os
from sentence_transformers import SentenceTransformer
from backend.agents.base_agent import BaseAgent
from backend.repositories.record_repository_new import RecordRepository
from backend.core.llm_service import LLMService
from typing import Optional, Tuple, Dict, Any
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

        # 加载模型（如果尚未加载）
        if not RecorderAgent._models_loaded:
            self._load_models()
            RecorderAgent._models_loaded = True

    def _load_models(self):
        """加载模型（只执行一次）"""
        try:
            print("开始加载模型...")
            RecorderAgent._encoder = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
            current_dir = os.path.dirname(os.path.abspath(__file__))
            model_dir = os.path.join(current_dir, "..", "checkpoints", "models")
            model_dir = os.path.abspath(model_dir)
            print(f"模型目录: {model_dir}")
            RecorderAgent._intensity_model = joblib.load(os.path.join(model_dir, "latest_intensity_model.pkl"))
            RecorderAgent._hedonic_model = joblib.load(os.path.join(model_dir, "latest_hedonic_model.pkl"))
            RecorderAgent._tension_model = joblib.load(os.path.join(model_dir, "latest_tension_model.pkl"))
            RecorderAgent._complexity_model = joblib.load(os.path.join(model_dir, "latest_complexity_model.pkl"))
            RecorderAgent._le_hedonic = joblib.load(os.path.join(model_dir, "le_hedonic.pkl"))
            RecorderAgent._le_tension = joblib.load(os.path.join(model_dir, "le_tension.pkl"))
            RecorderAgent._le_complexity = joblib.load(os.path.join(model_dir, "le_complexity.pkl"))
            print("模型加载成功")
        except Exception as e:
            print(f"模型加载失败: {e}")
            import traceback
            traceback.print_exc()
            # 如果加载失败，抛出异常，让上层知道
            raise

    def predict_four_dim(self, text: str) -> Dict[str, Any]:
        """调用四维模型预测"""
        # 调试：打印加载状态
        print(f"预测时 _models_loaded = {RecorderAgent._models_loaded}")
        if not RecorderAgent._models_loaded:
            print("模型未加载，使用规则后备")
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
            print(f"❌ 预测失败: {e}")
            import traceback
            traceback.print_exc()
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