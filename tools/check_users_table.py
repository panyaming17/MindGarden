#!/usr/bin/env python3
"""
检查users表的结构
"""
import mysql.connector
from config import DatabaseConfig

# 连接数据库
def check_users_table():
    print("开始检查users表结构...")
    
    # 解析数据库连接字符串
    import re
    db_url = DatabaseConfig.SQLALCHEMY_DATABASE_URL
    match = re.match(r"mysql\+pymysql://(.*):(.*)@(.*):(.*)/(.*)\?.*", db_url)
    if match:
        user, password, host, port, db = match.groups()
        print(f"数据库连接信息: 主机={host}, 端口={port}, 数据库={db}, 用户={user}")
        
        # 连接数据库
        try:
            conn = mysql.connector.connect(
                host=host,
                port=port,
                user=user,
                password=password,
                database=db
            )
            cursor = conn.cursor()
            
            # 检查users表结构
            cursor.execute("DESCRIBE users")
            print("\nusers表结构:")
            for row in cursor:
                print(f"  - {row[0]}: {row[1]}, 允许空: {row[2]}, 键: {row[3]}, 默认值: {row[4]}, 额外: {row[5]}")
            
            # 关闭连接
            cursor.close()
            conn.close()
        except Exception as e:
            print(f"数据库连接失败: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("无法解析数据库连接字符串")

if __name__ == "__main__":
    check_users_table()
