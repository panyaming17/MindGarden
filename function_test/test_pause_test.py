#!/usr/bin/env python3
"""
测试暂停测试接口
"""

import requests
import json

BASE_URL = "http://localhost:8001"

def test_pause_test():
    """测试暂停测试接口"""
    print("测试暂停测试接口...")
    pause_url = f"{BASE_URL}/api/conversations/pause-test"
    data = {
        "session_id": "test_session_123"
    }
    
    try:
        response = requests.post(pause_url, json=data, headers={"Content-Type": "application/json"})
        print(f"状态码: {response.status_code}")
        print(f"响应内容: {response.text}")
        if response.status_code == 200:
            result = response.json()
            print(f"成功: {result}")
        else:
            print(f"失败: {response.text}")
    except Exception as e:
        print(f"错误: {str(e)}")

if __name__ == "__main__":
    test_pause_test()
