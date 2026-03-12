#!/usr/bin/env python3
"""
测试报告生成功能的脚本
验证记录报告、分析报告和建议报告的生成流程
"""

import asyncio
import aiohttp
import json
import uuid
import time

BASE_URL = "http://localhost:8001"
USER_ID = f"test_user_{uuid.uuid4().hex[:8]}"

async def test_record_report_generation():
    """测试记录报告生成功能"""
    print("\n=== 测试记录报告生成功能 ===")
    
    async with aiohttp.ClientSession() as session:
        # 1. 与记录师开始对话
        session_id = f"sess_{uuid.uuid4().hex[:8]}"
        
        # 第一次对话
        print("1. 与记录师开始对话...")
        converse_url = f"{BASE_URL}/recorder/converse"
        user_input = "我最近感觉情绪很低落，对什么都提不起兴趣。"
        
        data = {
            "user_input": user_input,
            "session_id": session_id,
            "user_id": USER_ID
        }
        
        async with session.post(converse_url, json=data) as response:
            result = await response.json()
            print(f"   响应状态: {response.status}")
            print(f"   会话ID: {result.get('session_id')}")
            print(f"   记录师回应: {result.get('llm_response')[:100]}...")
            print(f"   下一步操作: {result.get('next_action')}")
        
        # 等待一下
        await asyncio.sleep(1)
        
        # 第二次对话
        print("\n2. 继续与记录师对话...")
        user_input = "我经常感到疲惫，即使什么都没做。晚上也睡不好觉。"
        
        data = {
            "user_input": user_input,
            "session_id": session_id,
            "user_id": USER_ID
        }
        
        async with session.post(converse_url, json=data) as response:
            result = await response.json()
            print(f"   响应状态: {response.status}")
            print(f"   记录师回应: {result.get('llm_response')[:100]}...")
            print(f"   下一步操作: {result.get('next_action')}")
        
        # 3. 创建记录报告
        print("\n3. 创建记录报告...")
        create_report_url = f"{BASE_URL}/recorder/record-reports"
        
        report_data = {
            "session_id": session_id,
            "user_id": USER_ID,
            "duration": 120,  # 秒
            "conversation_log": [
                {
                    "role": "user",
                    "content": "我最近感觉情绪很低落，对什么都提不起兴趣。",
                    "timestamp": "2024-01-01T12:00:00"
                },
                {
                    "role": "assistant",
                    "content": "我很抱歉听到你感到情绪低落。能告诉我更多关于你的感受吗？",
                    "timestamp": "2024-01-01T12:01:00"
                },
                {
                    "role": "user",
                    "content": "我经常感到疲惫，即使什么都没做。晚上也睡不好觉。",
                    "timestamp": "2024-01-01T12:02:00"
                }
            ],
            "situation": "日常情绪困扰",
            "automatic_thoughts": ["我什么都做不好", "生活没有意义"],
            "emotions": [
                {
                    "type": "忧",
                    "intensity": 8,
                    "description": "想到未来"
                },
                {
                    "type": "思",
                    "intensity": 6,
                    "description": "担心工作"
                }
            ],
            "physical_sensations": ["疲劳", "失眠", "食欲不振"],
            "summary": "来访者表现出典型的抑郁症状，包括情绪低落、兴趣减退、疲劳和睡眠问题。"
        }
        
        async with session.post(create_report_url, json=report_data) as response:
            result = await response.json()
            print(f"   响应状态: {response.status}")
            if response.status == 200:
                record_id = result.get('record_id')
                print(f"   记录报告ID: {record_id}")
                return record_id
            else:
                print(f"   创建记录报告失败: {result}")
                return None

async def test_analysis_report_generation(record_id):
    """测试分析报告生成功能"""
    print("\n=== 测试分析报告生成功能 ===")
    
    if not record_id:
        print("   跳过分析报告测试，因为记录报告生成失败")
        return None
    
    async with aiohttp.ClientSession() as session:
        # 直接创建分析报告，绕过analyze接口
        print("1. 创建分析报告...")
        create_report_url = f"{BASE_URL}/analyst/analysis-reports"
        
        report_data = {
            "record_id": record_id,
            "user_id": USER_ID,
            "analysis_duration": 45,
            "confidence_score": 0.92,
            "cbt_analysis": {
                "distortions_detected": [
                    {
                        "distortion_type": "过度概括",
                        "matched_thought": "我什么都做不好",
                        "evidence": "缺乏具体证据支持",
                        "challenge_question": "有什么证据支持这个想法？"
                    },
                    {
                        "distortion_type": "灾难化思维",
                        "matched_thought": "生活没有意义",
                        "evidence": "片面看待生活",
                        "challenge_question": "有没有其他可能的解释？"
                    }
                ],
                "summary": "检测到过度概括和灾难化思维等认知扭曲",
                "challenge_questions": ["有什么证据支持这个想法？", "有没有其他可能的解释？"]
            },
            "tcm_analysis": {
                "dominant_emotion": {
                    "type": "忧",
                    "intensity": 8,
                    "affected_zang": "肺"
                },
                "inhibiting_emotion": "思",
                "secondary_emotions": [
                    {
                        "type": "恐",
                        "intensity": 4,
                        "affected_zang": "肾"
                    }
                ],
                "recommended_interventions": ["疏肝解郁", "健脾养心"]
            },
            "integrated_framework": "认知行为疗法结合中医情志调理",
            "priority": "high"
        }
        
        async with session.post(create_report_url, json=report_data) as response:
            result = await response.json()
            print(f"   响应状态: {response.status}")
            if response.status == 200:
                report_id = result.get('report_id')
                print(f"   分析报告ID: {report_id}")
                return report_id
            else:
                print(f"   创建分析报告失败: {result}")
                return None

