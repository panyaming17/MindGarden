"""检查并启动后端服务"""
import requests
import subprocess
import time
import sys

BASE_URL = "http://localhost:8000"

def check_server():
    """检查后端服务是否运行"""
    try:
        response = requests.get(f"{BASE_URL}/docs", timeout=3)
        return response.status_code == 200
    except:
        return False

def start_server():
    """启动后端服务"""
    print("正在启动后端服务...")
    # 使用 start 命令在后台启动
    subprocess.Popen(
        ["python", "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"],
        cwd="D:\\GP\\Projects",
        creationflags=subprocess.CREATE_NEW_CONSOLE
    )
    
    # 等待服务启动
    for i in range(30):
        time.sleep(1)
        if check_server():
            print("✅ 后端服务已启动")
            return True
        print(f"等待服务启动... {i+1}s")
    
    print("❌ 服务启动超时")
    return False

if __name__ == "__main__":
    if check_server():
        print("✅ 后端服务已在运行")
        sys.exit(0)
    else:
        print("⚠️ 后端服务未运行")
        if start_server():
            sys.exit(0)
        else:
            sys.exit(1)
