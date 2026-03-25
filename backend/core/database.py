import sys
import os

# 添加项目根目录到 Python 路径
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from sqlalchemy import create_engine, Column, String, Text, Float, ForeignKey, TIMESTAMP, JSON, Enum, Integer, BigInteger, UniqueConstraint, Boolean, Index, ForeignKeyConstraint
from sqlalchemy.dialects.mysql import INTEGER
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from datetime import datetime
from config import DatabaseConfig

# 创建SQLAlchemy引擎
print(f"连接到数据库: {DatabaseConfig.SQLALCHEMY_DATABASE_URL}")
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

# ==================== 用户与权限 ====================

class UserDB(Base):
    """用户表"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment='用户ID')
    username = Column(String(50), unique=True, nullable=False, comment='用户名')
    email = Column(String(100), unique=True, nullable=False, comment='邮箱')
    password_hash = Column(String(255), nullable=False, comment='密码哈希')
    role = Column(Enum('user', 'admin','super_admin'), nullable=False, default='user', comment='角色')
    is_active = Column(Boolean, default=True, comment='软删除标记')
    created_at = Column(TIMESTAMP, default=datetime.utcnow, comment='创建时间')
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')

class SessionDB(Base):
    """会话表"""
    __tablename__ = "sessions"
    
    id = Column(String(50), primary_key=True, comment='会话ID')
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment='用户ID', index=True)
    token = Column(String(255), unique=True, nullable=False, comment='访问令牌', index=True)
    expires_at = Column(TIMESTAMP, nullable=False, comment='过期时间', index=True)
    created_at = Column(TIMESTAMP, default=datetime.utcnow, comment='创建时间')

class EmailVerificationCodeDB(Base):
    """邮箱验证码表"""
    __tablename__ = "email_verification_codes"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(100), nullable=False, comment='邮箱')
    code = Column(String(6), nullable=False, comment='验证码')
    type = Column(Enum('register', 'reset'), nullable=False, comment='类型')
    expires_at = Column(TIMESTAMP, nullable=False, comment='过期时间')
    created_at = Column(TIMESTAMP, default=datetime.utcnow, comment='创建时间')

# ==================== 对话与智能体 ====================

class DialogueDB(Base):
    """对话记录表"""
    __tablename__ = "dialogues"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment='对话ID')
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment='用户ID')
    session_id = Column(String(50), nullable=True, comment='会话ID（用于区分对话轮次）')
    role = Column(Enum('user', 'assistant'), nullable=False, comment='说话者')
    content = Column(Text, nullable=False, comment='内容')
    four_dim_intensity = Column(Float, nullable=True, comment='强度')
    four_dim_hedonic = Column(String(10), nullable=True, comment='快感度')
    four_dim_tension = Column(String(10), nullable=True, comment='紧张度')
    four_dim_complexity = Column(String(10), nullable=True, comment='复杂度')
    is_valuable = Column(Boolean, default=False, nullable=False, comment='是否有价值（触发分析师）')
    created_at = Column(TIMESTAMP, default=datetime.utcnow, comment='创建时间')
    
    # 索引
    __table_args__ = (
        Index('idx_user_session', 'user_id', 'session_id', 'created_at'),
    )

class UserArchiveDB(Base):
    """用户认知档案表"""
    __tablename__ = "user_archives"
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment='档案ID')
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment='用户ID')
    session_id = Column(String(50), ForeignKey("sessions.id"), nullable=False, comment='会话ID')
    archive_json = Column(JSON, nullable=False, comment='完整档案JSON')
    version = Column(Integer, default=1, comment='版本号')
    created_at = Column(TIMESTAMP, default=datetime.utcnow, comment='创建时间')
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')
    
    # 唯一约束
    __table_args__ = (
        UniqueConstraint('user_id', 'session_id', name='unique_user_session'),
    )

class AdviceDB(Base):
    """分析师建议表"""
    __tablename__ = "advices"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment='用户ID')
    dialogue_id = Column(BigInteger, ForeignKey("dialogues.id"), nullable=True, comment='触发建议的对话ID（可为空）')
    session_id = Column(String(50), nullable=False, comment='所属会话')
    advice_json = Column(JSON, nullable=False, comment='建议内容（含融合模式、策略要点等）')
    created_at = Column(TIMESTAMP, default=datetime.utcnow, comment='创建时间')
    
    # 索引
    __table_args__ = (
        Index('idx_user_session', 'user_id', 'session_id'),
    )

class StrategyDB(Base):
    """策略库表"""
    __tablename__ = "strategies"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    intensity_level = Column(Enum('低', '中', '高'), nullable=False, comment='强度等级')
    hedonic = Column(Enum('正性', '中性', '负性'), nullable=False, comment='快感度')
    tension = Column(Enum('低', '中', '高'), nullable=False, comment='紧张度')
    complexity = Column(Enum('简单', '复杂'), nullable=False, comment='复杂度')
    fusion_mode = Column(String(50), nullable=False, comment='融合模式')
    cbt_techniques = Column(Text, nullable=False, comment='CBT技术')
    tcm_methods = Column(Text, nullable=False, comment='中医方法')
    strategy_content = Column(Text, nullable=False, comment='完整话术')
    example = Column(Text, nullable=False, comment='示例')
    created_at = Column(TIMESTAMP, default=datetime.utcnow, comment='创建时间')
    
    # 唯一约束
    __table_args__ = (
        UniqueConstraint('intensity_level', 'hedonic', 'tension', 'complexity', name='unique_combo'),
    )

# ==================== 报告模块 ====================

class SessionReportDB(Base):
    """会话报告表（每次会话结束生成）"""
    __tablename__ = "session_reports"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment='用户ID')
    session_id = Column(String(50), nullable=False, comment='会话ID')
    record_report_json = Column(JSON, nullable=True, comment='记录报告（情境、情绪、思维、身体症状）')
    analysis_report_json = Column(JSON, nullable=True, comment='分析报告（四维图表数据、情绪变化、原因分析）')
    treatment_report_json = Column(JSON, nullable=True, comment='调理报告（建议总结、CBT作业）')
    created_at = Column(TIMESTAMP, default=datetime.utcnow, comment='创建时间')

# ==================== 情绪记录（日记） ====================

class MoodEntryDB(Base):
    """情绪日记表"""
    __tablename__ = "mood_entries"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment='用户ID')
    entry_date = Column(String(10), nullable=False, comment='日期（唯一约束 per user）')
    mood_label = Column(String(20), nullable=False, comment='情绪标签（如开心、焦虑）')
    signature_text = Column(Text, nullable=True, comment='签名语句')
    four_dim_intensity = Column(Float, nullable=True, comment='强度（可选）')
    four_dim_hedonic = Column(String(10), nullable=True, comment='快感度')
    four_dim_tension = Column(String(10), nullable=True, comment='紧张度')
    four_dim_complexity = Column(String(10), nullable=True, comment='复杂度')
    created_at = Column(TIMESTAMP, default=datetime.utcnow, comment='创建时间')
    
    # 唯一约束
    __table_args__ = (
        UniqueConstraint('user_id', 'entry_date', name='unique_user_date'),
    )

# ==================== 问卷自测 ====================

class QuestionnaireDB(Base):
    """问卷表"""
    __tablename__ = "questionnaires"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, comment='问卷名称（如PHQ-9、GAD-7）')
    description = Column(Text, nullable=True, comment='描述')
    questions_json = Column(JSON, nullable=False, comment='问题列表（含选项、分值）')
    scoring_rule = Column(JSON, nullable=True, comment='计分规则（总分与等级映射）')

class UserQuestionnaireResultDB(Base):
    """用户问卷结果表"""
    __tablename__ = "user_questionnaire_results"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment='用户ID')
    questionnaire_id = Column(Integer, ForeignKey("questionnaires.id"), nullable=False, comment='问卷ID')
    answers_json = Column(JSON, nullable=False, comment='用户答案')
    total_score = Column(Integer, nullable=True, comment='总分')
    severity = Column(String(20), nullable=True, comment='严重程度（如无、轻度、中度、重度）')
    created_at = Column(TIMESTAMP, default=datetime.utcnow, comment='创建时间')
    
    # 索引
    __table_args__ = (
        Index('idx_user_date', 'user_id', 'created_at'),
    )

# ==================== 预警模块 ====================

class AlertDB(Base):
    """预警表"""
    __tablename__ = "alerts"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment='用户ID')
    alert_type = Column(Enum('session', 'trend'), nullable=False, comment='类型（会话内趋势不佳 / 长期趋势）')
    alert_level = Column(Enum('warning', 'danger'), nullable=False, comment='级别')
    message = Column(Text, nullable=False, comment='预警内容')
    trigger_data = Column(JSON, nullable=True, comment='触发预警的数据（如情绪趋势）')
    is_acknowledged = Column(Boolean, default=False, comment='是否已处理')
    created_at = Column(TIMESTAMP, default=datetime.utcnow, comment='创建时间')

# ==================== 管理员日志 ====================

class AdminLogDB(Base):
    """管理员操作日志"""
    __tablename__ = "admin_logs"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    admin_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment='管理员ID')
    action = Column(String(50), nullable=False, comment='操作类型（如create_user, update_strategy）')
    target = Column(String(100), nullable=True, comment='操作对象')
    details = Column(Text, nullable=True, comment='详细信息')
    ip_address = Column(String(45), nullable=True, comment='IP地址')
    created_at = Column(TIMESTAMP, default=datetime.utcnow, comment='创建时间')

# 创建所有表
print("开始创建表...")
try:
    Base.metadata.create_all(bind=engine)
    print("表创建成功！")
except Exception as e:
    print(f"表创建失败: {e}")
