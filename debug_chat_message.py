"""
调试发送消息接口
打印请求数据和响应，帮助定位问题
"""
import requests
import json

BASE_URL = "http://localhost:8000"
USERNAME = "pym"
PASSWORD = "pym123456"

def login():
    """登录获取用户ID"""
    print("=== 登录 ===")
    url = f"{BASE_URL}/api/v1/auth/login"
    data = {
        "username": USERNAME,
        "password": PASSWORD
    }
    
    try:
        response = requests.post(url, json=data, timeout=30)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"登录响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
            user_id = result.get('user', {}).get('id')
            print(f"用户ID: {user_id}")
            return user_id
        else:
            print(f"登录失败: {response.text}")
            return None
    except Exception as e:
        print(f"异常: {e}")
        import traceback
        print(traceback.format_exc())
        return None

def test_send_message(user_id):
    """测试发送消息 - 打印详细调试信息"""
    print("\n=== 测试发送消息（调试模式）===")
    url = f"{BASE_URL}/api/v1/chat/message"
    
    # 准备请求数据
    data = {
        "user_id": user_id,
        "session_id": "test_session_001",
        "message": "测试消息"
    }
    
    print(f"请求URL: {url}")
    print(f"请求数据: {json.dumps(data, ensure_ascii=False, indent=2)}")
    
    try:
        response = requests.post(url, json=data, timeout=30)
        print(f"\n状态码: {response.status_code}")
        print(f"响应内容: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")
    except Exception as e:
        print(f"请求异常: {e}")
        import traceback
        print(traceback.format_exc())

def check_data_models():
    """检查数据模型定义"""
    print("\n=== 检查数据模型定义 ===")
    try:
        from backend.core.data_models import ChatMessage, ChatMessageResponse
        
        # 打印ChatMessage模型字段 - Pydantic V2
        print("\nChatMessage 模型字段:")
        for field_name, field_info in ChatMessage.model_fields.items():
            print(f"  - {field_name}: {field_info.annotation}")
        
        # 打印ChatMessageResponse模型字段 - Pydantic V2
        print("\nChatMessageResponse 模型字段:")
        for field_name, field_info in ChatMessageResponse.model_fields.items():
            print(f"  - {field_name}: {field_info.annotation}")
            
    except Exception as e:
        print(f"检查模型失败: {e}")
        import traceback
        print(traceback.format_exc())

if __name__ == "__main__":
    print("="*60)
    print("调试发送消息接口")
    print("="*60)
    
    # 检查数据模型
    check_data_models()
    
    # 登录
    user_id = login()
    
    if user_id:
        # 测试发送消息
        test_send_message(user_id)
    else:
        print("\n登录失败，无法继续测试")
