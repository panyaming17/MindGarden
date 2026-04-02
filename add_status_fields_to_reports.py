"""
为 session_reports 表添加状态字段
"""

from backend.core.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()

try:
    print("开始为 session_reports 表添加状态字段...")
    
    # 添加报告状态字段
    status_fields = [
        ('record_report_status', "VARCHAR(20) DEFAULT 'pending' COMMENT '记录报告状态：pending/generating/completed/failed'"),
        ('analysis_report_status', "VARCHAR(20) DEFAULT 'pending' COMMENT '分析报告状态：pending/generating/completed/failed'"),
        ('treatment_report_status', "VARCHAR(20) DEFAULT 'pending' COMMENT '调理报告状态：pending/generating/completed/failed'"),
        ('status_updated_at', 'TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT \'状态更新时间\''),
    ]
    
    for field_name, field_def in status_fields:
        try:
            sql = f"ALTER TABLE session_reports ADD COLUMN {field_name} {field_def}"
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
        SELECT COLUMN_NAME, COLUMN_TYPE, COLUMN_DEFAULT
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_SCHEMA = 'emotional_coaching_system_db' 
          AND TABLE_NAME = 'session_reports'
          AND COLUMN_NAME IN ('record_report_status', 'analysis_report_status', 
                              'treatment_report_status', 'status_updated_at')
        ORDER BY ORDINAL_POSITION
    """))
    
    print("\n新增的状态字段:")
    for row in result:
        print(f"  ✓ {row[0]:<30} {row[1]:<20} 默认值：{row[2]}")
    
except Exception as e:
    print(f"\n✗ 迁移失败：{e}")
    db.rollback()
    import traceback
    traceback.print_exc()
finally:
    db.close()
