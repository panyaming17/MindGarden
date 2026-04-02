import requests
import json

BASE_URL = "http://localhost:8001"

print("="*60)
print("测试发送消息功能")
print("="*60)

# 1. 测试健康检查
print("\n[1] 测试服务健康状态...")
try:
    response = requests.get(f"{BASE_URL}/health", timeout=5)
    print(f"✅ 服务运行正常 (状态码：{response.status_code})")
except Exception as e:
    print(f"❌ 服务未运行：{e}")
    exit(1)

# 2. 登录
print("\n[2] 测试登录...")
try:
    response = requests.post(
        f"{BASE_URL}/api/v1/auth/login",
        json={"username": "pym", "password": "pym123456"},
        timeout=30
    )
    if response.status_code == 200:
        result = response.json()
        user_id = result['user']['id']
        print(f"✅ 登录成功 (用户 ID: {user_id})")
    else:
        print(f"❌ 登录失败：{response.text}")
        exit(1)
except Exception as e:
    print(f"❌ 登录异常：{e}")
    exit(1)

# 3. 发送消息
print("\n[3] 测试发送消息...")
try:
    response = requests.post(
        f"{BASE_URL}/api/v1/chat/message",
        json={
            "user_id": user_id,
            "session_id": "test_session_001",
            "message": "我最近感到压力很大"
        },
        timeout=60
    )
    print(f"状态码：{response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ 发送消息成功")
        print(f"回复：{result.get('reply', 'N/A')}")
        print(f"\n完整响应:")
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"❌ 发送消息失败：{response.text}")
except Exception as e:
    print(f"❌ 发送消息异常：{e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*60)
print("测试完成")
print("="*60)
