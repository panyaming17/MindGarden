#!/usr/bin/env python3
"""
测试创建会话的逻辑脚本
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_create_session():
    """测试创建会话接口"""
    print("开始测试创建会话...")
    
    # 测试数据
    test_user_id = "user_631a3f3e"  # 确保这个用户ID存在
    
    # 创建会话的接口
    url = f"{BASE_URL}/api/v1/chat/new-session"
    headers = {
        "Content-Type": "application/json"
    }
    data = {
        "user_id": test_user_id
    }
    
    try:
        response = requests.post(url, headers=headers, data=json.dumps(data))
        print(f"状态码: {response.status_code}")
        print(f"响应内容: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")
        
        if response.status_code == 200:
            session_id = response.json().get("session_id")
            session_title = response.json().get("session_title")
            print(f"✅ 会话创建成功！")
            print(f"   会话ID: {session_id}")
            print(f"   会话标题: {session_title}")
            return session_id
        else:
            print(f"❌ 会话创建失败: {response.json().get('detail')}")
            return None
    
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        return None

def test_invalid_user():
    """测试使用不存在的用户ID创建会话"""
    print("\n测试使用不存在的用户ID...")
    
    url = f"{BASE_URL}/api/v1/chat/new-session"
    headers = {
        "Content-Type": "application/json"
    }
    data = {
        "user_id": "non_existent_user_123"
    }
    
    try:
        response = requests.post(url, headers=headers, data=json.dumps(data))
        print(f"状态码: {response.status_code}")
        print(f"响应内容: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")
        
        if response.status_code == 404:
            print("✅ 正确处理了不存在的用户ID")
        else:
            print("❌ 未能正确处理不存在的用户ID")
    
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")

def test_missing_user_id():
    """测试缺少用户ID的情况"""
    print("\n测试缺少用户ID...")
    
    url = f"{BASE_URL}/api/v1/chat/new-session"
    headers = {
        "Content-Type": "application/json"
    }
    data = {}
    
    try:
        response = requests.post(url, headers=headers, data=json.dumps(data))
        print(f"状态码: {response.status_code}")
        print(f"响应内容: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")
        
        if response.status_code == 422:
            print("✅ 正确处理了缺少用户ID的情况")
        else:
            print("❌ 未能正确处理缺少用户ID的情况")
    
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")

if __name__ == "__main__":
    print("====================================")
    print("测试创建会话逻辑")
    print("====================================")
    
    # 测试1: 正常创建会话
    session_id = test_create_session()
    
    # 测试2: 不存在的用户ID
    test_invalid_user()
    
    # 测试3: 缺少用户ID
    test_missing_user_id()
    
    print("\n====================================")
    print("测试完成")
    print("====================================")
    
    if session_id:
        print(f"\n提示: 您可以使用以下会话ID进行后续测试:")
        print(f"Session ID: {session_id}")
