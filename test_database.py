import asyncio
from backend.repositories.record_repository import RecordRepository
from backend.core.data_models import StructuredRecord, DiagnosisReport
from datetime import datetime
import json

async def test_database_connection():
    """测试数据库连接和基本操作"""
    print("正在测试数据库连接...")
    
    # 创建存储库实例
    repo = RecordRepository()
    
    try:
        # 测试1: 获取记录（应该返回测试数据）
        print("\n测试1: 获取记录")
        record = await repo.get_record_by_id("rec_123")
        if record:
            print(f"✅ 获取记录成功: {record.record_id}")
            print(f"   用户ID: {record.user_id}")
            print(f"   原始文本: {record.raw_text[:50]}...")
        else:
            print("❌ 获取记录失败")
        
        # 测试2: 保存新记录
        print("\n测试2: 保存新记录")
        # 使用唯一ID避免主键冲突
        import uuid
        unique_record_id = f"rec_test_{uuid.uuid4().hex[:8]}"
        new_record = StructuredRecord(
            record_id=unique_record_id,
            user_id="user_test_001",
            raw_text="测试记录：今天感觉很开心！",
            situation="测试情境",
            automatic_thoughts=["我今天做得很好", "我很有能力"],
            emotions=[{"type": "喜", "intensity": 9}],
            physical_sensations=["轻松", "愉悦"],
            created_at=datetime.now()
        )
        
        saved_id = await repo.save_record(new_record)
        print(f"✅ 保存记录成功: {saved_id}")
        
        # 测试3: 获取刚刚保存的记录
        print("\n测试3: 获取刚刚保存的记录")
        retrieved_record = await repo.get_record_by_id(unique_record_id)
        if retrieved_record:
            print(f"✅ 获取记录成功: {retrieved_record.record_id}")
            print(f"   用户ID: {retrieved_record.user_id}")
            print(f"   情境: {retrieved_record.situation}")
            print(f"   情绪: {retrieved_record.emotions}")
        else:
            print("❌ 获取记录失败")
        
        # 测试4: 保存诊断报告
        print("\n测试4: 保存诊断报告")
        unique_report_id = f"report_test_{uuid.uuid4().hex[:8]}"
        report = DiagnosisReport(
            id=unique_report_id,
            record_id=unique_record_id,
            user_id="user_test_001",
            cbt_analysis={"distortions": ["全或无思维"], "cognitive_restructuring": "建议更灵活地看待问题"},
            tcm_analysis={"dominant_emotion": "喜", "imbalance": "无明显失衡"},
            summary="这是一个测试诊断报告",
            recommendations=["保持积极心态", "继续努力"],
            confidence_score=0.95,
            analysis_time=1.5,
            created_at=datetime.now()
        )
        
        saved_report_id = await repo.save_diagnosis_report(report)
        print(f"✅ 保存报告成功: {saved_report_id}")
        
        # 测试5: 获取刚刚保存的报告
        print("\n测试5: 获取刚刚保存的报告")
        retrieved_report = await repo.get_report_by_id(unique_report_id)
        if retrieved_report:
            print(f"✅ 获取报告成功: {retrieved_report.id}")
            print(f"   记录ID: {retrieved_report.record_id}")
            print(f"   置信度: {retrieved_report.confidence_score}")
            print(f"   CBT分析: {retrieved_report.cbt_analysis}")
        else:
            print("❌ 获取报告失败")
        
        # 测试6: 获取用户的所有报告
        print("\n测试6: 获取用户的所有报告")
        user_reports = await repo.get_reports_by_user_id("user_test_001")
        if user_reports:
            print(f"✅ 获取用户报告成功，共 {len(user_reports)} 份报告")
            for r in user_reports:
                print(f"   - 报告ID: {r.id}, 创建时间: {r.created_at}")
        else:
            print("❌ 获取用户报告失败或没有报告")
        
        print("\n🎉 所有测试完成！")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        # 清理资源
        del repo

if __name__ == "__main__":
    asyncio.run(test_database_connection())