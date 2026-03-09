"""
规则库管理相关的API端点
"""
from fastapi import APIRouter, HTTPException, Depends, status, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import BaseModel

from backend.core.database import DBConfig, RuleDB
from backend.core.data_models import Rule, RuleCreate, RuleUpdate, RuleListResponse
from backend.core.audit_service import AuditService
from backend.api.auth_endpoints import get_current_user, get_db

router = APIRouter(prefix="/api/admin", tags=["admin_rules"])

# 获取当前管理员
async def get_current_admin(current_user = Depends(get_current_user)):
    """获取当前管理员"""
    if current_user.role not in ["admin", "super_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足，需要管理员权限"
        )
    return current_user

# 获取规则列表
@router.get("/rules", response_model=RuleListResponse)
async def get_rules(
    type: Optional[str] = Query(None, description="规则类型"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    page: int = Query(1, ge=1, description="页码"),
    per_page: int = Query(10, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """
    获取规则列表
    - 支持按类型过滤
    - 支持按名称搜索
    - 支持分页
    """
    # 构建查询
    query = db.query(RuleDB)
    
    # 按类型过滤
    if type:
        query = query.filter(RuleDB.type == type)
    
    # 按名称搜索
    if search:
        query = query.filter(RuleDB.name.ilike(f"%{search}%"))
    
    # 计算总数
    total = query.count()
    
    # 分页
    offset = (page - 1) * per_page
    rules = query.offset(offset).limit(per_page).all()
    
    # 转换为响应模型
    items = [
        Rule(
            id=rule.id,
            type=rule.type,
            name=rule.name,
            content=rule.content,
            version=rule.version,
            is_active=rule.is_active,
            created_at=rule.created_at,
            updated_at=rule.updated_at
        )
        for rule in rules
    ]
    
    return RuleListResponse(
        total=total,
        page=page,
        per_page=per_page,
        items=items
    )

# 创建规则
@router.post("/rules", response_model=Rule, status_code=status.HTTP_201_CREATED)
async def create_rule(
    rule_data: RuleCreate,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """
    创建规则
    """
    # 检查类型是否合法
    if rule_data.type not in ["cbt", "tcm"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="规则类型必须是 cbt 或 tcm"
        )
    
    # 创建规则
    new_rule = RuleDB(
        type=rule_data.type,
        name=rule_data.name,
        content=rule_data.content,
        version=rule_data.version,
        is_active=rule_data.is_active
    )
    
    db.add(new_rule)
    db.commit()
    db.refresh(new_rule)
    
    # 记录审计日志
    AuditService.log_action(
        db=db,
        admin_id=current_admin.id,
        action="create",
        target_type="rule",
        target_id=str(new_rule.id),
        details={
            "type": new_rule.type,
            "name": new_rule.name,
            "version": new_rule.version
        }
    )
    
    # 转换为响应模型
    return Rule(
        id=new_rule.id,
        type=new_rule.type,
        name=new_rule.name,
        content=new_rule.content,
        version=new_rule.version,
        is_active=new_rule.is_active,
        created_at=new_rule.created_at,
        updated_at=new_rule.updated_at
    )

# 更新规则
@router.put("/rules/{rule_id}", response_model=Rule)
async def update_rule(
    rule_id: int,
    rule_data: RuleUpdate,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """
    更新规则
    """
    # 查找规则
    rule = db.query(RuleDB).filter(RuleDB.id == rule_id).first()
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="规则不存在"
        )
    
    # 检查类型是否合法
    if rule_data.type and rule_data.type not in ["cbt", "tcm"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="规则类型必须是 cbt 或 tcm"
        )
    
    # 记录更新前的状态
    old_status = {
        "type": rule.type,
        "name": rule.name,
        "version": rule.version,
        "is_active": rule.is_active
    }
    
    # 更新规则
    if rule_data.type is not None:
        rule.type = rule_data.type
    if rule_data.name is not None:
        rule.name = rule_data.name
    if rule_data.content is not None:
        rule.content = rule_data.content
    if rule_data.version is not None:
        rule.version = rule_data.version
    if rule_data.is_active is not None:
        rule.is_active = rule_data.is_active
    
    # 记录更新后的状态
    new_status = {
        "type": rule.type,
        "name": rule.name,
        "version": rule.version,
        "is_active": rule.is_active
    }
    
    db.commit()
    db.refresh(rule)
    
    # 记录审计日志
    AuditService.log_action(
        db=db,
        admin_id=current_admin.id,
        action="update",
        target_type="rule",
        target_id=str(rule_id),
        details={
            "old_status": old_status,
            "new_status": new_status
        }
    )
    
    # 转换为响应模型
    return Rule(
        id=rule.id,
        type=rule.type,
        name=rule.name,
        content=rule.content,
        version=rule.version,
        is_active=rule.is_active,
        created_at=rule.created_at,
        updated_at=rule.updated_at
    )

# 删除规则
@router.delete("/rules/{rule_id}")
async def delete_rule(
    rule_id: int,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """
    删除规则
    """
    # 查找规则
    rule = db.query(RuleDB).filter(RuleDB.id == rule_id).first()
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="规则不存在"
        )
    
    # 记录删除前的规则信息
    rule_info = {
        "type": rule.type,
        "name": rule.name,
        "version": rule.version,
        "is_active": rule.is_active
    }
    
    # 删除规则
    db.delete(rule)
    db.commit()
    
    # 记录审计日志
    AuditService.log_action(
        db=db,
        admin_id=current_admin.id,
        action="delete",
        target_type="rule",
        target_id=str(rule_id),
        details={
            "rule_info": rule_info
        }
    )
    
    return {"message": "规则删除成功"}
