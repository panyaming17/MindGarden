"""
测试对话记录API的功能
"""
import httpx
import json
from datetime import datetime

BASE_URL = "http://localhost:8001"

async def test_create_conversation():
    """测试创建新对话"""
    print("测试1: 创建新对话")
    
    url = f"{BASE_URL}/api/conversations"
    data = {
        "title": "工作压力大",
        "emotion": "焦虑",
        "cognition_type": "过度担忧",
        "current_phase": "recorder",
        "active_step": 0,
        "current_role": "记录师"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=data, params={"user_id": "test_user_001"})
        
    print(f"状态码: {response.status_code}")
    print(f"响应: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")
    print()
    
    return response.json()

async def test_get_conversations():
    """测试获取对话列表"""
    print("测试2: 获取对话列表")
    
    url = f"{BASE_URL}/api/conversations"
    params = {
        "page": 1,
        "limit": 10,
        "user_id": "test_user_001"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params)
        
    print(f"状态码: {response.status_code}")
    print(f"响应: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")
    print()

async def test_get_conversation_detail(conversation_id):
    """测试获取对话详情"""
    print("测试3: 获取对话详情")
    
    url = f"{BASE_URL}/api/conversations/{conversation_id}"
    params = {
        "user_id": "test_user_001"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params)
        
    print(f"状态码: {response.status_code}")
    print(f"响应: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")
    print()

async def test_update_conversation(conversation_id):
    """测试更新对话"""
    print("测试4: 更新对话")
    
    url = f"{BASE_URL}/api/conversations/{conversation_id}"
    data = {
        "title": "工作压力大 - 更新",
        "emotion": "焦虑",
        "cognition_type": "过度担忧",
        "current_phase": "analyst",
        "active_step": 1,
        "current_role": "分析师"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.put(url, json=data, params={"user_id": "test_user_001"})
        
    print(f"状态码: {response.status_code}")
    print(f"响应: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")
    print()

async def test_delete_conversation(conversation_id):
    """测试删除对话"""
    print("测试5: 删除对话")
    
    url = f"{BASE_URL}/api/conversations/{conversation_id}"
    
    async with httpx.AsyncClient() as client:
        response = await client.delete(url, params={"user_id": "test_user_001"})
        
    print(f"状态码: {response.status_code}")
    print(f"响应: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")
    print()

async def main():
    """主测试函数"""
    print("开始测试对话记录API...\n")
    
    # 测试1: 创建新对话
    conversation = await test_create_conversation()
    conversation_id = conversation.get("id")
    
    if conversation_id:
        # 测试2: 获取对话列表
        await test_get_conversations()
        
        # 测试3: 获取对话详情
        await test_get_conversation_detail(conversation_id)
        
        # 测试4: 更新对话
        await test_update_conversation(conversation_id)
        
        # 测试5: 删除对话
        await test_delete_conversation(conversation_id)
    
    print("测试完成！")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
