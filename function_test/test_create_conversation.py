#!/usr/bin/env python3
"""
测试创建会话接口
"""

import requests
import json

BASE_URL = "http://localhost:8001"

def test_create_conversation():
    """测试创建会话接口"""
    print("测试创建会话接口...")
    create_url = f"{BASE_URL}/api/conversations/create"
    data = {
        "type": "multi-agent"
    }
    
    try:
        response = requests.post(create_url, json=data, headers={"Content-Type": "application/json"})
        print(f"状态码: {response.status_code}")
        print(f"响应内容: {response.text}")
        if response.status_code == 200:
            result = response.json()
            print(f"成功: {result}")
            return result.get("session_id")
        else:
            print(f"失败: {response.text}")
            return None
    except Exception as e:
        print(f"错误: {str(e)}")
        return None

if __name__ == "__main__":
    session_id = test_create_conversation()
