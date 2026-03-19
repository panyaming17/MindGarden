from sqlalchemy import create_engine, Column, String, Text, Float, ForeignKey, TIMESTAMP, JSON, Enum, Integer, BigInteger, UniqueConstraint, Boolean, Index
from sqlalchemy.dialects.mysql import INTEGER
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
from config import DatabaseConfig

# 创建SQLAlchemy引擎
engine = create_engine(
    DatabaseConfig.SQLALCHEMY_DATABASE_URL,
    **DatabaseConfig.SQLALCHEMY_ENGINE_OPTIONS
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建基础模型类
Base = declarative_base()

class DBConfig:
    """数据库配置类"""
    
    @staticmethod
    def get_db():
        """获取数据库会话的依赖函数"""
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

# SQLAlchemy模型定义

class StructuredRecordDB(Base):
    """结构化记录表对应的数据库模型"""
    __tablename__ = "structured_records"
    
    id = Column(String(50), primary_key=True)
    user_id = Column(String(50), nullable=False, index=True)
    raw_text = Column(Text, nullable=True)
    situation = Column(Text, nullable=True)
    automatic_thoughts = Column(JSON, nullable=True)  # 存储JSON数组
    emotions = Column(JSON, nullable=True)           # 存储情绪列表
    physical_sensations = Column(JSON, nullable=True)  # 存储身体感觉列表
    created_at = Column(TIMESTAMP, default=datetime.utcnow, index=True)
    
    # 关系
    diagnosis_reports = relationship("DiagnosisReportDB", back_populates="structured_record")

class DiagnosisReportDB(Base):
    """诊断报告表对应的数据库模型"""
    __tablename__ = "diagnosis_reports"
    
    id = Column(String(50), primary_key=True)
    record_id = Column(String(50), ForeignKey("structured_records.id"), nullable=False, index=True)
    user_id = Column(String(50), nullable=False, index=True)
    cbt_analysis = Column(JSON, nullable=True)
    tcm_analysis = Column(JSON, nullable=True)
    comprehensive_framework = Column(Text, nullable=True)
    confidence_score = Column(Float, nullable=True)
    analysis_duration = Column(Float, nullable=True)
    created_at = Column(TIMESTAMP, default=datetime.utcnow, index=True)
    
    # 关系
    structured_record = relationship("StructuredRecordDB", back_populates="diagnosis_reports")

class RuleVersionDB(Base):
    """规则库版本表对应的数据库模型"""
    __tablename__ = "rule_versions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    rule_type = Column(Enum('cbt', 'tcm'), nullable=False)
    version = Column(String(20), nullable=False)
    content_hash = Column(String(64), nullable=False)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint('rule_type', 'version', name='unique_rule_version'),
    )

class ConversationDB(Base):
    """对话记录表对应的数据库模型"""
    __tablename__ = "conversations"
    
    id = Column(String(50), primary_key=True, comment='对话ID')
    user_id = Column(String(50), nullable=False, comment='用户ID', index=True)
    title = Column(String(200), nullable=False, comment='对话标题')
    timestamp = Column(TIMESTAMP, default=datetime.utcnow, comment='对话时间戳', index=True)
    phase = Column(String(20), nullable=False, default="recording", comment='当前阶段', index=True)
    record_result_id = Column(String(50), nullable=True, comment='记录报告ID')  # 记录报告ID
    analysis_result_id = Column(String(50), nullable=True, comment='分析报告ID')  # 分析报告ID
    therapy_result_id = Column(String(50), nullable=True, comment='建议报告ID')  # 建议报告ID
    context = Column(JSON, nullable=True, comment='临时上下文数据')  # 临时上下文
    created_at = Column(TIMESTAMP, default=datetime.utcnow, comment='创建时间')
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')
    
    # 关系
    messages = relationship("MessageDB", back_populates="conversation")

class MessageDB(Base):
    """消息表对应的数据库模型"""
    __tablename__ = "messages"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment='消息唯一ID')
    conversation_id = Column(String(50), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, comment='所属会话ID')
    role = Column(Enum('user', 'recorder', 'analyst', 'therapist', 'system'), nullable=False, comment='发送者角色')
    content = Column(Text, nullable=False, comment='消息内容')
    input_tokens = Column(INTEGER(unsigned=True), nullable=True, comment='用户输入或API请求的token数')
    output_tokens = Column(INTEGER(unsigned=True), nullable=True, comment='模型回复的token数')
    created_at = Column(TIMESTAMP, default=datetime.utcnow, comment='消息发送时间')
    
    # 关系
    conversation = relationship("ConversationDB", back_populates="messages")
    
    # 索引
    __table_args__ = (
        Index('idx_conversation_time', 'conversation_id', 'created_at'),
    )

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
    
    # 关系
    sessions = relationship("SessionDB", back_populates="user")

