import httpx
import json

BASE_URL = "http://localhost:8001"

async def test_login_formats():
    """测试不同格式的登录请求"""
    print("测试不同格式的登录请求...")
    print("=" * 50)
    
    # 测试1: JSON格式的登录请求
    print("\n测试1: JSON格式的登录请求")
    url = f"{BASE_URL}/api/auth/login"
    json_data = {
        "username": "111",
        "password": "123456"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=json_data)
        
    print(f"状态码: {response.status_code}")
    print(f"响应: {response.text}")
    
    # 测试2: 表单格式的登录请求
    print("\n测试2: 表单格式的登录请求")
    form_data = {
        "username": "111",
        "password": "123456"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, data=form_data)
        
    print(f"状态码: {response.status_code}")
    print(f"响应: {response.text}")
    
    print("\n" + "=" * 50)
    print("测试完成！")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_login_formats())
