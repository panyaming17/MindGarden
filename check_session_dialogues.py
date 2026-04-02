"""
检查指定会话的对话记录
"""
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import json

# 数据库连接
DATABASE_URL = "mysql+pymysql://root:123456@localhost:3306/emotional_coaching_system_db?charset=utf8mb4"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

USER_ID = "user_631a3f3e"
SESSION_ID = "session_e9958859"

def check_session_dialogues():
    """检查指定会话的对话记录"""
    db = SessionLocal()
    try:
        # 查询指定会话的对话记录
        result = db.execute(text("""
            SELECT id, user_id, session_id, role, content, created_at 
            FROM dialogues 
            WHERE user_id = :user_id AND session_id = :session_id
            ORDER BY created_at ASC
        """), {"user_id": USER_ID, "session_id": SESSION_ID})
        
        dialogues = result.fetchall()
        print(f"会话 {SESSION_ID} 共有 {len(dialogues)} 条对话记录\n")
        
        for i, d in enumerate(dialogues):
            print(f"对话 {i+1}:")
            print(f"  - ID: {d.id}")
            print(f"  - 角色: {d.role}")
            print(f"  - 内容: {d.content[:50]}..." if len(d.content) > 50 else f"  - 内容: {d.content}")
            print(f"  - 创建时间: {d.created_at}")
            print()
    except Exception as e:
        print(f"查询失败: {e}")
    finally:
        db.close()

def check_all_sessions():
    """检查所有会话的对话数量"""
    db = SessionLocal()
    try:
        result = db.execute(text("""
            SELECT session_id, COUNT(*) as count 
            FROM dialogues 
            WHERE user_id = :user_id
            GROUP BY session_id
            ORDER BY count DESC
            LIMIT 10
        """), {"user_id": USER_ID})
        
        sessions = result.fetchall()
        print(f"用户 {USER_ID} 的会话对话数量:\n")
        for s in sessions:
            print(f"  - {s.session_id}: {s.count} 条对话")
    except Exception as e:
        print(f"查询失败: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    print("=== 检查会话对话记录 ===\n")
    
    check_session_dialogues()
    print("\n" + "="*50 + "\n")
    check_all_sessions()
    
    print("\n检查完成!")
