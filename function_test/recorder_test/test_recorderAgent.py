import unittest
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from unittest.mock import MagicMock, patch
from backend.agents.recorder_agent import RecorderAgent
from backend.core.llm_service import LLMService

class TestRecorderAgent(unittest.TestCase):
    def setUp(self):
        # 模拟 LLMService
        self.mock_llm = MagicMock(spec=LLMService)
        # 模拟 RecordRepository
        with patch('backend.agents.recorder_agent.RecordRepository') as MockRepo:
            self.mock_repo = MockRepo.return_value
            self.agent = RecorderAgent(llm_service=self.mock_llm)

    def test_predict_four_dim(self):
        """测试四维预测（需要真实模型文件，这里只做调用测试）"""
        text = "我明天要答辩，紧张得睡不着觉。"
        result = self.agent.predict_four_dim(text)
        self.assertIn("intensity", result)
        self.assertIn("hedonic", result)
        self.assertIn("tension", result)
        self.assertIn("complexity", result)
        print("四维预测结果:", result)

    def test_quick_screen_with_llm(self):
        """测试快速筛选功能，验证返回值格式"""
        # 测试快速筛选功能，确保能正常执行
        text = "我觉得自己一无是处。"
        is_valuable, dim = self.agent.quick_screen(text, use_llm=True)
        # 验证返回值格式正确
        self.assertIsInstance(is_valuable, bool)
        self.assertIsInstance(dim, dict)
        self.assertIn("intensity", dim)
        self.assertIn("hedonic", dim)
        self.assertIn("tension", dim)
        self.assertIn("complexity", dim)

    def test_quick_screen_by_model_only(self):
        """仅用四维模型判断，不应触发LLM"""
        # 测试快速筛选功能，确保能正常执行
        text = "今天天气不错。"
        is_valuable, dim = self.agent.quick_screen(text, use_llm=False)
        # 验证返回值格式正确
        self.assertIsInstance(is_valuable, bool)
        self.assertIsInstance(dim, dict)
        self.assertIn("intensity", dim)
        self.assertIn("hedonic", dim)
        self.assertIn("tension", dim)
        self.assertIn("complexity", dim)
        # 确保没有调用LLM
        self.mock_llm.chat_completion.assert_not_called()

    def test_recorder_process(self):
        """测试完整流程"""
        user_id = "test_user"
        user_input = "我最近总是失眠，心里很烦躁。"

        # 模拟 quick_screen 返回 True
        with patch.object(self.agent, 'quick_screen', return_value=(True, {"intensity":6, "hedonic":"负性", "tension":"中", "complexity":"简单"})):
            result = self.agent.recorder_process(user_input, user_id)

        self.assertEqual(result["user_id"], user_id)
        self.assertEqual(result["input"], user_input)
        self.assertTrue(result["is_valuable"])
        # 验证 save_dialogue 被调用
        self.mock_repo.create_dialogue.assert_called_once()

if __name__ == "__main__":
    unittest.main()