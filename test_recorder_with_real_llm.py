# 在你的主程序或路由中
from backend.core.llm_service import LLMService
from backend.agents.recorder_agent import RecorderAgent
import asyncio
import json

async def test_recorder_with_real_llm():
    # 1. 创建LLM服务实例，使用.env文件中的配置
    llm_service = LLMService() 
    
    # 2. 创建记录师智能体，并注入LLM服务
    recorder_agent = RecorderAgent(llm_service=llm_service)
    
    # 3. 模拟用户输入
    test_input = {
        "session_id": "test_session_001",
        "user_input": "我今天的项目汇报搞砸了，感觉同事都在看我笑话，我真是什么都做不好。",
        "is_new_session": True
    }
    
    # 4. 执行！
    async with llm_service:  # 使用异步上下文管理器管理会话
        result = await recorder_agent.execute(test_input)
        print(json.dumps(result, indent=2, ensure_ascii=False))

# 运行测试
if __name__ == "__main__":
    asyncio.run(test_recorder_with_real_llm())