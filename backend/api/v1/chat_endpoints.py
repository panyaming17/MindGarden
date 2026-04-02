"""
对话核心的API端点
"""
from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from datetime import datetime
import uuid
import json
import asyncio
from typing import List, Optional

from backend.core.database import DBConfig, UserDB, DialogueDB, SessionLocal, UserArchiveDB, ChatSessionDB, SessionReportDB
from backend.repositories.record_repository_new import RecordRepository
from backend.core.data_models import (
    ChatMessage,
    ChatMessageResponse,
    NewSessionResponse,
    SessionInfo,
    SessionList,
    ChatHistoryResponse,
    Dialogue,
)
from backend.agents.recorder_agent import RecorderAgent
from backend.agents.therapist_agent import TherapistAgent
from backend.agents.analyst_agent import AnalystAgent
from backend.core.llm_service import get_llm_service

# ========== 辅助函数 ==========

async def generate_all_reports_async(user_id: str, session_id: str, dialogue_history: List[dict], db_factory=None):
    """
    异步生成所有报告（记录师、分析师、调理师）
    
    :param user_id: 用户 ID
    :param session_id: 会话 ID
    :param dialogue_history: 对话历史列表
    :param db_factory: 数据库工厂函数
    """
    db = None
    try:
        print(f"DEBUG: [异步任务] 开始生成报告，用户 ID: {user_id}, 会话 ID: {session_id}")
        
        # 创建新的数据库会话
        if db_factory:
            db = next(db_factory())
        else:
            from backend.core.database import SessionLocal
            db = SessionLocal()
        
        # 获取用户认知档案
        archive = db.query(UserArchiveDB).filter(
            UserArchiveDB.user_id == user_id,
            UserArchiveDB.session_id == session_id
        ).first()
        
        # 获取分析师建议
        from backend.core.database import AdviceDB
        advices = db.query(AdviceDB).filter(
            AdviceDB.user_id == user_id,
            AdviceDB.session_id == session_id
        ).order_by(AdviceDB.created_at.asc()).all()
        
        # 准备档案数据
        archive_data = archive.archive_json if archive else {}
        
        # 准备建议数据
        advice_list = []
        for advice in advices:
            if advice.advice_json:
                advice_list.append(advice.advice_json)
        
        # 调用三个智能体分别生成报告
        llm_service = await get_llm_service()
        
        # 初始化三个智能体
        recorder_agent = get_recorder_agent()
        recorder_agent.llm_service = llm_service
        
        analyst_agent = get_analyst_agent()
        analyst_agent.llm_service = llm_service
        
        therapist_agent = get_therapist_agent()
        therapist_agent.llm_service = llm_service
        
        # 步骤 1: 记录师最终确定记录报告（处理剩余未分析的对话）
        print(f"DEBUG: [异步任务] 调用记录师最终确定记录报告")
        
        # 更新状态：记录报告生成中
        existing_report = db.query(SessionReportDB).filter(
            SessionReportDB.user_id == user_id,
            SessionReportDB.session_id == session_id
        ).first()
        
        if existing_report:
            existing_report.record_status = 'generating'
            existing_report.updated_at = datetime.utcnow()
            db.commit()
        
        record_report = await recorder_agent.finalize_record_report(user_id, session_id)
        
        # 更新状态：记录报告完成
        existing_report.record_status = 'completed'
        existing_report.updated_at = datetime.utcnow()
        db.commit()
        print(f"DEBUG: [异步任务] 记录报告生成完成")
        
        # 步骤 2: 从 dialogues 中提取四维数据
        print(f"DEBUG: [异步任务] 从 dialogues 中提取四维数据")
        four_dim_data = extract_four_dim_data_from_dialogues(dialogue_history)
        
        # 步骤 3: 从已保存的实时分析数据生成分析报告
        print(f"DEBUG: [异步任务] 从实时分析数据生成分析报告")
        
        # 更新状态：分析报告生成中
        existing_report.analysis_status = 'generating'
        existing_report.updated_at = datetime.utcnow()
        db.commit()
        
        # 获取聚合的实时分析洞察
        aggregated_insights = analyst_agent.repository.aggregate_session_insights(user_id, session_id)
        
        if aggregated_insights:
            # 使用已保存的分析数据构建报告
            print(f"DEBUG: [异步任务] 使用已保存的实时分析数据，洞察数量：{len(aggregated_insights.get('common_automatic_thoughts', []))}")
            
            # 构建分析报告
            analysis_report = {
                "four_dim_summary": {
                    "intensity_values": four_dim_data.get("intensity_values", []),
                    "hedonic_distribution": four_dim_data.get("hedonic_values", []),
                    "tension_distribution": four_dim_data.get("tension_values", []),
                    "complexity_analysis": four_dim_data.get("complexity_values", {})
                },
                "emotional_timeline": {
                    "timestamps": [item.get("timestamp", "") for item in four_dim_data.get("intensity_values", [])],
                    "intensity": [item.get("value", 0) for item in four_dim_data.get("intensity_values", [])],
                    "hedonic": four_dim_data.get("hedonic_values", []),
                    "tension": four_dim_data.get("tension_values", []),
                    "complexity": four_dim_data.get("complexity_values", {})
                },
                "cognitive_analysis": {
                    "mappings": aggregated_insights.get("cognitive_mappings", []),
                    "common_automatic_thoughts": aggregated_insights.get("common_automatic_thoughts", []),
                    "thinking_traps": aggregated_insights.get("thinking_traps", []),
                    "core_beliefs": aggregated_insights.get("core_beliefs", [])
                },
                "tcm_analysis": aggregated_insights.get("tcm_analysis", {
                    "dominant_emotion": "",
                    "related_organs": [],
                    "qi_dynamics": "",
                    "tcm_interpretation": ""
                }),
                "causes": aggregated_insights.get("causes", {
                    "cbt_perspective": "",
                    "tcm_perspective": ""
                }),
                "trends": aggregated_insights.get("trends", "")
            }
            
            # 如果实时数据不完整，使用 LLM 补充
            if not analysis_report["cognitive_analysis"]["mappings"] or not analysis_report["tcm_analysis"]["dominant_emotion"]:
                print(f"DEBUG: [异步任务] 实时分析数据不完整，使用 LLM 补充")
                analysis_report = await analyst_agent.generate_analysis_report_from_archive(
                    user_id, session_id, archive_data, four_dim_data, dialogue_history
                )
        else:
            # 没有实时数据，使用 LLM 生成完整报告
            print(f"DEBUG: [异步任务] 无实时分析数据，使用 LLM 生成完整报告")
            analysis_report = await analyst_agent.generate_analysis_report_from_archive(
                user_id, session_id, archive_data, four_dim_data, dialogue_history
            )
        
        # 更新状态：分析报告完成
        existing_report.analysis_status = 'completed'
        existing_report.updated_at = datetime.utcnow()
        db.commit()
        print(f"DEBUG: [异步任务] 分析报告生成完成")
        
        # 步骤 4: 调理师基于分析报告生成调理报告
        print(f"DEBUG: [异步任务] 调用调理师生成调理报告")
        
        # 更新状态：调理报告生成中
        existing_report.treatment_status = 'generating'
        existing_report.updated_at = datetime.utcnow()
        db.commit()
        
        treatment_report = await therapist_agent.generate_treatment_report(
            user_id, session_id, analysis_report
        )
        
        # 更新状态：调理报告完成
        existing_report.treatment_status = 'completed'
        existing_report.updated_at = datetime.utcnow()
        db.commit()
        print(f"DEBUG: [异步任务] 调理报告生成完成")
        
        # 保存到 session_reports 表
        # 先查询是否已存在
        existing_report = db.query(SessionReportDB).filter(
            SessionReportDB.user_id == user_id,
            SessionReportDB.session_id == session_id
        ).first()
        
        if existing_report:
            # 更新现有报告
            existing_report.record_report_json = record_report
            existing_report.analysis_report_json = analysis_report
            existing_report.treatment_report_json = treatment_report
            report_id = existing_report.id
            print(f"DEBUG: [异步任务] 更新现有报告，ID: {report_id}")
        else:
            # 创建新报告
            new_report = SessionReportDB(
                user_id=user_id,
                session_id=session_id,
                record_report_json=record_report,
                analysis_report_json=analysis_report,
                treatment_report_json=treatment_report
            )
            db.add(new_report)
            db.flush()  # 获取 ID
            report_id = new_report.id
            print(f"DEBUG: [异步任务] 创建新报告，ID: {report_id}")
        
        db.commit()
        
        # 标记 session_analysis_insights 为已迁移
        try:
            from backend.repositories.record_repository_new import RecordRepository
            repo = RecordRepository()
            repo.mark_insight_migrated(user_id, session_id)
            print(f"DEBUG: [异步任务] 已标记洞察为已迁移")
        except Exception as e:
            print(f"WARNING: [异步任务] 标记洞察迁移失败：{e}")
        
        print(f"DEBUG: [异步任务] 报告生成完成，用户 ID: {user_id}, 会话 ID: {session_id}, 报告 ID: {report_id}")
        
    except Exception as e:
        print(f"ERROR: [异步任务] 生成报告失败：{e}")
        import traceback
        traceback.print_exc()
        if db:
            db.rollback()
    finally:
        if db:
            db.close()

