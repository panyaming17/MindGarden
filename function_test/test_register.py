import http.client
import json

# 创建连接
conn = http.client.HTTPConnection("localhost", 8001)

# 准备请求数据
data = {
    "username": "testuser456",
    "password": "Password123!"
}

# 转换为JSON字符串
json_data = json.dumps(data)

# 设置请求头
headers = {
    "Content-Type": "application/json",
    "Content-Length": str(len(json_data))
}

# 发送请求
try:
    conn.request("POST", "/api/auth/register", json_data, headers)
    
    # 获取响应
    response = conn.getresponse()
    
    # 打印响应状态码
    print(f"状态码: {response.status}")
    
    # 打印响应头
    print("响应头:")
    for key, value in response.getheaders():
        print(f"{key}: {value}")
    
    # 打印响应内容
    print("响应内容:")
    response_content = response.read().decode("utf-8")
    print(response_content)
    
    # 尝试解析JSON
    try:
        response_json = json.loads(response_content)
        print("响应JSON:")
        print(json.dumps(response_json, ensure_ascii=False, indent=2))
    except json.JSONDecodeError as e:
        print(f"解析JSON失败: {str(e)}")
        
finally:
    # 关闭连接
    conn.close()
