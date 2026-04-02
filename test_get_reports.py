#!/usr/bin/env python3
"""
测试获取会话报告接口
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_login(username, password):
    """测试登录接口"""
    print("测试登录...")
    
    url = f"{BASE_URL}/api/v1/auth/login"
    headers = {
        "Content-Type": "application/json"
    }
    data = {
        "username": username,
        "password": password
    }
    
    try:
        response = requests.post(url, headers=headers, data=json.dumps(data))
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            token = result.get("access_token")
            user_id = result.get("user", {}).get("id")
            print("✅ 登录成功！")
            print(f"用户ID: {user_id}")
            return token, user_id
        else:
            print(f"❌ 登录失败: {response.json().get('detail')}")
            return None, None
    
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        return None, None

def test_get_reports(user_id, session_id, token):
    """测试获取会话报告接口"""
    print("\n测试获取会话报告...")
    
    # 使用正确的报告API路径
    report_paths = [
        f"{BASE_URL}/api/v1/report/session/{session_id}"
    ]
    
    for path in report_paths:
        print(f"\n尝试路径: {path}")
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        }
        
        try:
            response = requests.get(path, headers=headers)
            print(f"状态码: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ 获取会话报告成功！")
                print(f"响应内容: {json.dumps(result, ensure_ascii=False, indent=2)}")
                
                # 检查报告类型
                if "record_report" in result:
                    print("\n📋 记录报告:")
                    print(json.dumps(result.get("record_report"), ensure_ascii=False, indent=2))
                if "analysis_report" in result:
                    print("\n📊 分析报告:")
                    print(json.dumps(result.get("analysis_report"), ensure_ascii=False, indent=2))
                if "treatment_report" in result:
                    print("\n💊 调理报告:")
                    print(json.dumps(result.get("treatment_report"), ensure_ascii=False, indent=2))
                
                return True
            else:
                print(f"❌ 获取会话报告失败: {response.json().get('detail') if response.content else 'No content'}")
        
        except Exception as e:
            print(f"❌ 测试失败: {str(e)}")
    
    return False

def test_get_report_list(user_id, token):
    """测试获取报告列表接口"""
    print("\n测试获取报告列表...")
    
    # 使用正确的用户报告API路径
    list_paths = [
        f"{BASE_URL}/api/v1/report/user/{user_id}"
    ]
    
    for path in list_paths:
        print(f"\n尝试路径: {path}")
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        }
        try:
            response = requests.get(path, headers=headers)
            print(f"状态码: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ 获取报告列表成功！")
                print(f"响应内容: {json.dumps(result, ensure_ascii=False, indent=2)}")
                
                reports = result.get('reports', [])
                print(f"共{len(reports)}个报告")
                
                for i, report in enumerate(reports, 1):
                    print(f"\n报告 {i}:")
                    print(f"  会话ID: {report.get('session_id')}")
                    print(f"  创建时间: {report.get('created_at')}")
                
                return True
            else:
                print(f"❌ 获取报告列表失败: {response.json().get('detail') if response.content else 'No content'}")
        
        except Exception as e:
            print(f"❌ 测试失败: {str(e)}")
    
    return False

if __name__ == "__main__":
    print("====================================")
    print("测试获取会话报告")
    print("====================================")
    
    # 测试账号信息
    username = "pym"
    password = "pym123456"
    session_id = "session_70db0c09"
    
    # 1. 测试登录
    token, user_id = test_login(username, password)
    
    if token and user_id:
        # 2. 测试获取会话报告
        test_get_reports(user_id, session_id, token)
        
        # 3. 测试获取报告列表
        test_get_report_list(user_id, token)
    else:
        print("❌ 登录失败，无法继续测试")
    
    print("\n====================================")
    print("测试完成")
    print("====================================")