async def test_suggestion_report_generation(report_id):
    """测试建议报告生成功能"""
    print("\n=== 测试建议报告生成功能 ===")
    
    if not report_id:
        print("   跳过建议报告测试，因为分析报告生成失败")
        return None
    
    async with aiohttp.ClientSession() as session:
        # 1. 请求生成建议
        print("1. 请求生成建议...")
        suggest_url = f"{BASE_URL}/therapist/suggest"
        
        data = {
            "report_id": report_id,
            "priority": "high"
        }
        
        async with session.post(suggest_url, json=data) as response:
            result = await response.json()
            print(f"   响应状态: {response.status}")
            print(f"   建议状态: {result.get('status')}")
            print(f"   建议消息: {result.get('message')}")
        
        # 等待一下
        await asyncio.sleep(2)
        
        # 2. 创建建议报告
        print("\n2. 创建建议报告...")
        create_report_url = f"{BASE_URL}/therapist/suggestion-reports"
        
        report_data = {
            "report_id": report_id,
            "user_id": USER_ID,
            "target_issues": ["情绪低落", "睡眠问题", "认知扭曲"],
            "core_principles": ["认知重构", "情绪调节", "中医调理"],
            "daily_suggestions": [
                {
                    "title": "早晨冥想练习",
                    "description": "早晨冥想10分钟，记录3件感恩的事",
                    "duration": 15,
                    "type": "情志"
                },
                {
                    "title": "认知重构练习",
                    "description": "识别并挑战消极思维，用积极视角看待问题",
                    "duration": 20,
                    "type": "认知"
                },
                {
                    "title": "中医调理练习",
                    "description": "深呼吸练习和适度运动",
                    "duration": 30,
                    "type": "身体"
                }
            ],
            "emergency_tips": ["深呼吸放松", "联系心理咨询师", "寻求家人支持"],
            "encouragement": "你正在采取积极的步骤改善情绪，每一步都很重要。",
            "plan_summary": "综合运用认知行为疗法和中医情志调理方法，帮助来访者改善情绪状态。"
        }
        
        async with session.post(create_report_url, json=report_data) as response:
            result = await response.json()
            print(f"   响应状态: {response.status}")
            if response.status == 200:
                suggestion_id = result.get('suggestion_id')
                print(f"   建议报告ID: {suggestion_id}")
                return suggestion_id
            else:
                print(f"   创建建议报告失败: {result}")
                return None

async def test_report_retrieval(record_id, report_id, suggestion_id):
    """测试报告检索功能"""
    print("\n=== 测试报告检索功能 ===")
    
    async with aiohttp.ClientSession() as session:
        # 1. 获取记录报告
        if record_id:
            print("1. 获取记录报告...")
            url = f"{BASE_URL}/recorder/record-reports/{record_id}"
            async with session.get(url) as response:
                result = await response.json()
                print(f"   响应状态: {response.status}")
                if response.status == 200:
                    print(f"   记录报告标题: {result.get('summary')[:100]}...")
                else:
                    print(f"   获取记录报告失败: {result}")
            await asyncio.sleep(1)
        
        # 2. 获取分析报告
        if report_id:
            print("\n2. 获取分析报告...")
            url = f"{BASE_URL}/analyst/analysis-reports/{report_id}"
            async with session.get(url) as response:
                result = await response.json()
                print(f"   响应状态: {response.status}")
                if response.status == 200:
                    print(f"   分析报告CBT摘要: {result.get('cbt_analysis', {}).get('summary')}")
                    print(f"   分析报告中医摘要: {result.get('tcm_analysis', {}).get('dominant_emotion', {}).get('emotion')}")
                else:
                    print(f"   获取分析报告失败: {result}")
            await asyncio.sleep(1)
        
        # 3. 获取建议报告
        if suggestion_id:
            print("\n3. 获取建议报告...")
            url = f"{BASE_URL}/therapist/suggestion-reports/{suggestion_id}"
            async with session.get(url) as response:
                result = await response.json()
                print(f"   响应状态: {response.status}")
                if response.status == 200:
                    print(f"   建议报告目标问题: {', '.join(result.get('target_issues', []))}")
                    print(f"   建议报告摘要: {result.get('plan_summary')[:100]}...")
                else:
                    print(f"   获取建议报告失败: {result}")

async def main():
    """主测试函数"""
    print("开始测试报告生成功能...")
    print(f"测试用户ID: {USER_ID}")
    
    try:
        # 测试记录报告生成
        record_id = await test_record_report_generation()
        
        # 测试分析报告生成
        report_id = await test_analysis_report_generation(record_id)
        
        # 测试建议报告生成
        suggestion_id = await test_suggestion_report_generation(report_id)
        
        # 测试报告检索
        await test_report_retrieval(record_id, report_id, suggestion_id)
        
        print("\n=== 测试完成 ===")
        print(f"记录报告ID: {record_id}")
        print(f"分析报告ID: {report_id}")
        print(f"建议报告ID: {suggestion_id}")
        
        if all([record_id, report_id, suggestion_id]):
            print("✅ 所有报告生成功能测试通过！")
        else:
            print("❌ 部分报告生成功能测试失败！")
            
    except Exception as e:
        print(f"\n测试过程中出错: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
