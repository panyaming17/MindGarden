"""
手动数据库迁移 - 为 session_analysis_insights 表添加新字段
直接在数据库中执行，不依赖自动创建表
"""

from backend.core.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()

try:
    print("开始执行数据库迁移...")
    
    # 添加四维数据字段
    fields_to_add = [
        ('intensity_values', 'LONGTEXT NULL COMMENT \'强度值数组 [{"value": 6.5, "timestamp": "..."}, ...]\''),
        ('hedonic_counts', 'LONGTEXT NULL COMMENT \'快感度计数 {"负性": 3, "中性": 1, "正性": 1}\''),
        ('tension_counts', 'LONGTEXT NULL COMMENT \'紧张度计数 {"高": 1, "中": 1, "低": 3}\''),
        ('complexity_analysis', 'LONGTEXT NULL COMMENT \'复杂度分析 {"type": "复杂", "emotions": [...]}\''),
    ]
    
    for field_name, field_def in fields_to_add:
        try:
            sql = f"ALTER TABLE session_analysis_insights ADD COLUMN {field_name} {field_def}"
            db.execute(text(sql))
            print(f"✓ 已添加字段：{field_name}")
        except Exception as e:
            if "Duplicate column name" in str(e):
                print(f"  - 字段已存在：{field_name}，跳过")
            else:
                print(f"✗ 添加字段 {field_name} 失败：{e}")
    
    # 添加状态标记字段
    status_fields = [
        ('is_completed', 'BIT DEFAULT 0 COMMENT \'是否已完成分析\''),
        ('is_migrated', 'BIT DEFAULT 0 COMMENT \'是否已迁移到 session_reports\''),
    ]
    
    for field_name, field_def in status_fields:
        try:
            sql = f"ALTER TABLE session_analysis_insights ADD COLUMN {field_name} {field_def}"
            db.execute(text(sql))
            print(f"✓ 已添加字段：{field_name}")
        except Exception as e:
            if "Duplicate column name" in str(e):
                print(f"  - 字段已存在：{field_name}，跳过")
            else:
                print(f"✗ 添加字段 {field_name} 失败：{e}")
    
    db.commit()
    print("\n" + "=" * 60)
    print("数据库迁移完成！")
    print("=" * 60)
    
    # 验证字段是否添加成功
    print("\n验证字段:")
    result = db.execute(text("""
        SELECT COLUMN_NAME 
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_SCHEMA = 'emotional_coaching_system_db' 
          AND TABLE_NAME = 'session_analysis_insights'
          AND COLUMN_NAME IN ('intensity_values', 'hedonic_counts', 'tension_counts', 
                              'complexity_analysis', 'is_completed', 'is_migrated')
        ORDER BY COLUMN_NAME
    """))
    
    fields = [row[0] for row in result]
    print(f"找到 {len(fields)} 个新字段:")
    for field in fields:
        print(f"  ✓ {field}")
    
except Exception as e:
    print(f"\n✗ 迁移失败：{e}")
    db.rollback()
    import traceback
    traceback.print_exc()
finally:
    db.close()