class SessionDB(Base):
    """会话表对应的数据库模型"""
    __tablename__ = "sessions"
    
    id = Column(String(50), primary_key=True)
    user_id = Column(String(50), ForeignKey("users.id"), nullable=False, index=True)
    token = Column(String(255), unique=True, nullable=False, index=True)
    expires_at = Column(TIMESTAMP, nullable=False, index=True)
    created_at = Column(TIMESTAMP, default=datetime.utcnow, index=True)
    
    # 关系
    user = relationship("UserDB", back_populates="sessions")

class RecordReportDB(Base):
    """记录报告表对应的数据库模型"""
    __tablename__ = "record_reports"
    
    record_id = Column(String(50), primary_key=True)
    session_id = Column(String(50), nullable=False, index=True)
    user_id = Column(String(50), nullable=False, index=True)
    timestamp = Column(TIMESTAMP, default=datetime.utcnow, nullable=False)
    duration = Column(Float, nullable=False)
    conversation_log = Column(JSON, nullable=True)  # 完整对话历史
    situation = Column(Text, nullable=False)  # 引发情绪的具体事件或情境
    automatic_thoughts = Column(JSON, nullable=False)  # 自动思维列表
    emotions = Column(JSON, nullable=False)  # 情绪列表
    physical_sensations = Column(JSON, nullable=False)  # 身体感受列表
    summary = Column(Text, nullable=False)  # 本次记录简短总结
    created_at = Column(TIMESTAMP, default=datetime.utcnow, index=True)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow, index=True)

class AnalysisReportDB(Base):
    """分析报告表对应的数据库模型"""
    __tablename__ = "analysis_reports"
    
    report_id = Column(String(50), primary_key=True)
    record_id = Column(String(50), nullable=False, index=True)
    user_id = Column(String(50), nullable=False, index=True)
    timestamp = Column(TIMESTAMP, default=datetime.utcnow, nullable=False)
    analysis_duration = Column(Float, nullable=False)
    confidence_score = Column(Float, nullable=False)
    cbt_analysis = Column(JSON, nullable=False)  # CBT分析结果
    tcm_analysis = Column(JSON, nullable=False)  # 中医情志分析结果
    integrated_framework = Column(Text, nullable=False)  # 综合干预框架
    priority = Column(String(50), nullable=False)  # 干预优先级
    created_at = Column(TIMESTAMP, default=datetime.utcnow, index=True)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow, index=True)

class SuggestionReportDB(Base):
    """建议报告表对应的数据库模型"""
    __tablename__ = "suggestion_reports"
    
    suggestion_id = Column(String(50), primary_key=True)
    report_id = Column(String(50), nullable=False, index=True)
    user_id = Column(String(50), nullable=False, index=True)
    timestamp = Column(TIMESTAMP, default=datetime.utcnow, nullable=False)
    target_issues = Column(JSON, nullable=False)  # 本次疏导聚焦的问题
    core_principles = Column(JSON, nullable=False)  # 疏导核心理念
    daily_suggestions = Column(JSON, nullable=False)  # 每日可执行建议
    emergency_tips = Column(JSON, nullable=True)  # 情绪紧急时的应对技巧
    encouragement = Column(Text, nullable=False)  # 鼓励性结语
    plan_summary = Column(Text, nullable=False)  # 简短总结
    created_at = Column(TIMESTAMP, default=datetime.utcnow, index=True)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow, index=True)

class RuleDB(Base):
    """规则库表对应的数据库模型"""
    __tablename__ = "rules"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    type = Column(Enum('cbt', 'tcm'), nullable=False)
    name = Column(String(100), nullable=False)
    content = Column(JSON, nullable=False)  # 规则具体内容（如关键词、干预策略）
    version = Column(String(20), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(TIMESTAMP, default=datetime.utcnow, index=True)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow, index=True)

class AuditLog(Base):
    """审计日志表对应的数据库模型"""
    __tablename__ = 'audit_logs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    admin_id = Column(String(50), nullable=False, index=True)
    action = Column(String(50), nullable=False, index=True)
    target_type = Column(String(50), nullable=False, index=True)
    target_id = Column(String(50), nullable=False, index=True)
    details = Column(JSON, nullable=True)
    created_at = Column(TIMESTAMP, default=datetime.utcnow, index=True)

# 创建所有表
Base.metadata.create_all(bind=engine)