########     数据模型定义       ###########
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, date
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
    
    # 优先级
    priority: str  # "高", "中", "低"
    
    created_at: datetime

class SuggestionReport(BaseModel):
    """建议师输出的建议报告"""
    id: str
    diagnosis_id: str
    user_id: str
    
    # 调理建议
    suggestions: List[Dict[str, Any]]
    
    # 作业任务
    homework: Optional[List[Dict[str, Any]]] = None
    
    created_at: datetime

# 用户相关数据模型
class User(BaseModel):
    """用户模型"""
    id: str
    username: str
    email: str
    is_active: bool
    role: str
    created_at: datetime
    updated_at: datetime

class UserCreate(BaseModel):
    """创建用户请求模型"""
    username: str
    email: str
    password: str

class UserLogin(BaseModel):
    """用户登录请求模型"""
    username: str
    password: str

class UserResetPassword(BaseModel):
    """重置密码请求模型"""
    email: str
    code: str
    new_password: str

class UserUpdate(BaseModel):
    """更新用户信息请求模型"""
    username: Optional[str] = None
    email: Optional[str] = None

class Token(BaseModel):
    """令牌响应模型"""
    access_token: str
    token_type: str
    user: User

class TokenVerify(BaseModel):
    """验证令牌请求模型"""
    token: str

class SendRegisterCode(BaseModel):
    """发送注册验证码请求模型"""
    email: str

class SendResetCode(BaseModel):
    """发送重置密码验证码请求模型"""
    email: str

# 对话相关数据模型
class Dialogue(BaseModel):
    """对话模型"""
    id: int
    user_id: str
    session_id: str
    role: str
    content: str
    created_at: datetime

class DialogueCreate(BaseModel):
    """创建对话请求模型"""
    user_id: str
    session_id: str
    role: str
    content: str

class ChatRequest(BaseModel):
    """聊天请求模型"""
    message: str
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    """聊天响应模型"""
    response: str
    session_id: str

class ChatMessage(BaseModel):
    """聊天消息模型"""
    user_id: str
    message: str
    session_id: Optional[str] = None

class ChatMessageResponse(BaseModel):
    """聊天消息响应模型"""
    reply: str
    four_dim: Dict[str, Any]
    is_valuable: bool

class NewSessionResponse(BaseModel):
    """新建会话响应模型"""
    session_id: str
    message: str

class SessionInfo(BaseModel):
    """会话信息模型"""
    session_id: str
    user_id: str
    title: Optional[str] = None
    created_at: datetime
    updated_at: datetime

class SessionList(BaseModel):
    """会话列表响应模型"""
    sessions: List[SessionInfo]

class ChatHistoryResponse(BaseModel):
    """聊天历史响应模型"""
    dialogues: List[Dialogue]

class ChatSession(BaseModel):
    """对话会话模型"""
    session_id: str
    user_id: str
    title: Optional[str] = None
    created_at: datetime
    updated_at: datetime

class ChatSessionCreate(BaseModel):
    """创建对话会话请求模型"""
    user_id: str
    title: Optional[str] = None

class ChatHistory(BaseModel):
    """对话历史响应模型"""
    dialogues: List[Dialogue]

class ChatSessionList(BaseModel):
    """对话会话列表响应模型"""
    sessions: List[ChatSession]

# 记录报告相关数据模型
class EmotionItem(BaseModel):
    """情绪项模型"""
    type: str  # 情绪类型
    intensity: int  # 强度

class ConversationLogItem(BaseModel):
    """对话记录项模型"""
    role: str  # 角色：user/assistant
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
    suggestions: List[DailySuggestion]  # 建议列表
    homework: Optional[List[Dict[str, Any]]] = None  # 作业任务
    follow_up_questions: Optional[List[str]] = None  # 后续跟进问题

class SuggestionReportCreate(BaseModel):
    """创建建议报告请求模型"""
    report_id: str
    user_id: str
    target_issues: List[str]
    suggestions: List[DailySuggestion]
    homework: Optional[List[Dict[str, Any]]] = None
    follow_up_questions: Optional[List[str]] = None

