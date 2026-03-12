#!/usr/bin/env python3
"""
测试对话测试控制接口
"""

import asyncio
import aiohttp
import json

BASE_URL = "http://localhost:8001"

async def test_start_test():
    """测试开始测试接口"""
    print("1. 测试开始测试接口...")
    async with aiohttp.ClientSession() as session:
        start_url = f"{BASE_URL}/api/conversations/start-test"
        data = {
            "session_id": "test_session_123"
        }
        
        async with session.post(start_url, json=data) as response:
            print(f"   开始测试状态: {response.status}")
            try:
                result = await response.json()
                print(f"   响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
                if response.status == 200:
                    print("   开始测试成功")
                    return result.get("data", {}).get("session_id")
                else:
                    print("   开始测试失败")
                    return None
            except Exception as e:
                error_text = await response.text()
                print(f"   错误信息: {error_text}")
                print(f"   解析错误: {str(e)}")
                return None

async def test_pause_test(session_id):
    """测试暂停测试接口"""
    if not session_id:
        print("获取会话ID失败，无法测试暂停测试接口")
        return
    
    print("\n2. 测试暂停测试接口...")
    async with aiohttp.ClientSession() as session:
        pause_url = f"{BASE_URL}/api/conversations/pause-test"
        data = {
            "session_id": session_id
        }
        
        async with session.post(pause_url, json=data) as response:
            print(f"   暂停测试状态: {response.status}")
            try:
                result = await response.json()
                print(f"   响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
                if response.status == 200:
                    print("   暂停测试成功")
                else:
                    print("   暂停测试失败")
            except Exception as e:
                error_text = await response.text()
                print(f"   错误信息: {error_text}")
                print(f"   解析错误: {str(e)}")

async def test_start_test_with_invalid_session():
    """测试使用无效会话ID开始测试"""
    print("\n3. 测试使用空会话ID开始测试...")
    async with aiohttp.ClientSession() as session:
        start_url = f"{BASE_URL}/api/conversations/start-test"
        data = {
            "session_id": ""
        }
        
        async with session.post(start_url, json=data) as response:
            print(f"   状态: {response.status}")
            try:
                result = await response.json()
                print(f"   响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
            except Exception as e:
                error_text = await response.text()
                print(f"   错误信息: {error_text}")
                print(f"   解析错误: {str(e)}")

async def test_pause_test_with_invalid_session():
    """测试使用无效会话ID暂停测试"""
    print("\n4. 测试使用无效会话ID暂停测试...")
    async with aiohttp.ClientSession() as session:
        pause_url = f"{BASE_URL}/api/conversations/pause-test"
        data = {
            "session_id": "non_existent_session"
        }
        
        async with session.post(pause_url, json=data) as response:
            print(f"   状态: {response.status}")
            try:
                result = await response.json()
                print(f"   响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
            except Exception as e:
                error_text = await response.text()
                print(f"   错误信息: {error_text}")
                print(f"   解析错误: {str(e)}")

async def main():
    """主测试函数"""
    print("开始测试对话测试控制接口...")
    
    try:
        # 测试开始测试
        session_id = await test_start_test()
        
        # 测试暂停测试
        await test_pause_test(session_id)
        
        # 测试使用无效会话ID开始测试
        await test_start_test_with_invalid_session()
        
        # 测试使用无效会话ID暂停测试
        await test_pause_test_with_invalid_session()
        
        print("\n=== 测试完成 ===")
        
    except Exception as e:
        print(f"测试过程中出错: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
