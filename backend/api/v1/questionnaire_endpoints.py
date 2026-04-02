"""
新版问卷自测相关的API端点
"""
from fastapi import APIRouter, HTTPException, Depends, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from datetime import datetime, timedelta

from backend.core.database import (
    DBConfig, UserDB, QuestionnaireTemplateDB, UserQuestionnaireRecordDB,
    UserQuestionnaireScheduleDB, QuestionnaireScoringRuleDB, SessionLocal
)
from backend.core.data_models import (
    NextDueResponse, NextDueQuestionnaire,
    QuestionnaireTemplateResponse, QuestionOption, Question,
    QuestionnaireSubmitRequest, QuestionnaireSubmitResponse, QuestionnaireResultData,
    QuestionnaireSkipRequest, QuestionnaireSkipResponse,
    QuestionnaireHistoryResponse, QuestionnaireHistoryData,
    QuestionnaireRecordItem, QuestionnaireTrendData,
    QuestionnaireReminder
)
from backend.services.alert_service import AlertService
from backend.services.alert_websocket import alert_ws_manager

router = APIRouter(prefix="/api/questionnaires", tags=["questionnaires"])

# 必填问卷列表
REQUIRED_QUESTIONNAIRES = ['PHQ9', 'GAD7']

# 依赖注入获取数据库会话
def get_db():
    """获取数据库会话的依赖函数"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_user_schedule(user_id: str, db: Session):
    """初始化用户问卷调度（在登录时调用）"""
    # 检查是否已有调度记录
    existing_schedules = db.query(UserQuestionnaireScheduleDB).filter(
        UserQuestionnaireScheduleDB.user_id == user_id
    ).all()
    
    existing_codes = {s.template_code for s in existing_schedules}
    
    # 为必填问卷创建调度记录
    for code in REQUIRED_QUESTIONNAIRES:
        if code not in existing_codes:
            # 查询问卷模板确认存在
            template = db.query(QuestionnaireTemplateDB).filter(
                QuestionnaireTemplateDB.code == code,
                QuestionnaireTemplateDB.is_active == True
            ).first()
            
            if template:
                schedule = UserQuestionnaireScheduleDB(
                    user_id=user_id,
                    template_code=code,
                    first_login_at=datetime.utcnow(),
                    next_due_at=datetime.utcnow(),  # 首次立即检测
                    is_first_time=True
                )
                db.add(schedule)
    
    db.commit()


@router.get("/next-due", response_model=NextDueResponse)
async def get_next_due_questionnaires(
    user_id: str = Query(..., description="用户ID"),
    db: Session = Depends(get_db)
):
    """
    获取待测问卷列表
    
    查询 user_questionnaire_schedule 表中 next_due_at <= now() 的记录
    计算 days_overdue = datediff(now(), next_due_at)
    """
    # 先初始化调度（如果未初始化）
    init_user_schedule(user_id, db)
    
    now = datetime.utcnow()
    
    # 查询待测问卷
    schedules = db.query(UserQuestionnaireScheduleDB).filter(
        UserQuestionnaireScheduleDB.user_id == user_id,
        UserQuestionnaireScheduleDB.next_due_at <= now
    ).all()
    
    result = []
    for schedule in schedules:
        # 获取问卷模板信息
        template = db.query(QuestionnaireTemplateDB).filter(
            QuestionnaireTemplateDB.code == schedule.template_code
        ).first()
        
        if template:
            # 计算逾期天数
            days_overdue = (now - schedule.next_due_at).days
            
            result.append(NextDueQuestionnaire(
                template_code=schedule.template_code,
                template_name=template.name,
                due_at=schedule.next_due_at,
                days_overdue=max(0, days_overdue)
            ))
    
    return NextDueResponse(
        code=200,
        data=result
    )


@router.get("/{code}/template", response_model=dict)
async def get_questionnaire_template(
    code: str,
    db: Session = Depends(get_db)
):
    """
    获取问卷模板
    
    返回指定问卷的完整题目配置
    """
    template = db.query(QuestionnaireTemplateDB).filter(
        QuestionnaireTemplateDB.code == code,
        QuestionnaireTemplateDB.is_active == True
    ).first()
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="问卷模板不存在"
        )
    
    return {
        "code": 200,
        "data": {
            "code": template.code,
            "name": template.name,
            "description": template.description,
            "questions": template.questions
        }
    }


@router.post("/submit", response_model=QuestionnaireSubmitResponse)
async def submit_questionnaire(
    request: QuestionnaireSubmitRequest,
    user_id: str = Query(..., description="用户ID"),
    db: Session = Depends(get_db)
):
    """
    提交问卷
    
    提交用户的问卷答案并获取评分结果
    """
    # 验证用户是否存在
    user = db.query(UserDB).filter(UserDB.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # 获取问卷模板
    template = db.query(QuestionnaireTemplateDB).filter(
        QuestionnaireTemplateDB.code == request.template_code,
        QuestionnaireTemplateDB.is_active == True
    ).first()
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="问卷模板不存在"
        )
    
    # 验证答案完整性
    if len(request.answers) != len(template.questions):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"答案不完整，需要回答{len(template.questions)}道题"
        )
    
    # 计算总分
    total_score = sum(answer.score for answer in request.answers)
    
    # 根据评分规则判断等级
    level_rule = db.query(QuestionnaireScoringRuleDB).filter(
        QuestionnaireScoringRuleDB.template_code == request.template_code,
        QuestionnaireScoringRuleDB.rule_type == 'level',
        QuestionnaireScoringRuleDB.is_active == True
    ).all()
    
    result_level = "none"
    result_level_text = "正常"
    
    for rule in level_rule:
        min_score = rule.rule_config.get('min_score', 0)
        max_score = rule.rule_config.get('max_score', 999)
        if min_score <= total_score <= max_score:
            result_level = rule.rule_config.get('level', 'none')
            result_level_text = rule.rule_config.get('text', '正常')
            break
    
    # 获取建议
    suggestion_rule = db.query(QuestionnaireScoringRuleDB).filter(
        QuestionnaireScoringRuleDB.template_code == request.template_code,
        QuestionnaireScoringRuleDB.rule_type == 'suggestion',
        QuestionnaireScoringRuleDB.is_active == True
    ).first()
    
    suggestions = []
    if suggestion_rule:
        level_suggestions = suggestion_rule.rule_config.get(result_level, {})
        suggestions = level_suggestions.get('suggestions', [])
    
    # 构建结果分析
    result_analysis = {
        "summary": f"根据您的回答，您目前处于{result_level_text}状态",
        "risk_level": "high" if result_level in ['severe', 'moderately_severe'] else "normal",
        "suggestions": suggestions,
        "alert": None,
        "total_questions": len(template.questions),
        "answered_questions": len(request.answers)
    }
    
    # 保存记录
    record = UserQuestionnaireRecordDB(
        user_id=user_id,
        template_code=request.template_code,
        answers=[answer.dict() for answer in request.answers],
        total_score=total_score,
        result_level=result_level,
        result_analysis=result_analysis
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    
    # 更新调度表
    schedule = db.query(UserQuestionnaireScheduleDB).filter(
        UserQuestionnaireScheduleDB.user_id == user_id,
        UserQuestionnaireScheduleDB.template_code == request.template_code
    ).first()
    
    if schedule:
        schedule.last_completed_at = datetime.utcnow()
        schedule.is_first_time = False
        schedule.skipped_count = 0
        
        # 设置下次检测时间（根据间隔规则）
        interval_rule = db.query(QuestionnaireScoringRuleDB).filter(
            QuestionnaireScoringRuleDB.template_code == request.template_code,
            QuestionnaireScoringRuleDB.rule_type == 'interval',
            QuestionnaireScoringRuleDB.is_active == True
        ).first()
        
        if interval_rule:
            interval_days = interval_rule.rule_config.get('days', 3)
        else:
            interval_days = 3  # 默认3天
        
        schedule.next_due_at = datetime.utcnow() + timedelta(days=interval_days)
        db.commit()
    
    # ==================== 预警检查 ====================
    # 检查是否需要生成预警
    alert_service = AlertService(db)
    alert = await alert_service.check_questionnaire_alert(
        user_id=user_id,
        template_code=request.template_code,
        total_score=total_score,
        result_level=result_level
    )
    
    if alert:
        # 通过WebSocket推送预警
        alert_data = {
            "id": alert.id,
            "type": alert.type,
            "level": alert.level,
            "title": alert.title,
            "message": alert.message,
            "source_data": alert.source_data,
            "is_acknowledged": alert.is_acknowledged,
            "created_at": alert.created_at.isoformat() if alert.created_at else None
        }
        await alert_ws_manager.push_new_alert(user_id, alert_data)
        
        # 将预警信息添加到结果分析中
        result_analysis["alert_generated"] = {
            "alert_id": alert.id,
            "level": alert.level,
            "title": alert.title
        }
    # ==================== 预警检查结束 ====================
    
    return QuestionnaireSubmitResponse(
        code=200,
        data=QuestionnaireResultData(
            record_id=str(record.id),
            total_score=total_score,
            result_level=result_level,
            result_level_text=result_level_text,
            result_analysis=result_analysis,
            next_due_at=schedule.next_due_at if schedule else datetime.utcnow() + timedelta(days=3)
        )
    )


@router.post("/skip", response_model=QuestionnaireSkipResponse)
async def skip_questionnaire(
    request: QuestionnaireSkipRequest,
    user_id: str = Query(..., description="用户ID"),
    db: Session = Depends(get_db)
):
    """
    跳过问卷
    
    跳过当前问卷，推迟到下次检测
    """
    schedule = db.query(UserQuestionnaireScheduleDB).filter(
        UserQuestionnaireScheduleDB.user_id == user_id,
        UserQuestionnaireScheduleDB.template_code == request.template_code
    ).first()
    
    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="问卷调度记录不存在"
        )
    
    # 增加跳过次数
    schedule.skipped_count += 1
    
    # 推迟到明天同一时间
    schedule.next_due_at = datetime.utcnow() + timedelta(days=1)
    db.commit()
    
    return QuestionnaireSkipResponse(
        code=200,
        data={
            "next_remind_at": schedule.next_due_at
        }
    )


@router.get("/history", response_model=QuestionnaireHistoryResponse)
async def get_questionnaire_history(
    user_id: str = Query(..., description="用户ID"),
    template_code: Optional[str] = Query(None, description="问卷编码"),
    limit: int = Query(5, description="返回记录数量"),
    db: Session = Depends(get_db)
):
    """
    获取历史记录
    
    返回指定问卷的历史记录和趋势数据
    """
    # 如果未指定模板，默认返回第一个必填问卷的历史
    if not template_code:
        template_code = REQUIRED_QUESTIONNAIRES[0]
    
    # 获取模板信息
    template = db.query(QuestionnaireTemplateDB).filter(
        QuestionnaireTemplateDB.code == template_code
    ).first()
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="问卷模板不存在"
        )
    
    # 查询历史记录
    records = db.query(UserQuestionnaireRecordDB).filter(
        UserQuestionnaireRecordDB.user_id == user_id,
        UserQuestionnaireRecordDB.template_code == template_code
    ).order_by(UserQuestionnaireRecordDB.created_at.desc()).limit(limit).all()
    
    # 构建记录列表
    record_items = []
    trend_data = []
    
    for record in records:
        # 获取等级文本
        level_text = record.result_level
        level_rule = db.query(QuestionnaireScoringRuleDB).filter(
            QuestionnaireScoringRuleDB.template_code == template_code,
            QuestionnaireScoringRuleDB.rule_type == 'level',
            QuestionnaireScoringRuleDB.rule_config['level'].as_string() == record.result_level
        ).first()
        
        if level_rule:
            level_text = level_rule.rule_config.get('text', record.result_level)
        
        record_items.append(QuestionnaireRecordItem(
            id=record.id,
            total_score=record.total_score,
            result_level=record.result_level,
            result_level_text=level_text,
            created_at=record.created_at
        ))
        
        # 趋势数据（按日期聚合，取每天的最新记录）
        date_str = record.created_at.strftime('%Y-%m-%d')
        trend_data.append(QuestionnaireTrendData(
            date=date_str,
            score=record.total_score
        ))
    
    # 反转趋势数据（从早到晚）
    trend_data.reverse()
    
    return QuestionnaireHistoryResponse(
        code=200,
        data=QuestionnaireHistoryData(
            template_code=template_code,
            template_name=template.name,
            records=record_items,
            trend_data=trend_data
        )
    )


# WebSocket 相关函数
async def get_questionnaire_reminder(user_id: str, db: Session) -> QuestionnaireReminder:
    """
    获取问卷提醒信息（用于WebSocket推送）
    """
    now = datetime.utcnow()
    
    # 查询待测问卷
    schedules = db.query(UserQuestionnaireScheduleDB).filter(
        UserQuestionnaireScheduleDB.user_id == user_id,
        UserQuestionnaireScheduleDB.next_due_at <= now
    ).all()
    
    required_pending = 0
    optional_pending = 0
    overdue_required = []
    
    for schedule in schedules:
        if schedule.template_code in REQUIRED_QUESTIONNAIRES:
            required_pending += 1
            if schedule.skipped_count >= 3:
                overdue_required.append(schedule.template_code)
        else:
            optional_pending += 1
    
    return QuestionnaireReminder(
        type="questionnaire_reminder",
        required_pending=required_pending,
        optional_pending=optional_pending,
        overdue_required=overdue_required,
        force_remind=len(overdue_required) > 0
    )