# 情绪日记相关数据模型
class MoodEntry(BaseModel):
    """情绪日记模型"""
    id: int
    user_id: str
    date: date
    mood_label: str
    signature_text: str
    four_dim_intensity: Optional[float] = None
    four_dim_hedonic: Optional[str] = None
    four_dim_tension: Optional[str] = None
    four_dim_complexity: Optional[str] = None
    created_at: datetime

class MoodEntryCreate(BaseModel):
    """创建情绪日记请求模型"""
    user_id: str
    date: date
    mood_label: str
    signature_text: str
    four_dim: Optional[Dict[str, Any]] = None

class MoodCalendarDay(BaseModel):
    """情绪日历天模型"""
    date: str
    mood_label: str
    signature: str

class MoodCalendarResponse(BaseModel):
    """情绪日历响应模型"""
    days: List[MoodCalendarDay]

class MoodTrendResponse(BaseModel):
    """情绪趋势响应模型"""
    dates: List[str]
    intensities: List[float]
    labels: List[str]

# 问卷自测相关数据模型
class Questionnaire(BaseModel):
    """问卷模型"""
    id: int
    name: str
    description: str

class QuestionnaireList(BaseModel):
    """问卷列表响应模型"""
    questionnaires: List[Questionnaire]

class QuestionnaireDetail(BaseModel):
    """问卷详情响应模型"""
    questions: Dict[str, Any]
    scoring_rule: Optional[Dict[str, Any]] = None

class QuestionnaireSubmit(BaseModel):
    """提交问卷请求模型"""
    user_id: str
    questionnaire_id: int
    answers: Dict[str, int]

class QuestionnaireResult(BaseModel):
    """问卷结果响应模型"""
    total_score: int
    severity: str
    message: str

class UserQuestionnaireResult(BaseModel):
    """用户问卷结果模型"""
    id: int
    questionnaire_id: int
    questionnaire_name: str
    total_score: int
    severity: str
    created_at: datetime

class QuestionnaireHistory(BaseModel):
    """问卷历史响应模型"""
    results: List[UserQuestionnaireResult]

# ==================== 新版问卷自查数据模型 ====================

class QuestionOption(BaseModel):
    """题目选项"""
    id: str
    label: str
    desc: Optional[str] = None
    score: int

class Question(BaseModel):
    """问卷题目"""
    id: str
    type: str
    text: str
    options: List[QuestionOption]

class QuestionnaireTemplate(BaseModel):
    """问卷模板"""
    code: str
    name: str
    description: Optional[str] = None
    questions: List[Question]

class QuestionnaireTemplateResponse(BaseModel):
    """问卷模板响应"""
    code: str
    name: str
    description: Optional[str] = None
    questions: List[Question]

class QuestionnaireAnswer(BaseModel):
    """问卷答案"""
    question_id: str
    option_id: str
    score: int

class QuestionnaireSubmitRequest(BaseModel):
    """提交问卷请求"""
    template_code: str
    answers: List[QuestionnaireAnswer]

class QuestionnaireResultData(BaseModel):
    """问卷结果数据"""
    record_id: str
    total_score: int
    result_level: str
    result_level_text: str
    result_analysis: Dict[str, Any]
    next_due_at: datetime

class QuestionnaireSubmitResponse(BaseModel):
    """提交问卷响应"""
    code: int
    data: QuestionnaireResultData

class QuestionnaireSkipRequest(BaseModel):
    """跳过问卷请求"""
    template_code: str

class QuestionnaireSkipResponse(BaseModel):
    """跳过问卷响应"""
    code: int
    data: Dict[str, Any]

class NextDueQuestionnaire(BaseModel):
    """待测问卷项"""
    template_code: str
    template_name: str
    due_at: datetime
    days_overdue: int

class NextDueResponse(BaseModel):
    """待测问卷响应"""
    code: int
    data: List[NextDueQuestionnaire]

