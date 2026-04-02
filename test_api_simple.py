"""简单测试问卷API"""
import requests
import json

BASE_URL = "http://localhost:8000"

# 测试1: 检查服务是否运行
print("=== 测试服务状态 ===")
try:
    response = requests.get(f"{BASE_URL}/health", timeout=5)
    print(f"健康检查: {response.status_code}")
    print(f"响应: {response.json()}")
except Exception as e:
    print(f"错误: {e}")

# 测试2: 检查docs
print("\n=== 检查API文档 ===")
try:
    response = requests.get(f"{BASE_URL}/docs", timeout=5)
    print(f"Docs状态: {response.status_code}")
except Exception as e:
    print(f"错误: {e}")

# 测试3: 测试问卷API
print("\n=== 测试问卷API ===")
try:
    response = requests.get(f"{BASE_URL}/api/questionnaires/next-due?user_id=test_user", timeout=5)
    print(f"问卷API状态: {response.status_code}")
    if response.status_code != 404:
        print(f"响应: {response.json()}")
    else:
        print("路由未找到 - 需要检查后端是否正确加载路由")
except Exception as e:
    print(f"错误: {e}")