def extract_four_dim_data_from_dialogues(dialogues: List[dict]) -> dict:
    """
    从对话历史中提取四维数据
    
    :param dialogues: 对话历史列表，每个元素包含 four_dim 字段
    :return: 四维数据字典
    """
    intensity_values = []
    hedonic_stats = {"负性": 0, "中性": 0, "正性": 0}
    tension_stats = {"低": 0, "中": 0, "高": 0}
    complexity_values = {"type": "简单", "emotions": []}
    
    for dialogue in dialogues:
        four_dim = dialogue.get("four_dim", {})
        if not four_dim:
            continue
        
        # 强度值（带时间戳）
        intensity = four_dim.get("intensity")
        if intensity is not None:
            intensity_values.append({
                "value": float(intensity),
                "timestamp": dialogue.get("created_at", "")
            })
        
        # 快感度统计
        hedonic = four_dim.get("hedonic")
        if hedonic and hedonic in hedonic_stats:
            hedonic_stats[hedonic] += 1
        
        # 紧张度统计
        tension = four_dim.get("tension")
        if tension and tension in tension_stats:
            tension_stats[tension] += 1
        
        # 复杂度（直接使用已保存的分析结果）
        complexity = four_dim.get("complexity")
        if complexity:
            if isinstance(complexity, dict):
                complexity_values = complexity
            elif isinstance(complexity, str):
                try:
                    complexity_values = json.loads(complexity)
                except:
                    pass
    
    # 转换为前端需要的格式
    hedonic_values_formatted = [
        {"label": "负性", "value": hedonic_stats["负性"]},
        {"label": "中性", "value": hedonic_stats["中性"]},
        {"label": "正性", "value": hedonic_stats["正性"]}
    ]
    tension_values_formatted = [
        {"label": "低", "value": tension_stats["低"]},
        {"label": "中", "value": tension_stats["中"]},
        {"label": "高", "value": tension_stats["高"]}
    ]
    
    return {
        "intensity_values": intensity_values,
        "hedonic_values": hedonic_values_formatted,
        "tension_values": tension_values_formatted,
        "complexity_values": complexity_values
    }

