"""
预警WebSocket管理器 - 处理所有WebSocket连接和消息推送
"""
from typing import Dict, List, Optional
from datetime import datetime
from fastapi import WebSocket, WebSocketDisconnect


class AlertWebSocketManager:
    """预警WebSocket连接管理器"""
    
    def __init__(self):
        # 存储用户ID到WebSocket连接列表的映射
        self.active_connections: Dict[str, List[WebSocket]] = {}
    
    async def connect(self, user_id: str, websocket: WebSocket) -> bool:
        """
        建立WebSocket连接
        
        Args:
            user_id: 用户ID
            websocket: WebSocket连接对象
            
        Returns:
            bool: 连接是否成功
        """
        try:
            await websocket.accept()
            
            # 初始化用户的连接列表
            if user_id not in self.active_connections:
                self.active_connections[user_id] = []
            
            self.active_connections[user_id].append(websocket)
            
            # 发送连接成功消息
            await self._send_message(websocket, {
                "type": "connected",
                "timestamp": datetime.utcnow().isoformat(),
                "message": "WebSocket连接成功"
            })
            
            return True
        except Exception as e:
            print(f"WebSocket连接失败: {e}")
            return False
    
    async def disconnect(self, user_id: str, websocket: WebSocket):
        """
        断开WebSocket连接
        
        Args:
            user_id: 用户ID
            websocket: WebSocket连接对象
        """
        if user_id in self.active_connections:
            if websocket in self.active_connections[user_id]:
                self.active_connections[user_id].remove(websocket)
            
            # 如果用户没有活跃连接了，清理该用户的条目
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
    
    async def _send_message(self, websocket: WebSocket, message: dict) -> bool:
        """
        向单个WebSocket连接发送消息
        
        Args:
            websocket: WebSocket连接对象
            message: 消息内容
            
        Returns:
            bool: 发送是否成功
        """
        try:
            await websocket.send_json(message)
            return True
        except Exception as e:
            print(f"发送WebSocket消息失败: {e}")
            return False
    
    async def push_to_user(self, user_id: str, message: dict) -> int:
        """
        向指定用户的所有连接推送消息
        
        Args:
            user_id: 用户ID
            message: 消息内容
            
        Returns:
            int: 成功发送的连接数
        """
        if user_id not in self.active_connections:
            return 0
        
        success_count = 0
        disconnected = []
        
        for websocket in self.active_connections[user_id]:
            if await self._send_message(websocket, message):
                success_count += 1
            else:
                disconnected.append(websocket)
        
        # 清理断开的连接
        for websocket in disconnected:
            await self.disconnect(user_id, websocket)
        
        return success_count
    
    # ==================== 特定类型的消息推送 ====================
    
    async def push_new_alert(self, user_id: str, alert_data: dict) -> int:
        """
        推送新增预警消息
        
        Args:
            user_id: 用户ID
            alert_data: 预警数据
            
        Returns:
            int: 成功发送的连接数
        """
        message = {
            "type": "new_alert",
            "timestamp": datetime.utcnow().isoformat(),
            "data": alert_data
        }
        return await self.push_to_user(user_id, message)
    
    async def push_alert_update(self, user_id: str, alert_id: str, update_data: dict) -> int:
        """
        推送预警更新消息（如确认状态变更）
        
        Args:
            user_id: 用户ID
            alert_id: 预警ID
            update_data: 更新的数据
            
        Returns:
            int: 成功发送的连接数
        """
        message = {
            "type": "update_alert",
            "timestamp": datetime.utcnow().isoformat(),
            "data": {
                "id": alert_id,
                **update_data
            }
        }
        return await self.push_to_user(user_id, message)
    
    async def push_alert_delete(self, user_id: str, alert_id: str) -> int:
        """
        推送预警删除消息
        
        Args:
            user_id: 用户ID
            alert_id: 预警ID
            
        Returns:
            int: 成功发送的连接数
        """
        message = {
            "type": "delete_alert",
            "timestamp": datetime.utcnow().isoformat(),
            "data": {
                "id": alert_id
            }
        }
        return await self.push_to_user(user_id, message)
    
    async def push_batch_update(self, user_id: str, alerts: List[dict]) -> int:
        """
        推送批量更新消息（全量刷新）
        
        Args:
            user_id: 用户ID
            alerts: 预警列表
            
        Returns:
            int: 成功发送的连接数
        """
        message = {
            "type": "batch_update",
            "timestamp": datetime.utcnow().isoformat(),
            "data": {
                "alerts": alerts
            }
        }
        return await self.push_to_user(user_id, message)
    
    async def send_ping(self, user_id: str) -> int:
        """
        发送心跳消息
        
        Args:
            user_id: 用户ID
            
        Returns:
            int: 成功发送的连接数
        """
        message = {
            "type": "ping",
            "timestamp": datetime.utcnow().isoformat()
        }
        return await self.push_to_user(user_id, message)
    
    # ==================== 连接管理辅助方法 ====================
    
    def get_user_connections(self, user_id: str) -> List[WebSocket]:
        """获取用户的所有活跃连接"""
        return self.active_connections.get(user_id, [])
    
    def is_user_connected(self, user_id: str) -> bool:
        """检查用户是否有活跃连接"""
        return user_id in self.active_connections and len(self.active_connections[user_id]) > 0
    
    def get_connected_users(self) -> List[str]:
        """获取所有已连接的用户ID列表"""
        return list(self.active_connections.keys())
    
    def get_connection_count(self) -> int:
        """获取总连接数"""
        return sum(len(connections) for connections in self.active_connections.values())


# 全局WebSocket管理器实例
alert_ws_manager = AlertWebSocketManager()
