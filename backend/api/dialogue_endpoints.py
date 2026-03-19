"""
智能体对话相关的API端点
"""
from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
import uuid
from datetime import datetime

from backend.agents import AnalystAgent, TherapistAgent, DepressionPatientAgent
from backend.api.auth_endpoints import get_db
from backend.core.database import ConversationDB, MessageDB, RecordReportDB, AnalysisReportDB, SuggestionReportDB

router = APIRouter(prefix="/api/dialogue", tags=["dialogue"])
conversations_router = APIRouter(prefix="/api/conversations", tags=["conversations"])


class DialogueRequest(BaseModel):
    """对话请求模型"""
    message_type: str = "greeting"
    context: str = ""
    patient_id: str = "default_patient"


class DialogueResponse(BaseModel):
    """对话响应模型"""
    agent: str
    status: str
    response: str
    conversation_history: List[Dict[str, Any]]
    processing_time: float


class MultiAgentDialogueRequest(BaseModel):
    """多智能体对话请求模型"""
    patient_message: str
    patient_id: str = "default_patient"


class MultiAgentDialogueResponse(BaseModel):
    """多智能体对话响应模型"""
    patient_response: str
    analyst_response: Dict[str, Any]
    therapist_response: Dict[str, Any]
    conversation_history: List[Dict[str, Any]]


# 智能体实例
patient_agent = DepressionPatientAgent()
analyst_agent = AnalystAgent()
therapist_agent = TherapistAgent()

# 对话历史存储
conversation_histories = {}

# 会话测试状态存储
session_test_states = {}


from pydantic import BaseModel, Field

class StartTestRequest(BaseModel):
    """开始测试请求模型"""
    session_id: str = Field(..., description="对话会话ID")


class PauseTestRequest(BaseModel):
    """暂停测试请求模型"""
    session_id: str = Field(..., description="对话会话ID")


class CreateConversationRequest(BaseModel):
    """创建会话请求模型"""
    type: str = Field(..., description="会话类型")


@router.post("/patient", response_model=DialogueResponse)
async def get_patient_response(
    request: DialogueRequest
):
    """
    获取抑郁症来访者智能体的响应
    """
    # 生成患者响应
    result = await patient_agent.execute({
        "message_type": request.message_type,
        "context": request.context
    })
    
    # 保存对话历史
    if request.patient_id not in conversation_histories:
        conversation_histories[request.patient_id] = []
    
    conversation_histories[request.patient_id].append({
        "role": "patient",
        "message": result.get("response", ""),
        "timestamp": result.get("processing_time", 0)
    })
    
    return DialogueResponse(
        agent=result.get("agent", ""),
        status=result.get("status", "error"),
        response=result.get("response", ""),
        conversation_history=result.get("conversation_history", []),
        processing_time=result.get("processing_time", 0)
    )


@router.post("/multi-agent", response_model=MultiAgentDialogueResponse)
async def multi_agent_dialogue(
    request: MultiAgentDialogueRequest,
    db: Session = Depends(get_db)
):
    """
    多智能体对话接口
    - 抑郁症来访者智能体生成初始消息
    - 分析师智能体分析患者状态
    - 调理师智能体生成调理建议
    """
    try:
        # 1. 初始化对话历史
        if request.patient_id not in conversation_histories:
            conversation_histories[request.patient_id] = []
        
        # 2. 添加记录师的初始提问
        recorder_message = "您好，我是您的记录师。请告诉我您最近的情绪状态和遇到的问题，我会帮您记录并分析。"
        conversation_histories[request.patient_id].append({
            "role": "recorder",
            "message": recorder_message,
            "timestamp": 0
        })
        
        # 3. 患者响应
        patient_result = await patient_agent.execute({
            "message_type": "greeting",
            "context": request.patient_message
        })
        patient_response = patient_result.get("response", "")
        
        # 3. 构建模拟的记录报告数据
        mock_record_data = {
            "record_id": f"mock_record_{request.patient_id}",
            "user_id": request.patient_id,
            "situation": patient_response,
            "automatic_thoughts": [
                "我觉得自己什么都做不好",
                "没有人会关心我",
                "我的未来一片黑暗"
            ],
            "emotions": [
                {"type": "忧", "intensity": 8},
                {"type": "思", "intensity": 6}
            ],
            "physical_sensations": ["疲劳", "头痛", "失眠"]
        }
        
        # 4. 分析师智能体分析
        analyst_result = await analyst_agent.execute({
            "record_id": mock_record_data["record_id"]
        })
        
        # 5. 调理师智能体生成建议
        therapist_result = await therapist_agent.execute({
            "report_id": analyst_result.get("report_id", "")
        })
        
        # 6. 记录对话历史
        conversation_histories[request.patient_id].extend([
            {
                "role": "patient",
                "message": patient_response,
                "timestamp": patient_result.get("processing_time", 0)
            },
            {
                "role": "analyst",
                "message": analyst_result.get("diagnosis_preview", {}),
                "timestamp": analyst_result.get("processing_time", 0)
            },
            {
                "role": "therapist",
                "message": therapist_result.get("suggestion_summary", {}),
                "timestamp": therapist_result.get("processing_time", 0)
            },
            {
                "role": "recorder",
                "message": "感谢您的分享。我们已经完成了分析和调理建议的生成。如果您有任何其他问题，请随时告诉我。",
                "timestamp": 0
            }
        ])
        
        return MultiAgentDialogueResponse(
            patient_response=patient_response,
            analyst_response=analyst_result,
            therapist_response=therapist_result,
            conversation_history=conversation_histories[request.patient_id]
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"对话处理失败: {str(e)}"
        )


