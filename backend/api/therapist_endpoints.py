########     API端点       ###########
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from backend.agents.therapist_agent import TherapistAgent
from backend.core.database import DBConfig, SuggestionReportDB
from backend.core.data_models import (
    SuggestionReport, SuggestionReportCreate, DailySuggestion
)
from sqlalchemy.orm import Session
from datetime import datetime
import uuid
import time

router = APIRouter(prefix="/therapist", tags=["therapist"])
therapist_agent = TherapistAgent()

class SuggestionRequest(BaseModel):
    report_id: str
    priority: str = "normal"  # low, normal, high
    callback_url: str = None  # 异步回调地址

class SuggestionResponse(BaseModel):
    request_id: str
    status: str
    message: str
    suggestion_id: Optional[str] = None  # 建议报告生成完成时返回报告ID
    estimated_completion_time: Optional[int] = None

@router.post("/suggest", response_model=SuggestionResponse)
async def request_suggestion(request: SuggestionRequest, background_tasks: BackgroundTasks):
    """请求生成建议报告（支持同步/异步）"""
    request_id = f"req_{uuid.uuid4().hex[:8]}"
    
    # 简单任务直接同步处理
    if request.priority == "high":
        result = await therapist_agent.execute({"report_id": request.report_id})
        status = "completed" if result["status"] == "success" else "failed"
        return SuggestionResponse(
            request_id=request_id,
            status=status,
            message=result.get("error", "建议报告生成完成"),
            suggestion_id=result.get("suggestion_id")  # 返回建议报告ID
        )
    
    # 正常优先级任务放入后台
    background_tasks.add_task(
        process_suggestion_async,
        request_id,
        request.report_id,
        request.callback_url
    )
    
    return SuggestionResponse(
        request_id=request_id,
        status="queued",
        message="建议报告生成任务已加入队列",
        estimated_completion_time=30  # 预估30秒
    )

