#!/usr/bin/env python3
"""
测试LLM模型的随机选择功能
验证当某个模型调用失败时，是否会自动尝试下一个模型
"""
import os
import asyncio
import logging
import sys

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.core.llm_service import LLMService

# 配置日志
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    handlers=[
                        logging.StreamHandler(),
                    ])
logger = logging.getLogger(__name__)

async def test_random_model_selection():
    """测试随机模型选择功能"""
    logger.info("=== 开始测试随机模型选择功能 ===")
    
    async with LLMService() as llm_service:
        # 测试1: 正常调用，使用当前配置的提供商
        logger.info("\n--- 测试1: 正常调用（不使用try_all_providers） ---")
        try:
            result = await llm_service.chat_completion(
                messages=[{"role": "user", "content": "你好，你是谁？"}],
                try_all_providers=False
            )
            logger.info(f"调用成功，结果: {result[:100]}...")
        except Exception as e:
            logger.error(f"调用失败: {e}")
    
    async with LLMService() as llm_service:
        # 测试2: 尝试所有可用的提供商
        logger.info("\n--- 测试2: 尝试所有可用的提供商 ---")
        try:
            result = await llm_service.chat_completion(
                messages=[{"role": "user", "content": "你好，你是谁？"}],
                try_all_providers=True
            )
            logger.info(f"调用成功，结果: {result[:100]}...")
        except Exception as e:
            logger.error(f"所有提供商都调用失败: {e}")
    
    logger.info("\n=== 测试完成 ===")

if __name__ == "__main__":
    asyncio.run(test_random_model_selection())