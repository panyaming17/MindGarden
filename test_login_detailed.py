import requests
import json
import time

def test_login(username, password, expected_status, expected_detail):
    """测试登录接口"""
    url = "http://localhost:8001/api/auth/login"
    headers = {"Content-Type": "application/json"}
    data = {
        "username": username,
        "password": password
    }
    
    print(f"\nTesting login for user: {username}")
    print(f"Password: {password}")
    
    response = requests.post(url, headers=headers, data=json.dumps(data))
    print(f"Status code: {response.status_code}")
    
    if response.status_code == 200:
        print("Login successful!")
        print(f"Access token: {response.json().get('access_token', 'N/A')[:20]}...")
    else:
        print(f"Error message: {response.json().get('detail', 'N/A')}")
    
    # 验证结果
    if response.status_code == expected_status:
        if expected_detail:
            if response.json().get('detail') == expected_detail:
                print("✅ Test passed!")
            else:
                print(f"❌ Test failed! Expected detail: '{expected_detail}', got: '{response.json().get('detail')}'")
        else:
            print("✅ Test passed!")
    else:
        print(f"❌ Test failed! Expected status: {expected_status}, got: {response.status_code}")

if __name__ == "__main__":
    print("=== Testing Login API ===")
    
    # 测试1: 被禁用的用户登录
    print("\n=== Test 1: Disabled user login ===")
    test_login("pym", "123456", 401, "用户账号已被禁用")
    
    # 测试2: 正常用户登录
    print("\n=== Test 2: Active user login ===")
    test_login("admin", "123456", 200, None)
    
    # 测试3: 不存在的用户登录
    print("\n=== Test 3: Non-existent user login ===")
    test_login("nonexistent", "123456", 401, "用户名或密码错误")
    
    # 测试4: 密码错误的用户登录
    print("\n=== Test 4: Wrong password login ===")
    test_login("admin", "wrongpassword", 401, "用户名或密码错误")
    
    print("\n=== All tests completed ===")
