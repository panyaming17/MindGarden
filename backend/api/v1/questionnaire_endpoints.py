"""
问卷自测相关的API端点
"""
from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from typing import List

from backend.core.database import DBConfig, UserDB, QuestionnaireDB, UserQuestionnaireResultDB, SessionLocal
from backend.core.data_models import (
    Questionnaire,
    QuestionnaireList,
    QuestionnaireDetail,
    QuestionnaireSubmit,
    QuestionnaireResult,
    UserQuestionnaireResult,
    QuestionnaireHistory
)

router = APIRouter(prefix="/api/v1/questionnaire", tags=["questionnaire"])

# 依赖注入获取数据库会话
def get_db():
    """获取数据库会话的依赖函数"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 获取可用问卷列表接口
@router.get("/list", response_model=QuestionnaireList)
async def get_questionnaire_list(
    db: Session = Depends(get_db)
):
    """
    获取可用问卷列表
    """
    # 查询所有问卷
    questionnaires = db.query(QuestionnaireDB).all()
    
    # 转换为响应模型
    questionnaire_list = []
    for questionnaire in questionnaires:
        questionnaire_item = Questionnaire(
            id=questionnaire.id,
            name=questionnaire.name,
            description=questionnaire.description
        )
        questionnaire_list.append(questionnaire_item)
    
    # 构建响应
    response = QuestionnaireList(questionnaires=questionnaire_list)
    
    return response

# 获取问卷题目接口
@router.get("/{id}", response_model=QuestionnaireDetail)
async def get_questionnaire(
    id: int,
    db: Session = Depends(get_db)
):
    """
    获取问卷题目
    """
    # 查询问卷
    questionnaire = db.query(QuestionnaireDB).filter(QuestionnaireDB.id == id).first()
    
    if not questionnaire:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="问卷不存在"
        )
    
    # 构建响应
    response = QuestionnaireDetail(
        questions=questionnaire.questions_json,
        scoring_rule=questionnaire.scoring_rule
    )
    
    return response

# 提交问卷结果接口
@router.post("/submit", response_model=QuestionnaireResult)
async def submit_questionnaire(
    submit: QuestionnaireSubmit,
    db: Session = Depends(get_db)
):
    """
    提交问卷结果
    """
    # 检查用户是否存在
    user = db.query(UserDB).filter(UserDB.id == submit.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # 检查问卷是否存在
    questionnaire = db.query(QuestionnaireDB).filter(QuestionnaireDB.id == submit.questionnaire_id).first()
    if not questionnaire:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="问卷不存在"
        )
    
    # 计算总分
    total_score = 0
    for question_id, answer in submit.answers.items():
        # 这里应该根据问卷的计分规则计算分数
        # 为了简化，这里假设每个答案的分值就是答案本身
        total_score += answer
    
    # 确定严重程度
    severity = "无"
    if total_score >= 20:
        severity = "重度"
    elif total_score >= 10:
        severity = "中度"
    elif total_score >= 5:
        severity = "轻度"
    
    # 保存问卷结果
    new_result = UserQuestionnaireResultDB(
        user_id=submit.user_id,
        questionnaire_id=submit.questionnaire_id,
        answers_json=submit.answers,
        total_score=total_score,
        severity=severity
    )
    db.add(new_result)
    db.commit()
    db.refresh(new_result)
    
    # 构建响应
    response = QuestionnaireResult(
        total_score=total_score,
        severity=severity,
        message="问卷提交成功"
    )
    
    return response

# 获取用户问卷历史接口
@router.get("/history", response_model=QuestionnaireHistory)
async def get_questionnaire_history(
    user_id: str,
    db: Session = Depends(get_db)
):
    """
    获取用户问卷历史
    """
    # 检查用户是否存在
    user = db.query(UserDB).filter(UserDB.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # 查询用户的问卷结果
    results = db.query(UserQuestionnaireResultDB).filter(
        UserQuestionnaireResultDB.user_id == user_id
    ).order_by(UserQuestionnaireResultDB.created_at.desc()).all()
    
    # 转换为响应模型
    result_list = []
    for result in results:
        # 获取问卷信息
        questionnaire = db.query(QuestionnaireDB).filter(
            QuestionnaireDB.id == result.questionnaire_id
        ).first()
        
        result_item = UserQuestionnaireResult(
            id=result.id,
            questionnaire_id=result.questionnaire_id,
            questionnaire_name=questionnaire.name if questionnaire else "未知问卷",
            total_score=result.total_score,
            severity=result.severity,
            created_at=result.created_at
        )
        result_list.append(result_item)
    
    # 构建响应
    response = QuestionnaireHistory(results=result_list)
    
    return response
