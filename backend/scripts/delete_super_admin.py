#!/usr/bin/env python3
"""
删除超级管理员用户
"""

import sys
import os
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 定义数据库配置
class DatabaseConfig:
    SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_size": 10,
        "max_overflow": 20
    }

# 保存配置到模块
import sys
sys.modules['config'] = type('ConfigModule', (), {'DatabaseConfig': DatabaseConfig})()

# 导入必要的模块
from sqlalchemy import create_engine, Column, String, Text, Float, ForeignKey, TIMESTAMP, JSON, Enum, Integer, UniqueConstraint, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

# 创建SQLAlchemy引擎
engine = create_engine(
    DatabaseConfig.SQLALCHEMY_DATABASE_URL,
    **DatabaseConfig.SQLALCHEMY_ENGINE_OPTIONS
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建基础模型类
Base = declarative_base()

# 定义UserDB模型
class UserDB(Base):
    """用户表对应的数据库模型"""
    __tablename__ = "users"
    
    id = Column(String(50), primary_key=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    email = Column(String(100), unique=True, nullable=False, index=True)
    is_active = Column(Boolean, default=True, nullable=False)
    role = Column(String(20), default="user", nullable=False)  # user, admin, super_admin
    created_at = Column(TIMESTAMP, default=datetime.utcnow, index=True)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow, index=True)

def delete_super_admin():
    """删除超级管理员用户"""
    # 创建数据库会话
    db = SessionLocal()
    
    try:
        # 查找超级管理员
        super_admin = db.query(UserDB).filter(UserDB.username == "admin").first()
        
        if super_admin:
            # 删除超级管理员
            db.delete(super_admin)
            db.commit()
            print("超级管理员删除成功！")
        else:
            print("超级管理员不存在，无需删除。")
            
    except Exception as e:
        print(f"删除超级管理员失败: {str(e)}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    delete_super_admin()
