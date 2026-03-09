from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from config import DatabaseConfig
from backend.core.database import UserDB, SessionDB, Base

# 创建SQLAlchemy引擎
engine = create_engine(
    DatabaseConfig.SQLALCHEMY_DATABASE_URL,
    **DatabaseConfig.SQLALCHEMY_ENGINE_OPTIONS
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 获取数据库会话
db = SessionLocal()

try:
    # 打印开始信息
    print("开始重置users表...")
    
    # 删除sessions表（因为它依赖于users表）
    print("删除sessions表...")
    SessionDB.__table__.drop(engine, checkfirst=True)
    print("sessions表删除成功！")
    
    # 删除users表
    print("删除users表...")
    UserDB.__table__.drop(engine, checkfirst=True)
    print("users表删除成功！")
    
    # 重新创建users表
    print("重新创建users表...")
    UserDB.__table__.create(engine, checkfirst=True)
    print("users表创建成功！")
    
    # 重新创建sessions表
    print("重新创建sessions表...")
    SessionDB.__table__.create(engine, checkfirst=True)
    print("sessions表创建成功！")
    
    # 打印完成信息
    print("\n✅ users表和sessions表重置成功！")
    print("表结构现在与UserDB和SessionDB模型一致。")
    
finally:
    # 关闭数据库会话
    db.close()
