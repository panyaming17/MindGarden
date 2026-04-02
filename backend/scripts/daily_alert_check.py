"""
每日预警检查定时任务脚本

功能：
1. 检查所有用户的连续负面情绪
2. 生成相应的预警
3. 通过WebSocket推送预警

运行方式：
    python backend/scripts/daily_alert_check.py
    
或使用APScheduler定时执行
"""
import sys
import os
import asyncio

# 添加项目根目录到 Python 路径
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from datetime import datetime
from sqlalchemy.orm import Session

from backend.core.database import SessionLocal, UserDB
from backend.services.alert_service import AlertService
from backend.services.alert_websocket import alert_ws_manager
from backend.core.data_models import AlertLevel


async def daily_emotion_check():
    """
    每日情绪检查
    检查所有用户的连续负面情绪并生成预警
    """
    print(f"[{datetime.now().isoformat()}] 开始每日情绪检查...")
    
    db = SessionLocal()
    try:
        alert_service = AlertService(db)
        
        # 获取所有活跃用户
        users = db.query(UserDB).filter(UserDB.is_active == True).all()
        print(f"检查用户数: {len(users)}")
        
        generated_count = 0
        
        for user in users:
            try:
                # 检查连续负面情绪
                consecutive_days = alert_service._check_consecutive_negative_emotions(user.id)
                
                if consecutive_days >= 3:
                    print(f"用户 {user.id} 连续 {consecutive_days} 天负面情绪")
                    
                    # 检查是否已存在未确认的连续情绪预警
                    existing_alerts = alert_service.get_unacknowledged_alerts(user.id)
                    has_existing = any(
                        a.type == 'emotion' and '连续负面情绪' in a.title 
                        for a in existing_alerts
                    )
                    
                    if not has_existing:
                        # 根据连续天数确定预警等级
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
                            
                            # 通过WebSocket推送
                            await alert_ws_manager.push_new_alert(user.id, alert_data)
                            print(f"  -> 生成预警: {alert.id} ({alert.level})")
                            generated_count += 1
                    else:
                        print(f"  -> 已存在未确认的连续情绪预警，跳过")
                        
            except Exception as e:
                print(f"检查用户 {user.id} 时出错: {e}")
                continue
        
        print(f"[{datetime.now().isoformat()}] 每日检查完成，生成 {generated_count} 个预警")
        
    finally:
        db.close()


def run_daily_check():
    """运行每日检查（同步入口）"""
    asyncio.run(daily_emotion_check())


if __name__ == "__main__":
    run_daily_check()
