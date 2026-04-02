"""
测试结束会话接口，生成报告
"""
import requests
import json

BASE_URL = "http://localhost:8000"

# 使用有对话记录的会话
USER_ID = "user_631a3f3e"
SESSION_ID = "session_ba0393fe"  # 有12条对话的会话

def test_end_session():
    """测试结束会话并生成报告"""
    print("=== 测试结束会话并生成报告 ===")
    url = f"{BASE_URL}/api/v1/chat/end-session"
    
    data = {
        "user_id": USER_ID,
        "session_id": SESSION_ID
    }
    
    try:
        print(f"请求URL: {url}")
        print(f"请求参数: {json.dumps(data, ensure_ascii=False)}")
        
        response = requests.post(url, json=data)
        print(f"响应状态码: {response.status_code}")
        print(f"响应内容:\n{json.dumps(response.json(), ensure_ascii=False, indent=2)}")
        
        if response.status_code == 200:
            result = response.json()
            if "report_id" in result:
                print(f"\n✓ 报告生成成功，报告ID: {result['report_id']}")
                return True
            else:
                print(f"\n✗ 报告生成失败: {result.get('error', '未知错误')}")
                return False
        else:
            print(f"\n✗ 请求失败: {response.text}")
            return False
    except Exception as e:
        print(f"请求异常: {e}")
        return False

def test_get_report():
    """测试获取生成的报告"""
    print("\n=== 测试获取生成的报告 ===")
    url = f"{BASE_URL}/api/v1/report/session/{SESSION_ID}"
    
    try:
        response = requests.get(url)
        print(f"请求URL: {url}")
        print(f"响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"响应内容:\n{json.dumps(data, ensure_ascii=False, indent=2)}")
            
            # 检查三个报告
            print("\n报告检查结果:")
            print(f"  - 记录报告: {'✓ 存在' if data.get('record_report') else '✗ 不存在'}")
            print(f"  - 分析报告: {'✓ 存在' if data.get('analysis_report') else '✗ 不存在'}")
            print(f"  - 调理报告: {'✓ 存在' if data.get('treatment_report') else '✗ 不存在'}")
            return True
        else:
            print(f"请求失败: {response.text}")
            return False
    except Exception as e:
        print(f"请求异常: {e}")
        return False

if __name__ == "__main__":
    print("开始测试结束会话接口...\n")
    
    # 先测试获取报告（应该不存在）
    print("1. 先检查报告是否存在:")
    test_get_report()
    
    # 调用结束会话接口生成报告
    print("\n2. 调用结束会话接口生成报告:")
    success = test_end_session()
    
    # 再次获取报告
    if success:
        print("\n3. 再次获取报告:")
        test_get_report()
    
    print("\n测试完成!")
