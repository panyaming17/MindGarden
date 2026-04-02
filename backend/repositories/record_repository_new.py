from typing import Dict, Any, Optional, List
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_

from backend.core.database import DBConfig, DialogueDB as Dialogues, UserArchiveDB as UserArchives, StrategyDB as Strategies, AdviceDB as Advices, ChatSessionDB as ChatSessions, SessionAnalysisInsightDB as AnalysisInsights
from backend.core.data_models import StructuredRecord, DiagnosisReport, RecordReport, AnalysisReport, SuggestionReport, DailySuggestion

class RecordRepository:
    """记录存储库 - 负责数据持久化操作"""
    
    def __init__(self):
        # 获取数据库会话工厂
        self.db_factory = DBConfig.get_db
    
    # ---------- 原有的 save_record 方法（用于 StructuredRecord） ----------
    async def save_record(self, record: StructuredRecord) -> str:
        """保存结构化记录到数据库"""
        # 由于StructuredRecordDB表不存在，暂时返回记录ID
        return record.record_id

    # ---------- 新增：对话记录相关 ----------
    def save_dialogue(self, user_id: str, role: str, content: str,
                      four_dim: Optional[Dict[str, Any]] = None,
                      is_valuable: bool = False,session_id: Optional[str] = None) -> int:
        """
        保存一条对话记录
        :param user_id: 用户ID
        :param role: 'user' 或 'assistant'
        :param content: 对话内容
        :param four_dim: 四维数据字典，包含 intensity, hedonic, tension, complexity
        :param is_valuable: 是否有价值
        :return: 对话记录的ID
        """
        db = next(self.db_factory())
        try:
            four_dim_intensity = four_dim.get("intensity") if four_dim else None
            four_dim_hedonic = four_dim.get("hedonic") if four_dim else None
            four_dim_tension = four_dim.get("tension") if four_dim else None
            four_dim_complexity = four_dim.get("complexity") if four_dim else None

            db_dialogue = Dialogues(
                user_id=user_id,
                session_id=session_id,
                role=role,
                content=content,
                four_dim_intensity=four_dim_intensity,
                four_dim_hedonic=four_dim_hedonic,
                four_dim_tension=four_dim_tension,
                four_dim_complexity=four_dim_complexity,
                is_valuable=is_valuable,
                created_at=datetime.utcnow()
            )
            db.add(db_dialogue)
            db.commit()
            db.refresh(db_dialogue)
            return db_dialogue.id
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()

    def get_recent_dialogues(self, user_id: str, limit: int = 10, session_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        获取用户最近的对话历史
        :param user_id: 用户ID
        :param limit: 返回条数
        :param session_id: 会话ID，可选，如果提供则只返回该会话的对话
        :return: 对话记录列表，按时间倒序
        """
        db = next(self.db_factory())
        try:
            query = db.query(Dialogues).filter(Dialogues.user_id == user_id)
            if session_id:
                query = query.filter(Dialogues.session_id == session_id)
            records = query.order_by(Dialogues.created_at.desc()).limit(limit).all()
            # 转换为字典列表，便于返回
            result = []
            for r in records:
                result.append({
                    "id": r.id,
                    "role": r.role,
                    "content": r.content,
                    "four_dim": {
                        "intensity": r.four_dim_intensity,
                        "hedonic": r.four_dim_hedonic,
                        "tension": r.four_dim_tension,
                        "complexity": r.four_dim_complexity
                    } if r.four_dim_intensity is not None else None,
                    "is_valuable": r.is_valuable,
                    "created_at": r.created_at.isoformat()
                })
            return result
        finally:
            db.close()

    # ---------- 用户档案相关 ----------
    def get_user_archive(self, user_id: str, session_id: str) -> Optional[Dict]:
        """获取用户的认知档案（JSON格式）"""
        db = next(self.db_factory())
        try:
            archive = db.query(UserArchives).filter(
                UserArchives.user_id == user_id,
                UserArchives.session_id == session_id
            ).first()
            if archive:
                return {
                    "user_id": archive.user_id,
                    "session_id": archive.session_id,
                    "archive_json": archive.archive_json,
                    "version": archive.version,
                    "updated_at": archive.updated_at.isoformat()
                }
            return None
        finally:
            db.close()

    def save_user_archive(self, user_id: str, session_id: str, archive_json: Dict, version: int = 1):
        """
        保存或更新用户档案
        :param user_id: 用户ID
        :param session_id: 会话ID
        :param archive_json: 档案内容（字典）
        :param version: 版本号，若存在则覆盖
        """
        db = next(self.db_factory())
        try:
            # 检查是否已存在档案
            existing = db.query(UserArchives).filter(
                UserArchives.user_id == user_id,
                UserArchives.session_id == session_id
            ).first()
            
            if existing:
                # 更新现有档案
                existing.archive_json = archive_json
                existing.version = version
                existing.updated_at = datetime.utcnow()
            else:
                # 创建新档案
                new_archive = UserArchives(
                    user_id=user_id,
                    session_id=session_id,
                    archive_json=archive_json,
                    version=version
                )
                db.add(new_archive)
            
            # 提交事务
            db.commit()
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()

    # ---------- 策略库相关 ----------
    def find_strategy(self, intensity_level: str, hedonic: str,
                      tension: str, complexity: str) -> Optional[Dict[str, Any]]:
        """
        根据四维组合查找策略
        :param intensity_level: 强度等级（低/中/高）
        :param hedonic: 快感度（正性/中性/负性）
        :param tension: 紧张度（低/中/高）
        :param complexity: 复杂度（简单/复杂）
        :return: 策略字典，若无则返回 None
        """
        db = next(self.db_factory())
        try:
            strategy = db.query(Strategies).filter(
                and_(
                    Strategies.intensity_level == intensity_level,
                    Strategies.hedonic == hedonic,
                    Strategies.tension == tension,
                    Strategies.complexity == complexity
                )
            ).first()
            if strategy:
                return {
                    "id": strategy.id,
                    "intensity_level": strategy.intensity_level,
                    "hedonic": strategy.hedonic,
                    "tension": strategy.tension,
                    "complexity": strategy.complexity,
                    "fusion_mode": strategy.fusion_mode,
                    "cbt_techniques": strategy.cbt_techniques,
                    "tcm_methods": strategy.tcm_methods,
                    "strategy_content": strategy.strategy_content,
                    "example": strategy.example
                }
            return None
        finally:
            db.close()

    def list_all_strategies(self) -> List[Dict[str, Any]]:
        """获取所有策略（用于缓存或管理）"""
        db = next(self.db_factory())
        try:
            strategies = db.query(Strategies).all()
            return [
                {
                    "id": s.id,
                    "intensity_level": s.intensity_level,
                    "hedonic": s.hedonic,
                    "tension": s.tension,
                    "complexity": s.complexity,
                    "fusion_mode": s.fusion_mode,
                    "cbt_techniques": s.cbt_techniques,
                    "tcm_methods": s.tcm_methods,
                    "strategy_content": s.strategy_content,
                    "example": s.example
                }
                for s in strategies
            ]
        finally:
            db.close()

    # ---------- 建议记录相关 ----------
    def save_advice(self, user_id: str, advice_json: Dict[str, Any],
                    dialogue_id: Optional[int] = None, session_id: Optional[str] = None) -> int:
        """
        保存分析师生成的建议
        :param user_id: 用户ID
        :param advice_json: 建议内容（字典）
        :param dialogue_id: 触发该建议的对话ID（可选）
        :param session_id: 会话ID（可选）
        :return: 建议记录的ID
        """
        db = next(self.db_factory())
        try:
            advice = Advices(
                user_id=user_id,
                dialogue_id=dialogue_id,
                session_id=session_id,
                advice_json=advice_json,
                created_at=datetime.utcnow()
            )
            db.add(advice)
            db.commit()
            db.refresh(advice)
            return advice.id
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()

    def get_latest_advice(self, user_id: str) -> Optional[Dict[str, Any]]:
        """获取用户最新的建议"""
        db = next(self.db_factory())
        try:
            advice = db.query(Advices).filter(
                Advices.user_id == user_id
            ).order_by(Advices.created_at.desc()).first()
            if advice:
                return {
                    "id": advice.id,
                    "user_id": advice.user_id,
                    "dialogue_id": advice.dialogue_id,
                    "advice_json": advice.advice_json,
                    "created_at": advice.created_at.isoformat()
                }
            return None
        finally:
            db.close()

    # ---------- 实时分析洞察相关 ----------
    def save_analysis_insight(self, user_id: str, session_id: str, 
                             insight_data: Dict[str, Any],
                             dialogue_id: Optional[int] = None) -> int:
        """
        保存实时分析洞察数据
        :param user_id: 用户 ID
        :param session_id: 会话 ID
        :param insight_data: 洞察数据字典，包含：
            - common_automatic_thoughts: 常见自动思维列表
            - thinking_traps: 思维陷阱列表
            - core_beliefs: 核心信念列表
            - cognitive_mappings: 认知映射关系
            - tcm_dominant_emotion: 主导情志
            - tcm_related_organs: 相关脏腑
            - tcm_qi_dynamics: 气机动态
            - tcm_interpretation: 中医解读
            - cbt_perspective: CBT 视角分析
            - tcm_perspective: 中医视角分析
            - emotional_trend: 情绪趋势
        :param dialogue_id: 触发该洞察的对话 ID（可选）
        :return: 洞察记录的 ID
        """
        db = next(self.db_factory())
        try:
            insight = AnalysisInsights(
                user_id=user_id,
                session_id=session_id,
                dialogue_id=dialogue_id,
                common_automatic_thoughts=insight_data.get("common_automatic_thoughts", []),
                thinking_traps=insight_data.get("thinking_traps", []),
                core_beliefs=insight_data.get("core_beliefs", []),
                cognitive_mappings=insight_data.get("cognitive_mappings", []),
                tcm_dominant_emotion=insight_data.get("tcm_dominant_emotion"),
                tcm_related_organs=insight_data.get("tcm_related_organs", []),
                tcm_qi_dynamics=insight_data.get("tcm_qi_dynamics"),
                tcm_interpretation=insight_data.get("tcm_interpretation"),
                cbt_perspective=insight_data.get("cbt_perspective"),
                tcm_perspective=insight_data.get("tcm_perspective"),
                emotional_trend=insight_data.get("emotional_trend")
            )
            db.add(insight)
            db.commit()
            db.refresh(insight)
            return insight.id
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()

    def get_session_insights(self, user_id: str, session_id: str) -> List[Dict[str, Any]]:
        """
        获取会话的所有分析洞察
        :param user_id: 用户 ID
        :param session_id: 会话 ID
        :return: 洞察数据列表，按时间排序
        """
        db = next(self.db_factory())
        try:
            insights = db.query(AnalysisInsights).filter(
                and_(
                    AnalysisInsights.user_id == user_id,
                    AnalysisInsights.session_id == session_id
                )
            ).order_by(AnalysisInsights.created_at.asc()).all()
            
            result = []
            for insight in insights:
                result.append({
                    "id": insight.id,
                    "dialogue_id": insight.dialogue_id,
                    "common_automatic_thoughts": insight.common_automatic_thoughts,
                    "thinking_traps": insight.thinking_traps,
                    "core_beliefs": insight.core_beliefs,
                    "cognitive_mappings": insight.cognitive_mappings,
                    "tcm_dominant_emotion": insight.tcm_dominant_emotion,
                    "tcm_related_organs": insight.tcm_related_organs,
                    "tcm_qi_dynamics": insight.tcm_qi_dynamics,
                    "tcm_interpretation": insight.tcm_interpretation,
                    "cbt_perspective": insight.cbt_perspective,
                    "tcm_perspective": insight.tcm_perspective,
                    "emotional_trend": insight.emotional_trend,
                    "created_at": insight.created_at.isoformat() if insight.created_at else None
                })
            return result
        finally:
            db.close()

    def get_latest_insight(self, user_id: str, session_id: str) -> Optional[Dict[str, Any]]:
        """获取会话最新的分析洞察"""
        db = next(self.db_factory())
        try:
            insight = db.query(AnalysisInsights).filter(
                and_(
                    AnalysisInsights.user_id == user_id,
                    AnalysisInsights.session_id == session_id
                )
            ).order_by(AnalysisInsights.created_at.desc()).first()
            
            if insight:
                return {
                    "id": insight.id,
                    "dialogue_id": insight.dialogue_id,
                    "common_automatic_thoughts": insight.common_automatic_thoughts,
                    "thinking_traps": insight.thinking_traps,
                    "core_beliefs": insight.core_beliefs,
                    "cognitive_mappings": insight.cognitive_mappings,
                    "tcm_dominant_emotion": insight.tcm_dominant_emotion,
                    "tcm_related_organs": insight.tcm_related_organs,
                    "tcm_qi_dynamics": insight.tcm_qi_dynamics,
                    "tcm_interpretation": insight.tcm_interpretation,
                    "cbt_perspective": insight.cbt_perspective,
                    "tcm_perspective": insight.tcm_perspective,
                    "emotional_trend": insight.emotional_trend,
                    "created_at": insight.created_at.isoformat() if insight.created_at else None
                }
            return None
        finally:
            db.close()

    def aggregate_session_insights(self, user_id: str, session_id: str) -> Dict[str, Any]:
        """
        聚合会话的所有分析洞察，生成汇总数据
        :param user_id: 用户 ID
        :param session_id: 会话 ID
        :return: 聚合后的洞察数据
        """
        db = next(self.db_factory())
        try:
            insights = db.query(AnalysisInsights).filter(
                and_(
                    AnalysisInsights.user_id == user_id,
                    AnalysisInsights.session_id == session_id
                )
            ).order_by(AnalysisInsights.created_at.asc()).all()
            
            if not insights:
                return {}
            
            # 聚合数据
            all_thoughts = []
            all_traps = []
            all_beliefs = []
            all_mappings = []
            latest_tcm_emotion = None
            latest_tcm_organs = []
            latest_tcm_qi = None
            latest_tcm_interp = None
            latest_cbt = None
            latest_tcm = None
            latest_trend = None
            
            for insight in insights:
                if insight.common_automatic_thoughts:
                    all_thoughts.extend(insight.common_automatic_thoughts)
                if insight.thinking_traps:
                    all_traps.extend(insight.thinking_traps)
                if insight.core_beliefs:
                    all_beliefs.extend(insight.core_beliefs)
                if insight.cognitive_mappings:
                    all_mappings.extend(insight.cognitive_mappings)
                
                # 使用最新的中医分析
                if insight.tcm_dominant_emotion:
                    latest_tcm_emotion = insight.tcm_dominant_emotion
                if insight.tcm_related_organs:
                    latest_tcm_organs = insight.tcm_related_organs
                if insight.tcm_qi_dynamics:
                    latest_tcm_qi = insight.tcm_qi_dynamics
                if insight.tcm_interpretation:
                    latest_tcm_interp = insight.tcm_interpretation
                
                # 使用最新的原因分析
                if insight.cbt_perspective:
                    latest_cbt = insight.cbt_perspective
                if insight.tcm_perspective:
                    latest_tcm = insight.tcm_perspective
                
                # 使用最新的情绪趋势
                if insight.emotional_trend:
                    latest_trend = insight.emotional_trend
            
            # 去重
            unique_thoughts = list(dict.fromkeys(all_thoughts))
            unique_traps = list(dict.fromkeys(all_traps))
            unique_beliefs = list(dict.fromkeys(all_beliefs))
            
            return {
                "common_automatic_thoughts": unique_thoughts,
                "thinking_traps": unique_traps,
                "core_beliefs": unique_beliefs,
                "cognitive_mappings": all_mappings,
                "tcm_analysis": {
                    "dominant_emotion": latest_tcm_emotion,
                    "related_organs": latest_tcm_organs,
                    "qi_dynamics": latest_tcm_qi,
                    "tcm_interpretation": latest_tcm_interp
                },
                "causes": {
                    "cbt_perspective": latest_cbt,
                    "tcm_perspective": latest_tcm
                },
                "trends": latest_trend
            }
        finally:
            db.close()
    
    # ========== 新增：四维数据增量更新方法 ==========
    def update_four_dim_statistics(self, user_id: str, session_id: str,
                                   dialogue_id: Optional[int],
                                   intensity_value: Optional[float],
                                   hedonic_label: Optional[str],
                                   tension_label: Optional[str]) -> None:
        """
        增量更新四维数据统计
        
        :param user_id: 用户 ID
        :param session_id: 会话 ID
        :param dialogue_id: 触发更新的对话 ID
        :param intensity_value: 强度值（可选）
        :param hedonic_label: 快感度标签（可选）
        :param tension_label: 紧张度标签（可选）
        """
        db = next(self.db_factory())
        try:
            # 查询是否已存在该会话的洞察记录
            insight = db.query(AnalysisInsights).filter(
                AnalysisInsights.user_id == user_id,
                AnalysisInsights.session_id == session_id
            ).order_by(AnalysisInsights.created_at.desc()).first()
            
            if not insight:
                # 创建新记录
                insight = AnalysisInsights(
                    user_id=user_id,
                    session_id=session_id,
                    dialogue_id=dialogue_id,
                    intensity_values=[],
                    hedonic_counts={"负性": 0, "中性": 0, "正性": 0},
                    tension_counts={"低": 0, "中": 0, "高": 0},
                    complexity_analysis=None,
                    is_completed=False,
                    is_migrated=False
                )
                db.add(insight)
            
            # 增量更新强度值数组
            if intensity_value is not None:
                if insight.intensity_values is None:
                    insight.intensity_values = []
                insight.intensity_values.append({
                    "value": float(intensity_value),
                    "timestamp": datetime.utcnow().isoformat()
                })
            
            # 增量更新快感度计数
            if hedonic_label and hedonic_label in insight.hedonic_counts:
                insight.hedonic_counts[hedonic_label] += 1
            
            # 增量更新紧张度计数
            if tension_label and tension_label in insight.tension_counts:
                insight.tension_counts[tension_label] += 1
            
            # 更新 dialogue_id（总是使用最新的）
            insight.dialogue_id = dialogue_id
            insight.updated_at = datetime.utcnow()
            
            db.commit()
            
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()
    
    def update_complexity_analysis(self, user_id: str, session_id: str,
                                   dialogue_id: int,
                                   complexity_analysis: Dict[str, Any]) -> None:
        """
        更新复杂度分析（每 2 轮对话调用一次 LLM 分析）
        
        :param user_id: 用户 ID
        :param session_id: 会话 ID
        :param dialogue_id: 触发更新的对话 ID
        :param complexity_analysis: 复杂度分析结果 {"type": "复杂", "emotions": [...]}
        """
        db = next(self.db_factory())
        try:
            insight = db.query(AnalysisInsights).filter(
                AnalysisInsights.user_id == user_id,
                AnalysisInsights.session_id == session_id
            ).first()
            
            if insight:
                insight.complexity_analysis = complexity_analysis
                insight.dialogue_id = dialogue_id
                insight.updated_at = datetime.utcnow()
                db.commit()
            else:
                # 如果不存在，创建新记录
                insight = AnalysisInsights(
                    user_id=user_id,
                    session_id=session_id,
                    dialogue_id=dialogue_id,
                    intensity_values=[],
                    hedonic_counts={"负性": 0, "中性": 0, "正性": 0},
                    tension_counts={"低": 0, "中": 0, "高": 0},
                    complexity_analysis=complexity_analysis,
                    is_completed=False,
                    is_migrated=False
                )
                db.add(insight)
                db.commit()
                
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()
    
    def mark_insight_completed(self, user_id: str, session_id: str) -> None:
        """
        标记会话分析洞察为已完成
        
        :param user_id: 用户 ID
        :param session_id: 会话 ID
        """
        db = next(self.db_factory())
        try:
            insight = db.query(AnalysisInsights).filter(
                AnalysisInsights.user_id == user_id,
                AnalysisInsights.session_id == session_id
            ).first()
            
            if insight:
                insight.is_completed = True
                insight.updated_at = datetime.utcnow()
                db.commit()
                
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()
    
    def mark_insight_migrated(self, user_id: str, session_id: str) -> None:
        """
        标记会话分析洞察为已迁移到 session_reports
        
        :param user_id: 用户 ID
        :param session_id: 会话 ID
        """
        db = next(self.db_factory())
        try:
            insight = db.query(AnalysisInsights).filter(
                AnalysisInsights.user_id == user_id,
                AnalysisInsights.session_id == session_id
            ).first()
            
            if insight:
                insight.is_migrated = True
                insight.updated_at = datetime.utcnow()
                db.commit()
                
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()
    
    def get_session_insights(self, user_id: str, session_id: str) -> Optional[Dict]:
        """
        获取会话分析洞察（用于生成报告）
        
        :param user_id: 用户 ID
        :param session_id: 会话 ID
        :return: 洞察数据字典
        """
        db = next(self.db_factory())
        try:
            insight = db.query(AnalysisInsights).filter(
                AnalysisInsights.user_id == user_id,
                AnalysisInsights.session_id == session_id
            ).first()
            
            if not insight:
                return None
            
            return {
                "intensity_values": insight.intensity_values or [],
                "hedonic_counts": insight.hedonic_counts or {"负性": 0, "中性": 0, "正性": 0},
                "tension_counts": insight.tension_counts or {"低": 0, "中": 0, "高": 0},
                "complexity_analysis": insight.complexity_analysis or {"type": "简单", "emotions": []},
                "is_completed": insight.is_completed,
                "is_migrated": insight.is_migrated
            }
        finally:
            db.close()
