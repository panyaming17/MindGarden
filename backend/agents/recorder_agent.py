import joblib
import os
from sentence_transformers import SentenceTransformer
from backend.agents.base_agent import BaseAgent
from backend.repositories.record_repository_new import RecordRepository
from backend.core.llm_service import LLMService
from typing import Optional, Tuple, Dict, Any

class RecorderAgent(BaseAgent):
    """记录师智能体 - 负责情绪信息收集与结构化"""

    def __init__(self, agent_name: str = "recorder_agent", llm_service: Optional[LLMService] = None):
        super().__init__(agent_name)
        self.repository = RecordRepository()
        self.llm_service = llm_service
        self._init_prompts()
        self.active_sessions = {}

        # 加载情绪预测模型（建议在实例化时加载，避免重复加载）
        self.encoder = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
        # 修正模型加载路径 - 使用绝对路径
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # 从 agents 目录向上两级到项目根目录，再进入 backend/checkpoints/models
        model_dir = os.path.join(current_dir, "..", "..", "backend", "checkpoints", "models")
        model_dir = os.path.abspath(model_dir)
        
        self.intensity_model = joblib.load(os.path.join(model_dir, "latest_intensity_model.pkl"))
        self.hedonic_model = joblib.load(os.path.join(model_dir, "latest_hedonic_model.pkl"))
        self.tension_model = joblib.load(os.path.join(model_dir, "latest_tension_model.pkl"))
        self.complexity_model = joblib.load(os.path.join(model_dir, "latest_complexity_model.pkl"))   
        self.le_hedonic = joblib.load(os.path.join(model_dir, "le_hedonic.pkl"))
        self.le_tension = joblib.load(os.path.join(model_dir, "le_tension.pkl"))
        self.le_complexity = joblib.load(os.path.join(model_dir, "le_complexity.pkl"))

    def _init_prompts(self):
        self.system_prompt = """你是一个高效的语义筛选助手。你的任务是判断用户输入是否包含需要专业心理咨询师关注的内容。请仅回答“是”或“否”，不要输出其他任何内容。
        请判断以下用户发言是否包含：
        1) 对自我、他人或未来的负面评价、担忧、恐惧、自责等（例如“我太差了”、“他肯定讨厌我”）。
        2) 具体的事件或行为描述（例如“昨天和同事吵架了”、“最近总失眠”）。
        3) 情绪表达（愤怒、悲伤、焦虑等）或身体症状（胸闷、手抖等）。
        只回答“是”或“否”。
        发言：{text}"""

    def predict_four_dim(self, text: str) -> Dict[str, Any]:
        """调用四维模型预测"""
        emb = self.encoder.encode([text])
        intensity = float(self.intensity_model.predict(emb)[0])
        hedonic = self.le_hedonic.inverse_transform(self.hedonic_model.predict(emb))[0]
        tension = self.le_tension.inverse_transform(self.tension_model.predict(emb))[0]
        complexity = self.le_complexity.inverse_transform(self.complexity_model.predict(emb))[0]
        return {
            "intensity": round(intensity, 2),
            "hedonic": hedonic,
            "tension": tension,
            "complexity": complexity
        }

    def quick_screen(self, text: str, use_llm: bool = True) -> Tuple[bool, Dict[str, Any]]:
        """快速筛选，返回 (是否有价值, 四维结果)"""
        dim = self.predict_four_dim(text)
        # 基于四维模型的阈值判断
        if dim["intensity"] >= 4 or dim["tension"] == "高" or dim["complexity"] == "复杂":
            return True, dim

        # 需要时再用轻量LLM判断自动化思维等
        if use_llm and self.llm_service:
            try:
                prompt = self.system_prompt.format(text=text)
                # 假设 LLMService 有 chat_completion 方法，返回包含 message.content 的对象
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
                # 记录日志
                print(f"LLM 筛选失败: {e}")
                pass
        return False, dim

    def save_dialogue(self, user_id: str, content: str, role: str, four_dim: dict, is_valuable: bool):
        """存储对话到数据库（示例方法，需根据你的实际 repository 实现）"""
        # 这里假设 repository 有一个 create_dialogue 方法
        self.repository.create_dialogue(
            user_id=user_id,
            role=role,
            content=content,
            four_dim_intensity=four_dim.get("intensity"),
            four_dim_hedonic=four_dim.get("hedonic"),
            four_dim_tension=four_dim.get("tension"),
            four_dim_complexity=four_dim.get("complexity"),
            is_valuable=is_valuable
        )

    def recorder_process(self, user_input: str, user_id: str) -> Dict[str, Any]:
        """处理用户输入的入口方法"""
        is_valuable, dim = self.quick_screen(user_input)
        # 存储用户消息
        self.save_dialogue(user_id, user_input, "user", dim, is_valuable)
        return {
            "user_id": user_id,
            "input": user_input,
            "four_dim": dim,
            "is_valuable": is_valuable
        }

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行智能体任务的方法"""
        user_input = input_data.get("user_input", "")
        user_id = input_data.get("user_id", "")
        
        if not user_input or not user_id:
            return {
                "status": "error",
                "message": "缺少必要的输入参数"
            }
        
        try:
            result = self.recorder_process(user_input, user_id)
            return {
                "status": "success",
                "data": result
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"处理失败: {str(e)}"
            }