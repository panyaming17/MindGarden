#!/usr/bin/env python3
"""
为MySQL数据库的users表添加role字段
"""

import sys
import os
import pymysql

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import DatabaseConfig

def add_role_column():
    """为users表添加role字段"""
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
        cursor.execute("SHOW COLUMNS FROM users LIKE 'role'")
        result = cursor.fetchone()
        
        if not result:
            # 添加role字段
            cursor.execute("ALTER TABLE users ADD COLUMN role VARCHAR(20) DEFAULT 'user' NOT NULL")
            conn.commit()
            print("成功为users表添加role字段")
        else:
            print("role字段已存在，无需添加")
        
        conn.close()
        
    except Exception as e:
        print(f"添加role字段失败: {str(e)}")

if __name__ == "__main__":
    add_role_column()
