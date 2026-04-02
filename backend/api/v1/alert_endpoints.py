"""
预警相关的API端点 - 符合API文档规范
"""
from fastapi import APIRouter, HTTPException, Depends, status, Query, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from backend.core.database import DBConfig, UserDB, AlertDB, SessionLocal
from backend.core.data_models import (
    AlertType, AlertLevel,
    AlertListRequest, AlertListResponse,
    AlertAcknowledgeRequest, AlertAcknowledgeResponse,
    AlertBatchAcknowledgeRequest, AlertBatchAcknowledgeResponse,
    AlertStatsRequest, AlertStatsResponse,
    WebSocketMessage
)
from backend.services.alert_service import AlertService
from backend.services.alert_websocket import alert_ws_manager

router = APIRouter(prefix="/api", tags=["alert"])

# 依赖注入获取数据库会话
def get_db():
    """获取数据库会话的依赖函数"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ==================== RESTful API 接口 ====================

@router.get("/alerts", response_model=AlertListResponse)
async def get_alert_list(
    user_id: str = Query(..., description="用户ID"),
    type: Optional[str] = Query(None, description="预警类型筛选：questionnaire/emotion/conversation"),
    level: Optional[str] = Query(None, description="预警等级筛选：info/warning/danger"),
    status: Optional[str] = Query(None, description="状态筛选：acknowledged/unacknowledged"),
    start_date: Optional[str] = Query(None, description="开始日期，格式：YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="结束日期，格式：YYYY-MM-DD"),
    page: int = Query(1, description="页码，默认1"),
    page_size: int = Query(20, description="每页数量，默认20"),
    db: Session = Depends(get_db)
):
    """
    获取预警列表
    
    支持筛选、分页等功能
    """
    # 检查用户是否存在
    user = db.query(UserDB).filter(UserDB.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # 构建请求对象
    request = AlertListRequest(
        user_id=user_id,
        type=AlertType(type) if type else None,
        level=AlertLevel(level) if level else None,
        status=status,
        start_date=start_date,
        end_date=end_date,
        page=page,
        page_size=page_size
    )
    
    # 调用服务层
    alert_service = AlertService(db)
    result = alert_service.get_alert_list(request)
    
    return AlertListResponse(data=result)


@router.post("/alerts/{alert_id}/acknowledge", response_model=AlertAcknowledgeResponse)
async def acknowledge_alert(
    alert_id: str,
    request: AlertAcknowledgeRequest,
    db: Session = Depends(get_db)
):
    """
    确认预警
    
    将指定预警标记为已确认状态，并推送给用户的其他设备
    """
    # 检查用户是否存在
    user = db.query(UserDB).filter(UserDB.id == request.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # 调用服务层
    alert_service = AlertService(db)
    alert = alert_service.acknowledge_alert(alert_id, request.user_id, request.notes)
    
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="预警不存在"
        )
    
    # 推送更新给用户的所有设备（包括确认状态变更）
    update_data = {
        "is_acknowledged": alert.is_acknowledged,
        "acknowledged_at": alert.acknowledged_at.isoformat() if alert.acknowledged_at else None,
        "acknowledged_by": alert.acknowledged_by
    }
    await alert_ws_manager.push_alert_update(alert.user_id, alert_id, update_data)
    
    return AlertAcknowledgeResponse(data=update_data)


@router.post("/alerts/batch/acknowledge", response_model=AlertBatchAcknowledgeResponse)
async def batch_acknowledge_alerts(
    request: AlertBatchAcknowledgeRequest,
    db: Session = Depends(get_db)
):
    """
    批量确认预警
    
    同时确认多个预警，并推送给用户的其他设备
    """
    # 检查用户是否存在
    user = db.query(UserDB).filter(UserDB.id == request.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # 调用服务层
    alert_service = AlertService(db)
    result = alert_service.batch_acknowledge_alerts(request.alert_ids, request.user_id)
    
    # 推送批量更新
    for alert_id in request.alert_ids:
        if alert_id not in result.get("failed_ids", []):
            update_data = {
                "is_acknowledged": True,
                "acknowledged_by": request.user_id
            }
            await alert_ws_manager.push_alert_update(request.user_id, alert_id, update_data)
    
    return AlertBatchAcknowledgeResponse(data=result)


@router.get("/alerts/stats", response_model=AlertStatsResponse)
async def get_alert_stats(
    user_id: str = Query(..., description="用户ID"),
    start_date: Optional[str] = Query(None, description="开始日期"),
    end_date: Optional[str] = Query(None, description="结束日期"),
    db: Session = Depends(get_db)
):
    """
    获取预警统计
    
    返回预警的统计数据，包括总数、按类型/等级分布等
    """
    # 检查用户是否存在
    user = db.query(UserDB).filter(UserDB.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # 构建请求对象
    request = AlertStatsRequest(
        user_id=user_id,
        start_date=start_date,
        end_date=end_date
    )
    
    # 调用服务层
    alert_service = AlertService(db)
    result = alert_service.get_alert_stats(request)
    
    return AlertStatsResponse(data=result)


# ==================== WebSocket 实时推送 ====================

@router.websocket("/ws/alerts/{user_id}")
async def alert_websocket(websocket: WebSocket, user_id: str):
    """
    WebSocket实时推送接口
    
    连接地址: ws://localhost:8000/api/ws/alerts/{user_id}
    
    功能:
    1. 建立WebSocket连接时需要携带用户认证token（通过query参数）
    2. 连接成功后，服务端会推送该用户的新预警消息
    3. 支持的消息类型:
       - new_alert: 新增预警
       - update_alert: 预警更新（如确认状态变更）
       - delete_alert: 预警删除
       - batch_update: 批量更新（全量刷新）
       - connected: 连接成功
       - ping: 心跳
    4. 断线后需要客户端自动重连
    
    客户端响应:
    - pong: 心跳响应
    """
    # 获取token（从query参数）
    token = websocket.query_params.get("token")
    
    # 这里应该验证token，简化处理暂时跳过详细验证
    # 实际项目中应该调用认证服务验证token
    
    # 建立连接
    if not await alert_ws_manager.connect(user_id, websocket):
        await websocket.close(code=1008)
        return
    
    try:
        # 保持连接并处理客户端消息
        while True:
            # 接收客户端消息
            data = await websocket.receive_json()
            
            # 处理心跳响应
            if data.get("type") == "pong":
                # 客户端响应了心跳，可以记录最后一次pong时间
                pass
            # 可以在这里处理其他客户端消息类型
            
    except WebSocketDisconnect:
        # 客户端断开连接
        await alert_ws_manager.disconnect(user_id, websocket)
    except Exception as e:
        # 其他异常
        print(f"WebSocket异常: {e}")
        await alert_ws_manager.disconnect(user_id, websocket)


# ==================== 内部API（供其他模块调用） ====================

@router.post("/alerts/internal/check-questionnaire")
async def internal_check_questionnaire_alert(
    user_id: str,
    template_code: str,
    score: int,
    result_level: str,
    record_id: str,
    db: Session = Depends(get_db)
):
    """
    内部API：检查问卷预警
    
    供问卷模块调用，当用户提交问卷后检查是否需要生成预警
    """
    alert_service = AlertService(db)
    alert = alert_service.check_questionnaire_alert(
        user_id, template_code, score, result_level, record_id
    )
    
    if alert:
        # 转换为字典
        alert_data = {
            "id": alert.id,
            "type": alert.type,
            "level": alert.level,
            "title": alert.title,
            "message": alert.message,
            "source_data": alert.source_data,
            "is_acknowledged": alert.is_acknowledged,
            "created_at": alert.created_at.isoformat() if alert.created_at else None
        }
        
        # 通过WebSocket推送（使用新的管理器）
        await alert_ws_manager.push_new_alert(user_id, alert_data)
        
        return {"code": 200, "message": "预警已生成", "data": alert_data}
    
    return {"code": 200, "message": "无需生成预警", "data": None}


@router.post("/alerts/internal/check-emotion")
async def internal_check_emotion_alert(
    user_id: str,
    emotion_type: str,
    intensity: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    内部API：检查情绪预警
    
    供情绪记录模块调用，当用户记录情绪后检查是否需要生成预警
    """
    alert_service = AlertService(db)
    alert = alert_service.check_emotion_alert(user_id, emotion_type, intensity)
    
    if alert:
        alert_data = {
            "id": alert.id,
            "type": alert.type,
            "level": alert.level,
            "title": alert.title,
            "message": alert.message,
            "source_data": alert.source_data,
            "is_acknowledged": alert.is_acknowledged,
            "created_at": alert.created_at.isoformat() if alert.created_at else None
        }
        
        await alert_ws_manager.push_new_alert(user_id, alert_data)
        
        return {"code": 200, "message": "预警已生成", "data": alert_data}
    
    return {"code": 200, "message": "无需生成预警", "data": None}


