########     基础智能体类       ###########
from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseAgent(ABC):
    """智能体基类，定义所有智能体的通用接口"""
    
    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.created_at = time.time()
        self.active = True
    
    @abstractmethod
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行智能体任务的抽象方法，子类必须实现"""
        pass
    
    def get_agent_info(self) -> Dict[str, Any]:
        """获取智能体基本信息"""
        return {
            "agent_name": self.agent_name,
            "created_at": self.created_at,
            "active": self.active
        }
    
    def deactivate(self):
        """停用智能体"""
        self.active = False
    
    def activate(self):
        """激活智能体"""
        self.active = True

import time