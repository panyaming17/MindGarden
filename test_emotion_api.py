"""
情绪记录API测试脚本
使用账号：pym / pym123456
"""
import requests
import json
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000"
USERNAME = "pym"
PASSWORD = "pym123456"

# 情绪类型列表
EMOTION_TYPES = [
    {"type": "happy", "icon": "😊", "name": "开心", "color": "#FFD93D"},
    {"type": "excited", "icon": "🤩", "name": "兴奋", "color": "#FF6B6B"},
    {"type": "calm", "icon": "😌", "name": "平静", "color": "#6BCB77"},
    {"type": "grateful", "icon": "🥰", "name": "感恩", "color": "#FDCB6E"},
]

def login():
    """登录获取用户ID"""
    print("\n=== 登录 ===")
    url = f"{BASE_URL}/api/v1/auth/login"
    data = {
        "username": USERNAME,
        "password": PASSWORD
    }
    
    try:
        response = requests.post(url, json=data, timeout=10)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            user_id = result.get('user', {}).get('id')
            print(f"✅ 登录成功! 用户ID: {user_id}")
            return user_id
        else:
            print(f"❌ 登录失败: {response.text}")
            return None
    except Exception as e:
        print(f"❌ 异常: {e}")
        return None


def test_get_emotion_types():
    """测试获取情绪类型"""
    print("\n=== 测试1: 获取情绪类型列表 ===")
    url = f"{BASE_URL}/api/emotions/types"
    
    try:
        response = requests.get(url, timeout=10)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            emotions = data.get('data', {}).get('emotions', [])
            print(f"✅ 成功! 共{len(emotions)}种情绪类型")
            print(f"   前3种: {', '.join([e['name'] for e in emotions[:3]])}")
            return True
        else:
            print(f"❌ 失败: {response.text}")
            return False
    except Exception as e:
        print(f"❌ 异常: {e}")
        return False


def test_record_emotion(user_id):
    """测试记录情绪"""
    print("\n=== 测试2: 记录情绪 ===")
    url = f"{BASE_URL}/api/emotions/record"
    
    # 选择一种情绪
    emotion = EMOTION_TYPES[0]  # 开心
    now = datetime.now()
    
    params = {"user_id": user_id}
    body = {
        "emotion_type": emotion["type"],
        "emotion_icon": emotion["icon"],
        "emotion_name": emotion["name"],
        "emotion_color": emotion["color"],
        "signature": "今天天气真好，心情不错！",
        "record_date": now.strftime("%Y-%m-%d"),
        "record_time": now.strftime("%H:%M:%S")
    }
    
    try:
        response = requests.post(url, params=params, json=body, timeout=10)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            record_id = data.get('data', {}).get('id')
            print(f"✅ 记录成功! 记录ID: {record_id}")
            return record_id
        else:
            print(f"❌ 失败: {response.text}")
            return None
    except Exception as e:
        print(f"❌ 异常: {e}")
        return None


