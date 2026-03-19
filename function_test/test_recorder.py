import asyncio
import json
# 从正确的模块导入 RecorderAgent
from backend.agents.recorder_agent import RecorderAgent

async def test_recorder_agent():
    """测试记录师智能体的完整工作流程"""
    print("=== 测试记录师智能体 (模拟多轮对话) ===\n")
    
    # 1. 实例化智能体
    agent = RecorderAgent()
    print(f"智能体 '{agent.agent_name}' 初始化成功。\n")
    
    # 2. 模拟一个更自然的对话流程（用户逐步提供信息）
    test_conversation = [
        "最近工作压力很大，总觉得什么都做不好",  # 初始倾诉
        "嗯，昨天我负责的项目报告被领导批评了",  # 提供具体情境
        "我觉得自己能力不足，可能不适合这个岗位",  # 表达核心想法
        "身体上就是经常头痛，晚上也睡不好"         # 补充生理感受
    ]
    
    session_id = None
    
    print("开始模拟对话...")
    print("-" * 60)
    
    for i, user_input in enumerate(test_conversation):
        print(f"[轮次 {i+1}] 用户说：{user_input}")
        
        # 3. 准备输入数据
        input_data = {
            "session_id": session_id,
            "user_input": user_input,
            "is_new_session": (i == 0)  # 第一轮是新会话
        }
        
        # 4. 调用记录师智能体
        result = await agent.execute(input_data)
        
        # 5. 更新会话ID（保持同一会话）
        session_id = result.get("session_id")
        
        # 6. 打印记录师的回应摘要
        llm_response = result.get('llm_response', '')
        # 只打印前150个字符，避免输出过长
        response_preview = (llm_response[:150] + '...') if len(llm_response) > 150 else llm_response
        print(f"       记录师回应：{response_preview}")
        
        # 7. 打印处理状态
        print(f"       状态：{result.get('message')} | 下一步：{result.get('next_action')}")
        
        # 8. 如果本轮成功提取并保存了结构化记录，则展示结果
        if result.get("record_id"):
            print("-" * 60)
            print(f"🎉 记录完成！\n   记录ID：{result['record_id']}")
            print(f"   会话ID：{session_id}")
            
            # 结构化数据
            structured_data = result.get('structured_data')
            if structured_data:
                print("\n📊 提取的结构化数据摘要：")
                print(f"   情境：{structured_data.get('situation', '')[:50]}...")
                print(f"   自动思维数量：{len(structured_data.get('automatic_thoughts', []))}")
                print(f"   识别到的情绪：{[e.get('type') for e in structured_data.get('emotions', [])]}")
            
            # 可以选择将完整数据写入文件以便查看
            with open(f"test_record_{session_id}.json", 'w', encoding='utf-8') as f:
                json.dump({
                    "session_id": session_id,
                    "record_id": result['record_id'],
                    "full_response": result,
                    "structured_data": structured_data
                }, f, indent=2, ensure_ascii=False, default=str)
            print(f"   完整测试数据已保存至：test_record_{session_id}.json")
            break  # 记录已完成，退出测试循环
        
        print("-" * 60)
        await asyncio.sleep(0.8)  # 稍微增加等待时间，模拟更真实的交互间隔
    
    # 9. 如果所有轮次结束仍未生成记录（理论上不应发生，取决于模拟响应）
    if not result.get("record_id"):
        print("\n⚠️  测试结束，但未触发记录完成。")
        print("可能原因：模拟对话未包含足够关键词，或未达到信息收集阈值。")
        print(f"最后状态：{result.get('message')}")
        
    print(f"\n测试脚本执行完毕。")

if __name__ == "__main__":
    # 运行测试
    asyncio.run(test_recorder_agent())