########     数据模型定义       ###########
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class EmotionType(str, Enum):
    ANGER = "怒"
    JOY = "喜"
    WORRY = "忧"
    PENSIVE = "思"
    FEAR = "恐"

class CBTDistortionType(str, Enum):
    ALL_OR_NOTHING = "全或无思维"
    OVERGENERALIZATION = "过度概括"
    MENTAL_FILTER = "心理过滤"
    DISQUALIFYING_POSITIVE = "否定正面"
    JUMPING_TO_CONCLUSIONS = "妄下结论"
    MAGNIFICATION = "放大/缩小"
    EMOTIONAL_REASONING = "情绪化推理"
    SHOULD_STATEMENTS = "应该陈述"
    LABELING = "贴标签"
    PERSONALIZATION = "个人化"

class StructuredRecord(BaseModel):
    """记录师输出的结构化记录"""
    record_id: str
    user_id: str
    raw_text: str
    situation: str                    # 具体情境
    automatic_thoughts: List[str]     # 自动思维
    emotions: List[Dict[str, Any]]    # 情绪列表 [{"type": "忧", "intensity": 8}]
    physical_sensations: Optional[List[str]] = None  # 身体感受
    created_at: datetime

class DiagnosisReport(BaseModel):
    """分析师输出的诊断报告"""
    id: str
    record_id: str
    user_id: str
    
    # CBT分析结果
    cbt_analysis: Dict[str, Any]
    
    # 中医情志分析结果
    tcm_analysis: Dict[str, Any]
    
    # 综合建议框架
    summary: str
    recommendations: List[str]
    
    # 元数据
    confidence_score: float  # 分析置信度
    analysis_time: float # 分析耗时(秒)
    created_at: datetime

    # 在 RecordRepository 的 get_record_by_id 方法中，调整字段映射：
async def get_record_by_id(self, record_id: str) -> Optional[StructuredRecord]:
    # ... 前面的代码不变 ...
    if db_record:
        return StructuredRecord(
            record_id=db_record.id,  # 你的StructuredRecord模型使用record_id字段
            user_id=db_record.user_id,
            raw_text=db_record.raw_text or "",
            situation=db_record.situation or "",
            automatic_thoughts=db_record.automatic_thoughts or [],
            emotions=db_record.emotions or [],
            physical_sensations=db_record.physical_sensations or [],
            created_at=db_record.created_at
        )
    # ... 后面的代码不变 ...

# 对话记录相关数据模型
class Conversation(BaseModel):
    """对话记录数据模型"""
    id: str
    user_id: str
    title: str
    timestamp: datetime
    emotion: Optional[str] = None
    cognition_type: Optional[str] = None
    current_phase: str = "recorder"
    active_step: int = 0
    current_role: str = "记录师"
    created_at: datetime
    updated_at: datetime

class Message(BaseModel):
    """消息数据模型"""
    id: str
    conversation_id: str
    type: str  # user 或 assistant
    role: str
    content: str
    timestamp: datetime
    created_at: datetime

class ConversationCreate(BaseModel):
    """创建对话记录请求模型"""
    title: str
    emotion: Optional[str] = None
    cognition_type: Optional[str] = None
    current_phase: str = "recorder"
    active_step: int = 0
    current_role: str = "记录师"

class ConversationUpdate(BaseModel):
    """更新对话记录请求模型"""
    title: Optional[str] = None
    emotion: Optional[str] = None
    cognition_type: Optional[str] = None
    current_phase: Optional[str] = None
    active_step: Optional[int] = None
    current_role: Optional[str] = None

class ConversationListResponse(BaseModel):
    """对话列表响应模型"""
    id: str
    title: str
    timestamp: datetime
    emotion: Optional[str] = None
    cognition_type: Optional[str] = None
    current_phase: str
    created_at: datetime

class ConversationDetailResponse(BaseModel):
    """对话详情响应模型"""
    conversation: Conversation
    messages: List[Message]

# 用户相关数据模型
class User(BaseModel):
    """用户数据模型"""
    id: str
    username: str
    email: str
    is_active: bool
    role: str  # user, admin, super_admin
    created_at: datetime
    updated_at: datetime

class UserCreate(BaseModel):
    """用户创建请求模型"""
    username: str
    email: str
    code: str
    password: str
    role: str = "user"  # 用户角色，默认值为user

class UserLogin(BaseModel):
    """用户登录请求模型"""
    username: str
    password: str

class UserResetPassword(BaseModel):
    """用户重置密码请求模型"""
    username: str
    email: str
    code: str
    new_password: str

class Token(BaseModel):
    """令牌响应模型"""
    access_token: str
    token_type: str
    user: User

class TokenVerify(BaseModel):
    """令牌验证响应模型"""
    valid: bool
    user: Optional[User] = None

class UserUpdate(BaseModel):
    """用户更新请求模型"""
    email: Optional[str] = None

class SendRegisterCode(BaseModel):
    """发送注册验证码请求模型"""
    email: str

class SendResetCode(BaseModel):
    """发送重置密码验证码请求模型"""
    username: str
    email: str

# 记录报告相关数据模型
class EmotionItem(BaseModel):
    """情绪项模型"""
    type: str  # 怒/喜/忧/思/恐
    intensity: int  # 1-10 强度
    description: Optional[str] = None  # 用户对情绪的描述

