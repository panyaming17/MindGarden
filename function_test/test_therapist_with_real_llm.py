import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.agents.therapist_agent import TherapistAgent
from backend.core.data_models import DiagnosisReport
from backend.core.llm_service import LLMService

async def test_therapist_llm_call():
    """测试TherapistAgent的真实LLM调用"""
    print("开始测试TherapistAgent的真实LLM调用...")
    
    # 创建LLM服务实例
    llm_service = LLMService()
    
    # 创建TherapistAgent实例
    therapist_agent = TherapistAgent(llm_service=llm_service)
    
    # 创建模拟的DiagnosisReport
    mock_report = DiagnosisReport(
        report_id="test_report_001",
        user_id="test_user_001",
        record_id="test_record_001",
        cbt_diagnosis={
            "cognitive_distortions": ["全或无思维", "过度概括"],
            "severity": "轻度",
            "emotional_state": "焦虑",
            "cbt_recommendations": ["认知重构", "行为激活"]
        },
        tcm_diagnosis={
            "syndrome_pattern": "肝郁气滞",
            "five_elements_imbalance": "木克土",
            "tcm_recommendations": ["情志疏导", "肝气调养"]
        },
        holistic_analysis={
            "key_triggers": ["工作压力", "人际关系"],
            "mental_patterns": ["负面思维循环"],
            "physical_manifestations": ["失眠", "头痛"]
        },
        overall_recommendation="综合CBT和中医方法进行调理",
        created_at="2023-07-15T14:30:00Z"
    )
    
    # 模拟关键见解
    key_insights = {
        "emotional_triggers": ["工作压力", "截止日期"],
        "core_distortions": ["全或无思维"],
        "tcm_syndrome": "肝郁气滞",
        "recommended_approaches": ["认知重构", "情志疏导"]
    }
    
    # 模拟策略框架
    strategy_framework = {
        "cbt_strategies": ["认知重构", "思维记录"],
        "tcm_strategies": ["情志相胜", "五行音乐"],
        "integrated_plan": "先用认知重构调整思维模式，再用情志相胜法缓解情绪"
    }
    
    try:
        # 调用生成疏导方案的方法
        therapy_plan = await therapist_agent._generate_therapy_plan(
            mock_report, strategy_framework, key_insights
        )
        
        print("\n=== 测试结果 ===")
        print(f"疏导方案生成成功！")
        print(f"\n生成的疏导方案内容：")
        print(therapy_plan)
        print(f"\n方案长度：{len(therapy_plan)} 字符")
        
        return True
        
    except Exception as e:
        print(f"\n测试失败：{str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    asyncio.run(test_therapist_llm_call())