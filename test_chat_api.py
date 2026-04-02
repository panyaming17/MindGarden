import requests
import json

# API基础URL
BASE_URL = "http://localhost:8000/api/v1/chat"

# 测试获取用户会话列表
def test_get_sessions():
    print("测试获取用户会话列表...")
    url = f"{BASE_URL}/sessions"
    payload = {
        "user_id": "user_631a3f3e"
    }
    try:
        response = requests.post(url, json=payload)
        print(f"状态码: {response.status_code}")
        print(f"响应内容: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")
    except Exception as e:
        print(f"测试失败: {str(e)}")

# 测试获取对话记录
def test_get_chat_history():
    print("\n测试获取对话记录...")
    url = f"{BASE_URL}/history"
    payload = {
        "user_id": "user_631a3f3e",
        "session_id": "session_0d2d0440",
        "limit": 50
    }
    try:
        response = requests.post(url, json=payload)
        print(f"状态码: {response.status_code}")
        print(f"响应内容: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")
    except Exception as e:
        print(f"测试失败: {str(e)}")

# 测试发送消息
def test_send_message():
    print("\n测试发送消息...")
    url = f"{BASE_URL}/message"
    payload = {
        "user_id": "user_631a3f3e",
        "session_id": "session_0d2d0440",
        "message": "测试消息"
    }
    try:
        response = requests.post(url, json=payload)
        print(f"状态码: {response.status_code}")
        print(f"响应内容: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")
    except Exception as e:
        print(f"测试失败: {str(e)}")

# 测试创建新会话
def test_create_session():
    print("\n测试创建新会话...")
    url = f"{BASE_URL}/new-session"
    payload = {
        "user_id": "user_631a3f3e"
    }
    try:
        response = requests.post(url, json=payload)
        print(f"状态码: {response.status_code}")
        print(f"响应内容: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")
    except Exception as e:
        print(f"测试失败: {str(e)}")

if __name__ == "__main__":
    print("开始测试对话API...")
    test_create_session()
    test_send_message()
    test_get_chat_history()
    test_get_sessions()
    print("测试完成")
