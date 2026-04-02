"""
异步报告生成模块
实现增量保存和失败重试机制
"""
import asyncio
from typing import Dict, Any
from sqlalchemy.orm import Session

from backend.core.database import DBConfig, SessionReportDB
from backend.api.v1.chat_endpoints import get_analyst_agent, get_therapist_agent, extract_four_dim_data_from_dialogues


async def generate_reports_async(
    db_factory,
    report_id: int,
    user_id: str,
    session_id: str,
    dialogue_history: list,
    archive_data: dict
):
    """
    异步生成分析报告和调理报告（带重试机制）
    
    流程：
    1. 生成分析报告（最多重试 3 次）
    2. 如果分析报告成功，生成调理报告
    3. 更新数据库状态
    """
    
    db = next(db_factory())
    try:
        # ========== 生成分析报告（带重试） ==========
        analysis_report = None
        max_retries = 3
        
        for retry in range(max_retries):
            try:
                # 更新状态为"生成中"
                db_report = db.query(SessionReportDB).filter(
                    SessionReportDB.id == report_id
                ).first()
                if not db_report:
                    print(f"ERROR: 报告记录不存在 (report_id={report_id})")
                    return
                
                db_report.analysis_status = "generating"
                db_report.analysis_retry_count = retry + 1
                db.commit()
                
                print(f"DEBUG: 第{retry+1}次尝试生成分析报告...")
                
                # 调用分析师智能体
                analyst_agent = get_analyst_agent()
                
                # 从 dialogues 中提取四维数据（不再调用 update_four_dim_data）
                four_dim_data = extract_four_dim_data_from_dialogues(dialogue_history)
                
                # 生成分析报告
                analysis_report = await analyst_agent.generate_analysis_report_from_archive(
                    user_id, session_id, archive_data, four_dim_data, dialogue_history
                )
                
                # 生成成功，跳出重试循环
                if analysis_report and len(analysis_report) > 0:
                    print(f"DEBUG: 分析报告生成成功")
                    break
                else:
                    print(f"DEBUG: 分析报告为空，准备重试")
                
            except Exception as e:
                print(f"DEBUG: 第{retry+1}次生成分析报告失败：{e}")
                import traceback
                traceback.print_exc()
                if retry < max_retries - 1:
                    await asyncio.sleep(2 ** retry)  # 指数退避：2 秒，4 秒
                db.rollback()
        
        # 保存分析报告到数据库
        if analysis_report:
            db_report = db.query(SessionReportDB).filter(
                SessionReportDB.id == report_id
            ).first()
            db_report.analysis_report_json = analysis_report
            db_report.analysis_status = "completed"
            db.commit()
            
            # ========== 生成调理报告（依赖分析报告） ==========
            try:
                print("DEBUG: 开始生成调理报告...")
                therapist_agent = get_therapist_agent()
                treatment_report = await therapist_agent.generate_treatment_report(
                    user_id, session_id, analysis_report
                )
                
                # 保存调理报告
                db_report.treatment_report_json = treatment_report
                db_report.treatment_status = "completed"
                db.commit()
                print("DEBUG: 调理报告生成成功")
                
            except Exception as e:
                print(f"DEBUG: 调理报告生成失败：{e}")
                import traceback
                traceback.print_exc()
                db_report.treatment_status = "failed"
                db.commit()
        else:
            # 分析报告也失败了
            db_report = db.query(SessionReportDB).filter(
                SessionReportDB.id == report_id
            ).first()
            db_report.analysis_status = "failed"
            db.commit()
            print("DEBUG: 分析报告生成失败，已达最大重试次数")
            
    except Exception as e:
        print(f"ERROR: 异步生成报告异常：{e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()
