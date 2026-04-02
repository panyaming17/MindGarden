"""
结束会话接口的新实现
实现增量保存和异步报告生成
"""
import asyncio
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import datetime

from backend.core.database import get_db, SessionReportDB, ChatSessionDB, DialogueDB, UserArchiveDB, AdviceDB
from backend.api.v1.chat_endpoints import get_recorder_agent, get_analyst_agent, get_therapist_agent, get_llm_service, DBConfig
from backend.api.v1.async_report_generator import generate_reports_async


@router.post("/end-session")
async def end_session_new(
    request_data: dict,
    db: Session = Depends(get_db)
):
    """
    结束会话接口（新版本：增量保存 + 异步生成）
    
    流程：
    1. 立即生成并保存记录报告
    2. 异步生成分析报告（带重试）
    3. 异步生成调理报告（依赖分析报告）
    4. 立即返回响应，不等待报告完成
    """
    # 从请求中获取参数
    user_id = request_data.get("user_id")
    session_id = request_data.get("session_id")
    
    if not user_id or not session_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="缺少用户 ID 或会话 ID"
        )
    
    # 检查用户是否存在
    from backend.core.database import UserDB
    user = db.query(UserDB).filter(UserDB.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在，请先登录"
        )
    
    # 检查会话是否存在
    chat_session = db.query(ChatSessionDB).filter(
        ChatSessionDB.user_id == user_id,
        ChatSessionDB.session_id == session_id
    ).first()
    
    if not chat_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="会话不存在"
        )
    
    # 获取会话数据
    dialogues = db.query(DialogueDB).filter(
        DialogueDB.user_id == user_id,
        DialogueDB.session_id == session_id
    ).order_by(DialogueDB.created_at.asc()).all()
    
    archive = db.query(UserArchiveDB).filter(
        UserArchiveDB.user_id == user_id,
        UserArchiveDB.session_id == session_id
    ).first()
    
    advices = db.query(AdviceDB).filter(
        AdviceDB.user_id == user_id,
        AdviceDB.session_id == session_id
    ).order_by(AdviceDB.created_at.asc()).all()
    
    # 构建对话历史
    dialogue_history = []
    for d in dialogues:
        dialogue_history.append({
            "role": d.role,
            "content": d.content,
            "created_at": d.created_at.isoformat() if d.created_at else None,
            "four_dim": {
                "intensity": d.four_dim_intensity,
                "hedonic": d.four_dim_hedonic,
                "tension": d.four_dim_tension,
                "complexity": d.four_dim_complexity
            } if d.four_dim_intensity else None
        })
    
    archive_data = archive.archive_json if archive else {}
    
    # 初始化智能体
    try:
        llm_service = await get_llm_service()
        
        recorder_agent = get_recorder_agent()
        recorder_agent.llm_service = llm_service
        
        # ========== 阶段 1：生成记录报告（立即保存） ==========
        print(f"DEBUG: 调用记录师最终确定记录报告")
        record_report = await recorder_agent.finalize_record_report(user_id, session_id)
        
        # 查询是否已存在报告
        existing_report = db.query(SessionReportDB).filter(
            SessionReportDB.user_id == user_id,
            SessionReportDB.session_id == session_id
        ).first()
        
        if existing_report:
            # 更新现有报告
            existing_report.record_report_json = record_report
            existing_report.record_status = "completed"
            existing_report.analysis_status = "pending"
            existing_report.treatment_status = "pending"
            existing_report.analysis_retry_count = 0
            existing_report.treatment_retry_count = 0
            report_id = existing_report.id
        else:
            # 创建新报告
            new_report = SessionReportDB(
                user_id=user_id,
                session_id=session_id,
                record_report_json=record_report,
                analysis_report_json={},
                treatment_report_json={},
                record_status="completed",
                analysis_status="pending",
                treatment_status="pending",
                analysis_retry_count=0,
                treatment_retry_count=0
            )
            db.add(new_report)
            db.flush()
            report_id = new_report.id
        
        db.commit()  # ✅ 立即提交
        db.refresh(existing_report if existing_report else new_report)
        
        # ========== 阶段 2：异步生成分析报告和调理报告 ==========
        asyncio.create_task(
            generate_reports_async(
                db_factory=DBConfig.get_db,
                report_id=report_id,
                user_id=user_id,
                session_id=session_id,
                dialogue_history=dialogue_history,
                archive_data=archive_data
            )
        )
        
        # 立即返回
        return {
            "message": "会话已结束，报告正在生成中",
            "session_id": session_id,
            "report_id": report_id,
            "status": {
                "record_report": "completed",
                "analysis_report": "generating",
                "treatment_report": "pending"
            },
            "data": {
                "record_report": record_report,
                "analysis_report": None,
                "treatment_report": None
            }
        }
        
    except Exception as e:
        import traceback
        print(f"DEBUG: 生成会话报告失败：{e}")
        print(traceback.format_exc())
        return {
            "message": "会话已结束，但报告生成失败",
            "session_id": session_id,
            "error": str(e)
        }
