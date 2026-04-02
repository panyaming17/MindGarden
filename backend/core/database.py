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
    
    id = Column(String(50), primary_key=True, comment='用户ID')
    username = Column(String(50), unique=True, nullable=False, comment='用户名')
    email = Column(String(100), unique=True, nullable=False, comment='邮箱')
    password_hash = Column(String(255), nullable=False, comment='密码哈希')
    role = Column(Enum('user', 'admin','super_admin'), nullable=False, default='user', comment='角色')
    is_active = Column(Boolean, default=True, comment='软删除标记')
    created_at = Column(TIMESTAMP, default=datetime.utcnow, comment='创建时间')
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')

class SessionDB(Base):
    """登录会话表"""
    __tablename__ = "sessions"
    
    id = Column(String(50), primary_key=True, comment='登录会话ID')
    user_id = Column(String(50), ForeignKey("users.id"), nullable=False, comment='用户ID', index=True)
    token = Column(String(255), unique=True, nullable=False, comment='访问令牌', index=True)
    expires_at = Column(TIMESTAMP, nullable=False, comment='过期时间', index=True)
    created_at = Column(TIMESTAMP, default=datetime.utcnow, comment='创建时间')

class ChatSessionDB(Base):
    """对话会话表"""
    __tablename__ = "chat_sessions"
    
    session_id = Column(String(50), primary_key=True, comment='对话会话ID')
    user_id = Column(String(50), ForeignKey("users.id"), nullable=False, comment='用户ID', index=True)
    title = Column(String(255), nullable=True, comment='会话标题')
    created_at = Column(TIMESTAMP, default=datetime.utcnow, comment='创建时间')
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')

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
    user_id = Column(String(50), ForeignKey("users.id"), nullable=False, comment='用户ID')
    session_id = Column(String(50), ForeignKey("chat_sessions.session_id"), nullable=True, comment='对话会话ID（用于区分对话轮次）')
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
    user_id = Column(String(50), ForeignKey("users.id"), nullable=False, comment='用户ID')
    session_id = Column(String(50), ForeignKey("chat_sessions.session_id"), nullable=False, comment='对话会话ID')
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
    user_id = Column(String(50), ForeignKey("users.id"), nullable=False, comment='用户ID')
    dialogue_id = Column(BigInteger, ForeignKey("dialogues.id"), nullable=True, comment='触发建议的对话ID（可为空）')
    session_id = Column(String(50), ForeignKey("chat_sessions.session_id"), nullable=False, comment='所属对话会话')
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
    user_id = Column(String(50), ForeignKey("users.id"), nullable=False, comment='用户 ID')
    session_id = Column(String(50), ForeignKey("chat_sessions.session_id"), nullable=False, comment='会话 ID')
    record_report_json = Column(JSON, nullable=True, comment='记录报告（情境、情绪、思维、身体症状）')
    analysis_report_json = Column(JSON, nullable=True, comment='分析报告（四维图表数据、情绪变化、原因分析）')
    treatment_report_json = Column(JSON, nullable=True, comment='调理报告（建议总结、CBT 作业）')
    
    # 报告状态字段
    record_status = Column(String(20), default="completed", comment='记录报告状态：completed/generating/failed')
    analysis_status = Column(String(20), default="pending", comment='分析报告状态：pending/generating/completed/failed')
    treatment_status = Column(String(20), default="pending", comment='调理报告状态：pending/generating/completed/failed')
    
    # 重试计数
    analysis_retry_count = Column(Integer, default=0, comment='分析报告重试次数')
    treatment_retry_count = Column(Integer, default=0, comment='调理报告重试次数')
    
    created_at = Column(TIMESTAMP, default=datetime.utcnow, comment='创建时间')
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')
    
    # 索引
    __table_args__ = (
        Index('idx_user_session', 'user_id', 'session_id'),
    )



