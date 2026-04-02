"""
重新创建预警相关表
"""
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from sqlalchemy import create_engine, text
from backend.core.database import Base, engine, AlertDB, AlertRuleDB

def recreate_tables():
    """删除并重新创建预警表"""
    
    # 删除旧表（如果存在）
    with engine.connect() as conn:
        conn.execute(text("DROP TABLE IF EXISTS alerts"))
        conn.execute(text("DROP TABLE IF EXISTS alert_rules"))
        conn.commit()
        print("旧表已删除")
    
    # 创建新表
    Base.metadata.create_all(bind=engine, tables=[AlertDB.__table__, AlertRuleDB.__table__])
    print("新表已创建")
    
    print("\n预警表结构:")
    for column in AlertDB.__table__.columns:
        print(f"  - {column.name}: {column.type}")
    
    print("\n预警规则表结构:")
    for column in AlertRuleDB.__table__.columns:
        print(f"  - {column.name}: {column.type}")

if __name__ == "__main__":
    recreate_tables()
