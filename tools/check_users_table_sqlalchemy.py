#!/usr/bin/env python3
"""
使用SQLAlchemy检查users表的结构
"""
from backend.core.database import SessionLocal
from sqlalchemy import inspect

# 检查users表结构
def check_users_table():
    print("开始检查users表结构...")
    
    # 获取数据库会话
    db = SessionLocal()
    try:
        # 获取inspector
        inspector = inspect(db.bind)
        
        # 检查users表结构
        columns = inspector.get_columns('users')
        print("\nusers表结构:")
        for column in columns:
            print(f"  - {column['name']}: {column['type']}")
        
        # 检查chat_sessions表是否存在
        tables = inspector.get_table_names()
        print("\n数据库中的表:")
        for table in tables:
            print(f"  - {table}")
        
    except Exception as e:
        print(f"检查表结构失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    check_users_table()
