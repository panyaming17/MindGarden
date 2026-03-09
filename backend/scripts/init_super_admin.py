#!/usr/bin/env python3
"""
初始化超级管理员用户
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

# 定义密码哈希函数
def get_password_hash(password):
    """获取密码哈希值"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

# 导入bcrypt
import bcrypt

def init_super_admin():
    """初始化超级管理员用户"""
    # 创建所有表
    Base.metadata.create_all(bind=engine)
    
    # 创建数据库会话
    db = SessionLocal()
    
    try:
        # 检查是否已存在超级管理员
        super_admin = db.query(UserDB).filter(UserDB.username == "admin").first()
        
        if not super_admin:
            # 创建超级管理员用户
            # 设置密码
            password = "123456"  # 默认密码
            super_admin = UserDB(
                id=f"user_{os.urandom(8).hex()}",
                username="admin",
                password_hash=get_password_hash(password),
                email="admin@example.com",
                is_active=True,
                role="super_admin",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            db.add(super_admin)
            db.commit()
            db.refresh(super_admin)
            
            print("超级管理员创建成功！")
            print(f"用户名: admin")
            print(f"密码: {password}")
            print(f"邮箱: admin@example.com")
            print(f"角色: super_admin")
        else:
            print("超级管理员已存在，跳过创建。")
            print(f"用户名: {super_admin.username}")
            print(f"角色: {super_admin.role}")
            
    except Exception as e:
        print(f"创建超级管理员失败: {str(e)}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    init_super_admin()