@router.post("/alerts/internal/check-conversation")
async def internal_check_conversation_alert(
    user_id: str,
    session_id: str,
    content: str,
    emotion_intensity: Optional[float] = None,
    db: Session = Depends(get_db)
):
    """
    内部API：检查对话预警
    
    供对话模块调用，实时分析对话内容
    """
    alert_service = AlertService(db)
    alert = alert_service.check_conversation_alert(
        user_id, session_id, content, emotion_intensity
    )
    
    if alert:
        alert_data = {
            "id": alert.id,
            "type": alert.type,
            "level": alert.level,
            "title": alert.title,
            "message": alert.message,
            "source_data": alert.source_data,
            "is_acknowledged": alert.is_acknowledged,
            "created_at": alert.created_at.isoformat() if alert.created_at else None
        }
        
        await alert_ws_manager.push_new_alert(user_id, alert_data)
        
        return {"code": 200, "message": "预警已生成", "data": alert_data}
    
    return {"code": 200, "message": "无需生成预警", "data": None}


# ==================== 定时任务相关API ====================

@router.post("/alerts/internal/daily-check")
async def daily_emotion_check(
    db: Session = Depends(get_db)
):
    """
    内部API：每日情绪检查
    
    供定时任务调用，检查所有用户的连续负面情绪
    """
    from backend.core.database import UserDB
    
    alert_service = AlertService(db)
    
    # 获取所有活跃用户
    users = db.query(UserDB).filter(UserDB.is_active == True).all()
    
    generated_alerts = []
    
    for user in users:
        # 检查连续负面情绪
        consecutive_days = alert_service._check_consecutive_negative_emotions(user.id)
        
        if consecutive_days >= 3:
            # 检查是否已存在未确认的连续情绪预警
            existing_alerts = alert_service.get_unacknowledged_alerts(user.id)
            has_existing = any(
                a.type == 'emotion' and '连续负面情绪' in a.title 
                for a in existing_alerts
            )
            
            if not has_existing:
                # 创建预警
                from backend.core.data_models import AlertCreateRequest, AlertType, AlertLevel
                
                if consecutive_days >= 7:
                    alert = alert_service._create_consecutive_emotion_alert(
                        user.id, consecutive_days, AlertLevel.DANGER
                    )
                else:
                    alert = alert_service._create_consecutive_emotion_alert(
                        user.id, consecutive_days, AlertLevel.WARNING
                    )
                
                if alert:
                    alert_data = {
                        "id": alert.id,
                        "type": alert.type,
                        "level": alert.level,
                        "title": alert.title,
                        "message": alert.message,
                        "source_data": alert.source_data,
                        "is_acknowledged": alert.is_acknowledged,
                        "created_at": alert.created_at.isoformat() if alert.created_at else None
                    }
                    
                    # 推送预警
                    await alert_ws_manager.push_new_alert(user.id, alert_data)
                    generated_alerts.append(alert_data)
    
    return {
        "code": 200,
        "message": "每日检查完成",
        "data": {
            "checked_users": len(users),
            "generated_alerts": len(generated_alerts),
            "alerts": generated_alerts
        }
    }
