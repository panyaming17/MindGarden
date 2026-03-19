#!/usr/bin/env python3
"""
检查数据库中的对话记录
"""

import mysql.connector
from config import DatabaseConfig

# 连接数据库
def connect_db():
    return mysql.connector.connect(
        host=DatabaseConfig.DB_HOST,
        port=DatabaseConfig.DB_PORT,
        user=DatabaseConfig.DB_USER,
        password=DatabaseConfig.DB_PASSWORD,
        database=DatabaseConfig.DB_NAME
    )

def check_conversations():
    """检查对话记录"""
    print("检查对话记录...")
    conn = connect_db()
    cursor = conn.cursor()
    
    try:
        # 查询对话表
        cursor.execute("SELECT id, user_id, title, timestamp, phase FROM conversations ORDER BY created_at DESC LIMIT 10")
        conversations = cursor.fetchall()
        
        if conversations:
            print(f"找到 {len(conversations)} 条对话记录:")
            for conv in conversations:
                print(f"对话ID: {conv[0]}, 用户ID: {conv[1]}, 标题: {conv[2]}, 时间: {conv[3]}, 阶段: {conv[4]}")
        else:
            print("没有找到对话记录")
        
        # 查询消息表
        cursor.execute("SELECT conversation_id, role, content, created_at FROM messages ORDER BY created_at DESC LIMIT 20")
        messages = cursor.fetchall()
        
        if messages:
            print(f"\n找到 {len(messages)} 条消息记录:")
            for msg in messages:
                print(f"对话ID: {msg[0]}, 角色: {msg[1]}, 内容: {msg[2][:50]}..., 时间: {msg[3]}")
        else:
            print("\n没有找到消息记录")
            
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    check_conversations()
