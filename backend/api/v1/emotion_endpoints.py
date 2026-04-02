"""
情绪记录相关的API端点
"""
from fastapi import APIRouter, HTTPException, Depends, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from collections import defaultdict

from backend.core.database import (
    DBConfig, UserDB, EmotionRecordDB, EmotionRemindSettingDB, SessionLocal
)
from backend.core.data_models import (
    EmotionRecordCreate, EmotionRecordResponse, EmotionRecordListResponse,
    EmotionCalendarDay, EmotionCalendarResponse, EmotionDistributionItem,
    EmotionTrendItem, EmotionStatisticsResponse, EmotionRemindSettings,
    EmotionRemindSettingsResponse, EmotionNextRemindResponse
)
from backend.services.alert_service import AlertService
from backend.services.alert_websocket import alert_ws_manager

router = APIRouter(prefix="/api/emotions", tags=["emotions"])

# 情绪类型定义
EMOTION_TAGS = [
    {"type": "happy", "icon": "😊", "name": "开心", "color": "#FFD93D", "score": 8},
    {"type": "excited", "icon": "🤩", "name": "兴奋", "color": "#FF6B6B", "score": 9},
    {"type": "calm", "icon": "😌", "name": "平静", "color": "#6BCB77", "score": 6},
    {"type": "tired", "icon": "😴", "name": "疲惫", "color": "#95A5A6", "score": 4},
    {"type": "sad", "icon": "😢", "name": "难过", "color": "#74B9FF", "score": 2},
    {"type": "anxious", "icon": "😰", "name": "焦虑", "color": "#E17055", "score": 2},
    {"type": "angry", "icon": "😠", "name": "愤怒", "color": "#D63031", "score": 1},
    {"type": "worried", "icon": "😟", "name": "担忧", "color": "#FD79A8", "score": 3},
    {"type": "grateful", "icon": "🥰", "name": "感恩", "color": "#FDCB6E", "score": 8},
    {"type": "confused", "icon": "😕", "name": "困惑", "color": "#A29BFE", "score": 4},
    {"type": "peaceful", "icon": "🧘", "name": "安宁", "color": "#00B894", "score": 7},
    {"type": "lonely", "icon": "🥺", "name": "孤独", "color": "#636E72", "score": 3}
]

# 情绪分值映射
EMOTION_SCORES = {
    "excited": 9,
    "happy": 8,
    "grateful": 8,
    "peaceful": 7,
    "calm": 6,
    "tired": 4,
    "confused": 4,
    "worried": 3,
    "lonely": 3,
    "sad": 2,
    "anxious": 2,
    "angry": 1
}

