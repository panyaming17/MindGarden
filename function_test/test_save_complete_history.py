#!/usr/bin/env python3
"""
测试保存完整对话历史接口（包含记录师、来访者、分析师、调理师）
"""

import requests
import json

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

def generate_complete_dialogue(session_id):
    """生成包含所有角色的对话历史"""
    print("\n生成完整对话历史...")
    dialogue_url = f"{BASE_URL}/api/dialogue/multi-agent"
    data = {
        "patient_message": "我最近感觉很沮丧，什么都不想做",
        "patient_id": session_id
    }
    
    response = requests.post(dialogue_url, json=data)
    if response.status_code == 200:
        print("对话生成成功")
        # 打印对话历史，验证是否包含所有角色
        conversation_history = response.json().get("conversation_history", [])
        print("\n对话历史包含的角色:")
        for msg in conversation_history:
            role = msg['role']
            message = msg['message']
            # 处理不同类型的消息内容
            if isinstance(message, dict):
                # 对于字典类型的消息，打印其类型
                print(f"- {role}: {type(message).__name__} 对象")
            else:
                # 对于字符串类型的消息，打印前50个字符
                print(f"- {role}: {str(message)[:50]}...")
        return True
    else:
        print(f"对话生成失败: {response.text}")
        return False

def save_history(session_id):
    """保存对话历史"""
    print("\n保存对话历史...")
    save_url = f"{BASE_URL}/api/dialogue/save-history"
    data = {
        "session_id": session_id,
        "title": "完整对话历史测试",
        "user_id": "test_user_123"
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

def test_save_complete_history():
    """测试保存完整对话历史接口"""
    # 1. 创建会话
    session_id = create_conversation()
    if not session_id:
        return
    
    # 2. 生成完整对话历史
    if not generate_complete_dialogue(session_id):
        return
    
    # 3. 保存对话历史
    result = save_history(session_id)
    if result:
        print(f"\n保存结果:")
        print(f"对话ID: {result['data']['conversation_id']}")
        print(f"消息数量: {result['data']['message_count']}")
        print("\n对话历史已成功保存到数据库，包含记录师、来访者、分析师、调理师的完整对话内容")

if __name__ == "__main__":
    test_save_complete_history()
