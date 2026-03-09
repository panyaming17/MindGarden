#!/usr/bin/env python3
"""
在MySQL数据库中创建超级管理员用户
"""

import sys
import os
import pymysql
import bcrypt

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import DatabaseConfig

def get_password_hash(password):
    """获取密码哈希值"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def create_super_admin():
    """在MySQL数据库中创建超级管理员用户"""
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
        
        # 检查是否已存在超级管理员
        cursor.execute("SELECT * FROM users WHERE username = 'admin'")
        result = cursor.fetchone()
        
        if not result:
            # 创建超级管理员用户
            password = "123456"
            password_hash = get_password_hash(password)
            
            cursor.execute("""
                INSERT INTO users (id, username, password_hash, email, is_active, role, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, NOW(), NOW())
            """, (
                f"user_{os.urandom(8).hex()}",
                "admin",
                password_hash,
                "admin@example.com",
                1,
                "super_admin"
            ))
            
            conn.commit()
            print("超级管理员创建成功！")
            print(f"用户名: admin")
            print(f"密码: {password}")
            print(f"邮箱: admin@example.com")
            print(f"角色: super_admin")
        else:
            # 更新现有管理员的角色为super_admin
            cursor.execute("UPDATE users SET role = 'super_admin' WHERE username = 'admin'")
            conn.commit()
            print("超级管理员已存在，已更新角色为super_admin")
        
        conn.close()
        
    except Exception as e:
        print(f"创建超级管理员失败: {str(e)}")

if __name__ == "__main__":
    create_super_admin()
