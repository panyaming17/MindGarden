import os
import sys
import asyncio
import aiohttp
from dotenv import load_dotenv
import logging

# 配置日志
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def get_access_token(session, api_key, secret_key):
    """获取百度API的access_token"""
    logger.info("获取access_token...")
    token_url = "https://aip.baidubce.com/oauth/2.0/token"
    params = {
        "grant_type": "client_credentials",
        "client_id": api_key,
        "client_secret": secret_key
    }
    
    async with session.post(token_url, params=params) as token_response:
        token_status = token_response.status
        token_text = await token_response.text()
        logger.info(f"获取token响应: 状态码={token_status}, 内容={token_text}")
        
        if token_status != 200:
            raise Exception(f"获取token失败，状态码: {token_status}, 错误: {token_text}")
        
        import json
        token_data = json.loads(token_text)
        access_token = token_data.get("access_token")
        
        if not access_token:
            raise Exception(f"获取token失败，响应中没有access_token: {token_data}")
        
        logger.info(f"成功获取access_token: {access_token[:20]}...")
        return access_token

async def test_baidu_api_endpoint(session, access_token, base_url, model, messages):
    """测试指定的百度API端点"""
    logger.info(f"测试端点: {base_url}, 模型: {model}")
    
    payload = {
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 100,
        "model": model
    }
    
    url = f"{base_url}?access_token={access_token}"
    
    async with session.post(
        url,
        headers={"Content-Type": "application/json"},
        json=payload,
        timeout=aiohttp.ClientTimeout(total=30)
    ) as api_response:
        api_status = api_response.status
        api_text = await api_response.text()
        logger.info(f"API调用响应: 状态码={api_status}, 内容={api_text}")
        
        if api_status != 200:
            return False, f"状态码: {api_status}, 错误: {api_text}"
        
        import json
        api_data = json.loads(api_text)
        if 'result' in api_data:
            logger.info(f"API调用成功！回复内容: {api_data['result']}")
            return True, api_data['result']
        else:
            error_msg = api_data.get('error_msg', '未知错误')
            return False, f"API调用失败: {error_msg}"

async def test_baidu_api():
    """测试百度千帆API连接"""
    try:
        # 1. 加载环境变量
        logger.info("加载环境变量...")
        load_dotenv()
        
        # 2. 获取基本配置
        api_key = os.getenv("BAIDU_API_KEY")
        secret_key = os.getenv("BAIDU_SECRET_KEY")
        
        logger.info(f"基本配置信息: ")
        logger.info(f"  - api_key: {api_key[:10]}..." if api_key else None)
        logger.info(f"  - secret_key: {secret_key[:10]}..." if secret_key else None)
        
        # 3. 验证基本配置
        if not api_key:
            raise ValueError("未设置BAIDU_API_KEY环境变量")
        if not secret_key:
            raise ValueError("未设置BAIDU_SECRET_KEY环境变量")
        
        # 4. 创建会话
        logger.info("创建HTTP会话...")
        async with aiohttp.ClientSession() as session:
            # 5. 获取access_token
            access_token = await get_access_token(session, api_key, secret_key)
            
            # 6. 测试多个模型和端点组合
            test_cases = [
                # 标准端点
                {
                    "base_url": "https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/completions",
                    "models": ["ERNIE-Bot-4", "ERNIE-Bot-3.5", "ERNIE-Bot", "ernie-3.5-8k"]
                },
                # 可能的其他端点
                {
                    "base_url": "https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/eb-instant",
                    "models": ["ERNIE-Bot-turbo"]
                }
            ]
            
            test_messages = [
                {"role": "user", "content": "你好，我想测试百度API连接，请回复简单的问候语。"}
            ]
            
            success = False
            for test_case in test_cases:
                for model in test_case["models"]:
                    logger.info(f"\n=== 测试组合: 端点={test_case['base_url']}, 模型={model} ===")
                    result, message = await test_baidu_api_endpoint(
                        session, access_token, test_case["base_url"], model, test_messages
                    )
                    
                    if result:
                        logger.info(f"✓ 测试成功！模型: {model}, 端点: {test_case['base_url']}")
                        success = True
                        # 找到可用的组合后可以停止测试
                        return True, f"成功使用模型 {model} 和端点 {test_case['base_url']} 进行API调用"
                    else:
                        logger.info(f"✗ 测试失败: {message}")
            
            if not success:
                raise Exception("所有测试组合都失败了，请检查百度API的权限和配置")
                
    except Exception as e:
        logger.error(f"测试失败: {str(e)}")
        return False, str(e)

if __name__ == "__main__":
    logger.info("开始测试百度API连接...")
    success, result = asyncio.run(test_baidu_api())
    
    if success:
        logger.info(f"测试成功！{result}")
        sys.exit(0)
    else:
        logger.error(f"测试失败，请检查配置和权限: {result}")
        sys.exit(1)