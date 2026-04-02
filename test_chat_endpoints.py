"""
测试对话接口
使用真实用户账号：pym / pym123456
流程：登录 -> 创建会话 -> 发送消息 -> 获取会话列表 -> 获取对话记录 -> 编辑标题 -> 结束会话 -> 删除会话
"""
import requests
import json
import time

# 基础URL
BASE_URL = "http://localhost:8000"

# 真实用户账号
USERNAME = "pym"
PASSWORD = "pym123456"

def login():
    """登录获取用户ID"""
    print("\n=== 登录 ===")
    url = f"{BASE_URL}/api/v1/auth/login"
    data = {
        "username": USERNAME,
        "password": PASSWORD
    }
    
    try:
        response = requests.post(url, json=data, timeout=10)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"登录成功!")
            # 从user对象中获取id
            user_id = result.get('user', {}).get('id')
            print(f"用户ID: {user_id}")
            return user_id
        else:
            print(f"登录失败: {response.text}")
            return None
    except Exception as e:
        print(f"异常: {e}")
        return None

def test_create_session(user_id):
    """测试创建新会话"""
    print("\n=== 测试创建新会话 ===")
    url = f"{BASE_URL}/api/v1/chat/new-session"
    data = {
        "user_id": user_id
    }
    
    try:
        response = requests.post(url, json=data)
        print(f"状态码: {response.status_code}")
        print(f"响应内容: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")
        
        if response.status_code == 200:
            return response.json().get("session_id")
        else:
            print("创建会话失败")
            return None
    except Exception as e:
        print(f"请求失败: {e}")
        return None

def test_send_message(user_id, session_id):
    """测试发送消息"""
    print("\n=== 测试发送消息 ===")
    url = f"{BASE_URL}/api/v1/chat/message"
    data = {
        "user_id": user_id,
        "session_id": session_id,
        "message": "我最近感到压力很大，工作和生活都不太顺利。"
    }
    
    try:
        response = requests.post(url, json=data)
        print(f"状态码: {response.status_code}")
        print(f"响应内容: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")
    except Exception as e:
        print(f"请求失败: {e}")

def test_get_sessions(user_id):
    """测试获取用户会话列表"""
    print("\n=== 测试获取用户会话列表 ===")
    url = f"{BASE_URL}/api/v1/chat/sessions"
    data = {
        "user_id": user_id
    }
    
    try:
        response = requests.post(url, json=data)
        print(f"状态码: {response.status_code}")
        print(f"响应内容: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")
    except Exception as e:
        print(f"请求失败: {e}")

def test_get_chat_history(user_id, session_id):
    """测试获取对话记录"""
    print("\n=== 测试获取对话记录 ===")
    url = f"{BASE_URL}/api/v1/chat/history"
    data = {
        "user_id": user_id,
        "session_id": session_id,
        "limit": 50
    }
    
    try:
        response = requests.post(url, json=data)
        print(f"状态码: {response.status_code}")
        response_data = response.json()
        print(f"响应内容: {json.dumps(response_data, ensure_ascii=False, indent=2)}")
        
        # 打印对话记录列表
        if "dialogues" in response_data:
            print("\n=== 对话记录列表 ===")
            for i, dialogue in enumerate(response_data["dialogues"]):
                print(f"\n对话 {i+1}:")
                print(f"角色: {dialogue.get('role')}")
                print(f"内容: {dialogue.get('content')}")
                print(f"创建时间: {dialogue.get('created_at')}")
    except Exception as e:
        print(f"请求失败: {e}")

def test_edit_session_title(user_id, session_id):
    """测试编辑会话标题"""
    print("\n=== 测试编辑会话标题 ===")
    url = f"{BASE_URL}/api/v1/chat/edit-session-title"
    data = {
        "user_id": user_id,
        "session_id": session_id,
        "title": "测试会话 - 压力管理"
    }
    
    try:
        response = requests.post(url, json=data)
        print(f"状态码: {response.status_code}")
        print(f"响应内容: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")
    except Exception as e:
        print(f"请求失败: {e}")

def test_end_session(user_id, session_id):
    """测试结束会话"""
    print("\n=== 测试结束会话 ===")
    url = f"{BASE_URL}/api/v1/chat/end-session"
    data = {
        "user_id": user_id,
        "session_id": session_id
    }
    
    try:
        response = requests.post(url, json=data)
        print(f"状态码: {response.status_code}")
        print(f"响应内容: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")
    except Exception as e:
        print(f"请求失败: {e}")

def test_delete_session(user_id, session_id):
    """测试删除会话"""
    print("\n=== 测试删除会话 ===")
    url = f"{BASE_URL}/api/v1/chat/delete-session"
    data = {
        "user_id": user_id,
        "session_id": session_id
    }
    
    try:
        response = requests.post(url, json=data)
        print(f"状态码: {response.status_code}")
        print(f"响应内容: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")
    except Exception as e:
        print(f"请求失败: {e}")

if __name__ == "__main__":
    print("="*60)
    print("测试对话接口")
    print(f"用户名: {USERNAME}")
    print("="*60)
    
    # 先测试服务是否可用
    try:
        r = requests.get(f"{BASE_URL}/health", timeout=5)
        print(f"\n✅ 服务运行中 (状态: {r.status_code})")
    except:
        print(f"\n❌ 服务未运行，请先启动后端服务")
        exit(1)
    
    # 登录获取用户ID
    user_id = login()
    
    if not user_id:
        print("\n❌ 登录失败，无法继续测试")
        exit(1)
    
    print(f"\n✅ 登录成功，用户ID: {user_id}")
    
    # 测试创建会话
    session_id = test_create_session(user_id)
    
    if session_id:
        print(f"\n✅ 会话创建成功，会话ID: {session_id}")
        
        # 等待1秒，确保会话创建完成
        time.sleep(1)
        
        # 测试发送消息
        test_send_message(user_id, session_id)
        
        # 等待2秒，确保消息处理完成
        time.sleep(2)
        
        # 测试获取会话列表
        test_get_sessions(user_id)
        
        # 测试获取对话记录
        test_get_chat_history(user_id, session_id)
        
        # 测试编辑会话标题
        test_edit_session_title(user_id, session_id)
        
        # 测试结束会话
        test_end_session(user_id, session_id)
        
        # 等待3秒，确保会话结束和报告生成完成
        time.sleep(3)
        
        # 测试删除会话
        test_delete_session(user_id, session_id)
    else:
        print("\n❌ 创建会话失败，无法继续测试")
    
    print("\n" + "="*60)
    print("测试完成！")
    print("="*60)
