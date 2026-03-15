########     API端点       ###########
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from backend.agents.analyst_agent import AnalystAgent
from backend.core.database import DBConfig, AnalysisReportDB
from backend.core.data_models import (
    AnalysisReport, AnalysisReportCreate, CBTAnalysis, TCMAnalysis,
    DistortionItem, DominantEmotion, SecondaryEmotion
)
from sqlalchemy.orm import Session
from datetime import datetime
import uuid
import time

router = APIRouter(prefix="/analyst", tags=["analyst"])
analyst_agent = AnalystAgent()

class AnalysisRequest(BaseModel):
    record_id: str
    priority: str = "normal"  # low, normal, high
    callback_url: str = None  # 异步回调地址

class AnalysisResponse(BaseModel):
    request_id: str
    status: str
    message: str
    report_id: Optional[str] = None  # 分析完成时返回报告ID
    estimated_completion_time: Optional[int] = None

@router.post("/analyze", response_model=AnalysisResponse)
async def request_analysis(request: AnalysisRequest, background_tasks: BackgroundTasks):
    """请求分析（支持同步/异步）"""
    request_id = f"req_{uuid.uuid4().hex[:8]}"
    
    # 简单任务直接同步处理
    if request.priority == "high":
        result = await analyst_agent.execute({"record_id": request.record_id})
        status = "completed" if result["status"] == "success" else "failed"
        return AnalysisResponse(
            request_id=request_id,
            status=status,
            message=result.get("error", "分析完成"),
            report_id=result.get("report_id")  # 返回报告ID
        )
    
    # 正常优先级任务放入后台
    background_tasks.add_task(
        process_analysis_async,
        request_id,
        request.record_id,
        request.callback_url
    )
    
    return AnalysisResponse(
        request_id=request_id,
        status="queued",
        message="分析任务已加入队列",
        estimated_completion_time=30  # 预估30秒
    )

@router.get("/report/{report_id}")
async def get_report(report_id: str):
    """获取分析报告"""
    # 这里需要实现从数据库获取报告的逻辑
    # 暂时返回示例
    return {
        "report_id": report_id,
        "status": "available",
        "content": {
            "cbt_summary": "检测到过度概括思维",
            "tcm_summary": "主导情志为忧"
        }
    }

@router.get("/performance")
async def get_performance():
    """获取分析师性能指标"""
    metrics = analyst_agent.get_performance_metrics()
    return {
        "agent_name": analyst_agent.agent_name,
        "metrics": metrics,
        "timestamp": time.time()
    }

async def process_analysis_async(request_id: str, record_id: str, callback_url: str = None):
    """异步处理分析任务"""
    try:
        result = await analyst_agent.execute({"record_id": record_id})
        
        # 如果有回调URL，通知结果
        if callback_url:
            # 这里实现HTTP回调
            pass
            
    except Exception as e:
        print(f"异步分析失败: {e}")

