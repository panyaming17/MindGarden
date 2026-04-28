"""
记录师智能体的API端点
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
from backend.agents.recorder_agent import RecorderAgent
from backend.core.database import DBConfig, RecordReportDB
from backend.core.data_models import RecordReport, RecordReportCreate, EmotionItem, ConversationLogItem
from sqlalchemy.orm import Session
from datetime import datetime
import uuid

router = APIRouter(prefix="/recorder", tags=["recorder"])
recorder_agent = RecorderAgent()

class RecorderRequest(BaseModel):
    """记录师请求数据模型"""
    user_input: str
    session_id: Optional[str] = None  # 如果提供，则继续现有会话
    user_id: Optional[str] = None     # 用户标识

class RecorderResponse(BaseModel):
    """记录师响应数据模型"""
    session_id: str
    success: bool
    message: str
    llm_response: str  # 给用户的自然语言回应
    record_id: Optional[str] = None  # 如果记录完成，返回记录ID
    next_action: str  # continue_dialogue 或 trigger_analyst
    structured_data: Optional[Dict[str, Any]] = None

@router.post("/converse", response_model=RecorderResponse)
async def converse_with_recorder(request: RecorderRequest):
    """
    与记录师智能体对话
    - 如果是新会话，记录师会开始引导对话
    - 如果是继续会话，记录师会基于历史继续提问或提取结构化信息
    """
    try:
        # 确定是否是新会话
        is_new_session = request.session_id is None
        session_id = request.session_id or f"sess_{uuid.uuid4().hex[:8]}"
        
        # 准备输入数据
        input_data = {
            "session_id": session_id,
            "user_input": request.user_input,
            "is_new_session": is_new_session,
            "user_id": request.user_id
        }
        
        # 调用记录师智能体
        result = await recorder_agent.execute(input_data)
        
        # 返回标准化响应
        return RecorderResponse(
            session_id=session_id,
            success=result["success"],
            message=result["message"],
            llm_response=result.get("llm_response", ""),
            record_id=result.get("record_id"),
            next_action=result.get("next_action", "continue_dialogue"),
            structured_data=result.get("structured_data")
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"记录师对话失败: {str(e)}")

@router.get("/session/{session_id}")
async def get_session_info(session_id: str):
    """获取会话状态信息（用于调试）"""
    # 这里可以返回会话的当前状态、历史等
    return {
        "session_id": session_id,
        "status": "active",
        "agent": "recorder_agent"
    }

# 记录报告相关接口
@router.post("/record-reports", response_model=RecordReport)
async def create_record_report(
    report_data: RecordReportCreate,
    db: Session = Depends(DBConfig.get_db)
):
    """
    创建记录报告
    - 保存记录报告到数据库
    - 返回创建的记录报告
    """
    try:
        # 生成记录ID
        record_id = f"rec_{uuid.uuid4().hex[:8]}"
        
        # 转换conversation_log为JSON格式
        conversation_log_json = None
        if report_data.conversation_log:
            conversation_log_json = [item.dict() for item in report_data.conversation_log]
        
        # 转换emotions为JSON格式
        emotions_json = [item.dict() for item in report_data.emotions]
        
        # 创建记录报告实例
        new_report = RecordReportDB(
            record_id=record_id,
            session_id=report_data.session_id,
            user_id=report_data.user_id,
            timestamp=datetime.utcnow(),
            duration=report_data.duration,
            conversation_log=conversation_log_json,
            situation=report_data.situation,
            automatic_thoughts=report_data.automatic_thoughts,
            emotions=emotions_json,
            physical_sensations=report_data.physical_sensations,
            summary=report_data.summary
        )
        
        # 保存到数据库
        db.add(new_report)
        db.commit()
        db.refresh(new_report)
        
        # 转换为响应模型
        return RecordReport(
            record_id=new_report.record_id,
            session_id=new_report.session_id,
            user_id=new_report.user_id,
            timestamp=new_report.timestamp,
            duration=new_report.duration,
            conversation_log=[
                ConversationLogItem(**item) for item in new_report.conversation_log
            ] if new_report.conversation_log else None,
            situation=new_report.situation,
            automatic_thoughts=new_report.automatic_thoughts,
            emotions=[
                EmotionItem(**item) for item in new_report.emotions
            ],
            physical_sensations=new_report.physical_sensations,
            summary=new_report.summary
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建记录报告失败: {str(e)}")

@router.get("/record-reports/{record_id}", response_model=RecordReport)
async def get_record_report(
    record_id: str,
    db: Session = Depends(DBConfig.get_db)
):
    """
    获取记录报告
    - 根据记录ID获取记录报告
    - 返回记录报告详情
    """
    try:
        # 查询记录报告
        report = db.query(RecordReportDB).filter(RecordReportDB.record_id == record_id).first()
        
        if not report:
            raise HTTPException(status_code=404, detail="记录报告不存在")
        
        # 转换为响应模型
        return RecordReport(
            record_id=report.record_id,
            session_id=report.session_id,
            user_id=report.user_id,
            timestamp=report.timestamp,
            duration=report.duration,
            conversation_log=[
                ConversationLogItem(**item) for item in report.conversation_log
            ] if report.conversation_log else None,
            situation=report.situation,
            automatic_thoughts=report.automatic_thoughts,
            emotions=[
                EmotionItem(**item) for item in report.emotions
            ],
            physical_sensations=report.physical_sensations,
            summary=report.summary
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取记录报告失败: {str(e)}")

@router.get("/record-reports/user/{user_id}", response_model=List[RecordReport])
async def get_user_record_reports(
    user_id: str,
    db: Session = Depends(DBConfig.get_db)
):
    """
    获取用户的所有记录报告
    - 根据用户ID获取所有记录报告
    - 返回记录报告列表
    """
    try:
        # 查询用户的所有记录报告
        reports = db.query(RecordReportDB).filter(RecordReportDB.user_id == user_id).order_by(RecordReportDB.created_at.desc()).all()
        
        # 转换为响应模型列表
        return [
            RecordReport(
                record_id=report.record_id,
                session_id=report.session_id,
                user_id=report.user_id,
                timestamp=report.timestamp,
                duration=report.duration,
                conversation_log=[
                    ConversationLogItem(**item) for item in report.conversation_log
                ] if report.conversation_log else None,
                situation=report.situation,
                automatic_thoughts=report.automatic_thoughts,
                emotions=[
                    EmotionItem(**item) for item in report.emotions
                ],
                physical_sensations=report.physical_sensations,
                summary=report.summary
            )
            for report in reports
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取用户记录报告失败: {str(e)}")