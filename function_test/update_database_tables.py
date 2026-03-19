#!/usr/bin/env python3
"""
更新数据库表结构脚本
根据提供的SQL语句更新conversations和messages表结构
"""
from backend.core.database import engine
from sqlalchemy import text

def update_database_tables():
    """更新数据库表结构"""
    try:
        # 连接数据库
        with engine.connect() as conn:
            print("成功连接到数据库")
            
            # 1. 确保conversations表结构正确
            print("\n1. 检查并更新conversations表结构...")
            
            # 添加缺失的索引
            indexes = [
                ("idx_user_id", "user_id"),
                ("idx_timestamp", "timestamp"),
                ("idx_phase", "phase")
            ]
            
            for index_name, column_name in indexes:
                try:
                    # 先检查索引是否存在
                    check_index_sql = f"SHOW INDEX FROM conversations WHERE Key_name = '{index_name}';"
                    result = conn.execute(text(check_index_sql)).fetchall()
                    
                    if not result:
                        # 索引不存在，添加索引
                        add_index_sql = f"ALTER TABLE conversations ADD INDEX {index_name} ({column_name});"
                        conn.execute(text(add_index_sql))
                        print(f"✓ 已添加{index_name}索引")
                    else:
                        print(f"✓ {index_name}索引已存在")
                except Exception as e:
                    print(f"⚠ 处理{index_name}索引时出错: {e}")
            
            # 2. 重建messages表
            print("\n2. 重建messages表...")
            
            # 先删除现有表
            try:
                conn.execute(text("DROP TABLE IF EXISTS messages;"))
                print("✓ 已删除旧的messages表")
            except Exception as e:
                print(f"⚠ 删除messages表时出错: {e}")
            
            # 创建新表
            try:
                create_messages_table_sql = """
                CREATE TABLE messages (
                    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '消息唯一ID',
                    conversation_id VARCHAR(50) NOT NULL COMMENT '所属会话ID',
                    role ENUM('user', 'recorder', 'analyst', 'therapist', 'system') NOT NULL COMMENT '发送者角色',
                    content TEXT NOT NULL COMMENT '消息内容',
                    input_tokens INT UNSIGNED NULL COMMENT '用户输入或API请求的token数',
                    output_tokens INT UNSIGNED NULL COMMENT '模型回复的token数',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '消息发送时间',
                    FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE,
                    INDEX idx_conversation_time (conversation_id, created_at)
                ) COMMENT='消息表，存储对话中的每一条消息';
                """
                conn.execute(text(create_messages_table_sql))
                print("✓ 已创建新的messages表")
            except Exception as e:
                print(f"⚠ 创建messages表时出错: {e}")
            
            # 提交事务
            conn.commit()
            print("\n✅ 数据库表结构更新完成")
            
    except Exception as e:
        print(f"连接数据库时出错: {e}")

if __name__ == "__main__":
    update_database_tables()