from backend.agents.recorder_agent import RecorderAgent
from backend.agents.therapist_agent import TherapistAgent
from backend.agents.analyst_agent import AnalystAgent
from backend.core.llm_service import get_llm_service
from backend.core.data_models import (
    RecordReportJSON,
    AnalysisReportJSON,
    TreatmentReportJSON
)

router = APIRouter(prefix="/api/v1/chat", tags=["chat"])

# 依赖注入获取数据库会话
def get_db():
    """获取数据库会话的依赖函数"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 初始化智能体（服务启动时立即加载）
print("正在初始化智能体...")
recorder_agent = RecorderAgent()
therapist_agent = TherapistAgent()
analyst_agent = AnalystAgent()
print("智能体初始化完成")

def get_recorder_agent():
    return recorder_agent

def get_therapist_agent():
    return therapist_agent

def get_analyst_agent():
    return analyst_agent

# 全局LLM服务实例
llm_service = None

# 发送消息接口
@router.post("/message", response_model=ChatMessageResponse)
async def send_message(
    message: ChatMessage,
    db: Session = Depends(get_db)
):
    """
    发送消息
    """
    # 检查用户是否存在
    try:
        # 检查用户是否存在
        user = db.query(UserDB).filter(UserDB.id == message.user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户不存在，请先登录"
            )
    except Exception as e:
        import traceback
        print(f"DEBUG: 用户检查异常: {e}")
        print(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"用户检查失败: {str(e)}"
        )
    
    # 获取LLM服务实例
    global llm_service
    if llm_service is None:
        llm_service = await get_llm_service()
    
    # 确保调理师智能体使用LLM服务
    if not therapist_agent.llm_service:
        therapist_agent.llm_service = llm_service
    
    # 确保分析师智能体使用LLM服务
    if not analyst_agent.llm_service:
        analyst_agent.llm_service = llm_service
    
    # 生成对话ID
    dialogue_id = f"dialogue_{uuid.uuid4().hex[:8]}"
    
    # 调用记录师智能体处理用户消息
    try:
        recorder_result = await get_recorder_agent().execute({
            "user_id": message.user_id,
            "session_id": message.session_id,
            "message": message.message
        })
        # 确保recorder_result是一个字典
        if not isinstance(recorder_result, dict):
            recorder_result = {}
    except Exception as e:
        # 记录师智能体执行失败，使用默认值
        recorder_result = {
            "intensity": 0.0,
            "hedonic": "中性",
            "tension": "低",
            "complexity": "简单",
            "is_valuable": False
        }
    
    # 注：用户消息已由记录师智能体保存，此处不再重复保存
    
    # 异步触发分析师（如果消息有价值）
    print(f"DEBUG: 消息是否有价值: {recorder_result.get('is_valuable', False)}")
    if recorder_result.get("is_valuable", False):
        print(f"DEBUG: 触发分析师智能体，用户ID: {message.user_id}, 会话ID: {message.session_id}")
        try:
            # 确保分析师智能体使用LLM服务
            analyst = get_analyst_agent()
            if not analyst.llm_service:
                print(f"DEBUG: 初始化分析师智能体LLM服务")
                analyst.llm_service = llm_service
            
            print(f"DEBUG: 调用分析师智能体 execute 方法")
            # 注意：不传递 dialogue_id，因为 advices.dialogue_id 是整数类型，而这里生成的是字符串
            analyst_result = await analyst.execute({
                "user_id": message.user_id,
                "session_id": message.session_id,
                # "dialogue_id": dialogue_id,  # 注释掉，避免类型错误
                "user_input": message.message,
                "four_dim": {
                    "intensity": recorder_result.get("intensity"),
                    "hedonic": recorder_result.get("hedonic"),
                    "tension": recorder_result.get("tension"),
                    "complexity": recorder_result.get("complexity")
                }
            })
            print(f"DEBUG: 分析师智能体执行结果: {analyst_result}")
        except Exception as e:
            # 分析师智能体执行失败，打印错误信息
            print(f"ERROR: 分析师智能体执行失败: {e}")
            import traceback
            traceback.print_exc()
            pass
    
    # 调用调理师智能体生成回复
    try:
        therapist_result = await get_therapist_agent().execute({
            "user_id": message.user_id,
            "session_id": message.session_id,
            "user_input": message.message
        })
        
        # 确保therapist_result是一个字典
        if not isinstance(therapist_result, dict):
            therapist_result = {}
    except Exception as e:
        # 调理师智能体执行失败，使用默认回复
        therapist_result = {"data": {"reply": "我理解您的感受。"}}
    
    # 生成助手回复的对话ID
    assistant_dialogue_id = f"dialogue_{uuid.uuid4().hex[:8]}"
    
    # 获取助手回复，从data字段中获取
    assistant_reply = therapist_result.get("data", {}).get("reply", "我理解您的感受。")
    
    # 注：助手回复已由调理师智能体保存，此处不再重复保存
    
    # 构建响应
    response = ChatMessageResponse(
        reply=assistant_reply,
        four_dim={
            "intensity": recorder_result.get("intensity", 0.0),
            "hedonic": recorder_result.get("hedonic", "中性"),
            "tension": recorder_result.get("tension", "低"),
            "complexity": recorder_result.get("complexity", "简单")
        },
        is_valuable=recorder_result.get("is_valuable", False)
    )
    
    return response

# 创建新会话接口
@router.post("/new-session", response_model=NewSessionResponse)
async def create_new_session(
    session_data: dict,
    db: Session = Depends(get_db)
):
    """
    创建新会话
    """
    # 从JSON数据中获取user_id
    user_id = session_data.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="缺少用户ID"
        )
    
    # 检查用户是否存在
    try:
        # 检查用户是否存在
        user = db.query(UserDB).filter(UserDB.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户不存在，请先登录"
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="用户检查失败"
        )
    
    # 生成会话ID和标题
    session_id = f"session_{uuid.uuid4().hex[:8]}"
    session_title = f"会话_{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    
    # 验证会话ID和标题是否成功创建
    if not session_id or not session_title:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="会话创建失败，无法生成会话ID或标题"
        )
    
    # 创建对话会话记录
    new_chat_session = ChatSessionDB(
        session_id=session_id,
        user_id=user_id,
        title=session_title
    )
    db.add(new_chat_session)
    db.commit()
    
    # 构建响应
    response = NewSessionResponse(
        session_id=session_id,
        session_title=session_title,
        message="会话创建成功"
    )
    
    return response

# 结束会话接口
@router.post("/end-session")
async def end_session(
    session_data: dict,
    db: Session = Depends(get_db)
):
    """
    结束会话并异步生成会话报告
    立即响应，后台异步触发三个报告生成
    """
    # 从 JSON 数据中获取 user_id 和 session_id
    user_id = session_data.get("user_id")
    session_id = session_data.get("session_id")
    
    if not user_id or not session_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="缺少用户 ID 或会话 ID"
        )
    
    # 检查用户是否存在
    user = db.query(UserDB).filter(UserDB.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在，请先登录"
        )
    
    # 检查会话是否存在（从 chat_sessions 表查询）
    chat_session = db.query(ChatSessionDB).filter(
        ChatSessionDB.user_id == user_id,
        ChatSessionDB.session_id == session_id
    ).first()
    
    if not chat_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="会话不存在"
        )
    
    # 获取会话的对话记录
    dialogues = db.query(DialogueDB).filter(
        DialogueDB.user_id == user_id,
        DialogueDB.session_id == session_id
    ).order_by(DialogueDB.created_at.asc()).all()
    
    # 步骤 1: 确保对话已保存（记录师应该已经在每轮对话中保存了）
    print(f"DEBUG: 结束会话，对话数量：{len(dialogues)}")
    
    # 步骤 1.5: 先在 session_reports 表创建一条初始记录（用于状态轮询）
    existing_report = db.query(SessionReportDB).filter(
        SessionReportDB.user_id == user_id,
        SessionReportDB.session_id == session_id
    ).first()
    
    if not existing_report:
        # 创建初始记录，状态都为 pending
        initial_report = SessionReportDB(
            user_id=user_id,
            session_id=session_id,
            record_status='pending',
            analysis_status='pending',
            treatment_status='pending'
        )
        db.add(initial_report)
        db.commit()
        print(f"DEBUG: 已创建初始报告记录，ID: {initial_report.id}")
    
    # 步骤 2: 立即响应
    response_data = {
        "message": "结束会话已完成，正在生成报告中",
        "code": 200,
        "session_id": session_id,
        "dialogue_count": len(dialogues),
        "status": {
            "record_report": "pending",
            "analysis_report": "pending",
            "treatment_report": "pending"
        }
    }
    
    # 步骤 3: 异步触发报告生成
    if dialogues:
        # 构建对话历史（用于异步任务）
        dialogue_history = []
        for d in dialogues:
            dialogue_history.append({
                "role": d.role,
                "content": d.content,
                "created_at": d.created_at.isoformat() if d.created_at else None,
                "four_dim": {
                    "intensity": d.four_dim_intensity,
                    "hedonic": d.four_dim_hedonic,
                    "tension": d.four_dim_tension,
                    "complexity": d.four_dim_complexity
                } if d.four_dim_intensity else None
            })
        
        # 异步启动报告生成任务
        asyncio.create_task(
            generate_all_reports_async(user_id, session_id, dialogue_history, db_factory=get_db)
        )
        print(f"DEBUG: 已启动异步报告生成任务，用户 ID: {user_id}, 会话 ID: {session_id}")
    
    return response_data

# 查询报告状态接口
@router.get("/report-status/{session_id}")
async def get_report_status(
    session_id: str,
    db: Session = Depends(get_db)
):
    """
    查询会话报告的生成状态
    """
    # 查询会话报告
    report = db.query(SessionReportDB).filter(
        SessionReportDB.session_id == session_id
    ).first()
    
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="会话报告不存在"
        )
    
    # 返回状态信息
    return {
        "session_id": session_id,
        "status": {
            "record_report": report.record_status or 'pending',
            "analysis_report": report.analysis_status or 'pending',
            "treatment_report": report.treatment_status or 'pending'
        },
        "status_updated_at": report.updated_at.isoformat() if report.updated_at else None,
        "reports_available": {
            "record_report": report.record_report_json is not None,
            "analysis_report": report.analysis_report_json is not None,
            "treatment_report": report.treatment_report_json is not None
        }
    }

# 获取用户会话列表接口
@router.post("/sessions", response_model=SessionList)
async def get_user_sessions(
    user_data: dict,
    db: Session = Depends(get_db)
):
    """
    获取用户会话列表
    """
    # 打印传递的参数
    print(f"DEBUG: /chat/sessions 接口接收到的参数: {user_data}")
    
    # 从JSON数据中获取user_id
    user_id = user_data.get("user_id")
    print(f"DEBUG: 提取的用户ID: {user_id}")
    
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="缺少用户ID"
        )
    
    # 检查用户是否存在（直接使用user_id）
    user = db.query(UserDB).filter(UserDB.id == user_id).first()
    if not user:
        # 如果不存在，尝试将user_id作为字符串查询
        user = db.query(UserDB).filter(UserDB.username == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户不存在，请先登录"
            )

    # 从UserArchiveDB中获取用户的所有会话
    archives = db.query(UserArchiveDB).filter(
        UserArchiveDB.user_id == user.id
    ).order_by(UserArchiveDB.created_at.desc()).all()
    
    # 构建会话列表
    sessions = []
    for archive in archives:
        session_id = archive.session_id
        # 获取每个会话的最后一条消息
        last_dialogue = db.query(DialogueDB).filter(
            DialogueDB.user_id == user.id,
            DialogueDB.session_id == session_id
        ).order_by(DialogueDB.created_at.desc()).first()
        
        # 初始化默认值
        session_title = f"会话_{archive.created_at.strftime('%Y-%m-%d %H:%M:%S')}"
        thinking_traps = []
        emotional_response = ""
        
        # 处理档案数据
        if archive and archive.archive_json:
            try:
                # 直接使用archive_json字典，不需要再次解析
                archive_data = archive.archive_json
                
                # 获取标题
                if "title" in archive_data:
                    session_title = archive_data["title"]
                
                # 获取思维陷阱
                if "cognitive_patterns" in archive_data and "thinking_traps" in archive_data["cognitive_patterns"]:
                    thinking_traps = archive_data["cognitive_patterns"]["thinking_traps"]
                
                # 获取情绪反应
                if "situations" in archive_data and len(archive_data["situations"]) > 0:
                    emotional_response = archive_data["situations"][0].get("emotional_response", emotional_response)
            except Exception as e:
                print(f"处理档案数据失败: {e}")
                pass
        
        # 构建会话信息
        session_info = SessionInfo(
            session_id=session_id,
            user_id=user.id,  # 添加user_id字段
            title=session_title,
            last_message=last_dialogue.content if last_dialogue else "",
            created_at=archive.created_at,
            updated_at=archive.updated_at if hasattr(archive, 'updated_at') else archive.created_at,  # 添加updated_at字段
            thinking_traps=thinking_traps,
            emotional_response=emotional_response
        )
        sessions.append(session_info)
    
    # 按创建时间降序排序
    sessions.sort(key=lambda x: x.created_at, reverse=True)
    
    # 构建响应
    response = SessionList(sessions=sessions)
    
    return response

# 获取会话对话记录接口
@router.post("/history", response_model=ChatHistoryResponse)
async def get_chat_history(
    history_data: dict,
    db: Session = Depends(get_db)
):
    """
    获取会话对话记录
    """
    # 从JSON数据中获取参数
    user_id = history_data.get("user_id")      
    session_id = history_data.get("session_id")
    
    # 处理limit参数
    try:
        limit = int(history_data.get("limit", 50))
        # 设置合理的最大值
        max_limit = 100
        if limit > max_limit:
            limit = max_limit
    except (ValueError, TypeError):
        # 如果转换失败，使用默认值
        limit = 50

    if not user_id or not session_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="缺少用户ID或会话ID"
        )

    # 检查用户是否存在
    user = db.query(UserDB).filter(UserDB.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在，请先登录"
        )

    # 直接查询对话记录，根据会话ID和用户ID
    # 注意：这里直接使用user_id字符串进行匹配，因为数据库中存储的可能是字符串格式
    dialogues = db.query(DialogueDB).filter(
        DialogueDB.session_id == session_id
    ).order_by(DialogueDB.created_at.asc()).limit(limit).all()
    
    # 转换为响应模型
    dialogue_list = []
    for dialogue in dialogues:
        try:
            dialogue_item = Dialogue(
                id=str(dialogue.id),  # 转换为字符串
                user_id=user_id,  # 直接使用传入的user_id
                session_id=dialogue.session_id,
                role=dialogue.role,
                content=dialogue.content,
                four_dim_intensity=dialogue.four_dim_intensity,
                four_dim_hedonic=dialogue.four_dim_hedonic,
                four_dim_tension=dialogue.four_dim_tension,
                four_dim_complexity=dialogue.four_dim_complexity,
                is_valuable=dialogue.is_valuable,
                created_at=dialogue.created_at
            )
            dialogue_list.append(dialogue_item)
        except Exception as e:
            # 跳过有问题的对话
            continue

    # 构建响应
    response = ChatHistoryResponse(dialogues=dialogue_list)
    return response

# 编辑会话标题接口
@router.post("/edit-session-title")
async def edit_session_title(
    title_data: dict,
    db: Session = Depends(get_db)
):
    """
    编辑会话标题
    """
    # 从JSON数据中获取参数
    user_id = title_data.get("user_id")
    session_id = title_data.get("session_id")
    new_title = title_data.get("title")
    
    if not user_id or not session_id or not new_title:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="缺少用户ID、会话ID或新标题"
        )
    
    # 检查用户是否存在
    user = db.query(UserDB).filter(UserDB.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在，请先登录"
        )
    
    # 检查会话是否存在
    chat_session = db.query(ChatSessionDB).filter(
        ChatSessionDB.session_id == session_id,
        ChatSessionDB.user_id == user_id
    ).first()
    if not chat_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="会话不存在"
        )
    
    # 更新会话标题
    chat_session.title = new_title
    chat_session.updated_at = datetime.utcnow()
    db.commit()
    
    # 同时更新用户认知档案中的标题（如果存在）
    archive = db.query(UserArchiveDB).filter(
        UserArchiveDB.user_id == user_id,
        UserArchiveDB.session_id == session_id
    ).first()
    if archive and archive.archive_json:
        try:
            # 直接使用archive_json字典，不需要再次解析
            archive_data = archive.archive_json
            archive_data["title"] = new_title
            archive_data["updated_at"] = datetime.utcnow().isoformat()
            archive.archive_json = archive_data
            archive.updated_at = datetime.utcnow()
            db.commit()
        except Exception as e:
            # 忽略错误，继续执行
            pass
    
    return {"message": "会话标题更新成功", "session_id": session_id, "new_title": new_title}



# 删除会话接口
@router.post("/delete-session")
async def delete_session(
    session_data: dict,
    db: Session = Depends(get_db)
):
    """
    删除会话及其相关数据
    """
    # 从JSON数据中获取参数
    user_id = session_data.get("user_id")
    session_id = session_data.get("session_id")
    
    if not user_id or not session_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="缺少用户ID或会话ID"
        )
    
    # 检查用户是否存在
    user = db.query(UserDB).filter(UserDB.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在，请先登录"
        )
    
    # 检查会话是否存在，且属于该用户
    chat_session = db.query(ChatSessionDB).filter(
        ChatSessionDB.session_id == session_id,
        ChatSessionDB.user_id == user_id
    ).first()
    if not chat_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="会话不存在或不属于该用户"
        )
    
    # 导入需要的模型
    from backend.core.database import AdviceDB, SessionReportDB
    
    # 删除关联的建议记录
    advice_records = db.query(AdviceDB).filter(
        AdviceDB.session_id == session_id,
        AdviceDB.user_id == user_id
    ).all()
    for advice in advice_records:
        db.delete(advice)
    
    # 删除关联的用户认知档案
    archive = db.query(UserArchiveDB).filter(
        UserArchiveDB.session_id == session_id,
        UserArchiveDB.user_id == user_id
    ).first()
    if archive:
        db.delete(archive)
    
    # 删除关联的会话报告
    session_reports = db.query(SessionReportDB).filter(
        SessionReportDB.session_id == session_id,
        SessionReportDB.user_id == user_id
    ).all()
    for report in session_reports:
        db.delete(report)
    
    # 删除关联的对话记录
    dialogues = db.query(DialogueDB).filter(
        DialogueDB.session_id == session_id,
        DialogueDB.user_id == user_id
    ).all()
    for dialogue in dialogues:
        db.delete(dialogue)
    
    # 删除会话本身
    db.delete(chat_session)
    db.commit()
    
    return {"message": "会话删除成功", "session_id": session_id}
