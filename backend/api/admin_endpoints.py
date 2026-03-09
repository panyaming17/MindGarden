"""
后台管理相关的API端点
"""
from fastapi import APIRouter, HTTPException, Depends, status, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import BaseModel

from backend.core.database import DBConfig, UserDB, AuditLog
from backend.core.data_models import User, AuditLog as AuditLogModel, AuditLogListResponse
from backend.core.audit_service import AuditService
from backend.api.auth_endpoints import get_current_user, get_db

router = APIRouter(prefix="/api/admin", tags=["admin"])

# 获取当前管理员
def get_current_admin(current_user: UserDB = Depends(get_current_user)) -> UserDB:
    """获取当前管理员"""
    if current_user.role not in ["admin", "super_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足，需要管理员权限"
        )
    return current_user

# 用户更新请求模型
class UserUpdateAdmin(BaseModel):
    """用户更新请求模型（管理员用）"""
    is_active: Optional[bool] = None
    role: Optional[str] = None

# 用户列表响应模型
class UserListResponse(BaseModel):
    """用户列表响应模型"""
    total: int
    page: int
    per_page: int
    items: List[User]

# 获取所有用户列表
@router.get("/users", response_model=UserListResponse)
async def get_users(
    page: int = Query(1, ge=1, description="页码"),
    per_page: int = Query(10, ge=1, le=100, description="每页数量"),
    search: Optional[str] = Query(None, description="搜索关键词（用户名或邮箱）"),
    current_admin: UserDB = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    获取所有用户列表
    - 支持分页（page, per_page）
    - 支持搜索（username/email）
    - 仅管理员可访问
    """
    # 构建查询
    query = db.query(UserDB)
    
    # 搜索功能
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            (UserDB.username.like(search_pattern)) | 
            (UserDB.email.like(search_pattern))
        )
    
    # 计算总数
    total = query.count()
    
    # 分页
    offset = (page - 1) * per_page
    users = query.offset(offset).limit(per_page).all()
    
    # 转换为响应模型
    user_items = [
        User(
            id=user.id,
            username=user.username,
            email=user.email,
            is_active=user.is_active,
            role=user.role,
            created_at=user.created_at,
            updated_at=user.updated_at
        )
        for user in users
    ]
    
    return UserListResponse(
        total=total,
        page=page,
        per_page=per_page,
        items=user_items
    )

# 获取单个用户详情
@router.get("/users/{user_id}", response_model=User)
async def get_user(
    user_id: str,
    current_admin: UserDB = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    获取单个用户详情
    - 仅管理员可访问
    """
    user = db.query(UserDB).filter(UserDB.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    return User(
        id=user.id,
        username=user.username,
        email=user.email,
        is_active=user.is_active,
        role=user.role,
        created_at=user.created_at,
        updated_at=user.updated_at
    )

# 更新用户信息
@router.patch("/users/{user_id}", response_model=User)
async def update_user(
    user_id: str,
    update_data: UserUpdateAdmin,
    current_admin: UserDB = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    更新用户信息
    - 仅管理员可访问
    - 可更新is_active或role字段
    """
    user = db.query(UserDB).filter(UserDB.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # 防止超级管理员被降级
    if user.role == "super_admin" and current_admin.role != "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足，无法修改超级管理员"
        )
    
    # 记录更新前的状态
    old_status = {
        "is_active": user.is_active,
        "role": user.role
    }
    
    # 更新字段
    if update_data.is_active is not None:
        user.is_active = update_data.is_active
    if update_data.role is not None:
        # 防止非超级管理员设置超级管理员角色
        if update_data.role == "super_admin" and current_admin.role != "super_admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="权限不足，无法设置超级管理员角色"
            )
        user.role = update_data.role
    
    # 记录更新后的状态
    new_status = {
        "is_active": user.is_active,
        "role": user.role
    }
    
    db.commit()
    db.refresh(user)
    
    # 记录审计日志
    AuditService.log_action(
        db=db,
        admin_id=current_admin.id,
        action="update",
        target_type="user",
        target_id=user_id,
        details={
            "username": user.username,
            "old_status": old_status,
            "new_status": new_status
        }
    )
    
    return User(
        id=user.id,
        username=user.username,
        email=user.email,
        is_active=user.is_active,
        role=user.role,
        created_at=user.created_at,
        updated_at=user.updated_at
    )

# 软删除用户
@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    current_admin: UserDB = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    软删除用户（设置is_active=False）
    - 仅管理员可访问
    """
    user = db.query(UserDB).filter(UserDB.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # 防止超级管理员被删除
    if user.role == "super_admin" and current_admin.role != "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足，无法删除超级管理员"
        )
    
    # 记录删除前的状态
    user_info = {
        "username": user.username,
        "email": user.email,
        "role": user.role,
        "is_active": user.is_active
    }
    
    # 软删除
    user.is_active = False
    db.commit()
    
    # 记录审计日志
    AuditService.log_action(
        db=db,
        admin_id=current_admin.id,
        action="delete",
        target_type="user",
        target_id=user_id,
        details={
            "user_info": user_info
        }
    )
    
    return {"message": "用户删除成功"}

# 获取审计日志列表
@router.get("/logs/audit", response_model=AuditLogListResponse)
async def get_audit_logs(
    page: int = Query(1, ge=1, description="页码"),
    per_page: int = Query(10, ge=1, le=100, description="每页数量"),
    admin_id: Optional[str] = Query(None, description="管理员ID"),
    action: Optional[str] = Query(None, description="操作类型"),
    start_date: Optional[str] = Query(None, description="开始日期 (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="结束日期 (YYYY-MM-DD)"),
    current_admin: UserDB = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    获取审计日志列表
    - 支持分页（page, per_page）
    - 支持筛选（admin_id, action, start_date, end_date）
    - 仅管理员可访问
    """
    # 构建查询
    query = db.query(AuditLog)
    
    # 应用筛选条件
    if admin_id:
        query = query.filter(AuditLog.admin_id == admin_id)
    
    if action:
        query = query.filter(AuditLog.action == action)
    
    if start_date:
        from datetime import datetime
        try:
            start = datetime.strptime(start_date, "%Y-%m-%d")
            query = query.filter(AuditLog.created_at >= start)
        except ValueError:
            pass
    
    if end_date:
        from datetime import datetime, timedelta
        try:
            end = datetime.strptime(end_date, "%Y-%m-%d")
            # 结束日期设置为当天的23:59:59
            end = end + timedelta(days=1) - timedelta(seconds=1)
            query = query.filter(AuditLog.created_at <= end)
        except ValueError:
            pass
    
    # 按创建时间倒序排序
    query = query.order_by(AuditLog.created_at.desc())
    
    # 计算总数
    total = query.count()
    
    # 分页
    offset = (page - 1) * per_page
    logs = query.offset(offset).limit(per_page).all()
    
    # 转换为响应模型
    log_items = [
        AuditLogModel(
            id=log.id,
            admin_id=log.admin_id,
            action=log.action,
            target_type=log.target_type,
            target_id=log.target_id,
            details=log.details,
            created_at=log.created_at
        )
        for log in logs
    ]
    
    return AuditLogListResponse(
        total=total,
        page=page,
        per_page=per_page,
        items=log_items
    )


