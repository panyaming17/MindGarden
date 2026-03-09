import requests
import json

# 测试被禁用的用户登录
def test_disabled_user_login():
    url = "http://localhost:8001/api/auth/login"
    headers = {"Content-Type": "application/json"}
    data = {
        "username": "pym",
        "password": "123456"
    }
    
    response = requests.post(url, headers=headers, data=json.dumps(data))
    print(f"Status code: {response.status_code}")
    print(f"Response: {response.json()}")

# 测试正常用户登录
def test_active_user_login():
    url = "http://localhost:8001/api/auth/login"
    headers = {"Content-Type": "application/json"}
    data = {
        "username": "admin",
        "password": "123456"
    }
    
    response = requests.post(url, headers=headers, data=json.dumps(data))
    print(f"Status code: {response.status_code}")
    print(f"Response: {response.json()}")

if __name__ == "__main__":
    print("Testing disabled user login:")
    test_disabled_user_login()
    print("\nTesting active user login:")
    test_active_user_login()
