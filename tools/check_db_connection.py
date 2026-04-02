#!/usr/bin/env python3
"""
检查数据库连接和user_archives表的数据情况
"""
from backend.core.database import SessionLocal, UserArchiveDB, SessionDB, UserDB

# 检查数据库连接和user_archives表
def check_database():
    print("开始检查数据库连接...")
    
    # 获取数据库会话
    db = SessionLocal()
    try:
        # 测试数据库连接
        print("数据库连接成功！")
        
        # 检查user_archives表
        print("\n检查user_archives表...")
        
        # 查询表结构
        from sqlalchemy import inspect
        inspector = inspect(db.bind)
        columns = inspector.get_columns('user_archives')
        print("表结构:")
        for column in columns:
            print(f"  - {column['name']}: {column['type']}")
        
        # 查询记录数
        archive_count = db.query(UserArchiveDB).count()
        print(f"\nuser_archives表记录数: {archive_count}")
        
        # 查询所有记录
        if archive_count > 0:
            print("\n表中的记录:")
            archives = db.query(UserArchiveDB).all()
            for i, archive in enumerate(archives):
                print(f"\n记录 {i+1}:")
                print(f"  user_id: {archive.user_id}")
                print(f"  session_id: {archive.session_id}")
                print(f"  version: {archive.version}")
                print(f"  created_at: {archive.created_at}")
                print(f"  updated_at: {archive.updated_at}")
                print(f"  archive_json: {archive.archive_json}")
        else:
            print("\nuser_archives表为空，没有任何记录！")
        
        # 检查sessions表
        print("\n检查sessions表...")
        session_count = db.query(SessionDB).count()
        print(f"sessions表记录数: {session_count}")
        
        # 检查users表
        print("\n检查users表...")
        user_count = db.query(UserDB).count()
        print(f"users表记录数: {user_count}")
        
    except Exception as e:
        print(f"数据库检查失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()
        print("\n数据库连接已关闭")

if __name__ == "__main__":
    check_database()
