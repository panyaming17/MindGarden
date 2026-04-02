"""
问卷API测试脚本
"""
import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"
TEST_USER_ID = "user_test_001"

def test_get_next_due():
    """测试获取待测问卷"""
    print("\n" + "="*60)
    print("测试1: 获取待测问卷")
    print("="*60)
    
    url = f"{BASE_URL}/api/questionnaires/next-due"
    params = {"user_id": TEST_USER_ID}
    
    try:
        response = requests.get(url, params=params)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"响应数据:\n{json.dumps(data, ensure_ascii=False, indent=2)}")
            return True
        else:
            print(f"请求失败: {response.text}")
            return False
    except Exception as e:
        print(f"异常: {e}")
        return False


def test_get_template(code="PHQ9"):
    """测试获取问卷模板"""
    print("\n" + "="*60)
    print(f"测试2: 获取问卷模板 ({code})")
    print("="*60)
    
    url = f"{BASE_URL}/api/questionnaires/{code}/template"
    
    try:
        response = requests.get(url)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"问卷名称: {data['data']['name']}")
            print(f"题目数量: {len(data['data']['questions'])}")
            print(f"\n第一题示例:")
            if data['data']['questions']:
                first_q = data['data']['questions'][0]
                print(f"  ID: {first_q['id']}")
                print(f"  文本: {first_q['text']}")
                print(f"  选项数: {len(first_q['options'])}")
            return True
        else:
            print(f"请求失败: {response.text}")
            return False
    except Exception as e:
        print(f"异常: {e}")
        return False


def test_submit_questionnaire():
    """测试提交问卷"""
    print("\n" + "="*60)
    print("测试3: 提交问卷 (PHQ-9)")
    print("="*60)
    
    url = f"{BASE_URL}/api/questionnaires/submit"
    params = {"user_id": TEST_USER_ID}
    
    # 构造PHQ-9答案（模拟轻度抑郁）
    answers = [
        {"question_id": "phq-1", "option_id": "o1", "score": 1},
        {"question_id": "phq-2", "option_id": "o1", "score": 1},
        {"question_id": "phq-3", "option_id": "o2", "score": 2},
        {"question_id": "phq-4", "option_id": "o1", "score": 1},
        {"question_id": "phq-5", "option_id": "o0", "score": 0},
        {"question_id": "phq-6", "option_id": "o1", "score": 1},
        {"question_id": "phq-7", "option_id": "o1", "score": 1},
        {"question_id": "phq-8", "option_id": "o0", "score": 0},
        {"question_id": "phq-9", "option_id": "o0", "score": 0},
    ]
    
    body = {
        "template_code": "PHQ9",
        "answers": answers
    }
    
    try:
        response = requests.post(url, params=params, json=body)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"响应数据:\n{json.dumps(data, ensure_ascii=False, indent=2)}")
            return True
        else:
            print(f"请求失败: {response.text}")
            return False
    except Exception as e:
        print(f"异常: {e}")
        return False


def test_skip_questionnaire():
    """测试跳过问卷"""
    print("\n" + "="*60)
    print("测试4: 跳过问卷 (GAD-7)")
    print("="*60)
    
    url = f"{BASE_URL}/api/questionnaires/skip"
    params = {"user_id": TEST_USER_ID}
    
    body = {
        "template_code": "GAD7"
    }
    
    try:
        response = requests.post(url, params=params, json=body)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"响应数据:\n{json.dumps(data, ensure_ascii=False, indent=2)}")
            return True
        else:
            print(f"请求失败: {response.text}")
            return False
    except Exception as e:
        print(f"异常: {e}")
        return False


def test_get_history():
    """测试获取历史记录"""
    print("\n" + "="*60)
    print("测试5: 获取历史记录")
    print("="*60)
    
    url = f"{BASE_URL}/api/questionnaires/history"
    params = {
        "user_id": TEST_USER_ID,
        "template_code": "PHQ9",
        "limit": 5
    }
    
    try:
        response = requests.get(url, params=params)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"响应数据:\n{json.dumps(data, ensure_ascii=False, indent=2)}")
            return True
        else:
            print(f"请求失败: {response.text}")
            return False
    except Exception as e:
        print(f"异常: {e}")
        return False


def run_all_tests():
    """运行所有测试"""
    print("\n" + "="*60)
    print("问卷API测试开始")
    print("="*60)
    print(f"测试用户ID: {TEST_USER_ID}")
    print(f"基础URL: {BASE_URL}")
    
    results = []
    
    # 测试1: 获取待测问卷
    results.append(("获取待测问卷", test_get_next_due()))
    
    # 测试2: 获取问卷模板
    results.append(("获取PHQ-9模板", test_get_template("PHQ9")))
    results.append(("获取GAD-7模板", test_get_template("GAD7")))
    
    # 测试3: 提交问卷
    results.append(("提交问卷", test_submit_questionnaire()))
    
    # 测试4: 跳过问卷
    results.append(("跳过问卷", test_skip_questionnaire()))
    
    # 测试5: 获取历史记录
    results.append(("获取历史记录", test_get_history()))
    
    # 打印测试结果汇总
    print("\n" + "="*60)
    print("测试结果汇总")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{status}: {name}")
    
    print(f"\n总计: {passed}/{total} 通过")
    
    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
