#!/usr/bin/env python3
"""
使用真实账号测试登录和消息发送等操作
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
        print(f"响应内容: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")
        
        if response.status_code == 200:
            result = response.json()
            token = result.get("access_token")
            # 从 user.id 中获取用户ID
            user_id = result.get("user", {}).get("id")
            print("✅ 登录成功！")
            print(f"用户ID: {user_id}")
            print(f"Token: {token}")
            return token, user_id
        else:
            print(f"❌ 登录失败: {response.json().get('detail')}")
            return None, None
    
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        return None, None

def test_send_message(user_id, session_id, message, token):
    """测试发送消息接口"""
    print(f"\n测试发送消息: {message}")
    
    url = f"{BASE_URL}/api/v1/chat/message"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    data = {
        "user_id": user_id,
        "session_id": session_id,
        "message": message
    }
    
    try:
        response = requests.post(url, headers=headers, data=json.dumps(data))
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"响应内容: {json.dumps(result, ensure_ascii=False, indent=2)}")
            print("✅ 发送消息成功！")
            print(f"助手回复: {result.get('reply')}")
            return True
        else:
            print(f"❌ 发送消息失败: {response.json().get('detail')}")
            return False
    
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        return False

def test_get_chat_history(user_id, session_id, token, limit=50):
    """测试获取对话记录接口"""
    print("\n测试获取对话记录...")
    
    url = f"{BASE_URL}/api/v1/chat/history"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    data = {
        "user_id": user_id,
        "session_id": session_id,
        "limit": limit
    }
    
    try:
        response = requests.post(url, headers=headers, data=json.dumps(data))
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"响应内容: {json.dumps(result, ensure_ascii=False, indent=2)}")
            print(f"✅ 获取对话记录成功！共{len(result.get('dialogues', []))}条记录")
            return True
        else:
            print(f"❌ 获取对话记录失败: {response.json().get('detail')}")
            return False
    
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        return False

def test_end_session(user_id, session_id, token):
    """测试结束对话接口"""
    print("\n测试结束对话...")
    
    url = f"{BASE_URL}/api/v1/chat/end-session"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    data = {
        "user_id": user_id,
        "session_id": session_id
    }
    
    try:
        response = requests.post(url, headers=headers, data=json.dumps(data))
        print(f"状态码: {response.status_code}")
        print(f"响应内容: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")
        
        if response.status_code == 200:
            print("✅ 结束对话成功！")
            return True
        else:
            print(f"❌ 结束对话失败: {response.json().get('detail')}")
            return False
    
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        return False

def test_get_reports(user_id, session_id, token):
    """测试获取会话报告接口"""
    print("\n测试获取会话报告...")
    
    url = f"{BASE_URL}/api/v1/report/{session_id}"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    
    try:
        response = requests.get(url, headers=headers)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"响应内容: {json.dumps(result, ensure_ascii=False, indent=2)}")
            print("✅ 获取会话报告成功！")
            return True
        else:
            print(f"❌ 获取会话报告失败: {response.json().get('detail')}")
            return False
    
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        return False

def test_get_report_list(user_id, token):
    """测试获取报告列表接口"""
    print("\n测试获取报告列表...")
    
    url = f"{BASE_URL}/api/v1/report/list"
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
            print(f"✅ 获取报告列表成功！共{len(result.get('reports', []))}个报告")
            return True
        else:
            print(f"❌ 获取报告列表失败: {response.json().get('detail')}")
            return False
    
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        return False

if __name__ == "__main__":
    print("====================================")
    print("使用真实账号测试")
    print("====================================")
    
    # 测试账号信息
    username = "pym"
    password = "pym123456"
    session_id = "session_70db0c09"
    
    # 1. 测试登录
    token, user_id = test_login(username, password)
    
    if token and user_id:
        # 2. 测试获取对话记录
        test_get_chat_history(user_id, session_id, token)
        
        # 3. 测试发送消息
        test_send_message(user_id, session_id, "你好，我想咨询一下关于情绪管理的问题", token)
        test_send_message(user_id, session_id, "最近工作压力很大，经常感到焦虑", token)
        
        # 4. 再次测试获取对话记录
        test_get_chat_history(user_id, session_id, token)
        
        # 5. 测试结束对话（会生成三个报告）
        test_end_session(user_id, session_id, token)
        
        # 6. 测试获取会话报告
        test_get_reports(user_id, session_id, token)
        
        # 7. 测试获取报告列表
        test_get_report_list(user_id, token)
    else:
        print("❌ 登录失败，无法继续测试")
    
    print("\n====================================")
    print("测试完成")
    print("====================================")
