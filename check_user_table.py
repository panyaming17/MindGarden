#!/usr/bin/env python3
"""
查询数据库中的user表数据
"""
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from backend.core.database import engine, UserDB, SessionLocal
from sqlalchemy.orm import Session

def check_user_table():
    """检查user表数据"""
    print("===== 检查数据库连接 =====")
    print(f"数据库URL: {engine.url}")
    
    # 创建数据库会话
    db = SessionLocal()
    
    try:
        # 查询所有用户
        users = db.query(UserDB).all()
        
        print("\n===== user表数据 =====")
        if not users:
            print("user表为空，没有用户数据")
        else:
            print(f"找到 {len(users)} 个用户:")
            for user in users:
                print(f"ID: {user.id}, 用户名: {user.username}, 邮箱: {user.email}, 角色: {user.role}, 活跃状态: {user.is_active}")
        
    except Exception as e:
        print(f"查询失败: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check_user_table()