class QuestionnaireRecordItem(BaseModel):
    """问卷历史记录项"""
    id: int
    total_score: int
    result_level: str
    result_level_text: str
    created_at: datetime

class QuestionnaireTrendData(BaseModel):
    """问卷趋势数据"""
    date: str
    score: int

class QuestionnaireHistoryData(BaseModel):
    """问卷历史数据"""
    template_code: str
    template_name: str
    records: List[QuestionnaireRecordItem]
    trend_data: List[QuestionnaireTrendData]

class QuestionnaireHistoryResponse(BaseModel):
    """问卷历史响应"""
    code: int
    data: QuestionnaireHistoryData

class QuestionnaireReminder(BaseModel):
    """问卷提醒WebSocket消息"""
    type: str = "questionnaire_reminder"
    required_pending: int
    optional_pending: int
    overdue_required: List[str]
    force_remind: bool

# ==================== 预警相关数据模型 ====================

class AlertType(str, Enum):
    """预警类型"""
    QUESTIONNAIRE = "questionnaire"
    EMOTION = "emotion"
    CONVERSATION = "conversation"

class AlertLevel(str, Enum):
    """预警等级"""
    INFO = "info"
    WARNING = "warning"
    DANGER = "danger"

class Alert(BaseModel):
    """预警模型 - 新版（符合API文档规范）"""
    id: str
    type: AlertType
    level: AlertLevel
    title: str
    message: str
    source_data: Optional[Dict[str, Any]] = None
    is_acknowledged: bool
    created_at: datetime
    acknowledged_at: Optional[datetime] = None
    acknowledged_by: Optional[str] = None

class AlertListRequest(BaseModel):
    """获取预警列表请求"""
    user_id: str
    type: Optional[AlertType] = None
    level: Optional[AlertLevel] = None
    status: Optional[str] = None  # acknowledged/unacknowledged
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    page: int = 1
    page_size: int = 20

class AlertListResponse(BaseModel):
    """预警列表响应"""
    code: int = 200
    message: str = "success"
    data: Dict[str, Any]

class AlertAcknowledgeRequest(BaseModel):
    """确认预警请求"""
    user_id: str
    notes: Optional[str] = None

class AlertAcknowledgeResponse(BaseModel):
    """确认预警响应"""
    code: int = 200
    message: str = "success"
    data: Dict[str, Any]

class AlertBatchAcknowledgeRequest(BaseModel):
    """批量确认预警请求"""
    alert_ids: List[str]
    user_id: str

class AlertBatchAcknowledgeResponse(BaseModel):
    """批量确认预警响应"""
    code: int = 200
    message: str = "success"
    data: Dict[str, Any]

class AlertStatsRequest(BaseModel):
    """获取预警统计请求"""
    user_id: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None

class AlertStatsResponse(BaseModel):
    """预警统计响应"""
    code: int = 200
    message: str = "success"
    data: Dict[str, Any]

class WebSocketMessage(BaseModel):
    """WebSocket消息格式"""
    type: str
    timestamp: datetime
    data: Optional[Dict[str, Any]] = None
    message: Optional[str] = None

class AlertCreateRequest(BaseModel):
    """创建预警请求（内部使用）"""
    user_id: str
    type: AlertType
    level: AlertLevel
    title: str
    message: str
    source_data: Optional[Dict[str, Any]] = None

# 管理员功能相关数据模型
class IntensityLevel(str, Enum):
    LOW = "低"
    MEDIUM = "中"
    HIGH = "高"

class Hedonic(str, Enum):
    POSITIVE = "正性"
    NEUTRAL = "中性"
    NEGATIVE = "负性"

class Tension(str, Enum):
    LOW = "低"
    MEDIUM = "中"
    HIGH = "高"

class Complexity(str, Enum):
    SIMPLE = "简单"
    COMPLEX = "复杂"

class UserList(BaseModel):
    """用户列表响应模型"""
    users: List[User]
    total: int

class Strategy(BaseModel):
    """策略模型"""
    id: int
    intensity_level: str
    hedonic: str
    tension: str
    complexity: str
    fusion_mode: str
    cbt_techniques: str
    tcm_methods: str
    strategy_content: str
    example: str
    created_at: datetime

