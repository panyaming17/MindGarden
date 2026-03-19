#!/usr/bin/env python3
"""
测试管理员创建用户接口
"""

import asyncio
import aiohttp
import json

BASE_URL = "http://localhost:8001"

async def get_admin_token():
    """获取管理员令牌"""
    print("1. 获取管理员令牌...")
    async with aiohttp.ClientSession() as session:
        login_url = f"{BASE_URL}/api/auth/login"
        data = {
            "username": "admin",
            "password": "123456"
        }
        
        async with session.post(login_url, json=data) as response:
            result = await response.json()
            print(f"   登录状态: {response.status}")
            if response.status == 200:
                token = result.get("access_token")
                print(f"   获取令牌成功: {token[:20]}...")
                return token
            else:
                print(f"   登录失败: {result}")
                return None

async def test_create_user(token):
    """测试创建用户接口"""
    if not token:
        print("获取令牌失败，无法测试创建用户接口")
        return
    
    print("\n2. 测试创建用户接口...")
    async with aiohttp.ClientSession() as session:
        create_url = f"{BASE_URL}/api/admin/users"
        headers = {
            "Authorization": f"Bearer {token}"
        }
        
        # 测试创建普通用户
        user_data = {
            "username": "test_user_123",
            "email": "test_user_123@example.com",
            "password": "Test@123",
            "role": "user"
        }
        
        async with session.post(create_url, json=user_data, headers=headers) as response:
            print(f"   创建普通用户状态: {response.status}")
            try:
                result = await response.json()
                if response.status == 201:
                    print(f"   创建用户成功")
                    print(f"   用户名: {result.get('username')}")
                    print(f"   邮箱: {result.get('email')}")
                    print(f"   角色: {result.get('role')}")
                    print(f"   用户ID: {result.get('id')}")
                else:
                    print(f"   创建用户失败: {result}")
            except Exception as e:
                error_text = await response.text()
                print(f"   错误信息: {error_text}")
                print(f"   解析错误: {str(e)}")

async def test_create_admin_user(token):
    """测试创建管理员用户接口"""
    if not token:
        print("获取令牌失败，无法测试创建管理员用户接口")
        return
    
    print("\n3. 测试创建管理员用户接口...")
    async with aiohttp.ClientSession() as session:
        create_url = f"{BASE_URL}/api/admin/users"
        headers = {
            "Authorization": f"Bearer {token}"
        }
        
        # 测试创建管理员用户
        user_data = {
            "username": "test_admin_123",
            "email": "test_admin_123@example.com",
            "password": "Test@123",
            "role": "admin"
        }
        
        async with session.post(create_url, json=user_data, headers=headers) as response:
            print(f"   创建管理员用户状态: {response.status}")
            try:
                result = await response.json()
                if response.status == 201:
                    print(f"   创建管理员用户成功")
                    print(f"   用户名: {result.get('username')}")
                    print(f"   邮箱: {result.get('email')}")
                    print(f"   角色: {result.get('role')}")
                    print(f"   用户ID: {result.get('id')}")
                else:
                    print(f"   创建管理员用户失败: {result}")
            except Exception as e:
                error_text = await response.text()
                print(f"   错误信息: {error_text}")
                print(f"   解析错误: {str(e)}")

async def test_get_users(token):
    """测试获取用户列表接口"""
    if not token:
        print("获取令牌失败，无法测试获取用户列表接口")
        return
    
    print("\n4. 测试获取用户列表接口...")
    async with aiohttp.ClientSession() as session:
        users_url = f"{BASE_URL}/api/admin/users"
        headers = {
            "Authorization": f"Bearer {token}"
        }
        
        async with session.get(users_url, headers=headers) as response:
            print(f"   获取用户列表状态: {response.status}")
            try:
                result = await response.json()
                if response.status == 200:
                    print(f"   获取用户列表成功")
                    print(f"   总用户数: {result.get('total')}")
                    print(f"   每页数量: {result.get('per_page')}")
                    print(f"   当前页码: {result.get('page')}")
                    print("   用户列表:")
                    for user in result.get('items', []):
                        print(f"     - {user.get('username')} ({user.get('role')}) - {user.get('email')}")
                else:
                    print(f"   获取用户列表失败: {result}")
            except Exception as e:
                error_text = await response.text()
                print(f"   错误信息: {error_text}")
                print(f"   解析错误: {str(e)}")

async def main():
    """主测试函数"""
    print("开始测试管理员创建用户接口...")
    
    try:
        # 获取管理员令牌
        token = await get_admin_token()
        
        # 测试创建普通用户
        await test_create_user(token)
        
        # 测试创建管理员用户
        await test_create_admin_user(token)
        
        # 测试获取用户列表
        await test_get_users(token)
        
        print("\n=== 测试完成 ===")
        
    except Exception as e:
        print(f"测试过程中出错: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
