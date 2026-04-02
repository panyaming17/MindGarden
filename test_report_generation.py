"""
测试报告生成功能
需要提供的测试数据：
- user_id: 用户ID（已有用户）
- session_id: 会话ID（已有会话，且该会话有对话记录）
"""
import requests
import json

BASE_URL = "http://localhost:8000"

# 请提供以下测试数据：
TEST_USER_ID = "user_631a3f3e"  # 已有用户的ID
TEST_SESSION_ID = "session_ba0393fe"  # 已有会话的ID（需要有对话记录）

def test_end_session_and_generate_reports():
    """测试结束会话并生成三个报告"""
    print("=" * 60)
    print("测试结束会话并生成报告")
    print("=" * 60)
    
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
            print(f"\n响应内容:")
            print(json.dumps(result, ensure_ascii=False, indent=2))
            
            if "report_id" in result:
                print(f"\n✅ 报告生成成功!")
                print(f"   报告ID: {result['report_id']}")
                
                # 显示三个报告的摘要
                reports = result.get("reports", {})
                if reports:
                    print(f"\n📊 报告摘要:")
                    
                    record_report = reports.get("record_report", {})
                    if record_report:
                        print(f"\n  [记录报告]")
                        print(f"    - 情境数: {len(record_report.get('situations', []))}")
                        print(f"    - 情绪数: {len(record_report.get('emotions', []))}")
                        print(f"    - 自动思维数: {len(record_report.get('automatic_thoughts', []))}")
                    
                    analysis_report = reports.get("analysis_report", {})
                    if analysis_report:
                        print(f"\n  [分析报告]")
                        four_dim = analysis_report.get("four_dim_summary", {})
                        print(f"    - 平均强度: {four_dim.get('avg_intensity', 'N/A')}")
                        print(f"    - 思维陷阱: {len(analysis_report.get('cognitive_analysis', {}).get('thinking_traps', []))}")
                    
                    treatment_report = reports.get("treatment_report", {})
                    if treatment_report:
                        print(f"\n  [调理报告]")
                        print(f"    - 融合策略: {len(treatment_report.get('fusion_strategies', []))}")
                        print(f"    - CBT作业: {len(treatment_report.get('cbt_homework', []))}")
                        print(f"    - 中医实践: {len(treatment_report.get('tcm_practices', []))}")
                
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

def test_get_session_report():
    """测试获取生成的报告"""
    print("\n" + "=" * 60)
    print("测试获取会话报告")
    print("=" * 60)
    
    url = f"{BASE_URL}/api/v1/report/session/{TEST_SESSION_ID}"
    
    try:
        response = requests.get(url)
        print(f"\n响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n✅ 获取报告成功!")
            
            # 检查三个报告
            print(f"\n📋 报告详情:")
            
            if "record_report" in data and data["record_report"]:
                print(f"  ✓ 记录报告: 已存在")
            else:
                print(f"  ✗ 记录报告: 不存在")
                
            if "analysis_report" in data and data["analysis_report"]:
                print(f"  ✓ 分析报告: 已存在")
            else:
                print(f"  ✗ 分析报告: 不存在")
                
            if "treatment_report" in data and data["treatment_report"]:
                print(f"  ✓ 调理报告: 已存在")
            else:
                print(f"  ✗ 调理报告: 不存在")
            
            return True
        else:
            print(f"\n❌ 获取失败: {response.status_code}")
            print(f"响应内容: {response.text}")
            return False
            
    except Exception as e:
        print(f"\n❌ 请求异常: {e}")
        return False

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("报告生成测试脚本")
    print("=" * 60)
    print(f"\n使用测试数据:")
    print(f"  用户ID: {TEST_USER_ID}")
    print(f"  会话ID: {TEST_SESSION_ID}")
    
    # 第一步：结束会话并生成报告
    success = test_end_session_and_generate_reports()
    
    # 第二步：获取生成的报告
    if success:
        test_get_session_report()
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)