def test_get_history(user_id):
    """测试获取历史记录"""
    print("\n=== 测试3: 获取情绪历史 ===")
    url = f"{BASE_URL}/api/emotions/history"
    params = {
        "user_id": user_id,
        "limit": 10
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            total = data.get('data', {}).get('total', 0)
            records = data.get('data', {}).get('records', [])
            print(f"✅ 成功! 共{total}条记录")
            if records:
                print(f"   最新记录: {records[0].get('emotion_name')} - {records[0].get('signature', '')[:20]}...")
            return True
        else:
            print(f"❌ 失败: {response.text}")
            return False
    except Exception as e:
        print(f"❌ 异常: {e}")
        return False


def test_get_calendar(user_id):
    """测试获取日历数据"""
    print("\n=== 测试4: 获取情绪日历 ===")
    url = f"{BASE_URL}/api/emotions/calendar"
    now = datetime.now()
    params = {
        "user_id": user_id,
        "year": now.year,
        "month": now.month
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            days = data.get('data', {}).get('days', [])
            has_record_days = [d for d in days if d.get('has_record')]
            print(f"✅ 成功! 本月共{len(days)}天，有记录{len(has_record_days)}天")
            return True
        else:
            print(f"❌ 失败: {response.text}")
            return False
    except Exception as e:
        print(f"❌ 异常: {e}")
        return False


def test_get_statistics(user_id):
    """测试获取统计数据"""
    print("\n=== 测试5: 获取情绪统计 ===")
    url = f"{BASE_URL}/api/emotions/statistics"
    params = {
        "user_id": user_id,
        "days": 30
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            total = data.get('data', {}).get('total_records', 0)
            avg = data.get('data', {}).get('daily_average', 0)
            distribution = data.get('data', {}).get('distribution', [])
            print(f"✅ 成功! 共{total}条记录，日均{avg}条")
            if distribution:
                top = distribution[0]
                print(f"   最多的情绪: {top['name']} ({top['count']}次, {top['percent']}%)")
            return True
        else:
            print(f"❌ 失败: {response.text}")
            return False
    except Exception as e:
        print(f"❌ 异常: {e}")
        return False


def test_get_remind_settings(user_id):
    """测试获取提醒设置"""
    print("\n=== 测试6: 获取提醒设置 ===")
    url = f"{BASE_URL}/api/emotions/remind-settings"
    params = {"user_id": user_id}
    
    try:
        response = requests.get(url, params=params, timeout=10)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            settings = data.get('data', {})
            enabled = settings.get('remind_enabled')
            times = settings.get('remind_times')
            interval = settings.get('remind_interval')
            print(f"✅ 成功! 提醒启用: {enabled}, 每日{times}次, 间隔{interval}分钟")
            return True
        else:
            print(f"❌ 失败: {response.text}")
            return False
    except Exception as e:
        print(f"❌ 异常: {e}")
        return False


def test_update_remind_settings(user_id):
    """测试更新提醒设置"""
    print("\n=== 测试7: 更新提醒设置 ===")
    url = f"{BASE_URL}/api/emotions/remind-settings"
    params = {"user_id": user_id}
    body = {
        "remind_enabled": True,
        "remind_times": 3,
        "remind_interval": 240  # 4小时
    }
    
    try:
        response = requests.put(url, params=params, json=body, timeout=10)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            settings = data.get('data', {})
            print(f"✅ 更新成功! 每日{settings.get('remind_times')}次, 间隔{settings.get('remind_interval')}分钟")
            return True
        else:
            print(f"❌ 失败: {response.text}")
            return False
    except Exception as e:
        print(f"❌ 异常: {e}")
        return False


def test_check_next_remind(user_id):
    """测试检查下次提醒"""
    print("\n=== 测试8: 检查下次提醒 ===")
    url = f"{BASE_URL}/api/emotions/next-remind"
    params = {"user_id": user_id}
    
    try:
        response = requests.get(url, params=params, timeout=10)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            need = data.get('data', {}).get('need_remind')
            reason = data.get('data', {}).get('reason', '')
            print(f"✅ 成功! 需要提醒: {need}")
            if need:
                print(f"   原因: {reason}")
            return True
        else:
            print(f"❌ 失败: {response.text}")
            return False
    except Exception as e:
        print(f"❌ 异常: {e}")
        return False


def test_skip_remind(user_id):
    """测试跳过提醒"""
    print("\n=== 测试9: 跳过本次提醒 ===")
    url = f"{BASE_URL}/api/emotions/skip-remind"
    params = {"user_id": user_id}
    
    try:
        response = requests.post(url, params=params, timeout=10)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            next_time = data.get('data', {}).get('next_remind_at')
            print(f"✅ 跳过成功! 下次提醒: {next_time}")
            return True
        else:
            print(f"❌ 失败: {response.text}")
            return False
    except Exception as e:
        print(f"❌ 异常: {e}")
        return False


def run_all_tests():
    """运行所有测试"""
    print("="*60)
    print("情绪记录API测试开始")
    print("="*60)
    
    # 检查服务是否运行
    try:
        r = requests.get(f"{BASE_URL}/health", timeout=5)
        print(f"\n✅ 服务运行中 (状态: {r.status_code})")
    except:
        print(f"\n❌ 服务未运行，请先启动后端服务")
        return False
    
    # 登录获取用户ID
    user_id = login()
    if not user_id:
        print("\n❌ 登录失败，无法继续测试")
        return False
    
    # 运行测试
    results = []
    
    # 测试1: 获取情绪类型
    results.append(("获取情绪类型", test_get_emotion_types()))
    
    # 测试2: 记录情绪
    record_id = test_record_emotion(user_id)
    results.append(("记录情绪", record_id is not None))
    
    # 测试3: 获取历史记录
    results.append(("获取历史记录", test_get_history(user_id)))
    
    # 测试4: 获取日历
    results.append(("获取情绪日历", test_get_calendar(user_id)))
    
    # 测试5: 获取统计
    results.append(("获取情绪统计", test_get_statistics(user_id)))
    
    # 测试6: 获取提醒设置
    results.append(("获取提醒设置", test_get_remind_settings(user_id)))
    
    # 测试7: 更新提醒设置
    results.append(("更新提醒设置", test_update_remind_settings(user_id)))
    
    # 测试8: 检查下次提醒
    results.append(("检查下次提醒", test_check_next_remind(user_id)))
    
    # 测试9: 跳过提醒
    results.append(("跳过本次提醒", test_skip_remind(user_id)))
    
    # 打印测试结果汇总
    print("\n" + "="*60)
    print("测试结果汇总")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{status}: {name}")
    
    print(f"\n总计: {passed}/{total} 通过")
    
    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
