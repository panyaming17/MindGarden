#!/usr/bin/env python3
"""
验证数据库表结构脚本
检查conversations和messages表的结构和索引
"""
from backend.core.database import engine
from sqlalchemy import text

def check_database_structure():
    """检查数据库表结构"""
    try:
        # 连接数据库
        with engine.connect() as conn:
            print("成功连接到数据库")
            
            # 1. 检查conversations表结构
            print("\n=== conversations表结构 ===")
            result = conn.execute(text("DESCRIBE conversations;"))
            for row in result:
                print(f"{row[0]}: {row[1]}")
            
            # 检查conversations表索引
            print("\n=== conversations表索引 ===")
            result = conn.execute(text("SHOW INDEX FROM conversations;"))
            for row in result:
                print(f"{row[2]}: {row[4]}")
            
            # 2. 检查messages表结构
            print("\n=== messages表结构 ===")
            result = conn.execute(text("DESCRIBE messages;"))
            for row in result:
                print(f"{row[0]}: {row[1]}")
            
            # 检查messages表索引
            print("\n=== messages表索引 ===")
            result = conn.execute(text("SHOW INDEX FROM messages;"))
            for row in result:
                print(f"{row[2]}: {row[4]}")
            
            # 3. 检查当前数据库
            print("\n=== 当前数据库 ===")
            result = conn.execute(text("SELECT DATABASE();"))
            for row in result:
                print(f"当前数据库: {row[0]}")
            
    except Exception as e:
        print(f"连接数据库时出错: {e}")

if __name__ == "__main__":
    check_database_structure()
