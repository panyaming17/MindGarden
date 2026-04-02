"""
使用用户账号测试问卷API
用户名：pym 密码：pym123456
"""
import requests
import json

BASE_URL = "http://localhost:8000"
USERNAME = "pym"
PASSWORD = "pym123456"

def login():
    """登录获取token"""
    print("=== 登录 ===")
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
            print(f"登录成功!")
            user_id = result.get('user', {}).get('id')
            print(f"用户ID: {user_id}")
            return user_id
        else:
            print(f"登录失败: {response.text}")
            return None
    except Exception as e:
        print(f"异常: {e}")
        return None

def test_questionnaire_api(user_id):
    """测试问卷API"""
    print("\n=== 测试问卷API ===")
    
    # 测试1: 获取待测问卷
    print("\n1. 获取待测问卷...")
    url = f"{BASE_URL}/api/questionnaires/next-due"
    params = {"user_id": user_id}
    
    try:
        response = requests.get(url, params=params, timeout=10)
        print(f"   状态码: {response.status_code}")
        if response.status_code == 200:
            print(f"   响应: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")
        else:
            print(f"   错误: {response.text}")
    except Exception as e:
        print(f"   异常: {e}")
    
    # 测试2: 获取问卷模板
    print("\n2. 获取PHQ-9问卷模板...")
    url = f"{BASE_URL}/api/questionnaires/PHQ9/template"
    
    try:
        response = requests.get(url, timeout=10)
        print(f"   状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   问卷名称: {data.get('data', {}).get('name')}")
            print(f"   题目数量: {len(data.get('data', {}).get('questions', []))}")
        else:
            print(f"   错误: {response.text}")
    except Exception as e:
        print(f"   异常: {e}")

if __name__ == "__main__":
    print("="*60)
    print("使用账号测试问卷API")
    print(f"用户名: {USERNAME}")
    print("="*60)
    
    # 先测试服务是否可用
    try:
        r = requests.get(f"{BASE_URL}/health", timeout=5)
        print(f"\n✅ 服务运行中 (状态: {r.status_code})")
    except:
        print(f"\n❌ 服务未运行，请先启动后端服务")
        exit(1)
    
    # 登录
    user_id = login()
    
    if user_id:
        # 测试问卷API
        test_questionnaire_api(user_id)
    else:
        print("\n登录失败，无法继续测试")
