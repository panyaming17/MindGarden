import requests
import json

# API基础URL
BASE_URL = "http://localhost:8000/api/v1/chat"

# 测试获取用户会话列表
def test_get_sessions():
    print("测试获取用户会话列表...")
    url = f"{BASE_URL}/sessions"
    
    # 测试数据：使用用户提供的信息
    payload = {
        "user_id": "user_631a3f3e"
    }
    
    try:
        response = requests.post(url, json=payload)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            sessions = data.get("sessions", [])
            print(f"返回的会话数量: {len(sessions)}")
            
            # 打印每个会话的信息
            if sessions:
                print("\n会话详情:")
                for i, session in enumerate(sessions[:3]):  # 只打印前3个会话
                    print(f"\n会话 {i+1}:")
                    print(f"会话ID: {session['session_id']}")
                    print(f"标题: {session['title']}")
                    print(f"最后一条消息: {session['last_message'][:50]}..." if len(session['last_message']) > 50 else f"最后一条消息: {session['last_message']}")
                    print(f"创建时间: {session['created_at']}")
                    print(f"思维陷阱: {session['thinking_traps']}")
                    print(f"情绪反应: {session['emotional_response']}")
            else:
                print("无会话记录")
        else:
            print(f"错误信息: {response.text}")
            
    except Exception as e:
        print(f"测试失败: {str(e)}")

if __name__ == "__main__":
    print("开始测试会话列表接口...")
    test_get_sessions()
    print("测试完成")
