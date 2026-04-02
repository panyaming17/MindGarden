from backend.core.database import SessionLocal
from sqlalchemy import inspect

db = SessionLocal()
engine = db.get_bind()
inspector = inspect(engine)

print("=" * 60)
print("session_reports 表结构检查")
print("=" * 60)

columns = inspector.get_columns('session_reports')
print(f"\n当前字段列表 (共 {len(columns)} 个):")
for col in columns:
    print(f"  - {col['name']:<30} {col['type']}")

db.close()