class StrategyCreate(BaseModel):
    """创建策略请求模型"""
    intensity_level: str
    hedonic: str
    tension: str
    complexity: str
    fusion_mode: str
    cbt_techniques: str
    tcm_methods: str
    strategy_content: str
    example: str

class StrategyUpdate(BaseModel):
    """更新策略请求模型"""
    intensity_level: Optional[str] = None
    hedonic: Optional[str] = None
    tension: Optional[str] = None
    complexity: Optional[str] = None
    fusion_mode: Optional[str] = None
    cbt_techniques: Optional[str] = None
    tcm_methods: Optional[str] = None
    strategy_content: Optional[str] = None
    example: Optional[str] = None

class StrategyList(BaseModel):
    """策略列表响应模型"""
    strategies: List[Strategy]
    total: int

class AdminLog(BaseModel):
    """管理员日志模型"""
    id: int
    admin_id: str
    action: str
    target: str
    details: str
    ip_address: str
    created_at: datetime

class AdminLogList(BaseModel):
    """管理员日志列表响应模型"""
    logs: List[AdminLog]
    total: int


# ==================== 会话报告JSON数据结构模型 ====================

# 1. 记录报告（record_report_json）相关模型
class RecordReportSituation(BaseModel):
    """记录报告中的情境项"""
    description: str  # 情境描述
    time: str  # 时间戳（ISO格式）
    related: List[str]  # 相关情绪或思维

class RecordReportJSON(BaseModel):
    """记录报告JSON数据结构
    
    存储用户在对话中提及的关键信息，由记录师或分析师从对话中提取。
    """
    situations: List[RecordReportSituation]  # 具体情境列表
    emotions: List[Dict[str, Any]]  # 情绪列表，包含type和intensity
    automatic_thoughts: List[str]  # 自动思维列表
    physical_sensations: List[str]  # 身体症状列表
    cognitive_patterns: Optional[List[str]] = None  # 认知模式关键词

# 2. 分析报告（analysis_report_json）相关模型
class AnalysisReportEmotion(BaseModel):
    """分析报告中的情绪项"""
    type: str  # 情绪类型
    intensity: float  # 强度（0-10）
    percentage: float  # 占比（0-1）

class AnalysisReportFourDimData(BaseModel):
    """分析报告中的四维数据"""
    timestamp: str  # 时间戳
    intensity: float  # 强度值
    hedonic: str  # 快感度（正性/中性/负性）
    tension: str  # 紧张度（低/中/高）
    complexity: str  # 复杂度（简单/复杂）

class AnalysisReportJSON(BaseModel):
    """分析报告JSON数据结构
    
    存储分析师对用户情绪的四维分析和原因分析。
    """
    emotion_summary: str  # 情绪概况总结
    emotion_distribution: List[AnalysisReportEmotion]  # 情绪分布统计
    four_dim_data: List[AnalysisReportFourDimData]  # 四维数据变化
    reasons_analysis: str  # 情绪产生原因分析
    cognitive_patterns: List[str]  # 认知模式关键词

# 3. 调理报告（treatment_report_json）相关模型
class TreatmentReportSuggestion(BaseModel):
    """调理报告中的建议项"""
    type: str  # 建议类型（CBT/TCM/通用）
    title: str  # 建议标题
    content: str  # 建议内容

class TreatmentReportHomework(BaseModel):
    """调理报告中的作业项"""
    title: str  # 作业标题
    description: str  # 作业描述
    frequency: str  # 频率（每日/每周等）

class TreatmentReportJSON(BaseModel):
    """调理报告JSON数据结构
    
    存储调理师为用户生成的个性化调理建议和作业。
    """
    summary: str  # 调理总结
    suggestions: List[TreatmentReportSuggestion]  # 调理建议列表
    homework: List[TreatmentReportHomework]  # 作业任务列表
    cbt_focus: Optional[str] = None  # CBT调理重点
    tcm_focus: Optional[str] = None  # TCM调理重点

