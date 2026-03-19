#!/usr/bin/env python3
"""
使用 SQLAlchemy 检查数据库中的对话记录
"""

from backend.core.database import SessionLocal, ConversationDB, MessageDB

def check_conversations():
    """检查对话记录"""
    print("检查对话记录...")
    db = SessionLocal()
    
    try:
        # 查询对话表
        conversations = db.query(ConversationDB).order_by(ConversationDB.created_at.desc()).limit(10).all()
        
        if conversations:
            print(f"找到 {len(conversations)} 条对话记录:")
            for conv in conversations:
                print(f"对话ID: {conv.id}, 用户ID: {conv.user_id}, 标题: {conv.title}, 时间: {conv.timestamp}, 阶段: {conv.phase}")
        else:
            print("没有找到对话记录")
        
        # 查询消息表
        messages = db.query(MessageDB).order_by(MessageDB.created_at.desc()).limit(20).all()
        
        if messages:
            print(f"\n找到 {len(messages)} 条消息记录:")
            for msg in messages:
                print(f"对话ID: {msg.conversation_id}, 角色: {msg.role}, 内容: {msg.content[:50]}..., 时间: {msg.created_at}")
        else:
            print("\n没有找到消息记录")
            
    finally:
        db.close()

if __name__ == "__main__":
    check_conversations()
