import httpx
import json

BASE_URL = "http://localhost:8001"

async def test_user_login():
    """测试用户111的登录情况"""
    print("测试用户111的登录情况...")
    
    # 测试登录
    url = f"{BASE_URL}/api/auth/login"
    data = {
        "username": "111",
        "password": "123456"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, data=data)
        
    print(f"登录请求状态码: {response.status_code}")
    print(f"登录请求响应: {response.text}")
    print()
    
    # 检查用户是否存在（通过尝试重置密码）
    reset_url = f"{BASE_URL}/api/auth/reset-password"
    reset_data = {
        "username": "111",
        "new_password": "123456"
    }
    
    async with httpx.AsyncClient() as client:
        reset_response = await client.post(reset_url, json=reset_data)
        
    print(f"重置密码请求状态码: {reset_response.status_code}")
    print(f"重置密码请求响应: {reset_response.text}")
    print()
    
    # 尝试注册用户（如果不存在）
    register_url = f"{BASE_URL}/api/auth/register"
    register_data = {
        "username": "111",
        "password": "123456"
    }
    
    async with httpx.AsyncClient() as client:
        register_response = await client.post(register_url, json=register_data)
        
    print(f"注册请求状态码: {register_response.status_code}")
    print(f"注册请求响应: {register_response.text}")
    print()
    
    # 再次尝试登录
    async with httpx.AsyncClient() as client:
        response = await client.post(url, data=data)
        
    print(f"再次登录请求状态码: {response.status_code}")
    print(f"再次登录请求响应: {response.text}")
    print()

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_user_login())
