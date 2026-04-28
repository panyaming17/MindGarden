"""
记录存储库 (Record Repository)
职责：封装所有与记录和报告相关的数据库操作，提供数据访问接口。
"""
from typing import Dict, Any, Optional, List
from datetime import datetime
from sqlalchemy.orm import Session

from backend.core.database import DBConfig, StructuredRecordDB, DiagnosisReportDB, RecordReportDB, AnalysisReportDB, SuggestionReportDB
from backend.core.data_models import StructuredRecord, DiagnosisReport, RecordReport, AnalysisReport, SuggestionReport, DailySuggestion


class RecordRepository:
    """记录存储库 - 负责数据持久化操作"""
    
    def __init__(self):
        # 获取数据库会话工厂
        self.db_factory = DBConfig.get_db
    
    async def save_record(self, record: StructuredRecord) -> str:
        """保存结构化记录到数据库"""
        db = next(self.db_factory())  # 获取数据库会话
        try:
            # 将StructuredRecord转换为StructuredRecordDB
            db_record = StructuredRecordDB(
                id=record.record_id,
                user_id=record.user_id,
                raw_text=record.raw_text,
                situation=record.situation,
                automatic_thoughts=record.automatic_thoughts,
                emotions=record.emotions,
                physical_sensations=record.physical_sensations,
                created_at=record.created_at
            )
            
            # 添加到会话并提交
            db.add(db_record)
            db.commit()
            db.refresh(db_record)
            
            return db_record.id
        except Exception as e:
            db.rollback()  # 出错时回滚
            raise e
        finally:
            db.close()  # 关闭会话
    
    async def get_record_by_id(self, record_id: str) -> Optional[StructuredRecord]:
        """根据记录ID获取结构化记录"""
        db = next(self.db_factory())
        try:
            # 查找记录
            db_record = db.query(StructuredRecordDB).filter(
                StructuredRecordDB.id == record_id
            ).first()
            
            if db_record:
                # 转换为数据模型
                return StructuredRecord(
                    record_id=db_record.id,
                    user_id=db_record.user_id,
                    raw_text=db_record.raw_text or "",
                    situation=db_record.situation or "",
                    automatic_thoughts=db_record.automatic_thoughts or [],
                    emotions=db_record.emotions or [],
                    physical_sensations=db_record.physical_sensations or [],
                    created_at=db_record.created_at
                )
            return None
        except Exception as e:
            raise e
        finally:
            db.close()
    
    async def save_diagnosis_report(self, report: DiagnosisReport) -> str:
        """保存诊断报告到数据库"""
        db = next(self.db_factory())
        try:
            # 将DiagnosisReport转换为DiagnosisReportDB
            db_report = DiagnosisReportDB(
                id=report.id,
                record_id=report.record_id,
                user_id=report.user_id,
                cbt_analysis=report.cbt_analysis,
                tcm_analysis=report.tcm_analysis,
                comprehensive_framework=report.summary,  # 映射到数据库字段
                confidence_score=report.confidence_score,
                analysis_duration=report.analysis_time,  # 映射到数据库字段
                created_at=report.created_at or datetime.now()
            )
            
            # 添加到会话并提交
            db.add(db_report)
            db.commit()
            db.refresh(db_report)
            
            return db_report.id
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()
    
    async def get_report_by_id(self, report_id: str) -> Optional[DiagnosisReport]:
        """根据报告ID获取诊断报告"""
        db = next(self.db_factory())
        try:
            # 查找报告
            db_report = db.query(DiagnosisReportDB).filter(
                DiagnosisReportDB.id == report_id
            ).first()
            
            if db_report:
                # 转换为数据模型
                return DiagnosisReport(
                    id=db_report.id,
                    record_id=db_report.record_id,
                    user_id=db_report.user_id,
                    cbt_analysis=db_report.cbt_analysis or {},
                    tcm_analysis=db_report.tcm_analysis or {},
                    summary=db_report.comprehensive_framework or "",  # 映射到数据模型字段
                    recommendations=[],  # 数据库中没有这个字段，暂时返回空列表
                    confidence_score=db_report.confidence_score or 0.0,
                    analysis_time=db_report.analysis_duration or 0.0,  # 映射到数据模型字段
                    created_at=db_report.created_at
                )
            return None
        except Exception as e:
            raise e
        finally:
            db.close()
    
    async def get_reports_by_user_id(self, user_id: str) -> List[DiagnosisReport]:
        """根据用户ID获取所有诊断报告"""
        db = next(self.db_factory())
        try:
            # 查找用户的所有报告
            db_reports = db.query(DiagnosisReportDB).filter(
                DiagnosisReportDB.user_id == user_id
            ).all()
            
            # 转换为数据模型列表
            reports = []
            for db_report in db_reports:
                report = DiagnosisReport(
                    id=db_report.id,
                    record_id=db_report.record_id,
                    user_id=db_report.user_id,
                    cbt_analysis=db_report.cbt_analysis or {},
                    tcm_analysis=db_report.tcm_analysis or {},
                    summary=db_report.comprehensive_framework or "",
                    recommendations=[],  # 数据库中没有这个字段，暂时返回空列表
                    confidence_score=db_report.confidence_score or 0.0,
                    analysis_time=db_report.analysis_duration or 0.0,
                    created_at=db_report.created_at
                )
                reports.append(report)
            
            return reports
        except Exception as e:
            raise e
        finally:
            db.close()
    
    async def get_record_report_by_id(self, record_id: str) -> Optional[RecordReport]:
        """根据记录ID获取RecordReport"""
        db = next(self.db_factory())
        try:
            # 查找记录
            db_record = db.query(RecordReportDB).filter(
                RecordReportDB.record_id == record_id
            ).first()
            
            if db_record:
                # 转换为数据模型
                return RecordReport(
                    record_id=db_record.record_id,
                    session_id=db_record.session_id,
                    user_id=db_record.user_id,
                    timestamp=db_record.timestamp,
                    duration=db_record.duration,
                    conversation_log=db_record.conversation_log or [],
                    situation=db_record.situation or "",
                    automatic_thoughts=db_record.automatic_thoughts or [],
                    emotions=db_record.emotions or [],
                    physical_sensations=db_record.physical_sensations or [],
                    summary=db_record.summary or ""
                )
            return None
        except Exception as e:
            raise e
        finally:
            db.close()
    
    async def save_analysis_report(self, report: AnalysisReport) -> str:
        """保存分析报告到数据库"""
        db = next(self.db_factory())
        try:
            # 将AnalysisReport转换为AnalysisReportDB
            db_report = AnalysisReportDB(
                report_id=report.report_id,
                record_id=report.record_id,
                user_id=report.user_id,
                timestamp=report.timestamp,
                analysis_duration=report.analysis_duration,
                confidence_score=report.confidence_score,
                cbt_analysis=report.cbt_analysis.dict(),
                tcm_analysis=report.tcm_analysis.dict(),
                integrated_framework=report.integrated_framework,
                priority=report.priority
            )
            
            # 添加到会话并提交
            db.add(db_report)
            db.commit()
            db.refresh(db_report)
            
            return db_report.report_id
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()
    
    async def get_analysis_report_by_id(self, report_id: str) -> Optional[AnalysisReport]:
        """根据报告ID获取分析报告"""
        db = next(self.db_factory())
        try:
            # 查找报告
            db_report = db.query(AnalysisReportDB).filter(
                AnalysisReportDB.report_id == report_id
            ).first()
            
            if db_report:
                # 转换为数据模型
                from backend.core.data_models import CBTAnalysis, TCMAnalysis, DistortionItem, DominantEmotion, SecondaryEmotion
                
                return AnalysisReport(
                    report_id=db_report.report_id,
                    record_id=db_report.record_id,
                    user_id=db_report.user_id,
                    timestamp=db_report.timestamp,
                    analysis_duration=db_report.analysis_duration,
                    confidence_score=db_report.confidence_score,
                    cbt_analysis=CBTAnalysis(**db_report.cbt_analysis),
                    tcm_analysis=TCMAnalysis(**db_report.tcm_analysis),
                    integrated_framework=db_report.integrated_framework,
                    priority=db_report.priority
                )
            return None
        except Exception as e:
            raise e
        finally:
            db.close()
    
    async def get_analysis_reports_by_user_id(self, user_id: str) -> List[AnalysisReport]:
        """根据用户ID获取所有分析报告"""
        db = next(self.db_factory())
        try:
            # 查找用户的所有报告
            db_reports = db.query(AnalysisReportDB).filter(
                AnalysisReportDB.user_id == user_id
            ).all()
            
            # 转换为数据模型列表
            reports = []
            from backend.core.data_models import CBTAnalysis, TCMAnalysis, DistortionItem, DominantEmotion, SecondaryEmotion
            
            for db_report in db_reports:
                report = AnalysisReport(
                    report_id=db_report.report_id,
                    record_id=db_report.record_id,
                    user_id=db_report.user_id,
                    timestamp=db_report.timestamp,
                    analysis_duration=db_report.analysis_duration,
                    confidence_score=db_report.confidence_score,
                    cbt_analysis=CBTAnalysis(**db_report.cbt_analysis),
                    tcm_analysis=TCMAnalysis(**db_report.tcm_analysis),
                    integrated_framework=db_report.integrated_framework,
                    priority=db_report.priority
                )
                reports.append(report)
            
            return reports
        except Exception as e:
            raise e
        finally:
            db.close()
    
    async def get_analysis_report_by_record_id(self, record_id: str) -> Optional[AnalysisReport]:
        """根据记录ID获取分析报告"""
        db = next(self.db_factory())
        try:
            # 查找报告
            db_report = db.query(AnalysisReportDB).filter(
                AnalysisReportDB.record_id == record_id
            ).first()
            
            if db_report:
                # 转换为数据模型
                from backend.core.data_models import CBTAnalysis, TCMAnalysis, DistortionItem, DominantEmotion, SecondaryEmotion
                
                return AnalysisReport(
                    report_id=db_report.report_id,
                    record_id=db_report.record_id,
                    user_id=db_report.user_id,
                    timestamp=db_report.timestamp,
                    analysis_duration=db_report.analysis_duration,
                    confidence_score=db_report.confidence_score,
                    cbt_analysis=CBTAnalysis(**db_report.cbt_analysis),
                    tcm_analysis=TCMAnalysis(**db_report.tcm_analysis),
                    integrated_framework=db_report.integrated_framework,
                    priority=db_report.priority
                )
            return None
        except Exception as e:
            raise e
        finally:
            db.close()
    
    async def save_suggestion_report(self, report: SuggestionReport) -> str:
        """保存建议报告到数据库"""
        db = next(self.db_factory())
        try:
            # 将SuggestionReport转换为SuggestionReportDB
            db_report = SuggestionReportDB(
                suggestion_id=report.suggestion_id,
                report_id=report.report_id,
                user_id=report.user_id,
                timestamp=report.timestamp,
                target_issues=report.target_issues,
                core_principles=report.core_principles,
                daily_suggestions=[item.dict() for item in report.daily_suggestions],
                emergency_tips=report.emergency_tips,
                encouragement=report.encouragement,
                plan_summary=report.plan_summary
            )
            
            # 添加到会话并提交
            db.add(db_report)
            db.commit()
            db.refresh(db_report)
            
            return db_report.suggestion_id
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()
    
    async def get_suggestion_report_by_id(self, suggestion_id: str) -> Optional[SuggestionReport]:
        """根据建议报告ID获取建议报告"""
        db = next(self.db_factory())
        try:
            # 查找报告
            db_report = db.query(SuggestionReportDB).filter(
                SuggestionReportDB.suggestion_id == suggestion_id
            ).first()
            
            if db_report:
                # 转换为数据模型
                return SuggestionReport(
                    suggestion_id=db_report.suggestion_id,
                    report_id=db_report.report_id,
                    user_id=db_report.user_id,
                    timestamp=db_report.timestamp,
                    target_issues=db_report.target_issues or [],
                    core_principles=db_report.core_principles or [],
                    daily_suggestions=[
                        DailySuggestion(**item) for item in db_report.daily_suggestions
                    ] if db_report.daily_suggestions else [],
                    emergency_tips=db_report.emergency_tips,
                    encouragement=db_report.encouragement or "",
                    plan_summary=db_report.plan_summary or ""
                )
            return None
        except Exception as e:
            raise e
        finally:
            db.close()
    
    async def get_suggestion_reports_by_user_id(self, user_id: str) -> List[SuggestionReport]:
        """根据用户ID获取所有建议报告"""
        db = next(self.db_factory())
        try:
            # 查找用户的所有报告
            db_reports = db.query(SuggestionReportDB).filter(
                SuggestionReportDB.user_id == user_id
            ).all()
            
            # 转换为数据模型列表
            reports = []
            for db_report in db_reports:
                report = SuggestionReport(
                    suggestion_id=db_report.suggestion_id,
                    report_id=db_report.report_id,
                    user_id=db_report.user_id,
                    timestamp=db_report.timestamp,
                    target_issues=db_report.target_issues or [],
                    core_principles=db_report.core_principles or [],
                    daily_suggestions=[
                        DailySuggestion(**item) for item in db_report.daily_suggestions
                    ] if db_report.daily_suggestions else [],
                    emergency_tips=db_report.emergency_tips,
                    encouragement=db_report.encouragement or "",
                    plan_summary=db_report.plan_summary or ""
                )
                reports.append(report)
            
            return reports
        except Exception as e:
            raise e
        finally:
            db.close()
    
    async def get_suggestion_report_by_report_id(self, report_id: str) -> Optional[SuggestionReport]:
        """根据分析报告ID获取建议报告"""
        db = next(self.db_factory())
        try:
            # 查找报告
            db_report = db.query(SuggestionReportDB).filter(
                SuggestionReportDB.report_id == report_id
            ).first()
            
            if db_report:
                # 转换为数据模型
                return SuggestionReport(
                    suggestion_id=db_report.suggestion_id,
                    report_id=db_report.report_id,
                    user_id=db_report.user_id,
                    timestamp=db_report.timestamp,
                    target_issues=db_report.target_issues or [],
                    core_principles=db_report.core_principles or [],
                    daily_suggestions=[
                        DailySuggestion(**item) for item in db_report.daily_suggestions
                    ] if db_report.daily_suggestions else [],
                    emergency_tips=db_report.emergency_tips,
                    encouragement=db_report.encouragement or "",
                    plan_summary=db_report.plan_summary or ""
                )
            return None
        except Exception as e:
            raise e
        finally:
            db.close()