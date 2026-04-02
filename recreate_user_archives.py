#!/usr/bin/env python3
"""
重新创建user_archives表，确保外键约束正确指向chat_sessions表
"""
from sqlalchemy import create_engine, text
from config import DatabaseConfig

# 连接数据库
def recreate_user_archives_table():
    print("开始重新创建user_archives表...")
    
    # 创建数据库引擎
    engine = create_engine(
        DatabaseConfig.SQLALCHEMY_DATABASE_URL,
        **DatabaseConfig.SQLALCHEMY_ENGINE_OPTIONS
    )
    
    # 执行SQL语句删除并重新创建user_archives表
    try:
        with engine.connect() as conn:
            # 先删除user_archives表
            print("删除user_archives表...")
            conn.execute(text("DROP TABLE IF EXISTS user_archives;"))
            conn.commit()
            print("user_archives表删除成功！")
        
        # 重新创建所有表
        print("重新创建所有表...")
        from backend.core.database import Base
        Base.metadata.create_all(bind=engine)
        print("表创建成功！")
        
        # 检查外键约束
        with engine.connect() as conn:# 检查外键约束
            print("检查user_archives表的外键约束...")
            result = conn.execute(text("SHOW CREATE TABLE user_archives;"))
            for row in result:
                print(row[1])
        
    except Exception as e:
        print(f"重新创建表失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    recreate_user_archives_table()
