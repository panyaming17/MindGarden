#!/usr/bin/env python3
"""
测试get_chat_history函数
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
            dialogues = result.get('dialogues', [])
            print(f"✅ 获取对话记录成功！共{len(dialogues)}条记录")
            
            # 打印每条对话的内容
            print("\n对话记录列表:")
            print("=" * 50)
            for i, dialogue in enumerate(dialogues, 1):
                print(f"\n对话 {i}:")
                print(f"  角色: {dialogue.get('role')}")
                print(f"  内容: {dialogue.get('content')}")
                print(f"  时间: {dialogue.get('created_at')}")
                print(f"  ID: {dialogue.get('id')}")
                print(f"  会话ID: {dialogue.get('session_id')}")
                print(f"  用户ID: {dialogue.get('user_id')}")
                print(f"  是否有价值: {dialogue.get('is_valuable')}")
                # 打印四维情绪数据
                four_dim = dialogue.get('four_dim_intensity')
                if four_dim:
                    print(f"  情绪强度: {four_dim}")
                hedonic = dialogue.get('four_dim_hedonic')
                if hedonic:
                    print(f"  快感度: {hedonic}")
                tension = dialogue.get('four_dim_tension')
                if tension:
                    print(f"  紧张度: {tension}")
                complexity = dialogue.get('four_dim_complexity')
                if complexity:
                    print(f"  复杂度: {complexity}")
                print("-" * 40)
                
            return True
        else:
            print(f"❌ 获取对话记录失败: {response.json().get('detail')}")
            return False
    
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        return False

if __name__ == "__main__":
    print("====================================")
    print("测试get_chat_history函数")
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
    else:
        print("❌ 登录失败，无法继续测试")
    
    print("\n====================================")
    print("测试完成")
    print("====================================")
