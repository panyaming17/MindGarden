import requests
import json

# 测试删除会话接口
url = "http://localhost:8000/api/v1/chat/delete-session"

# 请求参数
payload = {
    "user_id": "user_631a3f3e",
    "session_id": "session_c10689d9"
}

# 设置请求头
headers = {
    "Content-Type": "application/json"
}

print("测试删除会话接口")
print(f"请求URL: {url}")
print(f"请求参数: {json.dumps(payload, indent=2, ensure_ascii=False)}")

# 发送请求
try:
    response = requests.post(url, json=payload, headers=headers)
    
    # 打印响应状态码
    print(f"\n响应状态码: {response.status_code}")
    
    # 打印响应内容
    response_json = response.json()
    print(f"响应内容: {json.dumps(response_json, indent=2, ensure_ascii=False)}")
    
    if response.status_code == 200:
        print("\n测试成功: 会话删除成功")
    else:
        print("\n测试失败: 会话删除失败")
        
except Exception as e:
    print(f"\n测试错误: {str(e)}")
