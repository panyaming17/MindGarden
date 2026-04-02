#!/usr/bin/env python3
"""
检查UserDB表的结构和数据
"""
from backend.core.database import SessionLocal, UserDB

# 检查UserDB表
db = SessionLocal()
try:
    print("=== 检查UserDB表 ===")
    # 尝试查询UserDB表
    try:
        users = db.query(UserDB).all()
        print(f"UserDB表存在，共有 {len(users)} 条记录")
        for user in users:
            print(f"  - 用户ID: {user.id}, 用户名: {user.username}, 邮箱: {user.email}, 角色: {user.role}, 活跃: {user.is_active}")
    except Exception as e:
        print(f"查询UserDB表失败: {e}")
finally:
    db.close()
