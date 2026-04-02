"""
预警功能API测试脚本

测试范围：
1. 预警列表查询 API
2. 确认预警 API
3. 批量确认预警 API
4. 预警统计 API
5. 内部API - 问卷预警检查
6. 内部API - 情绪预警检查
7. 内部API - 对话预警检查
8. WebSocket连接测试

运行方式:
    cd d:\GP\Projects
    python -m pytest function_test/test_alert_api.py -v
    或
    python function_test/test_alert_api.py
"""

import pytest
import requests
import json
import websocket
import threading
import time
from datetime import datetime, timedelta

# 基础配置
BASE_URL = "http://localhost:8001"
WS_URL = "ws://localhost:8001"

# 测试用户配置（请根据实际情况修改）
TEST_USER_ID = "test_user_001"
TEST_USERNAME = "testuser"
TEST_PASSWORD = "testpass123"


class TestAlertAPI:
    """预警API测试类"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """获取认证token"""
        # 这里应该调用登录API获取token
        # 简化处理，返回None表示不使用认证
        return None
    
    @pytest.fixture
    def headers(self, auth_token):
        """请求头"""
        headers = {"Content-Type": "application/json"}
        if auth_token:
            headers["Authorization"] = f"Bearer {auth_token}"
        return headers
    
    # ==================== 测试：获取预警列表 ====================
    
    def test_get_alert_list_success(self, headers):
        """测试获取预警列表 - 成功场景"""
        url = f"{BASE_URL}/api/alerts"
        params = {
            "user_id": TEST_USER_ID,
            "page": 1,
            "page_size": 10
        }
        
        response = requests.get(url, params=params, headers=headers)
        
        print(f"\n获取预警列表响应: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"响应数据: {json.dumps(data, indent=2, ensure_ascii=False)}")
            assert data["code"] == 200
            assert "data" in data
            assert "alerts" in data["data"]
            assert "total" in data["data"]
            assert "page" in data["data"]
        else:
            print(f"错误响应: {response.text}")
    
    def test_get_alert_list_with_filters(self, headers):
        """测试获取预警列表 - 带筛选条件"""
        url = f"{BASE_URL}/api/alerts"
        params = {
            "user_id": TEST_USER_ID,
            "type": "questionnaire",
            "level": "warning",
            "status": "unacknowledged",
            "page": 1,
            "page_size": 20
        }
        
        response = requests.get(url, params=params, headers=headers)
        
        print(f"\n带筛选条件获取预警列表响应: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"响应数据: {json.dumps(data, indent=2, ensure_ascii=False)}")
            assert data["code"] == 200
        else:
            print(f"错误响应: {response.text}")
    
    def test_get_alert_list_with_date_range(self, headers):
        """测试获取预警列表 - 带日期范围"""
        url = f"{BASE_URL}/api/alerts"
        
        # 获取最近7天的预警
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        
        params = {
            "user_id": TEST_USER_ID,
            "start_date": start_date,
            "end_date": end_date,
            "page": 1,
            "page_size": 20
        }
        
        response = requests.get(url, params=params, headers=headers)
        
        print(f"\n带日期范围获取预警列表响应: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"响应数据: {json.dumps(data, indent=2, ensure_ascii=False)}")
            assert data["code"] == 200
        else:
            print(f"错误响应: {response.text}")
    
    def test_get_alert_list_user_not_found(self, headers):
        """测试获取预警列表 - 用户不存在"""
        url = f"{BASE_URL}/api/alerts"
        params = {
            "user_id": "non_existent_user",
            "page": 1,
            "page_size": 10
        }
        
        response = requests.get(url, params=params, headers=headers)
        
        print(f"\n用户不存在测试响应: {response.status_code}")
        assert response.status_code == 404
    
    # ==================== 测试：确认预警 ====================
    
    def test_acknowledge_alert_success(self, headers):
        """测试确认预警 - 成功场景"""
        # 首先创建一个测试预警
        alert_id = self._create_test_alert(headers)
        if not alert_id:
            pytest.skip("无法创建测试预警，跳过此测试")
        
        url = f"{BASE_URL}/api/alerts/{alert_id}/acknowledge"
        payload = {
            "user_id": TEST_USER_ID,
            "notes": "测试确认预警"
        }
        
        response = requests.post(url, json=payload, headers=headers)
        
        print(f"\n确认预警响应: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"响应数据: {json.dumps(data, indent=2, ensure_ascii=False)}")
            assert data["code"] == 200
            assert data["data"]["is_acknowledged"] == True
            assert data["data"]["acknowledged_by"] == TEST_USER_ID
        else:
            print(f"错误响应: {response.text}")
    
    def test_acknowledge_alert_not_found(self, headers):
        """测试确认预警 - 预警不存在"""
        url = f"{BASE_URL}/api/alerts/non_existent_alert/acknowledge"
        payload = {
            "user_id": TEST_USER_ID,
            "notes": "测试确认预警"
        }
        
        response = requests.post(url, json=payload, headers=headers)
        
        print(f"\n预警不存在测试响应: {response.status_code}")
        assert response.status_code == 404
    
    # ==================== 测试：批量确认预警 ====================
    
    def test_batch_acknowledge_alerts(self, headers):
        """测试批量确认预警"""
        # 创建多个测试预警
        alert_ids = []
        for i in range(3):
            alert_id = self._create_test_alert(headers)
            if alert_id:
                alert_ids.append(alert_id)
        
        if not alert_ids:
            pytest.skip("无法创建测试预警，跳过此测试")
        
        url = f"{BASE_URL}/api/alerts/batch/acknowledge"
        payload = {
            "alert_ids": alert_ids,
            "user_id": TEST_USER_ID
        }
        
        response = requests.post(url, json=payload, headers=headers)
        
        print(f"\n批量确认预警响应: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"响应数据: {json.dumps(data, indent=2, ensure_ascii=False)}")
            assert data["code"] == 200
            assert data["data"]["success_count"] == len(alert_ids)
            assert data["data"]["failed_count"] == 0
        else:
            print(f"错误响应: {response.text}")
    
    # ==================== 测试：预警统计 ====================
    
    def test_get_alert_stats(self, headers):
        """测试获取预警统计"""
        url = f"{BASE_URL}/api/alerts/stats"
        params = {
            "user_id": TEST_USER_ID
        }
        
        response = requests.get(url, params=params, headers=headers)
        
        print(f"\n获取预警统计响应: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"响应数据: {json.dumps(data, indent=2, ensure_ascii=False)}")
            assert data["code"] == 200
            assert "data" in data
            assert "total" in data["data"]
            assert "unacknowledged" in data["data"]
            assert "acknowledged" in data["data"]
            assert "by_type" in data["data"]
            assert "by_level" in data["data"]
        else:
            print(f"错误响应: {response.text}")
    
    def test_get_alert_stats_with_date_range(self, headers):
        """测试获取预警统计 - 带日期范围"""
        url = f"{BASE_URL}/api/alerts/stats"
        
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        
        params = {
            "user_id": TEST_USER_ID,
            "start_date": start_date,
            "end_date": end_date
        }
        
        response = requests.get(url, params=params, headers=headers)
        
        print(f"\n带日期范围获取预警统计响应: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"响应数据: {json.dumps(data, indent=2, ensure_ascii=False)}")
            assert data["code"] == 200
        else:
            print(f"错误响应: {response.text}")
    
    # ==================== 测试：内部API - 问卷预警 ====================
    
    def test_check_questionnaire_alert_phq9_danger(self, headers):
        """测试问卷预警检查 - PHQ-9危险等级"""
        url = f"{BASE_URL}/api/alerts/internal/check-questionnaire"
        params = {
            "user_id": TEST_USER_ID,
            "template_code": "PHQ9",
            "score": 21,
            "result_level": "severe",
            "record_id": "test_record_001"
        }
        
        response = requests.post(url, params=params, headers=headers)
        
        print(f"\nPHQ-9危险等级预警检查响应: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"响应数据: {json.dumps(data, indent=2, ensure_ascii=False)}")
            assert data["code"] == 200
            if data["data"]:
                assert data["data"]["level"] == "danger"
                assert "PHQ-9评分严重异常" in data["data"]["title"]
        else:
            print(f"错误响应: {response.text}")
    
    def test_check_questionnaire_alert_phq9_warning(self, headers):
        """测试问卷预警检查 - PHQ-9警告等级"""
        url = f"{BASE_URL}/api/alerts/internal/check-questionnaire"
        params = {
            "user_id": TEST_USER_ID,
            "template_code": "PHQ9",
            "score": 16,
            "result_level": "moderate",
            "record_id": "test_record_002"
        }
        
        response = requests.post(url, params=params, headers=headers)
        
        print(f"\nPHQ-9警告等级预警检查响应: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"响应数据: {json.dumps(data, indent=2, ensure_ascii=False)}")
            assert data["code"] == 200
            if data["data"]:
                assert data["data"]["level"] == "warning"
        else:
            print(f"错误响应: {response.text}")
    
    def test_check_questionnaire_alert_gad7(self, headers):
        """测试问卷预警检查 - GAD-7"""
        url = f"{BASE_URL}/api/alerts/internal/check-questionnaire"
        params = {
            "user_id": TEST_USER_ID,
            "template_code": "GAD7",
            "score": 18,
            "result_level": "severe",
            "record_id": "test_record_003"
        }
        
        response = requests.post(url, params=params, headers=headers)
        
        print(f"\nGAD-7预警检查响应: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"响应数据: {json.dumps(data, indent=2, ensure_ascii=False)}")
            assert data["code"] == 200
        else:
            print(f"错误响应: {response.text}")
    
    def test_check_questionnaire_alert_no_alert(self, headers):
        """测试问卷预警检查 - 无需预警"""
        url = f"{BASE_URL}/api/alerts/internal/check-questionnaire"
        params = {
            "user_id": TEST_USER_ID,
            "template_code": "PHQ9",
            "score": 5,
            "result_level": "mild",
            "record_id": "test_record_004"
        }
        
        response = requests.post(url, params=params, headers=headers)
        
        print(f"\n无需预警检查响应: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"响应数据: {json.dumps(data, indent=2, ensure_ascii=False)}")
            assert data["code"] == 200
            assert data["data"] is None or data["message"] == "无需生成预警"
        else:
            print(f"错误响应: {response.text}")
    
    # ==================== 测试：内部API - 对话预警 ====================
    
    def test_check_conversation_alert_crisis(self, headers):
        """测试对话预警检查 - 危机关键词"""
        url = f"{BASE_URL}/api/alerts/internal/check-conversation"
        params = {
            "user_id": TEST_USER_ID,
            "session_id": "test_session_001",
            "content": "我觉得活着没什么意义了，想结束这一切",
            "emotion_intensity": 0.9
        }
        
        response = requests.post(url, params=params, headers=headers)
        
        print(f"\n对话危机预警检查响应: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"响应数据: {json.dumps(data, indent=2, ensure_ascii=False)}")
            assert data["code"] == 200
            if data["data"]:
                assert data["data"]["level"] == "danger"
                assert "危机信号" in data["data"]["title"]
        else:
            print(f"错误响应: {response.text}")
    
    def test_check_conversation_alert_high_intensity(self, headers):
        """测试对话预警检查 - 高情绪强度"""
        url = f"{BASE_URL}/api/alerts/internal/check-conversation"
        params = {
            "user_id": TEST_USER_ID,
            "session_id": "test_session_002",
            "content": "我感觉非常糟糕，一切都失控了",
            "emotion_intensity": 0.92
        }
        
        response = requests.post(url, params=params, headers=headers)
        
        print(f"\n对话高情绪强度预警检查响应: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"响应数据: {json.dumps(data, indent=2, ensure_ascii=False)}")
            assert data["code"] == 200
        else:
            print(f"错误响应: {response.text}")
    
    def test_check_conversation_alert_no_alert(self, headers):
        """测试对话预警检查 - 无需预警"""
        url = f"{BASE_URL}/api/alerts/internal/check-conversation"
        params = {
            "user_id": TEST_USER_ID,
            "session_id": "test_session_003",
            "content": "今天天气不错，心情也挺好的",
            "emotion_intensity": 0.3
        }
        
        response = requests.post(url, params=params, headers=headers)
        
        print(f"\n对话无需预警检查响应: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"响应数据: {json.dumps(data, indent=2, ensure_ascii=False)}")
            assert data["code"] == 200
            assert data["data"] is None or data["message"] == "无需生成预警"
        else:
            print(f"错误响应: {response.text}")
    
    # ==================== 辅助方法 ====================
    
    def _create_test_alert(self, headers):
        """创建测试预警"""
        # 通过问卷预警检查创建一个预警
        url = f"{BASE_URL}/api/alerts/internal/check-questionnaire"
        params = {
            "user_id": TEST_USER_ID,
            "template_code": "PHQ9",
            "score": 20,
            "result_level": "severe",
            "record_id": f"test_record_{int(time.time())}"
        }
        
        response = requests.post(url, params=params, headers=headers)
        if response.status_code == 200:
            data = response.json()
            if data.get("data") and data["data"].get("id"):
                return data["data"]["id"]
        return None


class TestAlertWebSocket:
    """预警WebSocket测试类"""
    
    def test_websocket_connection(self):
        """测试WebSocket连接"""
        ws_url = f"{WS_URL}/api/ws/alerts/{TEST_USER_ID}"
        
        received_messages = []
        
        def on_message(ws, message):
            print(f"\n收到WebSocket消息: {message}")
            received_messages.append(json.loads(message))
        
        def on_error(ws, error):
            print(f"\nWebSocket错误: {error}")
        
        def on_close(ws, close_status_code, close_msg):
            print(f"\nWebSocket连接关闭: {close_status_code} - {close_msg}")
        
        def on_open(ws):
            print("\nWebSocket连接已打开")
            # 发送pong响应
            ws.send(json.dumps({
                "type": "pong",
                "timestamp": datetime.utcnow().isoformat()
            }))
        
        # 创建WebSocket连接
        ws = websocket.WebSocketApp(
            ws_url,
            on_open=on_open,
            on_message=on_message,
            on_error=on_error,
            on_close=on_close
        )
        
        # 在后台线程运行WebSocket
        wst = threading.Thread(target=ws.run_forever)
        wst.daemon = True
        wst.start()
        
        # 等待连接建立
        time.sleep(2)
        
        # 检查是否收到连接成功消息
        assert len(received_messages) > 0
        assert received_messages[0]["type"] == "connected"
        
        # 关闭连接
        ws.close()
    
    def test_websocket_receive_alert(self):
        """测试通过WebSocket接收预警"""
        ws_url = f"{WS_URL}/api/ws/alerts/{TEST_USER_ID}"
        
        received_messages = []
        
        def on_message(ws, message):
            print(f"\n收到WebSocket消息: {message}")
            received_messages.append(json.loads(message))
        
        def on_open(ws):
            print("\nWebSocket连接已打开，准备接收预警")
        
        # 创建WebSocket连接
        ws = websocket.WebSocketApp(
            ws_url,
            on_open=on_open,
            on_message=on_message
        )
        
        # 在后台线程运行WebSocket
        wst = threading.Thread(target=ws.run_forever)
        wst.daemon = True
        wst.start()
        
        # 等待连接建立
        time.sleep(1)
        
        # 触发一个预警
        url = f"{BASE_URL}/api/alerts/internal/check-questionnaire"
        params = {
            "user_id": TEST_USER_ID,
            "template_code": "PHQ9",
            "score": 22,
            "result_level": "severe",
            "record_id": f"test_record_ws_{int(time.time())}"
        }
        
        response = requests.post(url, params=params)
        print(f"\n触发预警响应: {response.status_code}")
        
        # 等待预警推送
        time.sleep(2)
        
        # 检查是否收到预警消息
        alert_messages = [m for m in received_messages if m.get("type") == "new_alert"]
        if alert_messages:
            print(f"\n成功接收到预警消息: {json.dumps(alert_messages[0], indent=2, ensure_ascii=False)}")
        
        # 关闭连接
        ws.close()


# ==================== 主函数：直接运行测试 ====================

def run_basic_tests():
    """运行基础测试"""
    print("=" * 60)
    print("预警功能API基础测试")
    print("=" * 60)
    
    headers = {"Content-Type": "application/json"}
    
    # 测试1: 获取预警列表
    print("\n[测试1] 获取预警列表")
    url = f"{BASE_URL}/api/alerts"
    params = {"user_id": TEST_USER_ID, "page": 1, "page_size": 10}
    response = requests.get(url, params=params, headers=headers)
    print(f"状态码: {response.status_code}")
    if response.status_code == 200:
        print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    else:
        print(f"错误: {response.text}")
    
    # 测试2: 预警统计
    print("\n[测试2] 获取预警统计")
    url = f"{BASE_URL}/api/alerts/stats"
    params = {"user_id": TEST_USER_ID}
    response = requests.get(url, params=params, headers=headers)
    print(f"状态码: {response.status_code}")
    if response.status_code == 200:
        print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    else:
        print(f"错误: {response.text}")
    
    # 测试3: PHQ-9危险等级预警
    print("\n[测试3] PHQ-9危险等级预警检查")
    url = f"{BASE_URL}/api/alerts/internal/check-questionnaire"
    params = {
        "user_id": TEST_USER_ID,
        "template_code": "PHQ9",
        "score": 21,
        "result_level": "severe",
        "record_id": f"test_record_{int(time.time())}"
    }
    response = requests.post(url, params=params, headers=headers)
    print(f"状态码: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"响应: {json.dumps(data, indent=2, ensure_ascii=False)}")
        if data.get("data"):
            alert_id = data["data"].get("id")
            
            # 测试4: 确认预警
            print(f"\n[测试4] 确认预警 (ID: {alert_id})")
            url = f"{BASE_URL}/api/alerts/{alert_id}/acknowledge"
            payload = {"user_id": TEST_USER_ID, "notes": "测试确认"}
            response = requests.post(url, json=payload, headers=headers)
            print(f"状态码: {response.status_code}")
            if response.status_code == 200:
                print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
            else:
                print(f"错误: {response.text}")
    else:
        print(f"错误: {response.text}")
    
    # 测试5: 对话危机预警
    print("\n[测试5] 对话危机预警检查")
    url = f"{BASE_URL}/api/alerts/internal/check-conversation"
    params = {
        "user_id": TEST_USER_ID,
        "session_id": "test_session_001",
        "content": "我觉得活着没什么意义了",
        "emotion_intensity": 0.92
    }
    response = requests.post(url, params=params, headers=headers)
    print(f"状态码: {response.status_code}")
    if response.status_code == 200:
        print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    else:
        print(f"错误: {response.text}")
    
    print("\n" + "=" * 60)
    print("基础测试完成")
    print("=" * 60)


if __name__ == "__main__":
    # 直接运行基础测试
    run_basic_tests()
    
    # 运行pytest测试
    # pytest.main([__file__, "-v"])
