"""
简单测试脚本 - 测试发送消息功能
"""
import requests
import json
import time

BASE_URL = "http://localhost:8000"
USERNAME = "pym"
PASSWORD = "pym123456"

def test_health():
    """测试服务健康状态"""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        print(f"健康检查: {response.status_code}")
        return response.status_code == 200
    except Exception as e:
        print(f"健康检查失败: {e}")
        return False

def login():
    """登录获取用户ID"""
    print("\n=== 登录 ===")
    url = f"{BASE_URL}/api/v1/auth/login"
    data = {
        "username": USERNAME,
        "password": PASSWORD
    }
    
    try:
        response = requests.post(url, json=data, timeout=30)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            user_id = result.get('user', {}).get('id')
            print(f"用户ID: {user_id}")
            return user_id
        else:
            print(f"登录失败: {response.text}")
            return None
    except Exception as e:
        print(f"登录异常: {e}")
        return None

def test_send_message(user_id):
    """测试发送消息"""
    print("\n=== 测试发送消息 ===")
    url = f"{BASE_URL}/api/v1/chat/message"
    data = {
        "user_id": user_id,
        "session_id": "test_session_001",
        "message": "我最近感到压力很大"
    }
    
    print(f"请求数据: {json.dumps(data, ensure_ascii=False)}")
    
    try:
        response = requests.post(url, json=data, timeout=60)
        print(f"状态码: {response.status_code}")
        print(f"响应: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"请求异常: {e}")
        import traceback
        print(traceback.format_exc())
        return False

if __name__ == "__main__":
    print("="*60)
    print("简单测试 - 发送消息功能")
    print("="*60)
    
    # 等待服务启动
    print("\n等待服务启动...")
    for i in range(30):
        if test_health():
            print("✅ 服务已启动")
            break
        time.sleep(2)
        print(f"尝试 {i+1}/30...")
    else:
        print("❌ 服务启动超时")
        exit(1)
    
    # 登录
    user_id = login()
    if not user_id:
        print("❌ 登录失败")
        exit(1)
    
    # 测试发送消息
    if test_send_message(user_id):
        print("\n✅ 发送消息测试成功")
    else:
        print("\n❌ 发送消息测试失败")
