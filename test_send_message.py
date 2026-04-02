#!/usr/bin/env python3
"""
测试发送消息功能，检查用户认知档案是否能正确保存
"""
import requests
import json

# 测试发送消息
def test_send_message():
    url = "http://localhost:8000/api/v1/chat/message"
    headers = {
        "Content-Type": "application/json"
    }
    
    # 测试数据
    data = {
        "user_id": "user_631a3f3e",
        "session_id": "sess_test123",
        "message": "我最近工作压力很大，感觉喘不过气来，每天都很焦虑，担心自己做不好工作。"
    }
    
    print("发送测试消息...")
    response = requests.post(url, headers=headers, data=json.dumps(data))
    
    print(f"响应状态码: {response.status_code}")
    print(f"响应内容: {response.json()}")

if __name__ == "__main__":
    test_send_message()
