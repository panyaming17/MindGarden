"""测试三个报告生成并打印详细内容"""
import requests
import json

BASE_URL = "http://localhost:8000"

# 测试数据
TEST_USER_ID = "user_631a3f3e"
TEST_SESSION_ID = "session_ba0393fe"

def test_end_session_and_print_reports():
    """测试结束会话并打印三个报告的详细内容"""
    print("=" * 80)
    print("测试结束会话并生成报告")
    print("=" * 80)
    
    url = f"{BASE_URL}/api/v1/chat/end-session"
    data = {
        "user_id": TEST_USER_ID,
        "session_id": TEST_SESSION_ID
    }
    
    print(f"\n请求参数:")
    print(f"  用户ID: {TEST_USER_ID}")
    print(f"  会话ID: {TEST_SESSION_ID}")
    
    try:
        response = requests.post(url, json=data)
        print(f"\n响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            if "reports" in result:
                reports = result["reports"]
                
                # 打印记录报告
                print("\n" + "=" * 80)
                print("【记录报告】record_report")
                print("=" * 80)
                record_report = reports.get("record_report", {})
                print(json.dumps(record_report, ensure_ascii=False, indent=2))
                
                # 打印分析报告
                print("\n" + "=" * 80)
                print("【分析报告】analysis_report")
                print("=" * 80)
                analysis_report = reports.get("analysis_report", {})
                print(json.dumps(analysis_report, ensure_ascii=False, indent=2))
                
                # 打印调理报告
                print("\n" + "=" * 80)
                print("【调理报告】treatment_report")
                print("=" * 80)
                treatment_report = reports.get("treatment_report", {})
                print(json.dumps(treatment_report, ensure_ascii=False, indent=2))
                
                return True
            else:
                print(f"\n❌ 报告生成失败: {result.get('error', '未知错误')}")
                return False
        else:
            print(f"\n❌ 请求失败: {response.status_code}")
            print(f"响应内容: {response.text}")
            return False
            
    except Exception as e:
        print(f"\n❌ 请求异常: {e}")
        return False

if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("报告生成测试脚本 - 打印详细内容")
    print("=" * 80)
    
    success = test_end_session_and_print_reports()
    
    print("\n" + "=" * 80)
    print("测试完成")
    print("=" * 80)
