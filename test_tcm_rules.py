#!/usr/bin/env python3
"""
测试中医情志规则库结构
"""

from backend.core.rule_engine import RuleEngine
from backend.core.data_models import EmotionItem

# 创建规则引擎实例
rule_engine = RuleEngine()

def test_tcm_rules():
    """测试中医情志规则"""
    print("测试中医情志规则库结构...")
    
    # 测试数据：愤怒情绪
    test_emotions = [
        {"type": "怒", "intensity": 8, "duration": 30}
    ]
    
    # 分析中医情志模式
    result = rule_engine.analyze_tcm_patterns(test_emotions)
    print("\n中医情志分析结果：")
    print(f"主导情绪: {result['dominant_emotion']}")
    print(f"情志关系: {result['tcm_relationships']}")
    print(f"推荐干预: {result['recommended_interventions']}")
    print(f"关键词: {result['keywords']}")
    
    # 测试生成干预框架
    cbt_results = []  # 模拟空的CBT结果
    framework = rule_engine.generate_intervention_framework(cbt_results, result)
    print(f"\n综合干预框架: {framework}")
    
    # 测试其他情绪
    test_emotions_2 = [
        {"type": "忧", "intensity": 7, "duration": 20}
    ]
    
    result_2 = rule_engine.analyze_tcm_patterns(test_emotions_2)
    print("\n\n测试忧虑情绪：")
    print(f"主导情绪: {result_2['dominant_emotion']}")
    print(f"推荐干预: {result_2['recommended_interventions']}")

if __name__ == "__main__":
    test_tcm_rules()
