"""
智能体对话相关的API端点
"""
from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from typing import Dict, Any, List
from pydantic import BaseModel

from backend.agents import AnalystAgent, TherapistAgent, DepressionPatientAgent
from backend.api.auth_endpoints import get_db

router = APIRouter(prefix="/api/dialogue", tags=["dialogue"])


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
        
        # 2. 患者响应
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
