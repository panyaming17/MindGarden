"""
预警服务层 - 处理预警的创建、查询、确认等核心业务逻辑
"""
import uuid
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_

from backend.core.database import AlertDB, AlertRuleDB, UserDB, UserQuestionnaireRecordDB, EmotionRecordDB, DialogueDB
from backend.core.data_models import (
    AlertType, AlertLevel, AlertCreateRequest,
    AlertListRequest, AlertStatsRequest
)


class AlertService:
    """预警服务类"""
    
    # 负面情绪定义
    NEGATIVE_EMOTIONS = ['难过', '焦虑', '愤怒', '担忧', '疲惫', '孤独', 'sad', 'anxious', 'angry', 'worried', 'tired', 'lonely']
    
    # 危机关键词列表
    CRISIS_KEYWORDS = [
        # 自杀相关
        '自杀', '想死', '不想活', '结束生命', '了结',
        # 自伤相关
        '自残', '割腕', '伤害自己',
        # 绝望相关
        '活着没意义', '绝望', '没希望', '撑不下去',
        # 极端情绪
        '受不了', '崩溃', '疯了', '控制不住'
    ]
    
    def __init__(self, db: Session):
        self.db = db
    
    def generate_alert_id(self) -> str:
        """生成预警ID"""
        return f"alert_{uuid.uuid4().hex[:16]}"
    
    def create_alert(self, request: AlertCreateRequest) -> AlertDB:
        """创建预警"""
        alert = AlertDB(
            id=self.generate_alert_id(),
            user_id=request.user_id,
            type=request.type.value,
            level=request.level.value,
            title=request.title,
            message=request.message,
            source_data=request.source_data,
            is_acknowledged=False,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        self.db.add(alert)
        self.db.commit()
        self.db.refresh(alert)
        return alert
    
    def get_alert_list(self, request: AlertListRequest) -> Dict[str, Any]:
        """获取预警列表"""
        query = self.db.query(AlertDB).filter(AlertDB.user_id == request.user_id)
        
        # 类型筛选
        if request.type:
            query = query.filter(AlertDB.type == request.type.value)
        
        # 等级筛选
        if request.level:
            query = query.filter(AlertDB.level == request.level.value)
        
        # 状态筛选
        if request.status:
            if request.status == 'acknowledged':
                query = query.filter(AlertDB.is_acknowledged == True)
            elif request.status == 'unacknowledged':
                query = query.filter(AlertDB.is_acknowledged == False)
        
        # 日期筛选
        if request.start_date:
            start_dt = datetime.strptime(request.start_date, '%Y-%m-%d')
            query = query.filter(AlertDB.created_at >= start_dt)
        if request.end_date:
            end_dt = datetime.strptime(request.end_date, '%Y-%m-%d') + timedelta(days=1)
            query = query.filter(AlertDB.created_at < end_dt)
        
        # 获取总数
        total = query.count()
        
        # 分页
        alerts = query.order_by(AlertDB.created_at.desc()).offset(
            (request.page - 1) * request.page_size
        ).limit(request.page_size).all()
        
        # 转换为字典列表
        alert_list = []
        for alert in alerts:
            alert_list.append({
                "id": alert.id,
                "type": alert.type,
                "level": alert.level,
                "title": alert.title,
                "message": alert.message,
                "source_data": alert.source_data,
                "is_acknowledged": alert.is_acknowledged,
                "created_at": alert.created_at.isoformat() if alert.created_at else None,
                "acknowledged_at": alert.acknowledged_at.isoformat() if alert.acknowledged_at else None,
                "acknowledged_by": alert.acknowledged_by
            })
        
        return {
            "total": total,
            "page": request.page,
            "page_size": request.page_size,
            "alerts": alert_list
        }
    
    def acknowledge_alert(self, alert_id: str, user_id: str, notes: Optional[str] = None) -> Optional[AlertDB]:
        """确认预警"""
        alert = self.db.query(AlertDB).filter(AlertDB.id == alert_id).first()
        if not alert:
            return None
        
        alert.is_acknowledged = True
        alert.acknowledged_at = datetime.utcnow()
        alert.acknowledged_by = user_id
        alert.updated_at = datetime.utcnow()
        
        # 如果有备注，可以存储到source_data中
        if notes and alert.source_data:
            alert.source_data['acknowledge_notes'] = notes
        elif notes:
            alert.source_data = {'acknowledge_notes': notes}
        
        self.db.commit()
        self.db.refresh(alert)
        return alert
    
    def batch_acknowledge_alerts(self, alert_ids: List[str], user_id: str) -> Dict[str, Any]:
        """批量确认预警"""
        success_count = 0
        failed_ids = []
        
        for alert_id in alert_ids:
            alert = self.acknowledge_alert(alert_id, user_id)
            if alert:
                success_count += 1
            else:
                failed_ids.append(alert_id)
        
        return {
            "success_count": success_count,
            "failed_count": len(failed_ids),
            "failed_ids": failed_ids
        }
    
    def get_alert_stats(self, request: AlertStatsRequest) -> Dict[str, Any]:
        """获取预警统计"""
        query = self.db.query(AlertDB).filter(AlertDB.user_id == request.user_id)
        
        # 日期筛选
        if request.start_date:
            start_dt = datetime.strptime(request.start_date, '%Y-%m-%d')
            query = query.filter(AlertDB.created_at >= start_dt)
        if request.end_date:
            end_dt = datetime.strptime(request.end_date, '%Y-%m-%d') + timedelta(days=1)
            query = query.filter(AlertDB.created_at < end_dt)
        
        # 总数
        total = query.count()
        
        # 未确认数
        unacknowledged = query.filter(AlertDB.is_acknowledged == False).count()
        
        # 已确认数
        acknowledged = query.filter(AlertDB.is_acknowledged == True).count()
        
        # 按类型统计
        by_type = {}
        for alert_type in ['questionnaire', 'emotion', 'conversation']:
            count = query.filter(AlertDB.type == alert_type).count()
            by_type[alert_type] = count
        
        # 按等级统计
        by_level = {}
        for level in ['info', 'warning', 'danger']:
            count = query.filter(AlertDB.level == level).count()
            by_level[level] = count
        
        # 按日期统计
        by_date = {}
        date_query = query.with_entities(
            func.date(AlertDB.created_at).label('date'),
            func.count(AlertDB.id).label('count')
        ).group_by(func.date(AlertDB.created_at)).all()
        
        for row in date_query:
            by_date[row.date.isoformat()] = row.count
        
        return {
            "total": total,
            "unacknowledged": unacknowledged,
            "acknowledged": acknowledged,
            "by_type": by_type,
            "by_level": by_level,
            "by_date": by_date
        }
    
    def get_alert_by_id(self, alert_id: str) -> Optional[AlertDB]:
        """根据ID获取预警"""
        return self.db.query(AlertDB).filter(AlertDB.id == alert_id).first()
    
    # ==================== 预警触发规则 ====================
    
    def check_questionnaire_alert(self, user_id: str, template_code: str, score: int, 
                                   result_level: str, record_id: str) -> Optional[AlertDB]:
        """检查问卷预警"""
        # PHQ-9 预警规则
        if template_code == 'PHQ9':
            if score >= 20:
                return self._create_questionnaire_alert(
                    user_id, 'PHQ9', 'PHQ-9抑郁量表', score, result_level, 
                    record_id, AlertLevel.DANGER,
                    "PHQ-9评分严重异常",
                    f"您的PHQ-9评分为{score}分，显示重度抑郁倾向，建议尽快寻求专业帮助"
                )
            elif score >= 15:
                return self._create_questionnaire_alert(
                    user_id, 'PHQ9', 'PHQ-9抑郁量表', score, result_level,
                    record_id, AlertLevel.WARNING,
                    "PHQ-9评分异常",
                    f"您的PHQ-9评分为{score}分，显示中度抑郁倾向，建议关注心理健康状况"
                )
            elif score >= 10:
                return self._create_questionnaire_alert(
                    user_id, 'PHQ9', 'PHQ-9抑郁量表', score, result_level,
                    record_id, AlertLevel.INFO,
                    "PHQ-9评分提示",
                    f"您的PHQ-9评分为{score}分，显示轻度抑郁倾向，建议适当调节情绪"
                )
        
        # GAD-7 预警规则
        elif template_code == 'GAD7':
            if score >= 15:
                return self._create_questionnaire_alert(
                    user_id, 'GAD7', 'GAD-7焦虑量表', score, result_level,
                    record_id, AlertLevel.DANGER,
                    "GAD-7评分严重异常",
                    f"您的GAD-7评分为{score}分，显示重度焦虑倾向，建议尽快寻求专业帮助"
                )
            elif score >= 10:
                return self._create_questionnaire_alert(
                    user_id, 'GAD7', 'GAD-7焦虑量表', score, result_level,
                    record_id, AlertLevel.WARNING,
                    "GAD-7评分异常",
                    f"您的GAD-7评分为{score}分，显示中度焦虑倾向，建议关注心理健康状况"
                )
            elif score >= 5:
                return self._create_questionnaire_alert(
                    user_id, 'GAD7', 'GAD-7焦虑量表', score, result_level,
                    record_id, AlertLevel.INFO,
                    "GAD-7评分提示",
                    f"您的GAD-7评分为{score}分，显示轻度焦虑倾向，建议适当放松身心"
                )
        
        return None
    
    def _create_questionnaire_alert(self, user_id: str, template_code: str, 
                                     template_name: str, score: int, result_level: str,
                                     record_id: str, level: AlertLevel, 
                                     title: str, message: str) -> AlertDB:
        """创建问卷预警"""
        request = AlertCreateRequest(
            user_id=user_id,
            type=AlertType.QUESTIONNAIRE,
            level=level,
            title=title,
            message=message,
            source_data={
                "template_code": template_code,
                "template_name": template_name,
                "score": score,
                "result": self._get_result_text(result_level),
                "result_level": result_level,
                "date": datetime.now().strftime('%Y-%m-%d'),
                "record_id": record_id
            }
        )
        return self.create_alert(request)
    
    def _get_result_text(self, result_level: str) -> str:
        """获取结果等级文本"""
        level_map = {
            'none': '无',
            'mild': '轻度',
            'moderate': '中度',
            'severe': '重度'
        }
        return level_map.get(result_level, result_level)
    
    def check_emotion_alert(self, user_id: str, emotion_type: str, 
                            intensity: Optional[int] = None) -> Optional[AlertDB]:
        """检查情绪预警"""
        # 检查是否为负面情绪
        is_negative = any(neg in emotion_type.lower() for neg in self.NEGATIVE_EMOTIONS)
        
        if not is_negative:
            return None
        
        # 单日情绪强度 >= 8
        if intensity and intensity >= 8:
            return self._create_emotion_alert(
                user_id, AlertLevel.WARNING,
                "高强度情绪预警",
                f"您今日记录的{emotion_type}情绪强度较高，建议适当调节",
                {"emotion": emotion_type, "intensity": intensity, "date": datetime.now().strftime('%Y-%m-%d')}
            )
        
        # 检查连续负面情绪
        consecutive_days = self._check_consecutive_negative_emotions(user_id)
        if consecutive_days >= 7:
            return self._create_consecutive_emotion_alert(user_id, consecutive_days, AlertLevel.DANGER)
        elif consecutive_days >= 3:
            return self._create_consecutive_emotion_alert(user_id, consecutive_days, AlertLevel.WARNING)
        
        # 一周内负面情绪 >= 5天
        weekly_negative = self._check_weekly_negative_emotions(user_id)
        if weekly_negative >= 5:
            return self._create_emotion_alert(
                user_id, AlertLevel.INFO,
                "负面情绪趋势提醒",
                "本周负面情绪占比较高，建议关注心理健康",
                {"weekly_negative_days": weekly_negative}
            )
        
        return None
    
    def _create_emotion_alert(self, user_id: str, level: AlertLevel, 
                               title: str, message: str, source_data: Dict) -> AlertDB:
        """创建情绪预警"""
        request = AlertCreateRequest(
            user_id=user_id,
            type=AlertType.EMOTION,
            level=level,
            title=title,
            message=message,
            source_data=source_data
        )
        return self.create_alert(request)
    
    def _create_consecutive_emotion_alert(self, user_id: str, days: int, level: AlertLevel) -> AlertDB:
        """创建连续负面情绪预警"""
        # 获取最近的情绪记录
        recent_records = self.db.query(EmotionRecordDB).filter(
            EmotionRecordDB.user_id == user_id
        ).order_by(EmotionRecordDB.record_date.desc()).limit(days).all()
        
        emotion_records = []
        for record in recent_records:
            emotion_records.append({
                "date": record.record_date,
                "emotion": record.emotion_name,
                "intensity": 7  # 默认强度，实际应该从记录中获取
            })
        
        if level == AlertLevel.DANGER:
            title = "连续负面情绪预警"
            message = f"您已连续{days}天记录负面情绪，系统检测到情绪状态异常"
        else:
            title = "连续负面情绪提醒"
            message = f"您已连续{days}天记录负面情绪，建议关注情绪变化"
        
        return self._create_emotion_alert(
            user_id, level, title, message,
            {
                "consecutive_days": days,
                "emotion_records": emotion_records,
                "summary": f"连续{days}天负面情绪"
            }
        )
    
    def _check_consecutive_negative_emotions(self, user_id: str) -> int:
        """检查连续负面情绪天数"""
        # 获取最近30天的情绪记录
        records = self.db.query(EmotionRecordDB).filter(
            EmotionRecordDB.user_id == user_id
        ).order_by(EmotionRecordDB.record_date.desc()).limit(30).all()
        
        if not records:
            return 0
        
        # 按日期分组，检查每天的情绪
        date_emotions = {}
        for record in records:
            date = record.record_date
            if date not in date_emotions:
                date_emotions[date] = []
            date_emotions[date].append(record.emotion_name)
        
        # 计算连续负面情绪天数
        consecutive = 0
        for date in sorted(date_emotions.keys(), reverse=True):
            emotions = date_emotions[date]
            is_negative_day = any(
                any(neg in emotion.lower() for neg in self.NEGATIVE_EMOTIONS)
                for emotion in emotions
            )
            if is_negative_day:
                consecutive += 1
            else:
                break
        
        return consecutive
    
    def _check_weekly_negative_emotions(self, user_id: str) -> int:
        """检查一周内负面情绪天数"""
        # 获取最近7天的情绪记录
        records = self.db.query(EmotionRecordDB).filter(
            EmotionRecordDB.user_id == user_id
        ).order_by(EmotionRecordDB.record_date.desc()).limit(30).all()
        
        if not records:
            return 0
        
        # 按日期分组
        date_emotions = {}
        for record in records:
            date = record.record_date
            if date not in date_emotions:
                date_emotions[date] = []
            date_emotions[date].append(record.emotion_name)
        
        # 统计负面情绪天数（最近7天）
        negative_days = 0
        recent_dates = sorted(date_emotions.keys(), reverse=True)[:7]
        for date in recent_dates:
            emotions = date_emotions[date]
            if any(any(neg in emotion.lower() for neg in self.NEGATIVE_EMOTIONS) for emotion in emotions):
                negative_days += 1
        
        return negative_days
    
    def check_conversation_alert(self, user_id: str, session_id: str, 
                                  content: str, emotion_intensity: Optional[float] = None) -> Optional[AlertDB]:
        """检查对话内容预警"""
        # 检测危机关键词
        crisis_keywords = []
        for keyword in self.CRISIS_KEYWORDS:
            if keyword in content:
                crisis_keywords.append(keyword)
        
        if crisis_keywords:
            return self._create_conversation_alert(
                user_id, session_id, content, emotion_intensity,
                AlertLevel.DANGER, crisis_keywords
            )
        
        # 检测情绪强度
        if emotion_intensity and emotion_intensity >= 0.85:
            return self._create_conversation_alert(
                user_id, session_id, content, emotion_intensity,
                AlertLevel.WARNING, []
            )
        
        return None
    
    def _create_conversation_alert(self, user_id: str, session_id: str, 
                                    content: str, emotion_intensity: Optional[float],
                                    level: AlertLevel, crisis_keywords: List[str]) -> AlertDB:
        """创建对话预警"""
        if level == AlertLevel.DANGER:
            title = "对话危机信号检测"
            message = "AI检测到对话内容中存在潜在危机信号词汇，需要特别关注"
        else:
            title = "对话情绪异常"
            message = "AI检测到对话中情绪强度异常，建议关注用户状态"
        
        # 截取预览内容
        preview = content[:50] + "..." if len(content) > 50 else content
        
        request = AlertCreateRequest(
            user_id=user_id,
            type=AlertType.CONVERSATION,
            level=level,
            title=title,
            message=message,
            source_data={
                "session_id": session_id,
                "preview": preview,
                "emotion_intensity": emotion_intensity,
                "crisis_detected": len(crisis_keywords) > 0,
                "crisis_keywords": crisis_keywords,
                "risk_level": "high" if level == AlertLevel.DANGER else "medium"
            }
        )
        return self.create_alert(request)
    
    def get_unacknowledged_alerts(self, user_id: str) -> List[AlertDB]:
        """获取用户未确认的预警"""
        return self.db.query(AlertDB).filter(
            AlertDB.user_id == user_id,
            AlertDB.is_acknowledged == False
        ).order_by(AlertDB.created_at.desc()).all()
