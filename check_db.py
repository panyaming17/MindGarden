#!/usr/bin/env python3
"""
检查数据库表结构和数据
"""
from backend.core.database import SessionLocal, SessionDB, UserArchiveDB, DialogueDB

# 检查sessions表
db = SessionLocal()
try:
    print("=== 检查sessions表 ===")
    # 尝试查询sessions表
    try:
        sessions = db.query(SessionDB).all()
        print(f"sessions表存在，共有 {len(sessions)} 条记录")
        for session in sessions:
            print(f"  - 会话ID: {session.id}, 用户ID: {session.user_id}")
    except Exception as e:
        print(f"查询sessions表失败: {e}")
    
    print("\n=== 检查user_archives表 ===")
    # 尝试查询user_archives表
    try:
        archives = db.query(UserArchiveDB).all()
        print(f"user_archives表存在，共有 {len(archives)} 条记录")
        for archive in archives:
            print(f"  - 档案ID: {archive.id}, 用户ID: {archive.user_id}, 会话ID: {archive.session_id}")
    except Exception as e:
        print(f"查询user_archives表失败: {e}")
    
    print("\n=== 检查dialogues表 ===")
    # 尝试查询dialogues表
    try:
        dialogues = db.query(DialogueDB).all()
        print(f"dialogues表存在，共有 {len(dialogues)} 条记录")
        # 只打印前10条
        for i, dialogue in enumerate(dialogues[:10]):
            print(f"  - {i+1}. 用户ID: {dialogue.user_id}, 会话ID: {dialogue.session_id}, 角色: {dialogue.role}, 内容: {dialogue.content[:50]}..., 有价值: {dialogue.is_valuable}")
        if len(dialogues) > 10:
            print(f"  ... 还有 {len(dialogues) - 10} 条记录")
    except Exception as e:
        print(f"查询dialogues表失败: {e}")
finally:
    db.close()
