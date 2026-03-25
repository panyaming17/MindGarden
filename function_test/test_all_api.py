import requests
import json
import time
from datetime import date, datetime, timedelta

# API基础URL
BASE_URL = "http://localhost:8001"

# 测试用户信息
TEST_USER = {
    "username": "admin",
    "password": "admin123"
}

# 全局变量，用于存储测试过程中的数据
access_token = ""
user_id = "user_631a3f3e"
session_id = "session_12345678"
questionnaire_id = 1
alert_id = ""
admin_user_id = ""
strategy_id = ""

# 测试结果
results = []

def test_case(name, function):
    """执行测试用例并记录结果"""
    print(f"\n=== 测试: {name} ===")
    try:
        result = function()
        results.append({"name": name, "status": "成功", "message": result})
        print(f"✓ 成功: {result}")
    except Exception as e:
        results.append({"name": name, "status": "失败", "message": str(e)})
        print(f"✗ 失败: {str(e)}")

def test_register():
    """测试注册接口"""
    # 立即注册，使用固定的验证码"123456"
    url = f"{BASE_URL}/api/v1/auth/register"
    data = TEST_USER
    response = requests.post(url, json=data)
    response.raise_for_status()
    global user_id
    user_id = response.json()["id"]
    return f"注册成功，用户ID: {user_id}"

