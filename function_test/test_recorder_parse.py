import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.agents.recorder_agent import RecorderAgent
from backend.core.llm_service import LLMService

async def test_recorder_llm_parse():
    """测试RecorderAgent的LLM响应解析"""
    print("开始测试RecorderAgent的LLM响应解析...")
    
    # 创建LLM服务实例
    llm_service = LLMService()
    
    # 创建RecorderAgent实例
    recorder_agent = RecorderAgent(llm_service=llm_service)
    
    # 测试用户输入
    user_input = "最近工作压力很大，总觉得什么都做不好，领导一定对我很失望"
    session_id = "test_session_001"
    
    try:
        # 模拟构建对话上下文
        conversation_context = await recorder_agent._build_conversation_context(session_id)
        
        # 调用LLM获取原始响应
        raw_response = await recorder_agent._call_llm_with_structured_output(
            conversation_context, user_input, session_id
        )
        
        print(f"\n=== 原始LLM响应 ===")
        print(raw_response)
        
        # 测试解析响应
        structured_data, text_response = recorder_agent._parse_llm_response(raw_response)
        
        print(f"\n=== 解析结果 ===")
        print(f"结构化数据: {structured_data}")
        print(f"文本响应: {text_response}")
        
        return True
        
    except Exception as e:
        print(f"\n测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    asyncio.run(test_recorder_llm_parse())