#!/usr/bin/env python3
"""
测试更新规则接口
"""

import requests
import json

BASE_URL = "http://localhost:8001"

def get_admin_token():
    """获取管理员令牌"""
    print("获取管理员令牌...")
    login_url = f"{BASE_URL}/api/auth/login"
    data = {
        "username": "admin",
        "password": "123456"
    }
    
    response = requests.post(login_url, json=data)
    if response.status_code == 200:
        token = response.json().get("access_token")
        print(f"获取令牌成功: {token[:20]}...")
        return token
    else:
        print(f"登录失败: {response.text}")
        return None

def test_update_rule(token):
    """测试更新规则接口"""
    if not token:
        print("获取令牌失败，无法测试更新规则接口")
        return
    
    print("测试更新规则接口...")
    update_url = f"{BASE_URL}/api/admin/rules/2"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # 准备更新数据
    update_data = {
        "content": {
            "examples": [],
            "strategy": "寻找反例",
            "description": ""
        }
    }
    
    print(f"更新数据: {json.dumps(update_data, ensure_ascii=False, indent=2)}")
    
    try:
        response = requests.put(update_url, json=update_data, headers=headers)
        print(f"状态码: {response.status_code}")
        print(f"响应内容: {response.text}")
        if response.status_code == 200:
            print("更新规则成功")
        else:
            print("更新规则失败")
    except Exception as e:
        print(f"错误: {str(e)}")

if __name__ == "__main__":
    token = get_admin_token()
    test_update_rule(token)