@router.post("/suggestion-reports", response_model=SuggestionReport)
async def create_suggestion_report(
    report_data: SuggestionReportCreate,
    db: Session = Depends(DBConfig.get_db)
):
    """
    创建建议报告
    - 保存建议报告到数据库
    - 返回创建的建议报告
    """
    try:
        # 生成建议报告ID
        suggestion_id = f"sug_{uuid.uuid4().hex[:8]}"
        
        # 创建建议报告实例
        new_report = SuggestionReportDB(
            suggestion_id=suggestion_id,
            report_id=report_data.report_id,
            user_id=report_data.user_id,
            timestamp=datetime.utcnow(),
            target_issues=report_data.target_issues,
            core_principles=report_data.core_principles,
            daily_suggestions=[item.dict() for item in report_data.daily_suggestions],
            emergency_tips=report_data.emergency_tips,
            encouragement=report_data.encouragement,
            plan_summary=report_data.plan_summary
        )
        
        # 保存到数据库
        db.add(new_report)
        db.commit()
        db.refresh(new_report)
        
        # 转换为响应模型
        return SuggestionReport(
            suggestion_id=new_report.suggestion_id,
            report_id=new_report.report_id,
            user_id=new_report.user_id,
            timestamp=new_report.timestamp,
            target_issues=new_report.target_issues,
            core_principles=new_report.core_principles,
            daily_suggestions=[
                DailySuggestion(**item) for item in new_report.daily_suggestions
            ],
            emergency_tips=new_report.emergency_tips,
            encouragement=new_report.encouragement,
            plan_summary=new_report.plan_summary
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建建议报告失败: {str(e)}")

@router.get("/suggestion-reports/{suggestion_id}", response_model=SuggestionReport)
async def get_suggestion_report(
    suggestion_id: str,
    db: Session = Depends(DBConfig.get_db)
):
    """
    获取建议报告
    - 根据建议报告ID获取建议报告
    - 返回建议报告详情
    """
    try:
        # 查询建议报告
        report = db.query(SuggestionReportDB).filter(SuggestionReportDB.suggestion_id == suggestion_id).first()
        
        if not report:
            raise HTTPException(status_code=404, detail="建议报告不存在")
        
        # 转换为响应模型
        return SuggestionReport(
            suggestion_id=report.suggestion_id,
            report_id=report.report_id,
            user_id=report.user_id,
            timestamp=report.timestamp,
            target_issues=report.target_issues,
            core_principles=report.core_principles,
            daily_suggestions=[
                DailySuggestion(**item) for item in report.daily_suggestions
            ],
            emergency_tips=report.emergency_tips,
            encouragement=report.encouragement,
            plan_summary=report.plan_summary
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取建议报告失败: {str(e)}")

@router.get("/suggestion-reports/user/{user_id}", response_model=List[SuggestionReport])
async def get_user_suggestion_reports(
    user_id: str,
    db: Session = Depends(DBConfig.get_db)
):
    """
    获取用户的所有建议报告
    - 根据用户ID获取所有建议报告
    - 返回建议报告列表
    """
    try:
        # 查询用户的所有建议报告
        reports = db.query(SuggestionReportDB).filter(SuggestionReportDB.user_id == user_id).order_by(SuggestionReportDB.created_at.desc()).all()
        
        # 转换为响应模型列表
        return [
            SuggestionReport(
                suggestion_id=report.suggestion_id,
                report_id=report.report_id,
                user_id=report.user_id,
                timestamp=report.timestamp,
                target_issues=report.target_issues,
                core_principles=report.core_principles,
                daily_suggestions=[
                    DailySuggestion(**item) for item in report.daily_suggestions
                ],
                emergency_tips=report.emergency_tips,
                encouragement=report.encouragement,
                plan_summary=report.plan_summary
            )
            for report in reports
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取用户建议报告失败: {str(e)}")

@router.get("/suggestion-reports/report/{report_id}", response_model=SuggestionReport)
async def get_report_suggestion_report(
    report_id: str,
    db: Session = Depends(DBConfig.get_db)
):
    """
    获取分析报告的建议报告
    - 根据分析报告ID获取建议报告
    - 返回建议报告详情
    """
    try:
        # 查询建议报告
        report = db.query(SuggestionReportDB).filter(SuggestionReportDB.report_id == report_id).first()
        
        if not report:
            raise HTTPException(status_code=404, detail="建议报告不存在")
        
        # 转换为响应模型
        return SuggestionReport(
            suggestion_id=report.suggestion_id,
            report_id=report.report_id,
            user_id=report.user_id,
            timestamp=report.timestamp,
            target_issues=report.target_issues,
            core_principles=report.core_principles,
            daily_suggestions=[
                DailySuggestion(**item) for item in report.daily_suggestions
            ],
            emergency_tips=report.emergency_tips,
            encouragement=report.encouragement,
            plan_summary=report.plan_summary
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取建议报告失败: {str(e)}")

@router.get("/performance")
async def get_performance():
    """获取调理师性能指标"""
    metrics = therapist_agent.get_performance_metrics()
    return {
        "agent_name": therapist_agent.agent_name,
        "metrics": metrics,
        "timestamp": time.time()
    }

class GeneratePlanRequest(BaseModel):
    report_id: str
    user_preference: str = "balanced"

@router.post("/generate-plan")
async def generate_plan(request: GeneratePlanRequest):
    """生成调理计划"""
    try:
        result = await therapist_agent.execute({
            "report_id": request.report_id,
            "user_preference": request.user_preference
        })
        return {
            "status": "success",
            "message": "调理计划生成成功",
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成调理计划失败: {str(e)}")

async def process_suggestion_async(request_id: str, report_id: str, callback_url: str = None):
    """异步处理建议报告生成任务"""
    try:
        result = await therapist_agent.execute({"report_id": report_id})
        
        # 如果有回调URL，通知结果
        if callback_url:
            # 这里实现HTTP回调
            pass
            
    except Exception as e:
        print(f"异步生成建议报告失败: {e}")
