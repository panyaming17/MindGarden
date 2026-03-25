"""
管理员功能的API端点
"""
from fastapi import APIRouter, HTTPException, Depends, status, Query, Request
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from backend.core.database import DBConfig, UserDB, StrategyDB, AdminLogDB, SessionLocal
from backend.core.data_models import (
    User,
    UserCreate,
    UserUpdate,
    UserList,
    Strategy,
    StrategyCreate,
    StrategyUpdate,
    StrategyList,
    AdminLog,
    AdminLogList
)

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])

# 依赖注入获取数据库会话
def get_db():
    """获取数据库会话的依赖函数"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 记录管理员操作日志
def log_admin_action(
    admin_id: str,
    action: str,
    target: str,
    details: str,
    ip_address: str,
    db: Session
):
    """记录管理员操作日志"""
    log = AdminLogDB(
        admin_id=admin_id,
        action=action,
        target=target,
        details=details,
        ip_address=ip_address,
        created_at=datetime.utcnow()
    )
    db.add(log)
    db.commit()

# 获取用户列表接口
@router.get("/users", response_model=UserList)
async def get_users(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    keyword: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    获取用户列表（分页、搜索）
    """
    # 构建查询
    query = db.query(UserDB)
    
    # 搜索关键词
    if keyword:
        query = query.filter(
            (UserDB.username.like(f"%{keyword}%") |
             UserDB.email.like(f"%{keyword}%"))
        )
    
    # 计算总数
    total = query.count()
    
    # 分页查询
    users = query.order_by(UserDB.created_at.desc()).offset((page - 1) * size).limit(size).all()
    
    # 转换为响应模型
    user_list = []
    for user in users:
        user_item = User(
            id=user.id,
            username=user.username,
            email=user.email,
            is_active=user.is_active,
            role=user.role,
            created_at=user.created_at,
            updated_at=user.updated_at
        )
        user_list.append(user_item)
    
    # 构建响应
    response = UserList(
        users=user_list,
        total=total
    )
    
    return response