class ConversationLogItem(BaseModel):
    """对话日志项模型"""
    role: str  # user 或 assistant
    content: str  # 对话内容

class RecordReport(BaseModel):
    """记录报告模型"""
    record_id: str
    session_id: str
    user_id: str
    timestamp: datetime
    duration: float
    conversation_log: Optional[List[ConversationLogItem]] = None
    situation: str
    automatic_thoughts: List[str]
    emotions: List[EmotionItem]
    physical_sensations: List[str]
    summary: str

class RecordReportCreate(BaseModel):
    """创建记录报告请求模型"""
    session_id: str
    user_id: str
    duration: float
    conversation_log: Optional[List[ConversationLogItem]] = None
    situation: str
    automatic_thoughts: List[str]
    emotions: List[EmotionItem]
    physical_sensations: List[str]
    summary: str

# 分析报告相关数据模型
class DistortionItem(BaseModel):
    """认知扭曲项模型"""
    distortion_type: str  # 扭曲类型
    matched_thought: str  # 匹配的自动思维
    evidence: str  # 证据
    challenge_question: Optional[str] = None  # 挑战问题

class CBTAnalysis(BaseModel):
    """CBT分析模型"""
    distortions_detected: List[DistortionItem]  # 检测到的认知扭曲
    summary: str  # CBT分析摘要
    challenge_questions: Optional[List[str]] = None  # 用于认知重构的提问

class DominantEmotion(BaseModel):
    """主导情绪模型"""
    type: str  # 情绪类型
    intensity: int  # 强度
    affected_zang: str  # 受影响的脏腑

class SecondaryEmotion(BaseModel):
    """次要情绪模型"""
    type: str  # 情绪类型
    intensity: int  # 强度
    affected_zang: str  # 受影响的脏腑

class TCMAnalysis(BaseModel):
    """中医情志分析模型"""
    dominant_emotion: DominantEmotion  # 主导情绪
    inhibiting_emotion: str  # 相胜情绪
    secondary_emotions: List[SecondaryEmotion]  # 其他情绪及影响
    recommended_interventions: List[str]  # 音乐、呼吸、穴位等建议

class AnalysisReport(BaseModel):
    """分析报告模型"""
    report_id: str
    record_id: str
    user_id: str
    timestamp: datetime
    analysis_duration: float
    confidence_score: float
    cbt_analysis: CBTAnalysis
    tcm_analysis: TCMAnalysis
    integrated_framework: str
    priority: str

class AnalysisReportCreate(BaseModel):
    """创建分析报告请求模型"""
    record_id: str
    user_id: str
    analysis_duration: float
    confidence_score: float
    cbt_analysis: CBTAnalysis
    tcm_analysis: TCMAnalysis
    integrated_framework: str
    priority: str

# 建议报告相关数据模型
class DailySuggestion(BaseModel):
    """每日可执行建议模型"""
    title: str  # 建议标题
    description: str  # 具体做法
    duration: int  # 建议用时（分钟）
    type: str  # 类型（认知/行为/情志/身体）

class SuggestionReport(BaseModel):
    """建议报告模型"""
    suggestion_id: str
    report_id: str
    user_id: str
    timestamp: datetime
    target_issues: List[str]  # 本次疏导聚焦的问题
    core_principles: List[str]  # 疏导核心理念
    daily_suggestions: List[DailySuggestion]  # 每日可执行建议
    emergency_tips: Optional[List[str]] = None  # 情绪紧急时的应对技巧
    encouragement: str  # 鼓励性结语
    plan_summary: str  # 简短总结

class SuggestionReportCreate(BaseModel):
    """创建建议报告请求模型"""
    report_id: str
    user_id: str
    target_issues: List[str]
    core_principles: List[str]
    daily_suggestions: List[DailySuggestion]
    emergency_tips: Optional[List[str]] = None
    encouragement: str
    plan_summary: str

# 规则库相关数据模型
class RuleType(str, Enum):
    CBT = "cbt"
    TCM = "tcm"

class Rule(BaseModel):
    """规则库数据模型"""
    id: int
    type: str
    name: str
    content: Dict[str, Any]
    version: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

class RuleCreate(BaseModel):
    """创建规则请求模型"""
    type: str
    name: str
    content: Dict[str, Any]
    version: str
    is_active: bool = True

class RuleUpdate(BaseModel):
    """更新规则请求模型"""
    type: Optional[str] = None
    name: Optional[str] = None
    content: Optional[Dict[str, Any]] = None
    version: Optional[str] = None
    is_active: Optional[bool] = None

class RuleListResponse(BaseModel):
    """规则列表响应模型"""
    total: int
    page: int
    per_page: int
    items: List[Rule]

# 审计日志相关数据模型
class AuditLog(BaseModel):
    """审计日志数据模型"""
    id: int
    admin_id: str
    action: str
    target_type: str
    target_id: str
    details: Optional[Dict[str, Any]] = None
    created_at: datetime

class AuditLogListResponse(BaseModel):
    """审计日志列表响应模型"""
    total: int
    page: int
    per_page: int
    items: List[AuditLog]