"""
数据库迁移脚本 v1.0
功能：
1. 删除冗余表（session_four_dim_data, questionnaires, user_questionnaire_results）
2. 为 session_analysis_insights 表添加新字段
3. 验证迁移结果

使用方法：
    python backend/scripts/migrate_database.py
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# 现在可以导入 backend 模块
from sqlalchemy import create_engine, text, inspect
from backend.core.database import DBConfig

def check_table_exists(engine, table_name):
    """检查表是否存在"""
    inspector = inspect(engine)
    return table_name in inspector.get_table_names()

def check_column_exists(engine, table_name, column_name):
    """检查列是否存在"""
    inspector = inspect(engine)
    if not check_table_exists(engine, table_name):
        return False
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    return column_name in columns

def drop_table_if_exists(engine, table_name):
    """删除表"""
    with engine.connect() as conn:
        try:
            conn.execute(text(f"DROP TABLE IF EXISTS {table_name}"))
            conn.commit()
            print(f"✓ 已删除表：{table_name}")
            return True
        except Exception as e:
            print(f"✗ 删除表失败 {table_name}: {e}")
            conn.rollback()
            return False

def add_column_if_not_exists(engine, table_name, column_name, column_type, default=None):
    """添加列"""
    if check_column_exists(engine, table_name, column_name):
        print(f"  - 列已存在：{table_name}.{column_name}，跳过")
        return True
    
    with engine.connect() as conn:
        try:
            default_clause = f" DEFAULT {default}" if default is not None else ""
            sql = f"ALTER TABLE {table_name} ADD {column_name} {column_type}{default_clause}"
            conn.execute(text(sql))
            conn.commit()
            print(f"✓ 已添加列：{table_name}.{column_name}")
            return True
        except Exception as e:
            print(f"✗ 添加列失败 {table_name}.{column_name}: {e}")
            conn.rollback()
            return False

def migrate_database():
    """执行数据库迁移"""
    print("=" * 60)
    print("数据库迁移脚本 v1.0")
    print("=" * 60)
    
    # 获取数据库引擎
    try:
        db_factory = DBConfig.get_db
        # 获取一个会话来提取引擎
        db = next(db_factory())
        engine = db.get_bind()
        db.close()
        print("✓ 数据库连接成功")
    except Exception as e:
        print(f"✗ 数据库连接失败：{e}")
        return False
    
    # ========== 第一步：删除冗余表 ==========
    print("\n" + "=" * 60)
    print("第一步：删除冗余表")
    print("=" * 60)
    
    tables_to_drop = [
        'session_four_dim_data',
        'questionnaires',
        'user_questionnaire_results'
    ]
    
    drop_success = True
    for table_name in tables_to_drop:
        if check_table_exists(engine, table_name):
            if not drop_table_if_exists(engine, table_name):
                drop_success = False
        else:
            print(f"  - 表不存在：{table_name}，跳过")
    
    if not drop_success:
        print("\n✗ 删除表过程中出现错误")
        return False
    
    print("\n✓ 冗余表删除完成")
    
    # ========== 第二步：添加新字段 ==========
    print("\n" + "=" * 60)
    print("第二步：为 session_analysis_insights 添加新字段")
    print("=" * 60)
    
    # 检查表是否存在
    if not check_table_exists(engine, 'session_analysis_insights'):
        print("✗ session_analysis_insights 表不存在，无法添加字段")
        return False
    
    # 定义要添加的字段
    new_columns = [
        ('intensity_values', 'LONGTEXT', None),
        ('hedonic_counts', 'LONGTEXT', None),
        ('tension_counts', 'LONGTEXT', None),
        ('complexity_analysis', 'LONGTEXT', None),
        ('is_completed', 'BOOLEAN', 'FALSE'),
        ('is_migrated', 'BOOLEAN', 'FALSE'),
    ]
    
    add_success = True
    for column_name, column_type, default in new_columns:
        if not add_column_if_not_exists(engine, 'session_analysis_insights', column_name, column_type, default):
            add_success = False
    
    if not add_success:
        print("\n✗ 添加字段过程中出现错误")
        return False
    
    print("\n✓ 新字段添加完成")
    
    # ========== 第三步：验证迁移结果 ==========
    print("\n" + "=" * 60)
    print("第三步：验证迁移结果")
    print("=" * 60)
    
    verification_passed = True
    
    # 验证表已删除
    print("\n验证表删除:")
    for table_name in tables_to_drop:
        if not check_table_exists(engine, table_name):
            print(f"  ✓ {table_name} 已删除")
        else:
            print(f"  ✗ {table_name} 仍然存在")
            verification_passed = False
    
    # 验证新字段已添加
    print("\n验证新字段:")
    for column_name, _, _ in new_columns:
        if check_column_exists(engine, 'session_analysis_insights', column_name):
            print(f"  ✓ {column_name} 已添加")
        else:
            print(f"  ✗ {column_name} 添加失败")
            verification_passed = False
    
    if verification_passed:
        print("\n" + "=" * 60)
        print("✓ 数据库迁移成功完成！")
        print("=" * 60)
        return True
    else:
        print("\n" + "=" * 60)
        print("✗ 数据库迁移完成但验证失败，请检查日志")
        print("=" * 60)
        return False

if __name__ == "__main__":
    success = migrate_database()
    sys.exit(0 if success else 1)
