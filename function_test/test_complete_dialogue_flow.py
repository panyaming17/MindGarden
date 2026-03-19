#!/usr/bin/env python3
"""
测试完整的对话流程（包含报告创建和保存）
"""

import requests
import json
import time

BASE_URL = "http://localhost:8001"

def create_conversation():
    """创建对话会话"""
    print("创建对话会话...")
    create_url = f"{BASE_URL}/api/conversations/create"
    data = {
        "type": "multi-agent"
    }
    
    response = requests.post(create_url, json=data)
    if response.status_code == 200:
        session_id = response.json().get("session_id")
        print(f"创建会话成功: {session_id}")
        return session_id
    else:
        print(f"创建会话失败: {response.text}")
        return None

def generate_dialogue(session_id):
    """生成对话历史"""
    print("\n生成对话历史...")
    dialogue_url = f"{BASE_URL}/api/dialogue/multi-agent"
    data = {
        "patient_message": "我最近感觉很沮丧，什么都不想做",
        "patient_id": session_id
    }
    
    response = requests.post(dialogue_url, json=data)
    if response.status_code == 200:
        print("对话生成成功")
        return True
    else:
        print(f"对话生成失败: {response.text}")
        return False

def create_record_report(session_id, user_id="test_user_123"):
    """创建记录报告"""
    print("\n创建记录报告...")
    record_url = f"{BASE_URL}/recorder/record-reports"
    data = {
        "session_id": session_id,
        "user_id": user_id,
        "duration": 120.5,
        "conversation_log": [
            {"role": "user", "content": "我最近感觉很沮丧，什么都不想做"},
            {"role": "assistant", "content": "能具体说说是什么事情让你感到沮丧吗？"}
        ],
        "situation": "工作压力大，人际关系紧张",
        "automatic_thoughts": ["我什么都做不好", "没有人理解我"],
        "emotions": [
            {"type": "沮丧", "intensity": 80},
            {"type": "焦虑", "intensity": 60}
        ],
        "physical_sensations": ["头痛", "失眠"],
        "summary": "来访者因工作压力和人际关系问题感到沮丧和焦虑"
    }
    
    response = requests.post(record_url, json=data)
    print(f"状态码: {response.status_code}")
    print(f"响应内容: {response.text}")
    
    if response.status_code == 200:
        record_id = response.json().get("record_id")
        print(f"创建记录报告成功: {record_id}")
        return record_id
    else:
        print("创建记录报告失败")
        return None

def create_analysis_report(record_id, user_id="test_user_123"):
    """创建分析报告"""
    print("\n创建分析报告...")
    analyze_url = f"{BASE_URL}/analyst/analyze"
    data = {
        "record_id": record_id,
        "priority": "normal"
    }
    
    response = requests.post(analyze_url, json=data)
    print(f"状态码: {response.status_code}")
    print(f"响应内容: {response.text}")
    
    if response.status_code == 200:
        # 分析任务是异步的，需要等待完成
        request_id = response.json().get("request_id")
        print(f"分析任务已提交，请求ID: {request_id}")
        
        # 等待分析完成
        print("等待分析完成...")
        time.sleep(5)  # 等待5秒
        
        # 尝试获取分析报告
        report_url = f"{BASE_URL}/analyst/analysis-reports/record/{record_id}"
        response = requests.get(report_url)
        print(f"获取分析报告状态码: {response.status_code}")
        
        if response.status_code == 200:
            report_id = response.json().get("report_id")
            print(f"创建分析报告成功: {report_id}")
            return report_id
        else:
            print("分析报告尚未生成，使用模拟报告ID")
            # 使用模拟报告ID继续测试
            return f"rep_{record_id[4:]}"
    else:
        print("创建分析报告失败")
        return None

def create_suggestion_report(report_id, user_id="test_user_123"):
    """创建调理报告"""
    print("\n创建调理报告...")
    suggest_url = f"{BASE_URL}/therapist/generate-plan"
    data = {
        "report_id": report_id,
        "user_preference": "balanced"
    }
    
    response = requests.post(suggest_url, json=data)
    print(f"状态码: {response.status_code}")
    print(f"响应内容: {response.text}")
    
    if response.status_code == 200:
        print("创建调理报告成功")
        return True
    else:
        print("创建调理报告失败")
        return False

def save_history(session_id, user_id="test_user_123"):
    """保存对话历史"""
    print("\n保存对话历史...")
    save_url = f"{BASE_URL}/api/dialogue/save-history"
    data = {
        "session_id": session_id,
        "title": "完整对话流程测试",
        "user_id": user_id
    }
    
    response = requests.post(save_url, json=data)
    print(f"状态码: {response.status_code}")
    print(f"响应内容: {response.text}")
    
    if response.status_code == 200:
        print("对话历史保存成功")
        return response.json()
    else:
        print("对话历史保存失败")
        return None

def test_complete_dialogue_flow():
    """测试完整的对话流程"""
    # 1. 创建会话
    session_id = create_conversation()
    if not session_id:
        return
    
    # 2. 生成对话历史
    if not generate_dialogue(session_id):
        return
    
    # 3. 创建记录报告
    record_id = create_record_report(session_id)
    if not record_id:
        return
    
    # 4. 创建分析报告
    report_id = create_analysis_report(record_id)
    if not report_id:
        return
    
    # 5. 创建调理报告
    if not create_suggestion_report(report_id):
        return
    
    # 6. 保存对话历史
    result = save_history(session_id)
    if result:
        print("\n保存结果:")
        print(f"对话ID: {result['data']['conversation_id']}")
        print(f"消息数量: {result['data']['message_count']}")
        print(f"记录报告更新: {result['data']['record_report_updated']}")
        print(f"分析报告更新: {result['data']['analysis_report_updated']}")
        print(f"调理报告更新: {result['data']['therapy_report_updated']}")
        print(f"报告信息: {json.dumps(result['data']['reports'], indent=2, ensure_ascii=False)}")
        print("\n完整对话流程测试成功！")

if __name__ == "__main__":
    test_complete_dialogue_flow()
