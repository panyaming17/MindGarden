"""
测试认证相关的API端点
"""
import httpx
import json
from datetime import datetime

BASE_URL = "http://localhost:8001"

async def test_register():
    """测试注册新用户"""
    print("测试1: 注册新用户")
    
    url = f"{BASE_URL}/api/auth/register"
    data = {
        "username": "testuser456",
        "password": "Password123!"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=data)
        
    print(f"状态码: {response.status_code}")
    print(f"响应内容: {response.text}")
    try:
        print(f"响应JSON: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")
    except Exception as e:
        print(f"解析JSON失败: {str(e)}")
    print()
    
    return response.json()

async def test_login():
    """测试用户登录"""
    print("测试2: 用户登录")
    
    url = f"{BASE_URL}/api/auth/login"
    data = {
        "username": "testuser456",
        "password": "Password123!"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, data=data)
        
    print(f"状态码: {response.status_code}")
    print(f"响应内容: {response.text}")
    try:
        print(f"响应JSON: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")
    except Exception as e:
        print(f"解析JSON失败: {str(e)}")
    print()
    
    return response.json()

async def test_verify_token(token):
    """测试验证令牌"""
    print("测试3: 验证令牌")
    
    url = f"{BASE_URL}/api/auth/verify"
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)
        
    print(f"状态码: {response.status_code}")
    print(f"响应: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")
    print()

async def test_get_current_user(token):
    """测试获取当前用户信息"""
    print("测试4: 获取当前用户信息")
    
    url = f"{BASE_URL}/api/users/me"
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)
        
    print(f"状态码: {response.status_code}")
    print(f"响应: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")
    print()

async def test_update_user(token):
    """测试更新用户信息"""
    print("测试5: 更新用户信息")
    
    url = f"{BASE_URL}/api/users/me"
    headers = {
        "Authorization": f"Bearer {token}"
    }
    data = {}
    
    async with httpx.AsyncClient() as client:
        response = await client.put(url, json=data, headers=headers)
        
    print(f"状态码: {response.status_code}")
    print(f"响应: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")
    print()

async def test_reset_password():
    """测试重置密码"""
    print("测试6: 重置密码")
    
    url = f"{BASE_URL}/api/auth/reset-password"
    data = {
        "username": "testuser456",
        "new_password": "NewPassword123!"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=data)
        
    print(f"状态码: {response.status_code}")
    print(f"响应: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")
    print()

async def test_login_with_new_password():
    """测试使用新密码登录"""
    print("测试7: 使用新密码登录")
    
    url = f"{BASE_URL}/api/auth/login"
    data = {
        "username": "testuser456",
        "password": "NewPassword123!"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, data=data)
        
    print(f"状态码: {response.status_code}")
    print(f"响应: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")
    print()

async def main():
    """主测试函数"""
    print("开始测试认证API...\n")
    
    try:
        # 测试1: 注册新用户
        await test_register()
        
        # 测试2: 用户登录
        login_response = await test_login()
        access_token = login_response.get("access_token")
        
        if access_token:
            # 测试3: 验证令牌
            await test_verify_token(access_token)
            
            # 测试4: 获取当前用户信息
            await test_get_current_user(access_token)
            
            # 测试5: 更新用户信息
            await test_update_user(access_token)
        
        # 测试6: 重置密码
        await test_reset_password()
        
        # 测试7: 使用新密码登录
        await test_login_with_new_password()
        
    except Exception as e:
        print(f"测试过程中出现错误: {str(e)}")
    
    print("测试完成！")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
