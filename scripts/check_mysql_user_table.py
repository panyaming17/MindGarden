#!/usr/bin/env python3
"""
检查MySQL数据库中的用户表结构
"""

import sys
import os
import pymysql

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import DatabaseConfig

def check_mysql_user_table():
    """检查MySQL数据库中的用户表结构"""
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
        
        # 查看用户表结构
        print("用户表结构:")
        cursor.execute("DESCRIBE users")
        columns = cursor.fetchall()
        
        for column in columns:
            print(f"字段名: {column[0]}, 类型: {column[1]}, 是否为空: {column[2]}, 主键: {column[3]}, 默认值: {column[4]}, 额外: {column[5]}")
        
        # 查看用户数据
        print("\n用户数据:")
        cursor.execute("SELECT id, username, email, is_active, role FROM users")
        users = cursor.fetchall()
        
        for user in users:
            print(f"ID: {user[0]}, 用户名: {user[1]}, 邮箱: {user[2]}, 激活状态: {user[3]}, 角色: {user[4]}")
        
        conn.close()
        
    except Exception as e:
        print(f"检查MySQL用户表失败: {str(e)}")

if __name__ == "__main__":
    check_mysql_user_table()