class SessionAnalysisInsightDB(Base):
    """会话分析洞察表（用于实时保存分析师的分析字段）"""
    __tablename__ = "session_analysis_insights"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    session_id = Column(String(50), ForeignKey("chat_sessions.session_id"), nullable=False, comment='会话 ID')
    user_id = Column(String(50), ForeignKey("users.id"), nullable=False, comment='用户 ID')
    dialogue_id = Column(BigInteger, ForeignKey("dialogues.id"), nullable=True, comment='触发该洞察的对话 ID')
    
    # 认知分析字段
    common_automatic_thoughts = Column(JSON, nullable=True, comment='常见自动思维列表')
    thinking_traps = Column(JSON, nullable=True, comment='思维陷阱列表')
    core_beliefs = Column(JSON, nullable=True, comment='核心信念列表')
    
    # 认知映射关系
    cognitive_mappings = Column(JSON, nullable=True, comment='认知映射关系列表 [{situation, automatic_thought, emotion, core_belief}]')
    
    # 中医分析字段
    tcm_dominant_emotion = Column(String(20), nullable=True, comment='主导情志（喜、怒、忧、思、悲、恐、惊）')
    tcm_related_organs = Column(JSON, nullable=True, comment='相关脏腑列表')
    tcm_qi_dynamics = Column(String(200), nullable=True, comment='气机动态描述')
    tcm_interpretation = Column(Text, nullable=True, comment='中医解读')
    
    # 原因分析
    cbt_perspective = Column(Text, nullable=True, comment='CBT 视角分析')
    tcm_perspective = Column(Text, nullable=True, comment='中医视角分析')
    
    # 情绪趋势
    emotional_trend = Column(Text, nullable=True, comment='情绪趋势总结')
    
    # ========== 新增：四维数据增量统计字段 ==========
    # 强度值数组（增量追加）
    intensity_values = Column(JSON, nullable=True, comment='强度值数组 [{"value": 6.5, "timestamp": "..."}, ...]')
    # 快感度计数（增量累加）
    hedonic_counts = Column(JSON, nullable=True, comment='快感度计数 {"负性": 3, "中性": 1, "正性": 1}')
    # 紧张度计数（增量累加）
    tension_counts = Column(JSON, nullable=True, comment='紧张度计数 {"高": 1, "中": 1, "低": 3}')
    # 复杂度分析（每 2 轮对话增量更新）
    complexity_analysis = Column(JSON, nullable=True, comment='复杂度分析 {"type": "复杂", "emotions": [{"emotion": "忧", "value": 0.6}, ...]}')
    
    # ========== 新增：状态标记字段 ==========
    is_completed = Column(Boolean, default=False, comment='是否已完成分析（所有维度都已分析）')
    is_migrated = Column(Boolean, default=False, comment='是否已迁移到 session_reports 表')
    
    # 时间戳
    created_at = Column(TIMESTAMP, default=datetime.utcnow, comment='创建时间')
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')
    
    # 索引
    __table_args__ = (
        Index('idx_session_insight', 'session_id', 'user_id'),
        Index('idx_dialogue_insight', 'dialogue_id'),
    )

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

class QuestionnaireTemplateDB(Base):
    """问卷模板表"""
    __tablename__ = "questionnaire_templates"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    code = Column(String(50), unique=True, nullable=False, comment='问卷编码: PHQ9/GAD7/TCM_CONSTITUTION')
    name = Column(String(100), nullable=False, comment='问卷名称')
    description = Column(Text, nullable=True, comment='问卷说明')
    questions = Column(JSON, nullable=False, comment='题目配置JSON')
    scoring_rules = Column(JSON, nullable=True, comment='评分规则')
    version = Column(Integer, default=1, comment='版本号')
    is_active = Column(Boolean, default=True, comment='是否启用')
    created_at = Column(TIMESTAMP, default=datetime.utcnow, comment='创建时间')
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')

class UserQuestionnaireRecordDB(Base):
    """用户问卷记录表"""
    __tablename__ = "user_questionnaire_records"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(String(50), ForeignKey("users.id"), nullable=False, comment='用户ID')
    template_code = Column(String(50), nullable=False, comment='问卷类型')
    answers = Column(JSON, nullable=False, comment='答案详情 [{question_id, option_id, score}]')
    total_score = Column(Integer, nullable=False, comment='总分')
    result_level = Column(String(20), nullable=True, comment='结果等级: none/mild/moderate/severe')
    result_analysis = Column(JSON, nullable=True, comment='结果分析')
    created_at = Column(TIMESTAMP, default=datetime.utcnow, comment='创建时间')
    
    # 索引
    __table_args__ = (
        Index('idx_user_template', 'user_id', 'template_code'),
        Index('idx_created_at', 'created_at'),
    )

class UserQuestionnaireScheduleDB(Base):
    """问卷调度表（控制下次检测时间）"""
    __tablename__ = "user_questionnaire_schedule"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(String(50), nullable=False, comment='用户ID')
    template_code = Column(String(50), nullable=False, comment='问卷类型')
    first_login_at = Column(TIMESTAMP, nullable=True, comment='首次登录时间')
    last_completed_at = Column(TIMESTAMP, nullable=True, comment='上次完成时间')
    next_due_at = Column(TIMESTAMP, nullable=False, comment='下次应测时间')
    skipped_count = Column(Integer, default=0, comment='连续跳过次数')
    is_first_time = Column(Boolean, default=True, comment='是否首次')
    created_at = Column(TIMESTAMP, default=datetime.utcnow, comment='创建时间')
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')
    
    # 唯一约束
    __table_args__ = (
        UniqueConstraint('user_id', 'template_code', name='uk_user_template'),
    )