@router.get("/history/{patient_id}")
async def get_conversation_history(
    patient_id: str
):
    """
    获取对话历史
    """
    if patient_id not in conversation_histories:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="对话历史不存在"
        )
    
    return {
        "patient_id": patient_id,
        "conversation_history": conversation_histories[patient_id]
    }


@router.delete("/history/{patient_id}")
async def clear_conversation_history(
    patient_id: str
):
    """
    清除对话历史
    """
    if patient_id in conversation_histories:
        del conversation_histories[patient_id]
    
    return {
        "message": "对话历史已清除"
    }


@conversations_router.post("/start-test")
async def start_test(
    request: StartTestRequest
):
    """
    启动对话测试流程
    """
    try:
        # 验证请求参数
        if not request.session_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="session_id 不能为空"
            )
        
        # 检查会话状态
        if request.session_id in session_test_states:
            current_state = session_test_states[request.session_id].get("status")
            if current_state == "testing":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="测试已在进行中"
                )
        else:
            # 新会话，初始化状态为idle
            session_test_states[request.session_id] = {
                "status": "idle",
                "test_id": None,
                "start_time": None,
                "pause_time": None,
                "current_phase": "recorder"
            }
        
        # 生成测试ID
        test_id = f"test_{uuid.uuid4().hex[:8]}"
        start_time = datetime.utcnow().isoformat()
        
        # 更新会话状态
        session_test_states[request.session_id].update({
            "status": "testing",
            "test_id": test_id,
            "start_time": start_time,
            "pause_time": None,
            "current_phase": "recorder"
        })
        
        # 初始化对话历史
        if request.session_id not in conversation_histories:
            conversation_histories[request.session_id] = []
        
        # 启动测试流程（这里可以添加实际的测试逻辑）
        # 例如：开始定时发送患者消息和系统回复
        
        return {
            "status": "success",
            "message": "测试已成功开始",
            "data": {
                "session_id": request.session_id,
                "status": "testing",
                "start_time": start_time
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"开始测试失败: {str(e)}"
        )


@conversations_router.post("/pause-test")
async def pause_test(
    request: PauseTestRequest
):
    """
    暂停对话测试流程
    """
    try:
        # 验证请求参数
        if not request.session_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="session_id 不能为空"
            )
        
        # 检查会话状态
        if request.session_id not in session_test_states:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="会话不存在"
            )
        
        current_state = session_test_states[request.session_id].get("status")
        if current_state != "testing":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="会话未处于测试状态"
            )
        
        # 更新会话状态
        pause_time = datetime.utcnow().isoformat()
        
        session_test_states[request.session_id].update({
            "status": "paused",
            "pause_time": pause_time
        })
        
        # 暂停测试流程（这里可以添加实际的暂停逻辑）
        # 例如：停止定时发送消息
        
        return {
            "status": "success",
            "message": "测试已成功暂停",
            "data": {
                "session_id": request.session_id,
                "status": "paused",
                "pause_time": pause_time
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"暂停测试失败: {str(e)}"
        )


@conversations_router.post("/create")
async def create_conversation(
    request: CreateConversationRequest
):
    """
    创建对话会话
    """
    try:
        # 验证请求参数
        if not request.type:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="会话类型不能为空"
            )
        
        # 生成会话ID
        session_id = f"sess_{uuid.uuid4().hex[:8]}"
        
        # 初始化会话状态
        session_test_states[session_id] = {
            "status": "idle",
            "test_id": None,
            "start_time": None,
            "pause_time": None,
            "current_phase": "recorder"
        }
        
        # 初始化对话历史
        conversation_histories[session_id] = []
        
        return {
            "session_id": session_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建会话失败: {str(e)}"
        )


