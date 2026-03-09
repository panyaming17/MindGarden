import requests
import json

# 登录获取令牌
def get_token():
    url = "http://localhost:8001/api/auth/login"
    data = {
        "username": "admin",
        "password": "123456"
    }
    response = requests.post(url, json=data)
    if response.status_code == 200:
        return response.json().get("access_token")
    else:
        print(f"登录失败: {response.status_code}, {response.json()}")
        return None

# 测试获取规则列表
def test_get_rules(token):
    url = "http://localhost:8001/api/admin/rules"
    headers = {
        "Authorization": f"Bearer {token}"
    }
    response = requests.get(url, headers=headers)
    print(f"获取规则列表: {response.status_code}")
    if response.status_code == 200:
        print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    else:
        print(f"错误: {response.json()}")

# 测试创建规则
def test_create_rule(token):
    url = "http://localhost:8001/api/admin/rules"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    data = {
        "type": "cbt",
        "name": "测试规则",
        "content": {"keywords": ["测试", "示例"], "strategy": "测试策略"},
        "version": "1.0.0",
        "is_active": True
    }
    response = requests.post(url, headers=headers, json=data)
    print(f"创建规则: {response.status_code}")
    if response.status_code == 201:
        print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        return response.json().get("id")
    else:
        print(f"错误: {response.json()}")
        return None

# 测试更新规则
def test_update_rule(token, rule_id):
    url = f"http://localhost:8001/api/admin/rules/{rule_id}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    data = {
        "name": "更新后的测试规则",
        "version": "1.0.1"
    }
    response = requests.put(url, headers=headers, json=data)
    print(f"更新规则: {response.status_code}")
    if response.status_code == 200:
        print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    else:
        print(f"错误: {response.json()}")

# 测试删除规则
def test_delete_rule(token, rule_id):
    url = f"http://localhost:8001/api/admin/rules/{rule_id}"
    headers = {
        "Authorization": f"Bearer {token}"
    }
    response = requests.delete(url, headers=headers)
    print(f"删除规则: {response.status_code}")
    if response.status_code == 200:
        print(f"响应: {response.json()}")
    else:
        print(f"错误: {response.json()}")

if __name__ == "__main__":
    print("=== 测试规则库管理API ===")
    
    # 获取令牌
    token = get_token()
    if not token:
        exit(1)
    
    print(f"获取令牌成功: {token[:20]}...")
    
    # 测试获取规则列表
    print("\n=== 测试获取规则列表 ===")
    test_get_rules(token)
    
    # 测试创建规则
    print("\n=== 测试创建规则 ===")
    rule_id = test_create_rule(token)
    
    if rule_id:
        # 测试更新规则
        print("\n=== 测试更新规则 ===")
        test_update_rule(token, rule_id)
        
        # 测试再次获取规则列表
        print("\n=== 测试再次获取规则列表 ===")
        test_get_rules(token)
        
        # 测试删除规则
        print("\n=== 测试删除规则 ===")
        test_delete_rule(token, rule_id)
        
        # 测试最后获取规则列表
        print("\n=== 测试最后获取规则列表 ===")
        test_get_rules(token)
