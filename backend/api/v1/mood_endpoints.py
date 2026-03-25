"""
情绪日记相关的API端点
"""
from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from datetime import date, datetime
from typing import List, Optional

from backend.core.database import DBConfig, UserDB, MoodEntryDB, SessionLocal
from backend.core.data_models import (
    MoodEntry,
    MoodEntryCreate,
    MoodCalendarResponse,
    MoodTrendResponse,
    MoodCalendarDay
)

router = APIRouter(prefix="/api/v1/mood", tags=["mood"])

# 依赖注入获取数据库会话
def get_db():
    """获取数据库会话的依赖函数"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 添加/更新情绪记录接口
@router.post("/entry")
async def add_or_update_mood_entry(
    entry: MoodEntryCreate,
    db: Session = Depends(get_db)
):
    """
    添加/更新情绪记录
    """
    # 检查用户是否存在
    user = db.query(UserDB).filter(UserDB.id == entry.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # 检查是否已存在该日期的记录
    existing_entry = db.query(MoodEntryDB).filter(
        MoodEntryDB.user_id == entry.user_id,
        MoodEntryDB.entry_date == entry.date
    ).first()
    
    if existing_entry:
        # 更新现有记录
        existing_entry.mood_label = entry.mood_label
        existing_entry.signature_text = entry.signature_text
        if entry.four_dim:
            existing_entry.four_dim_intensity = entry.four_dim.get("intensity")
            existing_entry.four_dim_hedonic = entry.four_dim.get("hedonic")
            existing_entry.four_dim_tension = entry.four_dim.get("tension")
            existing_entry.four_dim_complexity = entry.four_dim.get("complexity")
        db.commit()
        db.refresh(existing_entry)
    else:
        # 创建新记录
        new_entry = MoodEntryDB(
            user_id=entry.user_id,
            entry_date=entry.date,
            mood_label=entry.mood_label,
            signature_text=entry.signature_text,
            four_dim_intensity=entry.four_dim.get("intensity") if entry.four_dim else None,
            four_dim_hedonic=entry.four_dim.get("hedonic") if entry.four_dim else None,
            four_dim_tension=entry.four_dim.get("tension") if entry.four_dim else None,
            four_dim_complexity=entry.four_dim.get("complexity") if entry.four_dim else None
        )
        db.add(new_entry)
        db.commit()
        db.refresh(new_entry)
    
    return {"message": "情绪记录保存成功"}

# 获取某月情绪记录（日历数据）接口
@router.get("/calendar", response_model=MoodCalendarResponse)
async def get_mood_calendar(
    user_id: str,
    year: int,
    month: int,
    db: Session = Depends(get_db)
):
    """
    获取某月情绪记录（日历数据）
    """
    # 检查用户是否存在
    user = db.query(UserDB).filter(UserDB.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # 构建月份的开始和结束日期
    start_date = date(year, month, 1)
    if month == 12:
        end_date = date(year + 1, 1, 1)
    else:
        end_date = date(year, month + 1, 1)
    
    # 查询该月的情绪记录
    entries = db.query(MoodEntryDB).filter(
        MoodEntryDB.user_id == user_id,
        MoodEntryDB.entry_date >= start_date,
        MoodEntryDB.entry_date < end_date
    ).all()
    
    # 构建日历数据
    days = []
    for entry in entries:
        day = MoodCalendarDay(
            date=entry.entry_date.isoformat(),
            mood_label=entry.mood_label,
            signature=entry.signature_text
        )
        days.append(day)
    
    # 构建响应
    response = MoodCalendarResponse(days=days)
    
    return response

# 获取情绪趋势（折线图数据）接口
@router.get("/trend", response_model=MoodTrendResponse)
async def get_mood_trend(
    user_id: str,
    start_date: date,
    end_date: date,
    db: Session = Depends(get_db)
):
    """
    获取情绪趋势（折线图数据）
    """
    # 检查用户是否存在
    user = db.query(UserDB).filter(UserDB.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # 查询时间范围内的情绪记录
    entries = db.query(MoodEntryDB).filter(
        MoodEntryDB.user_id == user_id,
        MoodEntryDB.entry_date >= start_date,
        MoodEntryDB.entry_date <= end_date
    ).order_by(MoodEntryDB.entry_date).all()
    
    # 构建趋势数据
    dates = []
    intensities = []
    labels = []
    
    for entry in entries:
        dates.append(entry.entry_date.isoformat())
        intensities.append(entry.four_dim_intensity or 0.0)
        labels.append(entry.mood_label)
    
    # 构建响应
    response = MoodTrendResponse(
        dates=dates,
        intensities=intensities,
        labels=labels
    )
    
    return response
