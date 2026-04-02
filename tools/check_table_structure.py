from backend.core.database import SessionLocal
from sqlalchemy import inspect

db = SessionLocal()
engine = db.get_bind()
inspector = inspect(engine)

print("=" * 60)
print("session_analysis_insights 表结构检查")
print("=" * 60)

columns = inspector.get_columns('session_analysis_insights')
print(f"\n当前字段列表 (共 {len(columns)} 个):")
for col in columns:
    print(f"  - {col['name']:<30} {col['type']}")

# 检查新字段是否存在
new_fields = [
    'intensity_values',
    'hedonic_counts',
    'tension_counts',
    'complexity_analysis',
    'is_completed',
    'is_migrated'
]

print("\n" + "=" * 60)
print("新字段检查:")
print("=" * 60)

for field in new_fields:
    exists = any(col['name'] == field for col in columns)
    status = "✓ 存在" if exists else "✗ 不存在"
    print(f"  {field:<30} {status}")

db.close()
