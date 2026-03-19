#!/usr/bin/env python3
"""
测试保存对话历史接口（包含报告关联功能）
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

def save_history(session_id, user_id="test_user_123"):
    """保存对话历史"""
    print("\n保存对话历史...")
    save_url = f"{BASE_URL}/api/dialogue/save-history"
    data = {
        "session_id": session_id,
        "title": "测试对话历史（带报告关联）",
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

def test_save_dialogue_with_reports():
    """测试保存对话历史（包含报告关联功能）"""
    # 1. 创建会话
    session_id = create_conversation()
    if not session_id:
        return
    
    # 2. 生成对话历史
    if not generate_dialogue(session_id):
        return
    
    # 3. 保存对话历史
    result = save_history(session_id)
    if result:
        print("\n保存结果:")
        print(f"对话ID: {result['data']['conversation_id']}")
        print(f"消息数量: {result['data']['message_count']}")
        print(f"记录报告更新: {result['data']['record_report_updated']}")
        print(f"分析报告更新: {result['data']['analysis_report_updated']}")
        print(f"调理报告更新: {result['data']['therapy_report_updated']}")
        print(f"报告信息: {json.dumps(result['data']['reports'], indent=2, ensure_ascii=False)}")
        print("\n对话历史已成功保存到数据库，并关联了相关报告")

if __name__ == "__main__":
    test_save_dialogue_with_reports()
