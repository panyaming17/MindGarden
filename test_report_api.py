"""
测试报告API接口
"""
import requests
import json

BASE_URL = "http://localhost:8000"

# 测试数据
USER_ID = "user_631a3f3e"
SESSION_ID = "session_test_001"

def test_get_session_report():
    """测试获取单个会话报告"""
    print("\n=== 测试获取单个会话报告 ===")
    url = f"{BASE_URL}/api/v1/report/session/{SESSION_ID}"
    
    try:
        response = requests.get(url)
        print(f"请求URL: {url}")
        print(f"响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"响应内容:\n{json.dumps(data, ensure_ascii=False, indent=2)}")
            
            # 检查三个报告是否存在
            if "record_report" in data:
                print("\n✓ 记录报告存在")
            else:
                print("\n✗ 记录报告不存在")
                
            if "analysis_report" in data:
                print("✓ 分析报告存在")
            else:
                print("✗ 分析报告不存在")
                
            if "treatment_report" in data:
                print("✓ 调理报告存在")
            else:
                print("✗ 调理报告不存在")
        else:
            print(f"请求失败: {response.status_code}")
            print(f"响应内容: {response.text}")
    except Exception as e:
        print(f"请求异常: {e}")

def test_get_user_reports():
    """测试获取用户所有报告列表"""
    print("\n=== 测试获取用户所有报告列表 ===")
    url = f"{BASE_URL}/api/v1/report/user/{USER_ID}"
    
    try:
        response = requests.get(url)
        print(f"请求URL: {url}")
        print(f"响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"响应内容:\n{json.dumps(data, ensure_ascii=False, indent=2)}")
            
            # 检查报告列表
            if "reports" in data:
                print(f"\n✓ 报告列表存在，共 {len(data['reports'])} 条记录")
                for i, report in enumerate(data['reports']):
                    print(f"\n  报告 {i+1}:")
                    print(f"    - ID: {report.get('id')}")
                    print(f"    - 会话ID: {report.get('session_id')}")
                    print(f"    - 创建时间: {report.get('created_at')}")
                    
                    # 检查三个报告字段
                    record = report.get('record_report_json')
                    analysis = report.get('analysis_report_json')
                    treatment = report.get('treatment_report_json')
                    
                    print(f"    - 记录报告: {'✓ 存在' if record else '✗ 不存在'}")
                    print(f"    - 分析报告: {'✓ 存在' if analysis else '✗ 不存在'}")
                    print(f"    - 调理报告: {'✓ 存在' if treatment else '✗ 不存在'}")
            else:
                print("\n✗ 报告列表不存在")
        else:
            print(f"请求失败: {response.status_code}")
            print(f"响应内容: {response.text}")
    except Exception as e:
        print(f"请求异常: {e}")

def test_end_session_and_generate_report():
    """测试结束会话并生成报告"""
    print("\n=== 测试结束会话并生成报告 ===")
    url = f"{BASE_URL}/api/v1/chat/end-session"
    
    data = {
        "user_id": USER_ID,
        "session_id": SESSION_ID
    }
    
    try:
        response = requests.post(url, json=data)
        print(f"请求URL: {url}")
        print(f"请求参数: {json.dumps(data, ensure_ascii=False)}")
        print(f"响应状态码: {response.status_code}")
        print(f"响应内容:\n{json.dumps(response.json(), ensure_ascii=False, indent=2)}")
    except Exception as e:
        print(f"请求异常: {e}")

if __name__ == "__main__":
    print("开始测试报告API接口...")
    
    # 测试获取报告（假设报告已存在）
    test_get_session_report()
    test_get_user_reports()
    
    # 测试结束会话生成报告
    # test_end_session_and_generate_report()
    
    print("\n测试完成!")