def test_send_verification_code():
    """测试发送验证码接口"""
    url = f"{BASE_URL}/api/v1/auth/send-verification-code"
    params = {
        "email": TEST_USER["email"],
        "type": "register"
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json()["message"]

def test_register():
    """测试注册接口"""
    url = f"{BASE_URL}/api/v1/auth/register"
    data = TEST_USER
    response = requests.post(url, json=data)
    response.raise_for_status()
    global user_id
    user_id = response.json()["id"]
    return f"注册成功，用户ID: {user_id}"

def test_login():
    """测试登录接口"""
    url = f"{BASE_URL}/api/v1/auth/login"
    data = {
        "username": TEST_USER["username"],
        "password": TEST_USER["password"]
    }
    response = requests.post(url, json=data)
    response.raise_for_status()
    global access_token
    access_token = response.json()["access_token"]
    return f"登录成功，获取到访问令牌"

def test_verify_token():
    """测试验证令牌接口"""
    url = f"{BASE_URL}/api/v1/auth/verify"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return "令牌验证成功"

def test_get_current_user():
    """测试获取当前用户信息接口"""
    url = f"{BASE_URL}/api/v1/auth/me"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return "获取当前用户信息成功"

def test_create_new_session():
    """测试创建新会话接口"""
    url = f"{BASE_URL}/api/v1/chat/new-session"
    # 直接将user_id作为查询参数传递
    response = requests.post(f"{url}?user_id={user_id}")
    response.raise_for_status()
    global session_id
    session_id = response.json()["session_id"]
    return f"创建新会话成功，会话ID: {session_id}"

def test_send_message():
    """测试发送消息接口"""
    url = f"{BASE_URL}/api/v1/chat/message"
    data = {
        "user_id": user_id,
        "session_id": session_id,
        "message": "我最近感觉压力很大"
    }
    response = requests.post(url, json=data)
    response.raise_for_status()
    return "发送消息成功"

def test_end_session():
    """测试结束会话接口"""
    url = f"{BASE_URL}/api/v1/chat/end-session"
    # 使用params参数传递查询参数
    params = {
        "user_id": user_id,
        "session_id": session_id
    }
    response = requests.post(url, params=params)
    response.raise_for_status()
    return response.json()["message"]

def test_get_user_sessions():
    """测试获取用户会话列表接口"""
    url = f"{BASE_URL}/api/v1/chat/sessions"
    params = {
        "user_id": user_id
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    return "获取用户会话列表成功"

def test_get_chat_history():
    """测试获取会话对话记录接口"""
    url = f"{BASE_URL}/api/v1/chat/history"
    params = {
        "user_id": user_id,
        "session_id": session_id
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    return "获取会话对话记录成功"

def test_get_session_report():
    """测试获取会话报告接口"""
    url = f"{BASE_URL}/api/v1/report/session/{session_id}"
    response = requests.get(url)
    # 会话报告可能不存在，所以不抛出异常
    if response.status_code == 404:
        return "会话报告不存在（正常，因为会话刚创建）"
    response.raise_for_status()
    return "获取会话报告成功"

def test_get_user_reports():
    """测试获取用户所有报告列表接口"""
    url = f"{BASE_URL}/api/v1/report/user/{user_id}"
    response = requests.get(url)
    response.raise_for_status()
    return "获取用户报告列表成功"

def test_add_mood_entry():
    """测试添加/更新情绪记录接口"""
    url = f"{BASE_URL}/api/v1/mood/entry"
    data = {
        "user_id": user_id,
        "date": date.today().isoformat(),
        "mood_label": "开心",
        "signature_text": "今天心情不错",
        "four_dim": {
            "intensity": 3.5,
            "hedonic": "正性",
            "tension": "低",
            "complexity": "简单"
        }
    }
    response = requests.post(url, json=data)
    response.raise_for_status()
    return response.json()["message"]

def test_get_mood_calendar():
    """测试获取某月情绪记录（日历数据）接口"""
    url = f"{BASE_URL}/api/v1/mood/calendar"
    params = {
        "user_id": user_id,
        "year": date.today().year,
        "month": date.today().month
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    return "获取情绪日历成功"

def test_get_mood_trend():
    """测试获取情绪趋势（折线图数据）接口"""
    url = f"{BASE_URL}/api/v1/mood/trend"
    params = {
        "user_id": user_id,
        "start_date": (date.today() - timedelta(days=30)).isoformat(),
        "end_date": date.today().isoformat()
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    return "获取情绪趋势成功"

def test_get_questionnaire_list():
    """测试获取可用问卷列表接口"""
    url = f"{BASE_URL}/api/v1/questionnaire/list"
    response = requests.get(url)
    response.raise_for_status()
    return "获取问卷列表成功"

def test_get_questionnaire():
    """测试获取问卷题目接口"""
    url = f"{BASE_URL}/api/v1/questionnaire/{questionnaire_id}"
    response = requests.get(url)
    # 问卷可能不存在，所以不抛出异常
    if response.status_code == 404:
        return f"问卷 {questionnaire_id} 不存在"
    response.raise_for_status()
    return f"获取问卷 {questionnaire_id} 成功"

def test_submit_questionnaire():
    """测试提交问卷结果接口"""
    url = f"{BASE_URL}/api/v1/questionnaire/submit"
    data = {
        "user_id": user_id,
        "questionnaire_id": questionnaire_id,
        "answers": {
            "1": 1,
            "2": 2,
            "3": 3
        }
    }
    response = requests.post(url, json=data)
    # 问卷可能不存在，所以不抛出异常
    if response.status_code == 404:
        return f"问卷 {questionnaire_id} 不存在"
    response.raise_for_status()
    return "提交问卷结果成功"

def test_get_questionnaire_history():
    """测试获取用户问卷历史接口"""
    url = f"{BASE_URL}/api/v1/questionnaire/history"
    params = {
        "user_id": user_id
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    return "获取问卷历史成功"

def test_get_alert_list():
    """测试获取用户未读预警接口"""
    url = f"{BASE_URL}/api/v1/alert/list"
    params = {
        "user_id": user_id
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    return "获取预警列表成功"

def test_get_users():
    """测试获取用户列表接口"""
    url = f"{BASE_URL}/api/v1/admin/users"
    response = requests.get(url)
    response.raise_for_status()
    return "获取用户列表成功"

def test_get_strategies():
    """测试获取策略列表接口"""
    url = f"{BASE_URL}/api/v1/admin/strategies"
    response = requests.get(url)
    response.raise_for_status()
    return "获取策略列表成功"

def test_get_admin_logs():
    """测试获取管理员操作日志接口"""
    url = f"{BASE_URL}/api/v1/admin/logs"
    response = requests.get(url)
    response.raise_for_status()
    return "获取管理员操作日志成功"

def run_all_tests():
    """运行所有测试用例"""
    print("开始测试登录、注册、对话相关的接口...")
    
    # 认证相关测试
    test_case("注册", test_register)
    test_case("登录", test_login)
    test_case("验证令牌", test_verify_token)
    test_case("获取当前用户信息", test_get_current_user)
    
    # 对话核心测试
    test_case("创建新会话", test_create_new_session)
    test_case("发送消息", test_send_message)
    test_case("结束会话", test_end_session)
    test_case("获取用户会话列表", test_get_user_sessions)
    test_case("获取会话对话记录", test_get_chat_history)
    
    # 打印测试结果
    print("\n=== 测试结果汇总 ===")
    success_count = 0
    fail_count = 0
    
    for result in results:
        status = "✓" if result["status"] == "成功" else "✗"
        print(f"{status} {result['name']}: {result['message']}")
        if result["status"] == "成功":
            success_count += 1
        else:
            fail_count += 1
    
    print(f"\n测试完成: {success_count} 成功, {fail_count} 失败")
    return success_count, fail_count

if __name__ == "__main__":
    run_all_tests()
