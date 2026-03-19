import asyncio
import json
from backend.agents.analyst_agent import AnalystAgent

async def test_analyst_agent():
    """测试分析师智能体"""
    print("=== 测试分析师智能体 ===\n")
    
    agent = AnalystAgent()
    
    # 测试数据：使用一个假设已存在的记录ID
    # 您需要先通过记录师测试生成一个真实的record_id，或确保数据库中有测试数据
    test_record_id = "rec_07dad292"  # 请替换为真实存在的记录ID
    
    print(f"开始分析记录: {test_record_id}")
    
    input_data = {
        "record_id": test_record_id
    }
    
    result = await agent.execute(input_data)
    
    print(f"分析状态: {result.get('status')}")
    print(f"处理时间: {result.get('processing_time', 0):.3f}秒")
    
    if result.get("status") == "success":
        print(f"\n✅ 分析成功!")
        print(f"生成的报告ID: {result.get('report_id')}")
        print(f"置信度: {result.get('analysis_summary', {}).get('confidence_score', 0):.2%}")
        
        # 打印诊断预览
        preview = result.get('diagnosis_preview', {})
        print(f"\n📋 CBT分析摘要: {preview.get('cbt_summary', '')}")
        print(f"📋 中医情志摘要: {preview.get('tcm_summary', '')}")
        
        # 获取性能指标
        metrics = agent.get_performance_metrics()
        print(f"\n📊 智能体性能: 已完成{metrics['total_analyses']}次分析，平均耗时{metrics['average_time_seconds']:.3f}秒")
        
    else:
        print(f"\n❌ 分析失败: {result.get('error', '未知错误')}")
    
    # 打印完整结果（用于调试）
    print(f"\n完整响应结果:")
    print(json.dumps(result, indent=2, ensure_ascii=False, default=str))

if __name__ == "__main__":
    asyncio.run(test_analyst_agent())