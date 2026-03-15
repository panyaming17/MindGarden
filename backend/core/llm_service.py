"""
大语言模型服务模块
统一封装不同厂商的LLM API调用，提供标准化的接口。
文件所在路径：backend/core/llm_service.py
"""
import os
import json
import asyncio
import logging
import random
from typing import Dict, Any, List, Optional
from enum import Enum
import aiohttp
from tenacity import retry, stop_after_attempt, wait_exponential
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 配置日志
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    handlers=[
                        logging.StreamHandler(),
                    ])
logger = logging.getLogger(__name__)

class LLMProvider(Enum):
    """支持的LLM提供商枚举"""
    DEEPSEEK = "deepseek"
    BAIDU_QIANFAN = "baidu_qianfan"  # 文心一言
    ZHIPU_AI = "zhipu_ai"  # 智谱AI
    MOONSHOT = "moonshot"  # 月之暗面
    CUSTOM = "custom"  # 自定义/本地部署

class LLMService:
    """统一的大语言模型服务"""
    
    def __init__(self, provider: str = None):
        """
        初始化LLM服务
        
        Args:
            provider: 提供商名称，从环境变量LLM_PROVIDER读取或指定
        """
        self.provider = provider or os.getenv("LLM_PROVIDER", "deepseek").lower()   #这一步是为了默认使用deepseek
        self._init_config() # 初始化配置
        self.session = None # 异步HTTP会话，在上下文管理器中初始化
        
        # 检查是否有任何可用的提供商
        if not self.get_available_providers():
            raise ValueError("没有可用的LLM提供商，请检查API密钥配置")
    
    def _init_config(self):
        """初始化各提供商的配置"""
        self.configs = {
            "deepseek": {
                "base_url": os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1"),
                "api_key": os.getenv("DEEPSEEK_API_KEY"),
                "model": os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
                "headers": lambda: {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.configs['deepseek']['api_key']}"
                }
            },
            "baidu_qianfan": {
                "base_url": os.getenv("BAIDU_BASE_URL", "https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/completions"),
                "api_key": os.getenv("BAIDU_API_KEY"),
                "secret_key": os.getenv("BAIDU_SECRET_KEY"),
                "model": os.getenv("BAIDU_MODEL", "ERNIE-Bot-4"),
                "access_token": None,
                "token_expiry": 0
            },
        }
        
        # 验证提供商是否支持
        if self.provider not in self.configs:
            raise ValueError(f"不支持的LLM提供商: {self.provider}")
        
        # 验证当前提供商的API密钥（如果有配置的话）
        config = self.configs[self.provider]
        if config.get("api_key") is None:
            logger.warning(f"当前配置的提供商{self.provider}没有API密钥，将使用可用的提供商")
        
        # 对百度千帆特殊验证secret_key（如果有配置的话）
        if self.provider == "baidu_qianfan" and config.get("secret_key") is None:
            logger.warning("当前配置的提供商baidu_qianfan没有SECRET_KEY，将使用可用的提供商")
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        if self.session:
            await self.session.close()
    
    async def chat_completion(self, 
                             messages: List[Dict[str, str]], 
                             temperature: float = 0.7,
                             max_tokens: int = 2000,
                             json_mode: bool = False,
                             try_all_providers: bool = False) -> str:
        """
        统一的聊天补全接口
        
        Args:
            messages: 消息列表，格式 [{"role": "user/system/assistant", "content": "..."}]
            temperature: 温度参数，控制随机性 (0.0-1.0)
            max_tokens: 最大生成token数
            json_mode: 是否强制JSON输出模式
            try_all_providers: 是否尝试所有可用的提供商（随机顺序），默认为False
            
        Returns:
            LLM返回的文本内容
        """
        if not self.session:
            self.session = aiohttp.ClientSession()
        
        # 获取可用的提供商列表
        available_providers = self.get_available_providers()
        
        if not available_providers:
            raise ValueError("没有可用的LLM提供商，请检查API密钥配置")
        
        # 如果设置了try_all_providers，随机打乱可用提供商列表
        # 否则使用当前配置的提供商
        providers_to_try = []
        if try_all_providers:
            # 随机打乱可用提供商列表
            providers_to_try = available_providers.copy()
            random.shuffle(providers_to_try)
            logger.info(f"将按随机顺序尝试以下提供商: {providers_to_try}")
        else:
            # 只尝试当前配置的提供商
            if self.provider in available_providers:
                providers_to_try = [self.provider]
            else:
                raise ValueError(f"当前配置的提供商 {self.provider} 不可用")
        
        # 遍历所有要尝试的提供商
        exceptions = []
        for provider in providers_to_try:
            try:
                logger.info(f"尝试使用提供商: {provider}")
                if provider == "deepseek":
                    return await self._call_deepseek_api(messages, temperature, max_tokens, json_mode)
                elif provider == "baidu_qianfan":
                    return await self._call_baidu_api(messages, temperature, max_tokens)
                else:
                    raise ValueError(f"提供商 {provider} 尚未实现")
                    
            except aiohttp.ClientError as e:
                error_msg = f"{provider} 网络请求错误: {e}"
                logger.error(error_msg)
                exceptions.append((provider, error_msg))
            except asyncio.TimeoutError:
                error_msg = f"{provider} API请求超时"
                logger.error(error_msg)
                exceptions.append((provider, error_msg))
            except Exception as e:
                error_msg = f"{provider} 调用异常: {type(e).__name__}: {e}"
                logger.error(error_msg)
                exceptions.append((provider, error_msg))
        
        # 如果所有提供商都失败了，抛出异常
        error_messages = [f"{prov}: {msg}" for prov, msg in exceptions]
        raise Exception(f"所有可用的LLM提供商调用都失败了: {'; '.join(error_messages)}")
    
    async def _call_deepseek_api(self, messages: List[Dict[str, str]], 
                                temperature: float, max_tokens: int, 
                                json_mode: bool) -> str:
        """调用DeepSeek API"""
        config = self.configs["deepseek"]
        
        # 确保session已初始化
        if not self.session:
            self.session = aiohttp.ClientSession()
            
        payload = {
            "model": config["model"],
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False
        }
        
        async with self.session.post(
            f"{config['base_url']}/chat/completions",
            headers=config["headers"](),
            json=payload,
            timeout=aiohttp.ClientTimeout(total=30)
        ) as response:
            return await self._parse_deepseek_response(response) # 解析DeepSeek响应 
    
    async def _call_baidu_api(self, messages: List[Dict[str, str]], 
                             temperature: float, max_tokens: int) -> str:
        """调用百度千帆（文心一言）API"""
        config = self.configs["baidu_qianfan"]
        
        # 百度API需要access_token
        access_token = await self._get_baidu_access_token()
        
        # 转换消息格式（百度API格式略有不同）
        baidu_messages = []
        for msg in messages:
            if msg["role"] == "system":
                # 百度API没有system角色，可以将system消息转为user消息
                baidu_messages.append({"role": "user", "content": msg["content"]})
            else:
                baidu_messages.append(msg)
        
        payload = {
            "messages": baidu_messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "model": config["model"]  # 添加模型名称参数
        }
        
        url = f"{config['base_url']}?access_token={access_token}"
        
        async with self.session.post(
            url,
            headers={"Content-Type": "application/json"},
            json=payload,
            timeout=aiohttp.ClientTimeout(total=30) 
        ) as response:
            return await self._parse_baidu_response(response)
    
    async def _get_baidu_access_token(self) -> str:
        """获取百度API的access_token（有效期30天）"""
        config = self.configs["baidu_qianfan"]
        
        # 简单缓存机制
        import time
        current_time = time.time()
        if config.get("access_token") and config.get("token_expiry", 0) > current_time:
            return config["access_token"]
        
        # 确保session已初始化
        if not self.session:
            self.session = aiohttp.ClientSession()
        
        # 获取新的token
        token_url = "https://aip.baidubce.com/oauth/2.0/token"
        params = {
            "grant_type": "client_credentials",
            "client_id": config["api_key"],
            "client_secret": config["secret_key"]
        }
        
        async with self.session.post(token_url, params=params) as response:
            if response.status == 200:
                token_data = await response.json()
                access_token = token_data.get("access_token")
                expires_in = token_data.get("expires_in", 2592000)  # 默认30天
                
                # 缓存token
                config["access_token"] = access_token
                config["token_expiry"] = current_time + expires_in - 600  # 提前10分钟过期
                
                return access_token
            else:
                raise Exception(f"获取百度access_token失败: {await response.text()}")

    #解析deepseek响应
    async def _parse_deepseek_response(self, response: aiohttp.ClientResponse) -> str:
        """解析DeepSeek API的响应"""
        if response.status == 200:
            result = await response.json()
            if 'choices' in result and len(result['choices']) > 0:
                return result['choices'][0]['message']['content'].strip()
            else:
                raise ValueError(f"无法解析DeepSeek API响应: {result}")
        else:
            error_text = await response.text()
            raise Exception(f"DeepSeek API调用失败，状态码: {response.status}, 错误: {error_text}")

    #解析百度千帆API响应
    async def _parse_baidu_response(self, response: aiohttp.ClientResponse) -> str:
        """解析百度千帆API的响应"""
        if response.status == 200:
            result = await response.json()
            if 'result' in result:
                return result['result'].strip()
            else:
                error_msg = result.get('error_msg', '未知错误')
                raise Exception(f"百度API错误: {error_msg}")
        else:
            error_text = await response.text()
            raise Exception(f"API调用失败，状态码: {response.status}, 错误: {error_text}")
    
    def get_available_providers(self) -> List[str]:
        """获取当前配置可用的提供商列表"""
        available = []
        for provider, config in self.configs.items():
            if config.get("api_key"):
                available.append(provider)
        return available

# 全局LLM服务实例（单例模式）
_llm_service_instance = None

async def get_llm_service() -> LLMService:
    """获取LLM服务实例（依赖注入友好）"""
    global _llm_service_instance # 全局变量，用于存储单例实例
    if _llm_service_instance is None:
        _llm_service_instance = LLMService()
        await _llm_service_instance.__aenter__()
    return _llm_service_instance

async def close_llm_service():
    """关闭LLM服务"""
    global _llm_service_instance
    if _llm_service_instance:
        await _llm_service_instance.__aexit__(None, None, None)
        _llm_service_instance = None