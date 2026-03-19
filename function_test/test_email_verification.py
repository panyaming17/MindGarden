import asyncio
import httpx
import random
import string

# 生成6位数字验证码
def generate_test_code():
    return ''.join(random.choices(string.digits, k=6))

async def test_email_verification():
    """测试邮箱验证功能"""
    base_url = "http://localhost:8001/api"
    test_email = "test@example.com"
    test_username = "testuser123"
    test_password = "Password123!"
    new_password = "NewPassword123!"
    
    async with httpx.AsyncClient() as client:
        print("=== 开始测试邮箱验证功能 ===")
        
        # 1. 测试发送注册验证码
        print("\n1. 测试发送注册验证码...")
        try:
            response = await client.post(
                f"{base_url}/auth/send-register-code",
                json={"email": test_email}
            )
            print(f"状态码: {response.status_code}")
            print(f"响应: {response.json()}")
        except Exception as e:
            print(f"错误: {str(e)}")
        
        # 2. 测试注册新用户
        print("\n2. 测试注册新用户...")
        # 由于我们使用了内存存储来模拟Redis，所以我们可以直接生成验证码
        test_code = generate_test_code()
        print(f"使用测试验证码: {test_code}")
        try:
            # 手动设置验证码到内存存储（这里需要修改代码来支持，所以先注释掉）
            # 我们可以直接使用一个固定的验证码
            fixed_code = "123456"
            response = await client.post(
                f"{base_url}/auth/register",
                json={
                    "username": test_username,
                    "email": test_email,
                    "code": fixed_code,
                    "password": test_password
                }
            )
            print(f"状态码: {response.status_code}")
            print(f"响应: {response.json()}")
        except Exception as e:
            print(f"错误: {str(e)}")
        
        # 3. 测试登录
        print("\n3. 测试登录...")
        try:
            response = await client.post(
                f"{base_url}/auth/login",
                json={
                    "username": test_username,
                    "password": test_password
                }
            )
            print(f"状态码: {response.status_code}")
            if response.status_code == 200:
                token = response.json()["access_token"]
                print("登录成功，获取到令牌")
                print(f"令牌: {token[:20]}...")
            else:
                print(f"响应: {response.json()}")
        except Exception as e:
            print(f"错误: {str(e)}")
        
        # 4. 测试发送重置密码验证码
        print("\n4. 测试发送重置密码验证码...")
        try:
            response = await client.post(
                f"{base_url}/auth/send-reset-code",
                json={
                    "username": test_username,
                    "email": test_email
                }
            )
            print(f"状态码: {response.status_code}")
            print(f"响应: {response.json()}")
        except Exception as e:
            print(f"错误: {str(e)}")
        
        # 5. 测试重置密码
        print("\n5. 测试重置密码...")
        try:
            fixed_code = "123456"
            response = await client.post(
                f"{base_url}/auth/reset-password",
                json={
                    "username": test_username,
                    "email": test_email,
                    "code": fixed_code,
                    "new_password": new_password
                }
            )
            print(f"状态码: {response.status_code}")
            print(f"响应: {response.json()}")
        except Exception as e:
            print(f"错误: {str(e)}")
        
        # 6. 测试使用新密码登录
        print("\n6. 测试使用新密码登录...")
        try:
            response = await client.post(
                f"{base_url}/auth/login",
                json={
                    "username": test_username,
                    "password": new_password
                }
            )
            print(f"状态码: {response.status_code}")
            if response.status_code == 200:
                token = response.json()["access_token"]
                print("登录成功，获取到令牌")
                print(f"令牌: {token[:20]}...")
            else:
                print(f"响应: {response.json()}")
        except Exception as e:
            print(f"错误: {str(e)}")
        
        # 7. 测试验证令牌
        print("\n7. 测试验证令牌...")
        try:
            response = await client.get(
                f"{base_url}/auth/verify",
                headers={"Authorization": f"Bearer {token}"}
            )
            print(f"状态码: {response.status_code}")
            print(f"响应: {response.json()}")
        except Exception as e:
            print(f"错误: {str(e)}")
        
        # 8. 测试获取当前用户信息
        print("\n8. 测试获取当前用户信息...")
        try:
            response = await client.get(
                f"{base_url}/users/me",
                headers={"Authorization": f"Bearer {token}"}
            )
            print(f"状态码: {response.status_code}")
            print(f"响应: {response.json()}")
        except Exception as e:
            print(f"错误: {str(e)}")
        
        # 9. 测试更新当前用户信息
        print("\n9. 测试更新当前用户信息...")
        try:
            new_email = "new_test@example.com"
            response = await client.put(
                f"{base_url}/users/me",
                headers={"Authorization": f"Bearer {token}"},
                json={"email": new_email}
            )
            print(f"状态码: {response.status_code}")
            print(f"响应: {response.json()}")
        except Exception as e:
            print(f"错误: {str(e)}")
        
        print("\n=== 测试完成 ===")

if __name__ == "__main__":
    asyncio.run(test_email_verification())
