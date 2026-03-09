from sqlalchemy.orm import Session
from datetime import datetime
from typing import Dict, Any, Optional
from backend.core.database import AuditLog


class AuditService:
    """审计日志服务"""
    
    @staticmethod
    def log_action(
        db: Session,
        admin_id: str,
        action: str,
        target_type: str,
        target_id: str,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        记录审计日志
        
        Args:
            db: 数据库会话
            admin_id: 管理员ID
            action: 操作类型 (create, update, delete, view)
            target_type: 目标类型 (user, rule, etc.)
            target_id: 目标ID
            details: 操作详情
        """
        try:
            # 创建审计日志记录
            audit_log = AuditLog(
                admin_id=admin_id,
                action=action,
                target_type=target_type,
                target_id=target_id,
                details=details,
                created_at=datetime.utcnow()
            )
            
            # 保存到数据库
            db.add(audit_log)
            db.commit()
            
            return True
        except Exception as e:
            # 记录失败时回滚事务
            db.rollback()
            print(f"审计日志记录失败: {str(e)}")
            return False
