#!/usr/bin/env python3
"""
检查用户表结构
"""

import sys
import os
import sqlite3

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def check_user_table():
    """检查用户表结构"""
    try:
        # 连接到数据库
        conn = sqlite3.connect('test.db')
        cursor = conn.cursor()
        
        # 查看用户表结构
        print("用户表结构:")
        cursor.execute("PRAGMA table_info(users)")
        columns = cursor.fetchall()
        
        for column in columns:
            print(f"字段名: {column[1]}, 类型: {column[2]}, 是否为主键: {column[5]}")
        
        # 查看用户数据
        print("\n用户数据:")
        cursor.execute("SELECT id, username, email, is_active, role FROM users")
        users = cursor.fetchall()
        
        for user in users:
            print(f"ID: {user[0]}, 用户名: {user[1]}, 邮箱: {user[2]}, 激活状态: {user[3]}, 角色: {user[4]}")
        
        conn.close()
        
    except Exception as e:
        print(f"检查用户表失败: {str(e)}")

if __name__ == "__main__":
    check_user_table()