class SaveHistoryRequest(BaseModel):
    """保存对话历史请求模型"""
    session_id: Optional[str] = None
    patient_id: Optional[str] = None
    title: str = Field(..., description="对话标题")
    user_id: str = Field(..., description="用户ID")




@router.post("/save-history")
async def save_conversation_history(
    request: SaveHistoryRequest,
    db: Session = Depends(get_db)
):
    """
    保存对话历史到数据库
    - 只有在记录报告完成后才保存对话
    - 确保对话记录关联到正确的报告
    """
    try:
        # 确定使用哪个ID作为对话历史的键
        history_key = request.session_id if request.session_id else request.patient_id
        
        if not history_key:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="session_id或patient_id至少需要提供一个"
            )
        
        # 检查是否存在相关的记录报告
        record_report = db.query(RecordReportDB).filter(
            RecordReportDB.session_id == history_key,
            RecordReportDB.user_id == request.user_id
        ).first()
        
        # 只有在记录报告完成后才保存对话
        if not record_report:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="记录报告尚未完成，无法保存对话"
            )
        
        # 检查对话历史是否存在
        if history_key not in conversation_histories:
            # 如果对话历史不存在，创建一个空的对话历史
            conversation_histories[history_key] = []
        
        # 获取对话历史
        history = conversation_histories[history_key]
        
        # 创建对话记录
        conversation_id = f"conv_{uuid.uuid4().hex[:8]}"
        conversation = ConversationDB(
            id=conversation_id,
            user_id=request.user_id,
            title=request.title,
            timestamp=datetime.utcnow(),
            phase="completed",
            record_result_id=None,  # 暂时设置为None，实际应用中需要关联真实的报告ID
            analysis_result_id=None,  # 暂时设置为None，实际应用中需要关联真实的报告ID
            therapy_result_id=None,  # 暂时设置为None，实际应用中需要关联真实的报告ID
            context=None  # 暂时设置为None，实际应用中可以存储对话上下文
        )
        db.add(conversation)
        
        # 创建消息记录
        messages = []
        for msg in history:
            # 处理角色值，确保符合枚举类型
            role = msg["role"]
            if role == "patient":
                role = "user"
            elif role not in ["user", "recorder", "analyst", "therapist", "system"]:
                role = "system"
                
            message = MessageDB(
                conversation_id=conversation_id,
                role=role,
                content=str(msg["message"]),
                created_at=datetime.utcnow()
            )
            messages.append(message)
            db.add(message)
        
        # 检查是否存在相关的记录报告
        record_report = db.query(RecordReportDB).filter(
            RecordReportDB.session_id == history_key,
            RecordReportDB.user_id == request.user_id
        ).first()
        
        # 检查是否存在相关的分析报告
        analysis_report = None
        if record_report:
            analysis_report = db.query(AnalysisReportDB).filter(
                AnalysisReportDB.record_id == record_report.record_id,
                AnalysisReportDB.user_id == request.user_id
            ).first()
        
        # 检查是否存在相关的调理报告
        suggestion_report = None
        if analysis_report:
            suggestion_report = db.query(SuggestionReportDB).filter(
                SuggestionReportDB.report_id == analysis_report.report_id,
                SuggestionReportDB.user_id == request.user_id
            ).first()
        
        # 如果存在记录报告，更新其对话日志
        if record_report:
            # 准备对话日志数据
            conversation_log = []
            for msg in history:
                conversation_log.append({
                    "role": "user" if msg["role"] == "patient" else "assistant",
                    "content": str(msg["message"])
                })
            
            # 更新记录报告
            record_report.conversation_log = conversation_log
            # 关联记录报告ID到对话记录
            conversation.record_result_id = record_report.record_id
        
        # 关联分析报告ID到对话记录
        if analysis_report:
            conversation.analysis_result_id = analysis_report.report_id
        
        # 关联调理报告ID到对话记录
        if suggestion_report:
            conversation.therapy_result_id = suggestion_report.suggestion_id
        
        # 提交事务
        db.commit()
        
        return {
            "status": "success",
            "message": "对话历史保存成功",
            "data": {
                "conversation_id": conversation_id,
                "message_count": len(history),
                "record_report_updated": record_report is not None,
                "analysis_report_updated": analysis_report is not None,
                "therapy_report_updated": suggestion_report is not None,
                "reports": {
                    "record_report_id": record_report.record_id if record_report else None,
                    "analysis_report_id": analysis_report.report_id if analysis_report else None,
                    "therapy_report_id": suggestion_report.suggestion_id if suggestion_report else None
                }
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"保存对话历史失败: {str(e)}"
        )


# 导出路由
__all__ = ["router", "conversations_router"]