# 添加用户接口
@router.post("/users", response_model=User)
async def add_user(
    user_data: UserCreate,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    添加用户
    """
    # 检查用户名是否已存在
    existing_user = db.query(UserDB).filter(UserDB.username == user_data.username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已存在"
        )
    
    # 检查邮箱是否已被注册
    existing_email = db.query(UserDB).filter(UserDB.email == user_data.email).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="邮箱已被注册"
        )
    
    # 创建新用户
    user_id = f"user_{datetime.utcnow().timestamp()}"
    new_user = UserDB(
        id=user_id,
        username=user_data.username,
        email=user_data.email,
        password_hash=user_data.password,  # 实际应该加密
        is_active=True,
        role=user_data.role
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # 获取IP地址
    ip_address = request.client.host if request.client else "127.0.0.1"
    
    # 记录操作日志
    log_admin_action(
        admin_id="admin",  # 实际应该从认证中获取
        action="create_user",
        target=user_data.username,
        details=f"创建用户 {user_data.username}",
        ip_address=ip_address,
        db=db
    )
    
    # 转换为响应模型
    return User(
        id=new_user.id,
        username=new_user.username,
        email=new_user.email,
        is_active=new_user.is_active,
        role=new_user.role,
        created_at=new_user.created_at,
        updated_at=new_user.updated_at
    )

# 编辑用户接口
@router.put("/users/{id}")
async def update_user(
    id: str,
    user_data: UserUpdate,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    编辑用户
    """
    # 检查用户是否存在
    user = db.query(UserDB).filter(UserDB.id == id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # 只更新role和is_active字段，其他字段不更新
    if user_data.role:
        user.role = user_data.role
    if user_data.is_active is not None:
        user.is_active = user_data.is_active
    
    user.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(user)
    
    # 获取IP地址
    ip_address = request.client.host if request.client else "127.0.0.1"
    
    # 记录操作日志
    log_admin_action(
        admin_id="admin",  # 实际应该从认证中获取
        action="update_user",
        target=user.username,
        details=f"更新用户 {user.username}，角色: {user.role}，活跃状态: {user.is_active}",
        ip_address=ip_address,
        db=db
    )
    
    return {"message": "用户信息更新成功"}

# 软删除用户接口
@router.delete("/users/{id}")
async def delete_user(
    id: str,
    request:Request,
    db: Session = Depends(get_db)
):
    """
    软删除用户
    """
    # 检查用户是否存在
    user = db.query(UserDB).filter(UserDB.id == id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # 软删除用户
    user.is_active = False
    user.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(user)
    
    # 记录操作日志
    log_admin_action(
        admin_id="admin",  # 实际应该从认证中获取
        action="delete_user",
        target=user.username,
        details=f"软删除用户 {user.username}",
        ip_address="127.0.0.1",  # 实际应该从请求中获取
        db=db
    )
    
    return {"message": "用户删除成功"}

# 获取策略列表接口
@router.get("/strategies", response_model=StrategyList)
async def get_strategies(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=1000),
    filters: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    获取策略列表
    """
    # 限制size的最大值，防止请求过多数据
    max_size = 1000
    if size > max_size:
        size = max_size
    
    # 构建查询
    query = db.query(StrategyDB)
    
    # 过滤条件
    if filters:
        # 这里可以根据实际需求实现过滤逻辑
        pass
    
    # 按创建时间正序排列
    query = query.order_by(StrategyDB.created_at.asc())
    
    # 计算总数
    total = query.count()
    
    # 分页查询
    strategies = query.offset((page - 1) * size).limit(size).all()
    
    # 转换为响应模型
    strategy_list = []
    for strategy in strategies:
        strategy_item = Strategy(
            id=strategy.id,
            intensity_level=strategy.intensity_level,
            hedonic=strategy.hedonic,
            tension=strategy.tension,
            complexity=strategy.complexity,
            fusion_mode=strategy.fusion_mode,
            cbt_techniques=strategy.cbt_techniques,
            tcm_methods=strategy.tcm_methods,
            strategy_content=strategy.strategy_content,
            example=strategy.example,
            created_at=strategy.created_at
        )
        strategy_list.append(strategy_item)
    
    # 构建响应
    response = StrategyList(
        strategies=strategy_list,
        total=total
    )
    
    return response

# 添加策略接口
@router.post("/strategies", response_model=Strategy)
async def add_strategy(
    request_data: dict,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    添加策略
    """
    try:
        # 从请求体中提取策略数据
        strategy_data = request_data.get("strategy_data")
        if not strategy_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="缺少策略数据"
            )
        
        # 检查策略是否已存在
        existing_strategy = db.query(StrategyDB).filter(
            StrategyDB.intensity_level == strategy_data.get("intensity_level"),
            StrategyDB.hedonic == strategy_data.get("hedonic"),
            StrategyDB.tension == strategy_data.get("tension"),
            StrategyDB.complexity == strategy_data.get("complexity")
        ).first()
        
        if existing_strategy:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="策略已存在"
            )
        
        # 创建新策略
        new_strategy = StrategyDB(
            intensity_level=strategy_data.get("intensity_level"),
            hedonic=strategy_data.get("hedonic"),
            tension=strategy_data.get("tension"),
            complexity=strategy_data.get("complexity"),
            fusion_mode=strategy_data.get("fusion_mode"),
            cbt_techniques=strategy_data.get("cbt_techniques"),
            tcm_methods=strategy_data.get("tcm_methods"),
            strategy_content=strategy_data.get("strategy_content"),
            example=strategy_data.get("example")
        )
        
        db.add(new_strategy)
        db.commit()
        db.refresh(new_strategy)
        
        # 获取IP地址
        ip_address = request.client.host if request.client else "127.0.0.1"
        
        # 记录操作日志
        log_admin_action(
            admin_id="admin",  # 实际应该从认证中获取
            action="create_strategy",
            target=strategy_data.get("fusion_mode"),
            details=f"创建策略 {strategy_data.get("fusion_mode")}",
            ip_address=ip_address,
            db=db
        )
        
        # 转换为响应模型
        return Strategy(
            id=new_strategy.id,
            intensity_level=new_strategy.intensity_level,
            hedonic=new_strategy.hedonic,
            tension=new_strategy.tension,
            complexity=new_strategy.complexity,
            fusion_mode=new_strategy.fusion_mode,
            cbt_techniques=new_strategy.cbt_techniques,
            tcm_methods=new_strategy.tcm_methods,
            strategy_content=new_strategy.strategy_content,
            example=new_strategy.example,
            created_at=new_strategy.created_at
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"ERROR: 添加策略失败: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"添加策略失败: {str(e)}"
        )

# 更新策略接口
@router.put("/strategies/{id}")
async def update_strategy(
    id: int,
    request_data: dict,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    更新策略
    """
    try:
        # 从请求体中提取策略数据
        strategy_data = request_data.get("strategy_data")
        if not strategy_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="缺少策略数据"
            )
        
        # 检查策略是否存在
        strategy = db.query(StrategyDB).filter(StrategyDB.id == id).first()
        if not strategy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="策略不存在"
            )
        
        # 更新策略信息
        if strategy_data.get("intensity_level"):
            strategy.intensity_level = strategy_data.get("intensity_level")
        if strategy_data.get("hedonic"):
            strategy.hedonic = strategy_data.get("hedonic")
        if strategy_data.get("tension"):
            strategy.tension = strategy_data.get("tension")
        if strategy_data.get("complexity"):
            strategy.complexity = strategy_data.get("complexity")
        if strategy_data.get("fusion_mode"):
            strategy.fusion_mode = strategy_data.get("fusion_mode")
        if strategy_data.get("cbt_techniques"):
            strategy.cbt_techniques = strategy_data.get("cbt_techniques")
        if strategy_data.get("tcm_methods"):
            strategy.tcm_methods = strategy_data.get("tcm_methods")
        if strategy_data.get("strategy_content"):
            strategy.strategy_content = strategy_data.get("strategy_content")
        if strategy_data.get("example"):
            strategy.example = strategy_data.get("example")
        
        db.commit()
        db.refresh(strategy)
        
        # 获取IP地址
        ip_address = request.client.host if request.client else "127.0.0.1"
        
        # 记录操作日志
        log_admin_action(
            admin_id="admin",  # 实际应该从认证中获取
            action="update_strategy",
            target=strategy.fusion_mode,
            details=f"更新策略 {strategy.fusion_mode}",
            ip_address=ip_address,
            db=db
        )
        
        return {"message": "策略更新成功"}
    except HTTPException:
        raise
    except Exception as e:
        print(f"ERROR: 更新策略失败: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新策略失败: {str(e)}"
        )

# 删除策略接口
@router.delete("/strategies/{id}")
async def delete_strategy(
    id: int,
    request: Request,  # 使用Request对象
    db: Session = Depends(get_db)
):
    """
    删除策略
    """
    # 检查策略是否存在
    strategy = db.query(StrategyDB).filter(StrategyDB.id == id).first()
    if not strategy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="策略不存在"
        )
    
    # 删除策略
    db.delete(strategy)
    db.commit()
    
    # 获取IP地址
    ip_address = request.client.host if request.client else "127.0.0.1"
    
    # 记录操作日志
    log_admin_action(
        admin_id="admin",  # 实际应该从认证中获取
        action="delete_strategy",
        target=strategy.fusion_mode,
        details=f"删除策略 {strategy.fusion_mode}",
        ip_address=ip_address,
        db=db
    )
    
    return {"message": "策略删除成功"}

# 获取管理员操作日志接口
@router.get("/logs", response_model=AdminLogList)
async def get_admin_logs(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    admin_id: Optional[str] = None,
    action: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    获取管理员操作日志
    """
    # 构建查询
    query = db.query(AdminLogDB)
    
    # 过滤条件
    if admin_id:
        query = query.filter(AdminLogDB.admin_id == admin_id)
    if action:
        query = query.filter(AdminLogDB.action == action)
    
    # 计算总数
    total = query.count()
    
    # 分页查询
    logs = query.order_by(AdminLogDB.created_at.desc()).offset((page - 1) * size).limit(size).all()
    
    # 转换为响应模型
    log_list = []
    for log in logs:
        log_item = AdminLog(
            id=log.id,
            admin_id=log.admin_id,
            action=log.action,
            target=log.target,
            details=log.details,
            ip_address=log.ip_address,
            created_at=log.created_at
        )
        log_list.append(log_item)
    
    # 构建响应
    response = AdminLogList(
        logs=log_list,
        total=total
    )
    
    return response
