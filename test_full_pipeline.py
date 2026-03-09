import asyncio
import json
from backend.agents.recorder_agent import RecorderAgent
from backend.agents.analyst_agent import AnalystAgent
from backend.agents.therapist_agent import TherapistAgent

async def test_full_pipeline():
    """测试完整的三智能体流水线：记录 -> 分析 -> 调理"""
    print("=== 测试完整智能体流水线 ===\n")
    
    # 1. 记录师：收集信息
    print("1. 🎤 记录师工作...")
    recorder = RecorderAgent()
    # 提供更完整的用户输入，包含具体情境、想法和情绪
    record_result = await recorder.execute({
        "user_input": "昨天下午领导找我谈话，说我的项目进度慢，然后我就觉得自己什么都做不好，领导一定对我很失望，胸口也有点闷，晚上还失眠了",
        "is_new_session": True
    })
    
    if not record_result.get("success"):
        print(f"❌ 记录失败: {record_result.get('message')}")
        return
    
    record_id = record_result.get("record_id")
    print(f"✅ 记录完成，ID: {record_id}")
    
    # 2. 分析师：专业分析
    print(f"\n2. 🔍 分析师工作 (分析记录 {record_id})...")
    analyst = AnalystAgent()
    analysis_result = await analyst.execute({"record_id": record_id})
    
    if analysis_result.get("status") != "success":
        print(f"❌ 分析失败: {analysis_result.get('error')}")
        return
    
    report_id = analysis_result.get("report_id")
    print(f"✅ 分析完成，报告ID: {report_id}")
    print(f"   主导情绪: {analysis_result.get('analysis_summary', {}).get('dominant_emotion')}")
    print(f"   置信度: {analysis_result.get('analysis_summary', {}).get('confidence_score', 0):.0%}")
    
    # 3. 调理师：生成疏导方案
    print(f"\n3. 💝 调理师工作 (基于报告 {report_id})...")
    therapist = TherapistAgent()
    therapy_result = await therapist.execute({"report_id": report_id})
    
    if therapy_result.get("status") != "success":
        print(f"❌ 调理方案生成失败: {therapy_result.get('error')}")
        return
    
    therapy_plan = therapy_result.get("therapy_plan", "")
    print(f"✅ 疏导方案生成成功 (长度: {len(therapy_plan)} 字符)")
    
    # 打印方案预览
    print(f"\n📄 疏导方案预览:")
    print("-" * 60)
    # 只打印前500个字符作为预览
    preview = therapy_plan[:500] + "..." if len(therapy_plan) > 500 else therapy_plan
    print(preview)
    print("-" * 60)
    
    # 4. 保存完整流水线结果
    pipeline_data = {
        "record_id": record_id,
        "report_id": report_id,
        "record_data": record_result.get("structured_data"),
        "analysis_summary": analysis_result,
        "therapy_plan": therapy_plan,
        "therapist_summary": therapy_result.get("therapist_summary"),
        "pipeline_timestamp": asyncio.get_event_loop().time()
    }
    
    filename = f"full_pipeline_{record_id}.json"
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(pipeline_data, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"\n💾 完整流水线数据已保存至: {filename}")
    print("\n🎉 三智能体流水线测试完成！")

if __name__ == "__main__":
    asyncio.run(test_full_pipeline())