# 依赖注入获取数据库会话
def get_db():
    """获取数据库会话的依赖函数"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_emotion_info(emotion_type: str) -> Dict[str, Any]:
    """获取情绪类型信息"""
    for emotion in EMOTION_TAGS:
        if emotion["type"] == emotion_type:
            return emotion
    return EMOTION_TAGS[0]  # 默认返回开心


def init_user_remind_settings(user_id: str, db: Session):
    """初始化用户提醒设置"""
    settings = db.query(EmotionRemindSettingDB).filter(
        EmotionRemindSettingDB.user_id == user_id
    ).first()
    
    if not settings:
        settings = EmotionRemindSettingDB(
            user_id=user_id,
            remind_enabled=True,
            remind_times=2,
            remind_interval=360,  # 6小时
            next_remind_at=datetime.utcnow() + timedelta(minutes=360)
        )
        db.add(settings)
        db.commit()
    
    return settings


@router.post("/record", response_model=EmotionRecordListResponse)
async def record_emotion(
    request: EmotionRecordCreate,
    db: Session = Depends(get_db)
):
    """
    记录情绪
    
    创建一条新的情绪记录
    """
    # 从请求体获取用户ID
    user_id = request.user_id
    
    # 检查用户是否存在
    user = db.query(UserDB).filter(UserDB.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # 获取情绪信息
    emotion_info = get_emotion_info(request.emotion_type)
    
    # 创建情绪记录
    record = EmotionRecordDB(
        user_id=user_id,
        emotion_type=request.emotion_type,
        emotion_icon=emotion_info["icon"],
        emotion_name=emotion_info["name"],
        emotion_color=emotion_info["color"],
        signature=request.signature,
        record_date=request.record_date,
        record_time=request.record_time
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    
    # 更新提醒设置中的上次记录时间
    settings = db.query(EmotionRemindSettingDB).filter(
        EmotionRemindSettingDB.user_id == user_id
    ).first()
    
    if settings:
        settings.last_record_at = datetime.utcnow()
        # 更新下次提醒时间
        if settings.remind_enabled:
            settings.next_remind_at = datetime.utcnow() + timedelta(minutes=settings.remind_interval)
        db.commit()
    else:
        # 初始化提醒设置
        init_user_remind_settings(user_id, db)
    
    # ==================== 预警检查 ====================
    # 在情绪记录后检查是否需要生成预警
    alert_service = AlertService(db)
    
    # 获取情绪强度（从EMOTION_SCORES映射）
    emotion_intensity = EMOTION_SCORES.get(request.emotion_type, 5)
    
    alert = alert_service.check_emotion_alert(
        user_id=user_id,
        emotion_type=request.emotion_type,
        intensity=emotion_intensity
    )
    
    # 如果有预警生成，通过WebSocket推送
    alert_data = None
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
    # ==================== 预警检查结束 ====================
    
    response_data = {
        "id": record.id,
        "emotion_type": record.emotion_type,
        "emotion_icon": record.emotion_icon,
        "emotion_name": record.emotion_name,
        "emotion_color": record.emotion_color,
        "signature": record.signature,
        "record_date": record.record_date,
        "record_time": record.record_time,
        "created_at": record.created_at.isoformat() if record.created_at else None
    }
    
    # 如果有预警，添加到响应中
    if alert_data:
        response_data["alert_generated"] = alert_data
    
    return EmotionRecordListResponse(
        code=200,
        message="记录成功",
        data=response_data
    )


@router.get("/history", response_model=EmotionRecordListResponse)
async def get_emotion_history(
    user_id: str = Query(..., description="用户ID"),
    limit: int = Query(50, description="返回数量限制"),
    offset: int = Query(0, description="分页偏移量"),
    start_date: Optional[str] = Query(None, description="开始日期 YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="结束日期 YYYY-MM-DD"),
    db: Session = Depends(get_db)
):
    """
    获取情绪历史记录
    
    返回用户的情绪记录列表，支持分页和日期筛选
    """
    query = db.query(EmotionRecordDB).filter(
        EmotionRecordDB.user_id == user_id
    )
    
    # 日期筛选
    if start_date:
        query = query.filter(EmotionRecordDB.record_date >= start_date)
    if end_date:
        query = query.filter(EmotionRecordDB.record_date <= end_date)
    
    # 获取总数
    total = query.count()
    
    # 分页查询
    records = query.order_by(
        EmotionRecordDB.created_at.desc()
    ).offset(offset).limit(limit).all()
    
    record_list = []
    for record in records:
        record_list.append({
            "id": record.id,
            "emotion_type": record.emotion_type,
            "emotion_icon": record.emotion_icon,
            "emotion_name": record.emotion_name,
            "emotion_color": record.emotion_color,
            "signature": record.signature,
            "record_date": record.record_date,
            "record_time": record.record_time,
            "created_at": record.created_at.isoformat() if record.created_at else None
        })
    
    return EmotionRecordListResponse(
        code=200,
        message="success",
        data={
            "total": total,
            "records": record_list
        }
    )


@router.get("/calendar", response_model=EmotionCalendarResponse)
async def get_emotion_calendar(
    user_id: str = Query(..., description="用户ID"),
    year: int = Query(..., description="年份"),
    month: int = Query(..., description="月份 1-12"),
    db: Session = Depends(get_db)
):
    """
    获取情绪日历数据
    
    返回指定月份的情绪记录日历视图
    """
    from calendar import monthrange
    
    # 获取该月的天数
    _, days_in_month = monthrange(year, month)
    
    # 构建日期范围
    start_date = f"{year:04d}-{month:02d}-01"
    end_date = f"{year:04d}-{month:02d}-{days_in_month:02d}"
    
    # 查询该月的记录
    records = db.query(EmotionRecordDB).filter(
        EmotionRecordDB.user_id == user_id,
        EmotionRecordDB.record_date >= start_date,
        EmotionRecordDB.record_date <= end_date
    ).all()
    
    # 按日期分组，取每天的最新记录
    day_records = {}
    for record in records:
        date = record.record_date
        if date not in day_records or record.created_at > day_records[date].created_at:
            day_records[date] = record
    
    # 构建日历数据
    days = []
    for day in range(1, days_in_month + 1):
        date_str = f"{year:04d}-{month:02d}-{day:02d}"
        record = day_records.get(date_str)
        
        if record:
            days.append({
                "date": date_str,
                "day": day,
                "has_record": True,
                "record": {
                    "id": record.id,
                    "emotion_type": record.emotion_type,
                    "emotion_icon": record.emotion_icon,
                    "emotion_color": record.emotion_color
                }
            })
        else:
            days.append({
                "date": date_str,
                "day": day,
                "has_record": False,
                "record": None
            })
    
    return EmotionCalendarResponse(
        code=200,
        message="success",
        data={
            "year": year,
            "month": month,
            "days": days
        }
    )


@router.get("/statistics", response_model=EmotionStatisticsResponse)
async def get_emotion_statistics(
    user_id: str = Query(..., description="用户ID"),
    days: int = Query(30, description="统计天数，默认30，可选7/30/90"),
    db: Session = Depends(get_db)
):
    """
    获取情绪统计数据
    
    返回情绪分布统计和趋势数据
    """
    # 计算日期范围
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    start_date_str = start_date.strftime("%Y-%m-%d")
    end_date_str = end_date.strftime("%Y-%m-%d")
    
    # 查询记录
    records = db.query(EmotionRecordDB).filter(
        EmotionRecordDB.user_id == user_id,
        EmotionRecordDB.record_date >= start_date_str,
        EmotionRecordDB.record_date <= end_date_str
    ).all()
    
    total_records = len(records)
    daily_average = round(total_records / days, 2) if days > 0 else 0
    
    # 情绪分布统计
    emotion_counts = defaultdict(int)
    for record in records:
        emotion_counts[record.emotion_type] += 1
    
    distribution = []
    for emotion in EMOTION_TAGS:
        count = emotion_counts.get(emotion["type"], 0)
        percent = round(count / total_records * 100, 1) if total_records > 0 else 0
        distribution.append({
            "type": emotion["type"],
            "name": emotion["name"],
            "color": emotion["color"],
            "count": count,
            "percent": percent
        })
    
    # 按数量排序
    distribution.sort(key=lambda x: x["count"], reverse=True)
    
    # 趋势数据（按日期聚合，取每天的最新记录）
    day_records = {}
    for record in records:
        date = record.record_date
        if date not in day_records or record.created_at > day_records[date].created_at:
            day_records[date] = record
    
    trend = []
    for date_str, record in sorted(day_records.items()):
        trend.append({
            "date": date_str,
            "emotion_type": record.emotion_type,
            "emotion_score": EMOTION_SCORES.get(record.emotion_type, 5),
            "has_record": True
        })
    
    return EmotionStatisticsResponse(
        code=200,
        message="success",
        data={
            "period": {
                "days": days,
                "start_date": start_date_str,
                "end_date": end_date_str
            },
            "total_records": total_records,
            "daily_average": daily_average,
            "distribution": distribution,
            "trend": trend
        }
    )


@router.get("/next-remind", response_model=EmotionNextRemindResponse)
async def get_next_remind(
    user_id: str = Query(..., description="用户ID"),
    db: Session = Depends(get_db)
):
    """
    检查下次提醒
    
    返回是否需要提醒以及下次提醒时间
    """
    settings = db.query(EmotionRemindSettingDB).filter(
        EmotionRemindSettingDB.user_id == user_id
    ).first()
    
    if not settings:
        settings = init_user_remind_settings(user_id, db)
    
    now = datetime.utcnow()
    need_remind = False
    reason = ""
    
    if settings.remind_enabled:
        # 检查是否到了提醒时间
        if settings.next_remind_at and now >= settings.next_remind_at:
            need_remind = True
            reason = "距离上次记录已超过设定时间"
        
        # 检查是否超过6小时未记录
        if settings.last_record_at:
            hours_since_last = (now - settings.last_record_at).total_seconds() / 3600
            if hours_since_last >= 6:
                need_remind = True
                reason = f"距离上次记录已超过{int(hours_since_last)}小时"
    
    # 获取上次记录
    last_record = db.query(EmotionRecordDB).filter(
        EmotionRecordDB.user_id == user_id
    ).order_by(EmotionRecordDB.created_at.desc()).first()
    
    last_record_data = None
    if last_record:
        last_record_data = {
            "id": last_record.id,
            "emotion_type": last_record.emotion_type,
            "emotion_icon": last_record.emotion_icon,
            "record_date": last_record.record_date,
            "record_time": last_record.record_time
        }
    
    return EmotionNextRemindResponse(
        code=200,
        message="success",
        data={
            "need_remind": need_remind,
            "reason": reason if need_remind else "",
            "next_remind_at": settings.next_remind_at.isoformat() if settings.next_remind_at else None,
            "last_record": last_record_data
        }
    )


@router.post("/skip-remind", response_model=EmotionNextRemindResponse)
async def skip_remind(
    user_id: str = Query(..., description="用户ID"),
    db: Session = Depends(get_db)
):
    """
    跳过本次提醒
    
    推迟下次提醒时间
    """
    settings = db.query(EmotionRemindSettingDB).filter(
        EmotionRemindSettingDB.user_id == user_id
    ).first()
    
    if not settings:
        settings = init_user_remind_settings(user_id, db)
    
    # 推迟到6小时后
    settings.next_remind_at = datetime.utcnow() + timedelta(minutes=360)
    db.commit()
    
    return EmotionNextRemindResponse(
        code=200,
        message="已跳过本次提醒",
        data={
            "next_remind_at": settings.next_remind_at.isoformat()
        }
    )


@router.get("/remind-settings", response_model=EmotionRemindSettingsResponse)
async def get_remind_settings(
    user_id: str = Query(..., description="用户ID"),
    db: Session = Depends(get_db)
):
    """
    获取提醒设置
    """
    settings = db.query(EmotionRemindSettingDB).filter(
        EmotionRemindSettingDB.user_id == user_id
    ).first()
    
    if not settings:
        settings = init_user_remind_settings(user_id, db)
    
    return EmotionRemindSettingsResponse(
        code=200,
        message="success",
        data={
            "remind_enabled": settings.remind_enabled,
            "remind_times": settings.remind_times,
            "remind_interval": settings.remind_interval,
            "last_remind_at": settings.last_remind_at.isoformat() if settings.last_remind_at else None,
            "next_remind_at": settings.next_remind_at.isoformat() if settings.next_remind_at else None
        }
    )


@router.put("/remind-settings", response_model=EmotionRemindSettingsResponse)
async def update_remind_settings(
    settings_data: EmotionRemindSettings,
    user_id: str = Query(..., description="用户ID"),
    db: Session = Depends(get_db)
):
    """
    更新提醒设置
    """
    settings = db.query(EmotionRemindSettingDB).filter(
        EmotionRemindSettingDB.user_id == user_id
    ).first()
    
    if not settings:
        settings = init_user_remind_settings(user_id, db)
    
    # 更新设置
    settings.remind_enabled = settings_data.remind_enabled
    settings.remind_times = settings_data.remind_times
    settings.remind_interval = settings_data.remind_interval
    
    # 如果启用了提醒，更新下次提醒时间
    if settings.remind_enabled:
        settings.next_remind_at = datetime.utcnow() + timedelta(minutes=settings.remind_interval)
    
    db.commit()
    
    return EmotionRemindSettingsResponse(
        code=200,
        message="设置已更新",
        data={
            "remind_enabled": settings.remind_enabled,
            "remind_times": settings.remind_times,
            "remind_interval": settings.remind_interval,
            "last_remind_at": settings.last_remind_at.isoformat() if settings.last_remind_at else None,
            "next_remind_at": settings.next_remind_at.isoformat() if settings.next_remind_at else None
        }
    )


@router.get("/types", response_model=Dict[str, Any])
async def get_emotion_types():
    """
    获取所有情绪类型定义
    
    返回支持的情绪类型列表
    """
    return {
        "code": 200,
        "message": "success",
        "data": {
            "emotions": EMOTION_TAGS
        }
    }
