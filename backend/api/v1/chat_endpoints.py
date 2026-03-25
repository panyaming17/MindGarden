"""
对话核心的API端点
"""
from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from datetime import datetime
import uuid
from typing import List, Optional

from backend.core.database import DBConfig, UserDB, DialogueDB, SessionLocal
from backend.core.data_models import (
    ChatMessage,
    ChatMessageResponse,
    NewSessionResponse,
    SessionInfo,
    SessionList,
    ChatHistoryResponse,
    Dialogue
)
from backend.agents.recorder_agent import RecorderAgent
from backend.agents.therapist_agent import TherapistAgent
from backend.agents.analyst_agent import AnalystAgent
from backend.core.llm_service import get_llm_service

router = APIRouter(prefix="/api/v1/chat", tags=["chat"])

# 依赖注入获取数据库会话
def get_db():
    """获取数据库会话的依赖函数"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 初始化智能体
recorder_agent = RecorderAgent()
therapist_agent = TherapistAgent()
analyst_agent = AnalystAgent()

# 全局LLM服务实例
llm_service = None

# 发送消息接口
@router.post("/message", response_model=ChatMessageResponse)
async def send_message(
    message: ChatMessage,
    db: Session = Depends(get_db)
):
    """
    发送消息
    """
    # 检查用户是否存在
    try:
        print(f"DEBUG: 开始用户检查，用户ID: {message.user_id}")
        # 检查用户是否存在
        user = db.query(UserDB).filter(UserDB.id == message.user_id).first()
        if not user:
            # 用户不存在，创建新用户
            username = str(message.user_id)
            email = f"{message.user_id}@example.com"
            password_hash = "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW"  # 123456的哈希值
            
            new_user = UserDB(
                username=username,
                email=email,
                password_hash=password_hash,
                is_active=True,
                role="user"
            )
            db.add(new_user)
            db.commit()
            db.refresh(new_user)
            user = new_user
            print(f"DEBUG: 用户创建成功，用户ID: {user.id}")
        else:
            print(f"DEBUG: 用户已存在，用户ID: {user.id}")
    except Exception as e:
        print(f"ERROR: 用户检查/创建失败: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="用户检查/创建失败"
        )
    
    # 获取LLM服务实例
    global llm_service
    if llm_service is None:
        llm_service = await get_llm_service()
    
    # 确保调理师智能体使用LLM服务
    if not therapist_agent.llm_service:
        therapist_agent.llm_service = llm_service
    
    # 确保分析师智能体使用LLM服务
    if not analyst_agent.llm_service:
        analyst_agent.llm_service = llm_service
    
    # 生成对话ID
    dialogue_id = f"dialogue_{uuid.uuid4().hex[:8]}"
    
    # 调用记录师智能体处理用户消息
    try:
        recorder_result = await recorder_agent.execute({
            "user_id": message.user_id,
            "session_id": message.session_id,
            "message": message.message
        })
        # 确保recorder_result是一个字典
        if not isinstance(recorder_result, dict):
            recorder_result = {}
    except Exception as e:
        # 记录师智能体执行失败，使用默认值
        recorder_result = {
            "intensity": 0.0,
            "hedonic": "中性",
            "tension": "低",
            "complexity": "简单",
            "is_valuable": False
        }
    
    # 注：用户消息已由记录师智能体保存，此处不再重复保存
    
    # 异步触发分析师（如果消息有价值）
    if recorder_result.get("is_valuable", False):
        try:
            await analyst_agent.execute({
                "user_id": message.user_id,
                "session_id": message.session_id,
                "dialogue_id": dialogue_id,
                "user_input": message.message,
                "four_dim": {
                    "intensity": recorder_result.get("intensity"),
                    "hedonic": recorder_result.get("hedonic"),
                    "tension": recorder_result.get("tension"),
                    "complexity": recorder_result.get("complexity")
                }
            })
        except Exception as e:
            # 分析师智能体执行失败，忽略
            pass
    
    # 调用调理师智能体生成回复
    try:
        # 打印调试信息
        print(f"DEBUG: therapist_agent.llm_service = {therapist_agent.llm_service}")
        
        therapist_result = await therapist_agent.execute({
            "user_id": message.user_id,
            "session_id": message.session_id,
            "user_input": message.message  # 修正参数名，使用user_input而不是message
        })
        
        # 打印调试信息
        print(f"DEBUG: therapist_result = {therapist_result}")
        
        # 确保therapist_result是一个字典
        if not isinstance(therapist_result, dict):
            therapist_result = {}
    except Exception as e:
        # 打印错误信息
        print(f"ERROR: 调理师智能体执行失败: {str(e)}")
        import traceback
        traceback.print_exc()
        # 调理师智能体执行失败，使用默认回复
        therapist_result = {"data": {"reply": "我理解您的感受。"}}
    
    # 生成助手回复的对话ID
    assistant_dialogue_id = f"dialogue_{uuid.uuid4().hex[:8]}"
    
    # 获取助手回复，从data字段中获取
    assistant_reply = therapist_result.get("data", {}).get("reply", "我理解您的感受。")
    
    # 注：助手回复已由调理师智能体保存，此处不再重复保存
    
    # 构建响应
    response = ChatMessageResponse(
        reply=assistant_reply,
        four_dim={
            "intensity": recorder_result.get("intensity", 0.0),
            "hedonic": recorder_result.get("hedonic", "中性"),
            "tension": recorder_result.get("tension", "低"),
            "complexity": recorder_result.get("complexity", "简单")
        },
        is_valuable=recorder_result.get("is_valuable", False)
    )
    
    return response

# 创建新会话接口
@router.post("/new-session", response_model=NewSessionResponse)
async def create_new_session(
    session_data: dict,
    db: Session = Depends(get_db)
):
    """
    创建新会话
    """
    # 从JSON数据中获取user_id
    user_id = session_data.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="缺少用户ID"
        )
    
    # 检查用户是否存在
    user = db.query(UserDB).filter(UserDB.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # 生成会话ID和标题
    session_id = f"session_{uuid.uuid4().hex[:8]}"
    session_title = f"会话_{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    
    # 验证会话ID和标题是否成功创建
    if not session_id or not session_title:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="会话创建失败，无法生成会话ID或标题"
        )
    
    # 会话ID会在第一条消息发送时自动存储到dialogues表中
    # 这里不需要额外的会话表，会话信息通过dialogues表的session_id字段来区分
    
    # 构建响应
    response = NewSessionResponse(
        session_id=session_id,
        session_title=session_title
    )
    
    return response

# 结束会话接口
@router.post("/end-session")
async def end_session(
    session_data: dict,
    db: Session = Depends(get_db)
):
    """
    结束会话
    """
    # 从JSON数据中获取user_id和session_id
    user_id = session_data.get("user_id")
    session_id = session_data.get("session_id")
    
    if not user_id or not session_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="缺少用户ID或会话ID"
        )
    
    # 检查用户是否存在
    user = db.query(UserDB).filter(UserDB.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # 检查会话是否存在
    dialogues = db.query(DialogueDB).filter(
        DialogueDB.user_id == user_id,
        DialogueDB.session_id == session_id
    ).all()
    
    if not dialogues:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="会话不存在"
        )
    
    # 这里可以添加结束会话的逻辑，比如生成会话报告等
    
    return {"message": "会话已结束"}

# 获取用户会话列表接口
@router.post("/sessions", response_model=SessionList)
async def get_user_sessions(
    user_data: dict,
    db: Session = Depends(get_db)
):
    """
    获取用户会话列表
    """
    # 从JSON数据中获取user_id
    user_id = user_data.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="缺少用户ID"
        )
    
    # 检查用户是否存在
    user = db.query(UserDB).filter(UserDB.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # 查询用户的所有会话ID
    # 从DialogueDB中获取所有唯一的会话ID
    session_ids = db.query(DialogueDB.session_id).filter(
        DialogueDB.user_id == user_id
    ).distinct().all()
    
    # 构建会话列表
    sessions = []
    for (session_id,) in session_ids:
        # 获取每个会话的最后一条消息
        last_dialogue = db.query(DialogueDB).filter(
            DialogueDB.user_id == user_id,
            DialogueDB.session_id == session_id
        ).order_by(DialogueDB.created_at.desc()).first()
        
        # 构建会话信息
        session_info = SessionInfo(
            session_id=session_id,
            title=f"会话_{session_id[-8:]}",  # 简单使用会话ID的后8位作为标题
            last_message=last_dialogue.content if last_dialogue else "",
            created_at=last_dialogue.created_at if last_dialogue else datetime.now()
        )
        sessions.append(session_info)
    
    # 按创建时间降序排序
    sessions.sort(key=lambda x: x.created_at, reverse=True)
    
    # 构建响应
    response = SessionList(sessions=sessions)
    
    return response

# 获取会话对话记录接口
@router.post("/history", response_model=ChatHistoryResponse)
async def get_chat_history(
    history_data: dict,
    db: Session = Depends(get_db)
):
    """
    获取会话对话记录
    """
    # 从JSON数据中获取参数
    user_id = history_data.get("user_id")
    session_id = history_data.get("session_id")
    limit = history_data.get("limit", 50)
    
    if not user_id or not session_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="缺少用户ID或会话ID"
        )
    
    # 检查用户是否存在
    user = db.query(UserDB).filter(UserDB.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # 检查会话是否存在
    dialogues = db.query(DialogueDB).filter(
        DialogueDB.user_id == user_id,
        DialogueDB.session_id == session_id
    ).all()
    
    # 转换为响应模型
    dialogue_list = []
    for dialogue in dialogues:
        dialogue_item = Dialogue(
            id=dialogue.id,
            user_id=dialogue.user_id,
            session_id=dialogue.session_id,
            role=dialogue.role,
            content=dialogue.content,
            four_dim_intensity=dialogue.four_dim_intensity,
            four_dim_hedonic=dialogue.four_dim_hedonic,
            four_dim_tension=dialogue.four_dim_tension,
            four_dim_complexity=dialogue.four_dim_complexity,
            is_valuable=dialogue.is_valuable,
            created_at=dialogue.created_at
        )
        dialogue_list.append(dialogue_item)
    
    # 构建响应
    response = ChatHistoryResponse(dialogues=dialogue_list)
    
    return response
