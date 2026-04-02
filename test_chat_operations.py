#!/usr/bin/env python3
"""
测试对话操作相关接口
包括：结束对话、获取对话记录、删除对话记录
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_end_session(user_id, session_id):
    """测试结束对话接口"""
    print("\n测试结束对话...")
    
    url = f"{BASE_URL}/api/v1/chat/end-session"
    headers = {
        "Content-Type": "application/json"
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

def test_get_chat_history(user_id, session_id, limit=50):
    """测试获取对话记录接口"""
    print("\n测试获取对话记录...")
    
    url = f"{BASE_URL}/api/v1/chat/history"
    headers = {
        "Content-Type": "application/json"
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

def test_delete_session(user_id, session_id):
    """测试删除对话记录接口"""
    print("\n测试删除对话...")
    
    url = f"{BASE_URL}/api/v1/chat/delete-session"
    headers = {
        "Content-Type": "application/json"
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
            print("✅ 删除对话成功！")
            return True
        else:
            print(f"❌ 删除对话失败: {response.json().get('detail')}")
            return False
    
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        return False

def test_get_sessions(user_id):
    """测试获取会话列表接口"""
    print("\n测试获取会话列表...")
    
    url = f"{BASE_URL}/api/v1/chat/sessions"
    headers = {
        "Content-Type": "application/json"
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
            print(f"✅ 获取会话列表成功！共{len(result.get('sessions', []))}个会话")
            return result.get('sessions', [])
        else:
            print(f"❌ 获取会话列表失败: {response.json().get('detail')}")
            return []
    
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        return []

def test_edit_session_title(user_id, session_id, new_title):
    """测试编辑会话标题接口"""
    print("\n测试编辑会话标题...")
    
    url = f"{BASE_URL}/api/v1/chat/edit-session-title"
    headers = {
        "Content-Type": "application/json"
    }
    data = {
        "user_id": user_id,
        "session_id": session_id,
        "title": new_title
    }
    
    try:
        response = requests.post(url, headers=headers, data=json.dumps(data))
        print(f"状态码: {response.status_code}")
        print(f"响应内容: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")
        
        if response.status_code == 200:
            print("✅ 编辑会话标题成功！")
            return True
        else:
            print(f"❌ 编辑会话标题失败: {response.json().get('detail')}")
            return False
    
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        return False

def create_test_session(user_id):
    """创建测试会话"""
    print("\n创建测试会话...")
    
    url = f"{BASE_URL}/api/v1/chat/new-session"
    headers = {
        "Content-Type": "application/json"
    }
    data = {
        "user_id": user_id
    }
    
    try:
        response = requests.post(url, headers=headers, data=json.dumps(data))
        if response.status_code == 200:
            result = response.json()
            session_id = result.get("session_id")
            print(f"✅ 创建会话成功！会话ID: {session_id}")
            return session_id
        else:
            print(f"❌ 创建会话失败: {response.json().get('detail')}")
            return None
    
    except Exception as e:
        print(f"❌ 创建会话失败: {str(e)}")
        return None

def send_test_message(user_id, session_id, message):
    """发送测试消息"""
    print(f"\n发送测试消息: {message}")
    
    url = f"{BASE_URL}/api/v1/chat/message"
    headers = {
        "Content-Type": "application/json"
    }
    data = {
        "user_id": user_id,
        "session_id": session_id,
        "message": message
    }
    
    try:
        response = requests.post(url, headers=headers, data=json.dumps(data))
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 发送消息成功！")
            print(f"助手回复: {result.get('reply')}")
            return True
        else:
            print(f"❌ 发送消息失败: {response.json().get('detail')}")
            return False
    
    except Exception as e:
        print(f"❌ 发送消息失败: {str(e)}")
        return False

if __name__ == "__main__":
    print("====================================")
    print("测试对话操作接口")
    print("====================================")
    
    # 测试数据
    test_user_id = "user_631a3f3e"
    
    # 1. 创建测试会话
    session_id = create_test_session(test_user_id)
    
    if session_id:
        # 2. 发送测试消息
        send_test_message(test_user_id, session_id, "我最近心情不太好")
        send_test_message(test_user_id, session_id, "感觉工作压力很大")
        
        # 3. 测试获取对话记录
        test_get_chat_history(test_user_id, session_id)
        
        # 4. 测试编辑会话标题
        test_edit_session_title(test_user_id, session_id, "测试会话标题")
        
        # 5. 测试获取会话列表
        test_get_sessions(test_user_id)
        
        # 6. 测试结束对话
        test_end_session(test_user_id, session_id)
        
        # 7. 测试删除对话
        test_delete_session(test_user_id, session_id)
        
        # 8. 再次测试获取会话列表
        test_get_sessions(test_user_id)
    else:
        print("❌ 创建会话失败，无法继续测试")
    
    print("\n====================================")
    print("测试完成")
    print("====================================")
