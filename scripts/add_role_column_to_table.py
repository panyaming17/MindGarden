#!/usr/bin/env python3
"""
为数据库表添加role字段
"""

import sys
import os
import pymysql

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import DatabaseConfig

def add_role_column_to_table(table_name="users"):
    """为指定表添加role字段"""
    try:
        # 连接到MySQL数据库
        conn = pymysql.connect(
            host=DatabaseConfig.DB_HOST,
            port=DatabaseConfig.DB_PORT,
            user=DatabaseConfig.DB_USER,
            password=DatabaseConfig.DB_PASSWORD,
            database=DatabaseConfig.DB_NAME,
            charset='utf8mb4'
        )
        
        cursor = conn.cursor()
        
        # 检查role字段是否存在
        cursor.execute(f"SHOW COLUMNS FROM {table_name} LIKE 'role'")
        result = cursor.fetchone()
        
        if not result:
            # 添加role字段
            cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN role VARCHAR(20) DEFAULT 'user' NOT NULL")
            conn.commit()
            print(f"成功为{table_name}表添加role字段")
        else:
            print(f"{table_name}表中role字段已存在，无需添加")
        
        conn.close()
        
    except Exception as e:
        print(f"添加role字段失败: {str(e)}")

def verify_table_structure(table_name="users"):
    """验证表结构"""
    try:
        # 连接到MySQL数据库
        conn = pymysql.connect(
            host=DatabaseConfig.DB_HOST,
            port=DatabaseConfig.DB_PORT,
            user=DatabaseConfig.DB_USER,
            password=DatabaseConfig.DB_PASSWORD,
            database=DatabaseConfig.DB_NAME,
            charset='utf8mb4'
        )
        
        cursor = conn.cursor()
        
        # 查看表结构
        print(f"{table_name}表结构:")
        cursor.execute(f"DESCRIBE {table_name}")
        columns = cursor.fetchall()
        
        for column in columns:
            print(f"字段名: {column[0]}, 类型: {column[1]}, 是否为空: {column[2]}, 主键: {column[3]}, 默认值: {column[4]}, 额外: {column[5]}")
        
        # 查看前5条数据
        print(f"\n{table_name}表前5条数据:")
        cursor.execute(f"SELECT * FROM {table_name} LIMIT 5")
        rows = cursor.fetchall()
        
        # 获取字段名
        cursor.execute(f"DESCRIBE {table_name}")
        column_names = [column[0] for column in cursor.fetchall()]
        
        # 打印表头
        print(" | ".join(column_names))
        print("-" * 80)
        
        # 打印数据
        for row in rows:
            print(" | ".join(str(item) for item in row))
        
        conn.close()
        
    except Exception as e:
        print(f"验证表结构失败: {str(e)}")

if __name__ == "__main__":
    # 为users表添加role字段
    add_role_column_to_table("users")
    
    # 验证表结构
    verify_table_structure("users")
