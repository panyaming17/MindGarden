import requests
import json

# 测试接口URL
url = "http://localhost:8001/analyst/analyze"

# 请求头
headers = {
    "Content-Type": "application/json"
}

# 请求数据 - 使用high优先级
payload = {
    "record_id": "rec_123",
    "priority": "high"
}

print("正在测试高优先级分析接口...")
print(f"URL: {url}")
print(f"请求数据: {json.dumps(payload, ensure_ascii=False, indent=2)}")
print("-" * 50)

try:
    # 发送POST请求
    response = requests.post(url, headers=headers, json=payload)
    
    # 打印响应状态码
    print(f"响应状态码: {response.status_code}")
    
    # 打印响应内容
    response_json = response.json()
    print("响应内容:")
    print(json.dumps(response_json, ensure_ascii=False, indent=2))
    
    # 如果有report_id，可以测试获取报告
    if response.status_code == 200 and response_json.get("status") == "completed" and "report_id" in response_json:
        print("\n" + "-" * 50)
        print("正在测试获取报告接口...")
        report_url = f"http://localhost:8001/analyst/report/{response_json['report_id']}"
        report_response = requests.get(report_url)
        print(f"报告接口状态码: {report_response.status_code}")
        if report_response.status_code == 200:
            print("报告内容:")
            print(json.dumps(report_response.json(), ensure_ascii=False, indent=2))
            
except requests.exceptions.RequestException as e:
    print(f"请求失败: {e}")
except json.JSONDecodeError as e:
    print(f"响应解析失败: {e}")
    print(f"响应内容: {response.text}")