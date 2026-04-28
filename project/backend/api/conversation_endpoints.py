"""
对话记录相关的API端点
"""
from fastapi import APIRouter, HTTPException, Query, Depends
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import uuid

from backend.core.database import DBConfig, ConversationDB, MessageDB
from backend.core.data_models import (
    Conversation,
    Message,
    ConversationCreate,
    ConversationUpdate,
    ConversationListResponse,
    ConversationDetailResponse
)

router = APIRouter(prefix="/api/conversations", tags=["conversations"])

# 依赖注入获取数据库会话
def get_db():
    return next(DBConfig.get_db())

@router.get("", response_model=List[ConversationListResponse])
async def get_conversations(
    page: int = Query(1, ge=1, description="页码"),
    limit: int = Query(10, ge=1, le=100, description="每页数量"),
    user_id: Optional[str] = Query(None, description="用户ID，用于权限验证"),
    db: Session = Depends(get_db)
):
    """
    获取对话列表
    - 支持分页
    - 可选用户ID过滤（权限验证）
    """
    try:
        # 构建查询
        query = db.query(ConversationDB)
        
        # 如果提供了user_id，添加过滤条件
        if user_id:
            query = query.filter(ConversationDB.user_id == user_id)
        
        # 计算偏移量
        offset = (page - 1) * limit
        
        # 执行查询
        conversations = query.order_by(ConversationDB.created_at.desc()).offset(offset).limit(limit).all()
        
        # 转换为响应模型
        response = []
        for conv in conversations:
            response.append(ConversationListResponse(
                id=conv.id,
                title=conv.title,
                timestamp=conv.timestamp,
                emotion=conv.emotion,
                cognition_type=conv.cognition_type,
                current_phase=conv.current_phase,
                created_at=conv.created_at
            ))
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取对话列表失败: {str(e)}")

@router.get("/{conversation_id}", response_model=ConversationDetailResponse)
async def get_conversation_detail(
    conversation_id: str,
    user_id: Optional[str] = Query(None, description="用户ID，用于权限验证"),
    db: Session = Depends(get_db)
):
    """
    获取单个对话详情
    - 包含完整对话信息和所有消息
    - 支持用户权限验证
    """
    try:
        # 查询对话
        conversation = db.query(ConversationDB).filter(ConversationDB.id == conversation_id).first()
        
        if not conversation:
            raise HTTPException(status_code=404, detail="对话记录不存在")
        
        # 权限验证
        if user_id and conversation.user_id != user_id:
            raise HTTPException(status_code=403, detail="无权访问此对话记录")
        
        # 查询消息
        messages = db.query(MessageDB).filter(MessageDB.conversation_id == conversation_id).order_by(MessageDB.timestamp).all()
        
        # 转换为响应模型
        conversation_response = Conversation(
            id=conversation.id,
            user_id=conversation.user_id,
            title=conversation.title,
            timestamp=conversation.timestamp,
            emotion=conversation.emotion,
            cognition_type=conversation.cognition_type,
            current_phase=conversation.current_phase,
            active_step=conversation.active_step,
            current_role=conversation.current_role,
            created_at=conversation.created_at,
            updated_at=conversation.updated_at
        )
        
        messages_response = []
        for msg in messages:
            messages_response.append(Message(
                id=msg.id,
                conversation_id=msg.conversation_id,
                type=msg.type,
                role=msg.role,
                content=msg.content,
                timestamp=msg.timestamp,
                created_at=msg.created_at
            ))
        
        return ConversationDetailResponse(
            conversation=conversation_response,
            messages=messages_response
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取对话详情失败: {str(e)}")

@router.post("", response_model=Conversation)
async def create_conversation(
    conversation_data: ConversationCreate,
    user_id: Optional[str] = Query(None, description="用户ID，用于权限验证"),
    db: Session = Depends(get_db)
):
    """
    创建新对话记录
    - 自动生成对话ID和时间戳
    - 支持用户权限验证
    """
    try:
        # 生成对话ID
        conversation_id = f"conv_{uuid.uuid4().hex[:8]}"
        
        # 创建对话记录
        db_conversation = ConversationDB(
            id=conversation_id,
            user_id=user_id or f"user_{uuid.uuid4().hex[:6]}",  # 如果没有提供user_id，生成一个临时的
            title=conversation_data.title,
            timestamp=datetime.utcnow(),
            emotion=conversation_data.emotion,
            cognition_type=conversation_data.cognition_type,
            current_phase=conversation_data.current_phase,
            active_step=conversation_data.active_step,
            current_role=conversation_data.current_role,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # 保存到数据库
        db.add(db_conversation)
        db.commit()
        db.refresh(db_conversation)
        
        # 转换为响应模型
        return Conversation(
            id=db_conversation.id,
            user_id=db_conversation.user_id,
            title=db_conversation.title,
            timestamp=db_conversation.timestamp,
            emotion=db_conversation.emotion,
            cognition_type=db_conversation.cognition_type,
            current_phase=db_conversation.current_phase,
            active_step=db_conversation.active_step,
            current_role=db_conversation.current_role,
            created_at=db_conversation.created_at,
            updated_at=db_conversation.updated_at
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"创建对话记录失败: {str(e)}")

@router.put("/{conversation_id}", response_model=Conversation)
async def update_conversation(
    conversation_id: str,
    conversation_data: ConversationUpdate,
    user_id: Optional[str] = Query(None, description="用户ID，用于权限验证"),
    db: Session = Depends(get_db)
):
    """
    更新对话记录
    - 只更新提供的字段
    - 支持用户权限验证
    """
    try:
        # 查询对话
        db_conversation = db.query(ConversationDB).filter(ConversationDB.id == conversation_id).first()
        
        if not db_conversation:
            raise HTTPException(status_code=404, detail="对话记录不存在")
        
        # 权限验证
        if user_id and db_conversation.user_id != user_id:
            raise HTTPException(status_code=403, detail="无权修改此对话记录")
        
        # 更新字段
        update_data = conversation_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_conversation, field, value)
        
        # 更新时间戳
        db_conversation.updated_at = datetime.utcnow()
        
        # 保存到数据库
        db.commit()
        db.refresh(db_conversation)
        
        # 转换为响应模型
        return Conversation(
            id=db_conversation.id,
            user_id=db_conversation.user_id,
            title=db_conversation.title,
            timestamp=db_conversation.timestamp,
            emotion=db_conversation.emotion,
            cognition_type=db_conversation.cognition_type,
            current_phase=db_conversation.current_phase,
            active_step=db_conversation.active_step,
            current_role=db_conversation.current_role,
            created_at=db_conversation.created_at,
            updated_at=db_conversation.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"更新对话记录失败: {str(e)}")

@router.delete("/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    user_id: Optional[str] = Query(None, description="用户ID，用于权限验证"),
    db: Session = Depends(get_db)
):
    """
    删除对话记录
    - 级联删除相关的消息
    - 支持用户权限验证
    """
    try:
        # 查询对话
        db_conversation = db.query(ConversationDB).filter(ConversationDB.id == conversation_id).first()
        
        if not db_conversation:
            raise HTTPException(status_code=404, detail="对话记录不存在")
        
        # 权限验证
        if user_id and db_conversation.user_id != user_id:
            raise HTTPException(status_code=403, detail="无权删除此对话记录")
        
        # 删除相关的消息
        db.query(MessageDB).filter(MessageDB.conversation_id == conversation_id).delete()
        
        # 删除对话
        db.delete(db_conversation)
        db.commit()
        
        return {"message": "对话记录删除成功"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"删除对话记录失败: {str(e)}")