class QuestionnaireScoringRuleDB(Base):
    """问卷评分规则表"""
    __tablename__ = "questionnaire_scoring_rules"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    template_code = Column(String(50), nullable=False, comment='问卷编码')
    rule_type = Column(Enum('level', 'suggestion', 'interval', 'alert'), nullable=False, comment='规则类型')
    rule_config = Column(JSON, nullable=False, comment='规则配置')
    priority = Column(Integer, default=0, comment='优先级')
    is_active = Column(Boolean, default=True, comment='是否启用')
    created_at = Column(TIMESTAMP, default=datetime.utcnow, comment='创建时间')
    
    # 索引
    __table_args__ = (
        Index('idx_template_type', 'template_code', 'rule_type'),
    )

# ==================== 情绪记录 ====================

class EmotionRecordDB(Base):
    """情绪记录表"""
    __tablename__ = "emotion_records"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(String(50), ForeignKey("users.id"), nullable=False, comment='用户ID')
    emotion_type = Column(String(50), nullable=False, comment='情绪类型：happy/excited/calm/tired/sad/anxious/angry/worried/grateful/confused/peaceful/lonely')
    emotion_icon = Column(String(10), nullable=False, comment='情绪图标emoji')
    emotion_name = Column(String(20), nullable=False, comment='情绪名称')
    emotion_color = Column(String(20), nullable=False, comment='情绪颜色代码')
    signature = Column(String(200), nullable=True, comment='用户签名/备注')
    record_date = Column(String(10), nullable=False, comment='记录日期')
    record_time = Column(String(8), nullable=False, comment='记录时间')
    created_at = Column(TIMESTAMP, default=datetime.utcnow, comment='创建时间')
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')
    
    # 索引
    __table_args__ = (
        Index('idx_user_date', 'user_id', 'record_date'),
        Index('idx_user_created', 'user_id', 'created_at'),
    )

class EmotionRemindSettingDB(Base):
    """情绪提醒配置表"""
    __tablename__ = "emotion_remind_settings"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(String(50), ForeignKey("users.id"), nullable=False, unique=True, comment='用户ID')
    remind_enabled = Column(Boolean, default=True, comment='是否启用提醒')
    remind_times = Column(Integer, default=2, comment='每日提醒次数')
    remind_interval = Column(Integer, default=360, comment='提醒间隔（分钟）')
    last_remind_at = Column(TIMESTAMP, nullable=True, comment='上次提醒时间')
    next_remind_at = Column(TIMESTAMP, nullable=True, comment='下次提醒时间')
    last_record_at = Column(TIMESTAMP, nullable=True, comment='上次记录时间')
    created_at = Column(TIMESTAMP, default=datetime.utcnow, comment='创建时间')
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')


# ==================== 预警模块 ====================

class AlertDB(Base):
    """预警表 - 新版（符合API文档规范）"""
    __tablename__ = "alerts"
    
    id = Column(String(64), primary_key=True, comment='预警ID')
    user_id = Column(String(50), ForeignKey("users.id"), nullable=False, comment='用户ID', index=True)
    type = Column(Enum('questionnaire', 'emotion', 'conversation'), nullable=False, comment='预警类型')
    level = Column(Enum('info', 'warning', 'danger'), nullable=False, comment='预警等级')
    title = Column(String(255), nullable=False, comment='预警标题')
    message = Column(Text, nullable=False, comment='预警内容')
    source_data = Column(JSON, nullable=True, comment='关联数据（JSON格式）')
    is_acknowledged = Column(Boolean, default=False, comment='是否已确认', index=True)
    acknowledged_at = Column(TIMESTAMP, nullable=True, comment='确认时间')
    acknowledged_by = Column(String(50), ForeignKey("users.id"), nullable=True, comment='确认人ID')
    created_at = Column(TIMESTAMP, default=datetime.utcnow, comment='创建时间', index=True)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')
    
    # 索引
    __table_args__ = (
        Index('idx_alerts_user_created', 'user_id', 'created_at'),
        Index('idx_alerts_user_ack', 'user_id', 'is_acknowledged'),
    )

class AlertRuleDB(Base):
    """预警规则表（用于动态配置规则）"""
    __tablename__ = "alert_rules"
    
    id = Column(String(64), primary_key=True, comment='规则ID')
    type = Column(String(32), nullable=False, comment='规则类型: questionnaire/emotion/conversation')
    name = Column(String(128), nullable=False, comment='规则名称')
    condition = Column(JSON, nullable=False, comment='触发条件（JSON格式）')
    level = Column(Enum('info', 'warning', 'danger'), nullable=False, comment='预警等级')
    title_template = Column(String(255), nullable=False, comment='标题模板')
    message_template = Column(Text, nullable=False, comment='内容模板')
    is_active = Column(Boolean, default=True, comment='是否启用')
    created_at = Column(TIMESTAMP, default=datetime.utcnow, comment='创建时间')
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')

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
