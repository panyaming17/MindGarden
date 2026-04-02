#!/usr/bin/env python3
"""
测试获取用户会话列表接口
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_login(username, password):
    """测试登录接口"""
    print("测试登录...")
    
    url = f"{BASE_URL}/api/v1/auth/login"
    headers = {
        "Content-Type": "application/json"
    }
    data = {
        "username": username,
        "password": password
    }
    
    try:
        response = requests.post(url, headers=headers, data=json.dumps(data))
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            token = result.get("access_token")
            user_id = result.get("user", {}).get("id")
            print("✅ 登录成功！")
            print(f"用户ID: {user_id}")
            return token, user_id
        else:
            print(f"❌ 登录失败: {response.json().get('detail')}")
            return None, None
    
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        return None, None

def test_get_sessions(user_id, token):
    """测试获取用户会话列表接口"""
    print("\n测试获取用户会话列表...")
    
    url = f"{BASE_URL}/api/v1/chat/sessions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    data = {
        "user_id": user_id
    }
    
    try:
        response = requests.post(url, headers=headers, data=json.dumps(data))
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"响应内容: {json.dumps(result, ensure_ascii=False, indent=2)}")
            sessions = result.get('sessions', [])
            print(f"✅ 获取会话列表成功！共{sessions}个会话")
            
            # 打印每个会话的详细信息
            print("\n会话列表:")
            print("=" * 60)
            for i, session in enumerate(sessions, 1):
                print(f"\n会话 {i}:")
                print(f"  会话ID: {session.get('session_id')}")
                print(f"  标题: {session.get('title')}")
                print(f"  最后消息: {session.get('last_message')}")
                print(f"  创建时间: {session.get('created_at')}")
                print(f"  思维陷阱: {session.get('thinking_traps')}")
                print(f"  情绪反应: {session.get('emotional_response')}")
                print("-" * 50)
            
            return True
        else:
            print(f"❌ 获取会话列表失败: {response.json().get('detail')}")
            return False
    
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        return False

if __name__ == "__main__":
    print("====================================")
    print("测试获取用户会话列表接口")
    print("====================================")
    
    # 测试账号信息
    username = "pym"
    password = "pym123456"
    
    # 1. 测试登录
    token, user_id = test_login(username, password)
    
    if token and user_id:
        # 2. 测试获取会话列表
        test_get_sessions(user_id, token)
    else:
        print("❌ 登录失败，无法继续测试")
    
    print("\n====================================")
    print("测试完成")
    print("====================================")
