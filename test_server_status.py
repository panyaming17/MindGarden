"""检查后端服务状态"""
import requests

try:
    response = requests.get("http://localhost:8000/docs", timeout=5)
    if response.status_code == 200:
        print("✅ 后端服务正在运行")
    else:
        print(f"⚠️ 后端服务返回状态码: {response.status_code}")
except Exception as e:
    print(f"❌ 后端服务未运行: {e}")