# 分析报告相关接口
@router.post("/analysis-reports", response_model=AnalysisReport)
async def create_analysis_report(
    report_data: AnalysisReportCreate,
    db: Session = Depends(DBConfig.get_db)
):
    """
    创建分析报告
    - 保存分析报告到数据库
    - 返回创建的分析报告
    """
    try:
        # 生成报告ID
        report_id = f"ana_{uuid.uuid4().hex[:8]}"
        
        # 转换cbt_analysis为JSON格式
        cbt_analysis_json = {
            "distortions_detected": [item.dict() for item in report_data.cbt_analysis.distortions_detected],
            "summary": report_data.cbt_analysis.summary,
            "challenge_questions": report_data.cbt_analysis.challenge_questions
        }
        
        # 转换tcm_analysis为JSON格式
        tcm_analysis_json = {
            "dominant_emotion": report_data.tcm_analysis.dominant_emotion.dict(),
            "inhibiting_emotion": report_data.tcm_analysis.inhibiting_emotion,
            "secondary_emotions": [item.dict() for item in report_data.tcm_analysis.secondary_emotions],
            "recommended_interventions": report_data.tcm_analysis.recommended_interventions
        }
        
        # 创建分析报告实例
        new_report = AnalysisReportDB(
            report_id=report_id,
            record_id=report_data.record_id,
            user_id=report_data.user_id,
            timestamp=datetime.utcnow(),
            analysis_duration=report_data.analysis_duration,
            confidence_score=report_data.confidence_score,
            cbt_analysis=cbt_analysis_json,
            tcm_analysis=tcm_analysis_json,
            integrated_framework=report_data.integrated_framework,
            priority=report_data.priority
        )
        
        # 保存到数据库
        db.add(new_report)
        db.commit()
        db.refresh(new_report)
        
        # 转换为响应模型
        return AnalysisReport(
            report_id=new_report.report_id,
            record_id=new_report.record_id,
            user_id=new_report.user_id,
            timestamp=new_report.timestamp,
            analysis_duration=new_report.analysis_duration,
            confidence_score=new_report.confidence_score,
            cbt_analysis=CBTAnalysis(
                distortions_detected=[
                    DistortionItem(**item) for item in new_report.cbt_analysis["distortions_detected"]
                ],
                summary=new_report.cbt_analysis["summary"],
                challenge_questions=new_report.cbt_analysis.get("challenge_questions")
            ),
            tcm_analysis=TCMAnalysis(
                dominant_emotion=DominantEmotion(**new_report.tcm_analysis["dominant_emotion"]),
                inhibiting_emotion=new_report.tcm_analysis["inhibiting_emotion"],
                secondary_emotions=[
                    SecondaryEmotion(**item) for item in new_report.tcm_analysis["secondary_emotions"]
                ],
                recommended_interventions=new_report.tcm_analysis["recommended_interventions"]
            ),
            integrated_framework=new_report.integrated_framework,
            priority=new_report.priority
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建分析报告失败: {str(e)}")

@router.get("/analysis-reports/{report_id}", response_model=AnalysisReport)
async def get_analysis_report(
    report_id: str,
    db: Session = Depends(DBConfig.get_db)
):
    """
    获取分析报告
    - 根据报告ID获取分析报告
    - 返回分析报告详情
    """
    try:
        # 查询分析报告
        report = db.query(AnalysisReportDB).filter(AnalysisReportDB.report_id == report_id).first()
        
        if not report:
            raise HTTPException(status_code=404, detail="分析报告不存在")
        
        # 转换为响应模型
        return AnalysisReport(
            report_id=report.report_id,
            record_id=report.record_id,
            user_id=report.user_id,
            timestamp=report.timestamp,
            analysis_duration=report.analysis_duration,
            confidence_score=report.confidence_score,
            cbt_analysis=CBTAnalysis(
                distortions_detected=[
                    DistortionItem(**item) for item in report.cbt_analysis["distortions_detected"]
                ],
                summary=report.cbt_analysis["summary"],
                challenge_questions=report.cbt_analysis.get("challenge_questions")
            ),
            tcm_analysis=TCMAnalysis(
                dominant_emotion=DominantEmotion(**report.tcm_analysis["dominant_emotion"]),
                inhibiting_emotion=report.tcm_analysis["inhibiting_emotion"],
                secondary_emotions=[
                    SecondaryEmotion(**item) for item in report.tcm_analysis["secondary_emotions"]
                ],
                recommended_interventions=report.tcm_analysis["recommended_interventions"]
            ),
            integrated_framework=report.integrated_framework,
            priority=report.priority
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取分析报告失败: {str(e)}")

@router.get("/analysis-reports/user/{user_id}", response_model=List[AnalysisReport])
async def get_user_analysis_reports(
    user_id: str,
    db: Session = Depends(DBConfig.get_db)
):
    """
    获取用户的所有分析报告
    - 根据用户ID获取所有分析报告
    - 返回分析报告列表
    """
    try:
        # 查询用户的所有分析报告
        reports = db.query(AnalysisReportDB).filter(AnalysisReportDB.user_id == user_id).order_by(AnalysisReportDB.created_at.desc()).all()
        
        # 转换为响应模型列表
        return [
            AnalysisReport(
                report_id=report.report_id,
                record_id=report.record_id,
                user_id=report.user_id,
                timestamp=report.timestamp,
                analysis_duration=report.analysis_duration,
                confidence_score=report.confidence_score,
                cbt_analysis=CBTAnalysis(
                    distortions_detected=[
                        DistortionItem(**item) for item in report.cbt_analysis["distortions_detected"]
                    ],
                    summary=report.cbt_analysis["summary"],
                    challenge_questions=report.cbt_analysis.get("challenge_questions")
                ),
                tcm_analysis=TCMAnalysis(
                    dominant_emotion=DominantEmotion(**report.tcm_analysis["dominant_emotion"]),
                    inhibiting_emotion=report.tcm_analysis["inhibiting_emotion"],
                    secondary_emotions=[
                        SecondaryEmotion(**item) for item in report.tcm_analysis["secondary_emotions"]
                    ],
                    recommended_interventions=report.tcm_analysis["recommended_interventions"]
                ),
                integrated_framework=report.integrated_framework,
                priority=report.priority
            )
            for report in reports
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取用户分析报告失败: {str(e)}")

@router.get("/analysis-reports/record/{record_id}", response_model=AnalysisReport)
async def get_record_analysis_report(
    record_id: str,
    db: Session = Depends(DBConfig.get_db)
):
    """
    获取记录的分析报告
    - 根据记录ID获取分析报告
    - 返回分析报告详情
    """
    try:
        # 查询分析报告
        report = db.query(AnalysisReportDB).filter(AnalysisReportDB.record_id == record_id).first()
        
        if not report:
            raise HTTPException(status_code=404, detail="分析报告不存在")
        
        # 转换为响应模型
        return AnalysisReport(
            report_id=report.report_id,
            record_id=report.record_id,
            user_id=report.user_id,
            timestamp=report.timestamp,
            analysis_duration=report.analysis_duration,
            confidence_score=report.confidence_score,
            cbt_analysis=CBTAnalysis(
                distortions_detected=[
                    DistortionItem(**item) for item in report.cbt_analysis["distortions_detected"]
                ],
                summary=report.cbt_analysis["summary"],
                challenge_questions=report.cbt_analysis.get("challenge_questions")
            ),
            tcm_analysis=TCMAnalysis(
                dominant_emotion=DominantEmotion(**report.tcm_analysis["dominant_emotion"]),
                inhibiting_emotion=report.tcm_analysis["inhibiting_emotion"],
                secondary_emotions=[
                    SecondaryEmotion(**item) for item in report.tcm_analysis["secondary_emotions"]
                ],
                recommended_interventions=report.tcm_analysis["recommended_interventions"]
            ),
            integrated_framework=report.integrated_framework,
            priority=report.priority
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取分析报告失败: {str(e)}")