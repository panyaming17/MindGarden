"""
测试 end_session 接口的异步报告生成功能

测试流程：
1. 登录获取用户 ID
2. 调用 end_session 接口结束会话
3. 轮询查询报告状态
4. 验证三个报告是否正确生成

测试数据：
- 用户名：pym
- 密码：pym123456
- 会话 ID：session_0c6e2665
"""

import requests
import time
import json
from datetime import datetime

# 配置
BASE_URL = "http://localhost:8000/api/v1"
USERNAME = "pym"
PASSWORD = "pym123456"
SESSION_ID = "session_0c6e2665"

# 颜色输出
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_header(text):
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text.center(60)}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}\n")

def print_success(text):
    print(f"{Colors.OKGREEN}✓ {text}{Colors.ENDC}")

def print_error(text):
    print(f"{Colors.FAIL}✗ {text}{Colors.ENDC}")

def print_info(text):
    print(f"{Colors.OKCYAN}ℹ {text}{Colors.ENDC}")

def print_warning(text):
    print(f"{Colors.WARNING}⚠ {text}{Colors.ENDC}")

# 步骤 1: 登录
def login():
    print_header("步骤 1: 登录获取用户信息")
    
    try:
        response = requests.post(
            f"{BASE_URL}/auth/login",
            json={
                "username": USERNAME,
                "password": PASSWORD
            },
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            user_id = result.get("user_id") or result.get("user", {}).get("id") or result.get("id")
            access_token = result.get("access_token") or result.get("token")
            
            print_success(f"登录成功！")
            print_info(f"用户 ID: {user_id}")
            print_info(f"Token: {access_token[:20] if access_token else 'N/A'}...")
            
            return user_id, access_token
        else:
            print_error(f"登录失败！状态码：{response.status_code}")
            print_error(f"响应：{response.text}")
            return None, None
            
    except Exception as e:
        print_error(f"登录异常：{e}")
        return None, None

# 步骤 2: 调用 end_session 接口
def end_session(user_id, session_id):
    print_header("步骤 2: 调用 end_session 接口")
    
    try:
        start_time = time.time()
        
        response = requests.post(
            f"{BASE_URL}/chat/end-session",
            json={
                "user_id": user_id,
                "session_id": session_id
            }
        )
        
        end_time = time.time()
        response_time = (end_time - start_time) * 1000  # 毫秒
        
        print_info(f"响应时间：{response_time:.2f}ms")
        
        if response.status_code == 200:
            result = response.json()
            print_success(f"end_session 调用成功！")
            print_info(f"消息：{result.get('message')}")
            print_info(f"对话数量：{result.get('dialogue_count')}")
            print_info(f"初始状态：")
            
            status = result.get('status', {})
            print(f"  - 记录报告：{status.get('record_report')}")
            print(f"  - 分析报告：{status.get('analysis_report')}")
            print(f"  - 调理报告：{status.get('treatment_report')}")
            
            return True
        else:
            print_error(f"end_session 调用失败！状态码：{response.status_code}")
            print_error(f"响应：{response.text}")
            return False
            
    except Exception as e:
        print_error(f"end_session 异常：{e}")
        return False

# 步骤 3: 轮询报告状态
def poll_report_status(session_id, max_attempts=30, interval=2):
    print_header("步骤 3: 轮询报告状态")
    
    print_info(f"轮询间隔：{interval}秒")
    print_info(f"最大尝试次数：{max_attempts}")
    print_info(f"开始时间：{datetime.now().strftime('%H:%M:%S')}")
    print()
    
    for attempt in range(1, max_attempts + 1):
        try:
            time.sleep(interval)
            
            response = requests.get(
                f"{BASE_URL}/chat/report-status/{session_id}"
            )
            
            if response.status_code == 200:
                result = response.json()
                status = result.get('status', {})
                reports_available = result.get('reports_available', {})
                
                current_time = datetime.now().strftime('%H:%M:%S')
                
                # 显示状态
                print(f"[{current_time}] 第 {attempt} 次查询:")
                
                # 记录报告
                record_status = status.get('record_report', 'unknown')
                record_available = reports_available.get('record_report', False)
                status_icon = get_status_icon(record_status, record_available)
                print(f"  {status_icon} 记录报告：{record_status} (数据：{'✓' if record_available else '✗'})")
                
                # 分析报告
                analysis_status = status.get('analysis_report', 'unknown')
                analysis_available = reports_available.get('analysis_report', False)
                status_icon = get_status_icon(analysis_status, analysis_available)
                print(f"  {status_icon} 分析报告：{analysis_status} (数据：{'✓' if analysis_available else '✗'})")
                
                # 调理报告
                treatment_status = status.get('treatment_report', 'unknown')
                treatment_available = reports_available.get('treatment_report', False)
                status_icon = get_status_icon(treatment_status, treatment_available)
                print(f"  {status_icon} 调理报告：{treatment_status} (数据：{'✓' if treatment_available else '✗'})")
                
                # 检查是否全部完成
                if (record_status == 'completed' and 
                    analysis_status == 'completed' and 
                    treatment_status == 'completed' and
                    record_available and 
                    analysis_available and 
                    treatment_available):
                    
                    print()
                    print_success("所有报告已生成完成！")
                    print_info(f"完成时间：{datetime.now().strftime('%H:%M:%S')}")
                    print_info(f"总耗时：{attempt * interval}秒")
                    
                    return True
                
            else:
                print_error(f"查询失败！状态码：{response.status_code}")
                
        except Exception as e:
            print_error(f"查询异常：{e}")
    
    print_warning("轮询超时，报告未完全生成")
    return False

def get_status_icon(status, available):
    if status == 'completed' and available:
        return f"{Colors.OKGREEN}✓{Colors.ENDC}"
    elif status == 'generating':
        return f"{Colors.WARNING}⏳{Colors.ENDC}"
    elif status == 'pending':
        return f"{Colors.OKCYAN}⏸️{Colors.ENDC}"
    elif status == 'failed':
        return f"{Colors.FAIL}❌{Colors.ENDC}"
    else:
        return f"{Colors.OKBLUE}?{Colors.ENDC}"

# 步骤 4: 获取完整报告
def get_full_report(session_id):
    print_header("步骤 4: 获取完整报告")
    
    try:
        response = requests.get(
            f"{BASE_URL}/report/session/{session_id}"
        )
        
        if response.status_code == 200:
            result = response.json()
            
            print_success("成功获取完整报告！")
            print_info(f"报告 ID: {result.get('id')}")
            print_info(f"用户 ID: {result.get('user_id')}")
            print_info(f"会话 ID: {result.get('session_id')}")
            print_info(f"创建时间：{result.get('created_at')}")
            
            # 检查报告内容
            record_report = result.get('record_report')
            analysis_report = result.get('analysis_report')
            treatment_report = result.get('treatment_report')
            
            print()
            print_info("报告内容检查:")
            
            if record_report:
                print_success(f"  ✓ 记录报告：{len(str(record_report))} 字符")
            else:
                print_error(f"  ✗ 记录报告：为空")
            
            if analysis_report:
                print_success(f"  ✓ 分析报告：{len(str(analysis_report))} 字符")
            else:
                print_error(f"  ✗ 分析报告：为空")
            
            if treatment_report:
                print_success(f"  ✓ 调理报告：{len(str(treatment_report))} 字符")
            else:
                print_error(f"  ✗ 调理报告：为空")
            
            return True
        else:
            print_error(f"获取报告失败！状态码：{response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"获取报告异常：{e}")
        return False

# 主测试流程
def main():
    print_header("End Session 异步报告生成测试")
    
    print_info(f"测试服务器：{BASE_URL}")
    print_info(f"测试用户：{USERNAME}")
    print_info(f"测试会话：{SESSION_ID}")
    
    # 步骤 1: 登录
    user_id, token = login()
    if not user_id:
        print_error("登录失败，测试终止")
        return
    
    # 步骤 2: 调用 end_session
    print()
    if not end_session(user_id, SESSION_ID):
        print_error("end_session 调用失败，测试终止")
        return
    
    # 步骤 3: 轮询报告状态
    print()
    success = poll_report_status(SESSION_ID, max_attempts=30, interval=2)
    
    # 步骤 4: 获取完整报告
    print()
    if success:
        get_full_report(SESSION_ID)
    
    # 测试总结
    print_header("测试总结")
    
    if success:
        print_success("✓ 测试通过！")
        print_info("end_session 接口成功异步启动了报告生成")
        print_info("三个报告都已正确生成并保存")
    else:
        print_error("✗ 测试失败！")
        print_warning("报告未能在预期时间内完成生成")
        print_info("请检查后端日志排查问题")
    
    print()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.WARNING}测试被用户中断{Colors.ENDC}")
    except Exception as e:
        print(f"\n{Colors.FAIL}测试异常：{e}{Colors.ENDC}")
