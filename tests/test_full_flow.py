"""
完整测试脚本 - 测试对话全流程（包括保存报告）
流程：登录 -> 创建会话 -> 发送消息 -> 结束会话（生成报告）-> 查询报告
"""
import requests
import json
import time

BASE_URL = "http://localhost:8001"  # 使用 8001 端口
USERNAME = "pym"
PASSWORD = "pym123456"

def login():
    """登录获取用户 ID"""
    print("\n" + "="*60)
    print("[1] 登录")
    print("="*60)
    url = f"{BASE_URL}/api/v1/auth/login"
    data = {"username": USERNAME, "password": PASSWORD}
    
    response = requests.post(url, json=data, timeout=30)
    if response.status_code == 200:
        result = response.json()
        user_id = result['user']['id']
        print(f"✅ 登录成功 (用户 ID: {user_id})")
        return user_id
    else:
        print(f"❌ 登录失败：{response.text}")
        return None

def create_session(user_id):
    """创建新会话"""
    print("\n" + "="*60)
    print("[2] 创建会话")
    print("="*60)
    url = f"{BASE_URL}/api/v1/chat/new-session"
    data = {"user_id": user_id}
    
    response = requests.post(url, json=data, timeout=30)
    if response.status_code == 200:
        result = response.json()
        session_id = result['session_id']
        print(f"✅ 会话创建成功 (会话 ID: {session_id})")
        return session_id
    else:
        print(f"❌ 创建会话失败：{response.text}")
        return None

def send_message(user_id, session_id, message):
    """发送消息"""
    print(f"\n[发送消息] {message}")
    url = f"{BASE_URL}/api/v1/chat/message"
    data = {
        "user_id": user_id,
        "session_id": session_id,
        "message": message
    }
    
    response = requests.post(url, json=data, timeout=60)
    if response.status_code == 200:
        result = response.json()
        print(f"✅ 回复：{result.get('reply', 'N/A')[:100]}...")
        return result
    else:
        print(f"❌ 发送消息失败：{response.text}")
        return None

def end_session(user_id, session_id):
    """结束会话并生成报告"""
    print("\n" + "="*60)
    print("[3] 结束会话（生成报告）")
    print("="*60)
    url = f"{BASE_URL}/api/v1/chat/end-session"
    data = {"user_id": user_id, "session_id": session_id}
    
    print("正在结束会话并生成报告，这可能需要一些时间...")
    response = requests.post(url, json=data, timeout=120)  # 增加超时时间
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ {result.get('message', '会话已结束')}")
        if 'report_id' in result:
            print(f"   报告 ID: {result['report_id']}")
        return result
    else:
        print(f"❌ 结束会话失败：{response.text}")
        return None

def get_session_report(user_id, session_id):
    """获取会话报告"""
    print("\n" + "="*60)
    print("[4] 获取会话报告")
    print("="*60)
    url = f"{BASE_URL}/api/v1/report/session/{session_id}"
    data = {"user_id": user_id}
    
    response = requests.post(url, json=data, timeout=30)
    if response.status_code == 200:
        result = response.json()
        print(f"✅ 获取报告成功")
        print(f"\n--- 记录报告 ---")
        print(json.dumps(result.get('record_report', {}), ensure_ascii=False, indent=2))
        print(f"\n--- 分析报告 ---")
        print(json.dumps(result.get('analysis_report', {}), ensure_ascii=False, indent=2))
        print(f"\n--- 调理报告 ---")
        print(json.dumps(result.get('treatment_report', {}), ensure_ascii=False, indent=2))
        return result
    else:
        print(f"❌ 获取报告失败：{response.text}")
        return None

def main():
    """主测试流程"""
    print("\n" + "="*60)
    print("完整对话流程测试")
    print("="*60)
    
    # 1. 登录
    user_id = login()
    if not user_id:
        return
    
    # 2. 创建会话
    session_id = create_session(user_id)
    if not session_id:
        return
    
    # 3. 发送多条消息
    print("\n" + "="*60)
    print("发送对话消息")
    print("="*60)
    
    messages = [
        "我最近感到压力很大，工作和生活都不太顺利。",
        "我总是觉得自己做得不够好，担心被同事超越。",
        "每天晚上都睡不着，脑子里全是工作的事情。"
    ]
    
    for msg in messages:
        send_message(user_id, session_id, msg)
        time.sleep(1)  # 等待 1 秒
    
    # 4. 结束会话（生成报告）
    end_result = end_session(user_id, session_id)
    if not end_result:
        print("\n❌ 会话结束失败，无法查询报告")
        return
    
    # 5. 查询报告
    time.sleep(2)  # 等待报告完全保存
    report = get_session_report(user_id, session_id)
    
    print("\n" + "="*60)
    print("测试完成")
    print("="*60)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n测试被用户中断")
    except Exception as e:
        print(f"\n❌ 测试异常：{e}")
        import traceback
        traceback.print_exc()
