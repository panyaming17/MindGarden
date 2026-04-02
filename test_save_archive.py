#!/usr/bin/env python3
"""
测试保存用户认知档案
"""
from backend.repositories.record_repository_new import RecordRepository

# 测试数据
user_id = "user_631a3f3e"
session_id = "sess_test123"
test_archive = {
    "session_id": "sess_test123",
    "user_id": "user_631a3f3e",
    "created_at": "2026-03-27T00:00:00Z",
    "updated_at": "2026-03-27T00:00:00Z",
    "title": "测试会话",
    "basic_info": {
        "age": None,
        "gender": None,
        "occupation": None,
        "main_issues": ["工作压力", "焦虑"]
    },
    "emotional_timeline": {
        "summary": "用户近期工作压力大，感到焦虑",
        "trends": {
            "intensity": "高",
            "hedonic": "负性",
            "tension": "高",
            "complexity": "复杂"
        },
        "key_events": [
            {
                "timestamp": "2026-03-27T00:00:00Z",
                "event": "用户提到工作压力大",
                "description": "我最近工作压力很大，感觉喘不过气来",
                "four_dim": { "intensity": 8.0, "hedonic": "负性", "tension": "高", "complexity": "复杂" }
            }
        ]
    },
    "cognitive_patterns": {
        "common_automatic_thoughts": ["我做不好工作", "我会被解雇"],
        "thinking_traps": ["过度概括", "情绪化推理"],
        "core_beliefs": ["我无能", "我不值得被认可"]
    },
    "situations": [
        {
            "timestamp": "2026-03-27T00:00:00Z",
            "description": "工作任务繁重",
            "related_thoughts": ["我做不好工作"],
            "emotional_response": "焦虑、沮丧"
        }
    ],
    "intervention_history": [],
    "current_focus": "工作压力管理",
    "summary": "用户因工作压力大而感到焦虑，需要帮助管理压力和负面情绪"
}

# 测试保存用户认知档案
def test_save_user_archive():
    print("开始测试保存用户认知档案...")
    
    # 实例化 RecordRepository
    repository = RecordRepository()
    
    try:
        # 保存用户认知档案
        repository.save_user_archive(user_id, session_id, test_archive, version=1)
        print("测试保存用户认知档案成功！")
        
        # 验证保存结果
        saved_archive = repository.get_user_archive(user_id, session_id)
        if saved_archive:
            print("验证保存结果成功！")
            print(f"保存的档案ID: {saved_archive.get('user_id')}")
            print(f"保存的会话ID: {saved_archive.get('session_id')}")
            print(f"保存的版本号: {saved_archive.get('version')}")
            print(f"保存的档案内容: {saved_archive.get('archive_json')}")
        else:
            print("验证保存结果失败：未找到保存的档案")
    except Exception as e:
        print(f"测试保存用户认知档案失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_save_user_archive()