# 会话报告相关数据模型
class SessionReport(BaseModel):
    """会话报告模型"""
    id: int
    user_id: str
    session_id: str
    record_report_json: Optional[RecordReportJSON] = None
    analysis_report_json: Optional[AnalysisReportJSON] = None
    treatment_report_json: Optional[TreatmentReportJSON] = None
    created_at: datetime

class SessionReportCreate(BaseModel):
    """创建会话报告请求模型"""
    user_id: str
    session_id: str
    record_report_json: Optional[RecordReportJSON] = None
    analysis_report_json: Optional[AnalysisReportJSON] = None
    treatment_report_json: Optional[TreatmentReportJSON] = None

class SessionReportResponse(BaseModel):
    """会话报告响应模型"""
    id: int
    user_id: str
    session_id: str
    record_report: Optional[RecordReportJSON] = None
    analysis_report: Optional[AnalysisReportJSON] = None
    treatment_report: Optional[TreatmentReportJSON] = None
    created_at: datetime

class SessionReportListResponse(BaseModel):
    """会话报告列表响应模型"""
    reports: List[SessionReport]
    total: int

class SessionReportDetailResponse(BaseModel):
    """会话报告详情响应模型"""
    id: int
    user_id: str
    session_id: str
    record_report: RecordReportJSON
    analysis_report: AnalysisReportJSON
    treatment_report: TreatmentReportJSON
    created_at: datetime

class ReportList(BaseModel):
    """报告列表响应模型"""
    reports: List[SessionReport]
    total: int


# ==================== 情绪记录功能数据模型 ====================

class EmotionTypeNew(str, Enum):
    """情绪类型枚举"""
    HAPPY = "happy"
    EXCITED = "excited"
    CALM = "calm"
    TIRED = "tired"
    SAD = "sad"
    ANXIOUS = "anxious"
    ANGRY = "angry"
    WORRIED = "worried"
    GRATEFUL = "grateful"
    CONFUSED = "confused"
    PEACEFUL = "peaceful"
    LONELY = "lonely"

class EmotionRecordCreate(BaseModel):
    """创建情绪记录请求"""
    user_id: str  # 用户ID
    emotion_type: str
    emotion_icon: str
    emotion_name: str
    emotion_color: str
    signature: Optional[str] = None
    record_date: str  # YYYY-MM-DD
    record_time: str  # HH:mm:ss

class EmotionRecordResponse(BaseModel):
    """情绪记录响应"""
    id: int
    emotion_type: str
    emotion_icon: str
    emotion_name: str
    emotion_color: str
    signature: Optional[str]
    record_date: str
    record_time: str
    created_at: datetime

class EmotionRecordListResponse(BaseModel):
    """情绪记录列表响应"""
    code: int
    message: str
    data: Dict[str, Any]

class EmotionCalendarDay(BaseModel):
    """情绪日历天"""
    date: str
    day: int
    has_record: bool
    record: Optional[Dict[str, Any]] = None

class EmotionCalendarResponse(BaseModel):
    """情绪日历响应"""
    code: int
    message: str
    data: Dict[str, Any]

class EmotionDistributionItem(BaseModel):
    """情绪分布项"""
    type: str
    name: str
    color: str
    count: int
    percent: float

class EmotionTrendItem(BaseModel):
    """情绪趋势项"""
    date: str
    emotion_type: Optional[str] = None
    emotion_score: Optional[int] = None
    has_record: bool

class EmotionStatisticsResponse(BaseModel):
    """情绪统计响应"""
    code: int
    message: str
    data: Dict[str, Any]

class EmotionRemindSettings(BaseModel):
    """情绪提醒设置"""
    remind_enabled: bool
    remind_times: int
    remind_interval: int

class EmotionRemindSettingsResponse(BaseModel):
    """情绪提醒设置响应"""
    code: int
    message: str
    data: Dict[str, Any]

class EmotionNextRemindResponse(BaseModel):
    """下次提醒响应"""
    code: int
    message: str
    data: Dict[str, Any]
