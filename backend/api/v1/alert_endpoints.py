"""
预警相关的API端点
"""
from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from typing import List

from backend.core.database import DBConfig, UserDB, AlertDB, SessionLocal
from backend.core.data_models import (
    Alert,
    AlertList,
    AlertAcknowledge
)

router = APIRouter(prefix="/api/v1/alert", tags=["alert"])

# 依赖注入获取数据库会话
def get_db():
    """获取数据库会话的依赖函数"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 获取用户未读预警接口
@router.get("/list", response_model=AlertList)
async def get_alert_list(
    user_id: str,
    db: Session = Depends(get_db)
):
    """
    获取用户未读预警
    """
    # 检查用户是否存在
    user = db.query(UserDB).filter(UserDB.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # 查询用户的未读预警
    alerts = db.query(AlertDB).filter(
        AlertDB.user_id == user_id,
        AlertDB.is_acknowledged == False
    ).order_by(AlertDB.created_at.desc()).all()
    
    # 转换为响应模型
    alert_list = []
    for alert in alerts:
        alert_item = Alert(
            id=alert.id,
            type=alert.alert_type,
            level=alert.alert_level,
            message=alert.message,
            created_at=alert.created_at
        )
        alert_list.append(alert_item)
    
    # 构建响应
    response = AlertList(alerts=alert_list)
    
    return response

# 确认预警接口
@router.post("/acknowledge")
async def acknowledge_alert(
    acknowledge: AlertAcknowledge,
    db: Session = Depends(get_db)
):
    """
    确认预警
    """
    # 查询预警
    alert = db.query(AlertDB).filter(AlertDB.id == acknowledge.alert_id).first()
    
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="预警不存在"
        )
    
    # 标记为已处理
    alert.is_acknowledged = True
    db.commit()
    db.refresh(alert)
    
    return {"message": "预警已确认"}
