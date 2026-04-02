"""
报告相关的API端点
"""
from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from typing import List

from backend.core.database import DBConfig, UserDB, SessionReportDB, SessionLocal
from backend.core.data_models import (
    SessionReport,
    SessionReportResponse,
    ReportList
)

router = APIRouter(prefix="/api/v1/report", tags=["report"])

# 依赖注入获取数据库会话
def get_db():
    """获取数据库会话的依赖函数"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 获取会话报告接口
@router.get("/session/{session_id}")
async def get_session_report(
    session_id: str,
    db: Session = Depends(get_db)
):
    """
    获取会话报告（记录、分析、调理）
    """
    # 查询会话报告
    report = db.query(SessionReportDB).filter(
        SessionReportDB.session_id == session_id
    ).first()
    
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="会话报告不存在"
        )
    
    # 直接返回原始数据，避免FastAPI响应验证
    return {
        "id": report.id,
        "user_id": report.user_id,
        "session_id": report.session_id,
        "record_report": report.record_report_json,
        "analysis_report": report.analysis_report_json,
        "treatment_report": report.treatment_report_json,
        "created_at": report.created_at.isoformat() if report.created_at else None
    }

# 获取用户所有报告列表接口
@router.get("/user/{user_id}")
async def get_user_reports(
    user_id: str,
    db: Session = Depends(get_db)
):
    """
    获取用户所有报告列表
    """
    # 检查用户是否存在
    user = db.query(UserDB).filter(UserDB.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # 查询用户的所有报告
    reports = db.query(SessionReportDB).filter(
        SessionReportDB.user_id == user_id
    ).order_by(SessionReportDB.created_at.desc()).all()
    
    # 构建原始报告列表
    report_list = []
    for report in reports:
        report_item = {
            "id": report.id,
            "user_id": report.user_id,
            "session_id": report.session_id,
            "record_report_json": report.record_report_json,
            "analysis_report_json": report.analysis_report_json,
            "treatment_report_json": report.treatment_report_json,
            "created_at": report.created_at.isoformat() if report.created_at else None
        }
        report_list.append(report_item)
    
    # 直接返回原始数据，避免FastAPI响应验证
    return {
        "reports": report_list,
        "total": len(report_list)
    }
