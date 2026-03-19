import sys
import os
# 添加项目根目录到Python路径，确保导入正常
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.core.rule_engine import RuleEngine

def test_rule_engine():
    print("=== 测试规则引擎 (RuleEngine) ===\n")
    engine = RuleEngine()
    
    # 测试1: CBT分析
    print("\n1. 测试CBT分析：")
    test_thoughts = ["我能力不足，什么都做不好", "领导肯定对我很失望", "我永远都无法完成这个项目"]
    cbt_results = engine.analyze_cbt_patterns(test_thoughts)
    print(f"   输入自动思维：{test_thoughts}")          
    print(f"   分析结果：{cbt_results}")
    print(f"   是否检测到扭曲：{len(cbt_results) > 0}")
    
    # 测试2: 中医 psychos分析
    print("\n2. 测试中医 psychos分析：")
    test_emotions = [{"type": "忧", "intensity": 8}, {"type": "思", "intensity": 7}, {"type": "恐", "intensity": 6}]
    tcm_results = engine.analyze_tcm_patterns(test_emotions)
    print(f"   输入情绪：{test_emotions}")
    print(f"   分析结果：{tcm_results}")
    dominant = tcm_results.get('dominant_emotion')
    if dominant:
        print(f"   主导 psychos：{dominant.get('type')}， 强度：{dominant.get('intensity')}")
        print(f"   影响脏腑：{dominant.get('affected_zang', 'N/A')}")
    else:
        print("   ❌ 未识别出主导 psychos")
        
    # 测试3: 综合框架生成
    print("\n3. 测试综合干预框架生成：")
    framework = engine.generate_intervention_framework(cbt_results, tcm_results)
    print(f"   生成的框架：{framework}")

if __name__ == "__main__":
    test_rule_engine()