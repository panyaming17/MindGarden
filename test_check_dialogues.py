"""检查会话对话数量"""
import requests

BASE_URL = "http://localhost:8000"

response = requests.post(f"{BASE_URL}/api/v1/chat/history", json={"user_id": "user_631a3f3e", "session_id": "session_ba0393fe"})
if response.status_code == 200:
    data = response.json()
    dialogues = data.get("dialogues", [])
    print(f"会话 session_ba0393fe 共有 {len(dialogues)} 条对话")
    for i, d in enumerate(dialogues[:10]):
        print(f"{i+1}. [{d['role']}] {d['content'][:50]}...")
else:
    print(f"获取失败: {response.status_code}")
    print(response.text)
