from typing import Dict, Any, Optional, List
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_

from backend.core.database import DBConfig, Dialogues, UserArchives, Strategies, Advices
from backend.core.data_models import StructuredRecord, DiagnosisReport, RecordReport, AnalysisReport, SuggestionReport, DailySuggestion

class RecordRepository:
    """记录存储库 - 负责数据持久化操作"""
    
    def __init__(self):
        # 获取数据库会话工厂
        self.db_factory = DBConfig.get_db
    
    # ---------- 原有的 save_record 方法（用于 StructuredRecord） ----------
    async def save_record(self, record: StructuredRecord) -> str:
        """保存结构化记录到数据库"""
        db = next(self.db_factory())  # 获取数据库会话
        try:
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
            db.add(db_record)
            db.commit()
            db.refresh(db_record)
            return db_record.id
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()

    # ---------- 新增：对话记录相关 ----------
    def save_dialogue(self, user_id: str, role: str, content: str,
                      four_dim: Optional[Dict[str, Any]] = None,
                      is_valuable: bool = False) -> int:
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

    def get_recent_dialogues(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        获取用户最近的对话历史
        :param user_id: 用户ID
        :param limit: 返回条数
        :return: 对话记录列表，按时间倒序
        """
        db = next(self.db_factory())
        try:
            records = db.query(Dialogues).filter(
                Dialogues.user_id == user_id
            ).order_by(Dialogues.created_at.desc()).limit(limit).all()
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
    def get_user_archive(self, user_id: str) -> Optional[Dict[str, Any]]:
        """获取用户的认知档案（JSON格式）"""
        db = next(self.db_factory())
        try:
            archive = db.query(UserArchives).filter(UserArchives.user_id == user_id).first()
            if archive:
                return {
                    "user_id": archive.user_id,
                    "archive_json": archive.archive_json,
                    "version": archive.version,
                    "updated_at": archive.updated_at.isoformat()
                }
            return None
        finally:
            db.close()

    def save_user_archive(self, user_id: str, archive_json: Dict[str, Any], version: int = 1) -> None:
        """
        保存或更新用户档案
        :param user_id: 用户ID
        :param archive_json: 档案内容（字典）
        :param version: 版本号，若存在则覆盖
        """
        db = next(self.db_factory())
        try:
            existing = db.query(UserArchives).filter(UserArchives.user_id == user_id).first()
            if existing:
                existing.archive_json = archive_json
                existing.version = version
                existing.updated_at = datetime.utcnow()
            else:
                new_archive = UserArchives(
                    user_id=user_id,
                    archive_json=archive_json,
                    version=version,
                    updated_at=datetime.utcnow()
                )
                db.add(new_archive)
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
                    dialogue_id: Optional[int] = None) -> int:
        """
        保存分析师生成的建议
        :param user_id: 用户ID
        :param advice_json: 建议内容（字典）
        :param dialogue_id: 触发该建议的对话ID（可选）
        :return: 建议记录的ID
        """
        db = next(self.db_factory())
        try:
            advice = Advices(
                user_id=user_id,
                dialogue_id=dialogue_id,
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