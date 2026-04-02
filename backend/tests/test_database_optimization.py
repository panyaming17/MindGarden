"""
数据库优化单元测试
测试新增的增量聚合功能
"""

import pytest
import sys
from pathlib import Path
from datetime import datetime

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.repositories.record_repository_new import RecordRepository
from backend.core.database import SessionLocal, DialogueDB, SessionAnalysisInsightDB


class TestFourDimIncrementalUpdates:
    """测试四维数据增量更新功能"""
    
    def setup_method(self):
        """每个测试前的准备工作"""
        self.repository = RecordRepository()
        self.db = SessionLocal()
        self.test_user_id = "test_user_001"
        self.test_session_id = "test_session_001"
        
        # 创建测试对话记录（用于满足外键约束）
        from backend.core.database import DialogueDB
        test_dialogue = DialogueDB(
            user_id=self.test_user_id,
            session_id=self.test_session_id,
            role="user",
            content="test content",
            created_at=datetime.now()
        )
        self.db.add(test_dialogue)
        self.db.commit()
        self.test_dialogue_id = test_dialogue.id
        
    def teardown_method(self):
        """每个测试后的清理工作"""
        # 清理测试数据
        try:
            self.db.query(DialogueDB).filter(
                DialogueDB.user_id == self.test_user_id,
                DialogueDB.session_id == self.test_session_id
            ).delete()
            self.db.query(SessionAnalysisInsightDB).filter(
                SessionAnalysisInsightDB.user_id == self.test_user_id,
                SessionAnalysisInsightDB.session_id == self.test_session_id
            ).delete()
            self.db.commit()
        except:
            self.db.rollback()
        finally:
            self.db.close()
    
    def test_update_four_dim_statistics_first_time(self):
        """测试首次更新四维统计"""
        # 执行更新
        self.repository.update_four_dim_statistics(
            user_id=self.test_user_id,
            session_id=self.test_session_id,
            dialogue_id=self.test_dialogue_id,
            intensity_value=6.5,
            hedonic_label="负性",
            tension_label="中"
        )
        
        # 验证结果
        insights = self.repository.get_session_insights(
            self.test_user_id, 
            self.test_session_id
        )
        
        assert insights is not None
        assert len(insights['intensity_values']) == 1
        assert insights['intensity_values'][0]['value'] == 6.5
        assert insights['hedonic_counts']['负性'] == 1
        assert insights['tension_counts']['中'] == 1
        assert insights['is_completed'] == False
        assert insights['is_migrated'] == False
    
    def test_update_four_dim_statistics_incremental(self):
        """测试增量更新四维统计"""
        # 第一次更新
        self.repository.update_four_dim_statistics(
            user_id=self.test_user_id,
            session_id=self.test_session_id,
            dialogue_id=self.test_dialogue_id,
            intensity_value=6.5,
            hedonic_label="负性",
            tension_label="中"
        )
        
        # 第二次更新
        self.repository.update_four_dim_statistics(
            user_id=self.test_user_id,
            session_id=self.test_session_id,
            dialogue_id=self.test_dialogue_id,
            intensity_value=7.2,
            hedonic_label="负性",
            tension_label="高"
        )
        
        # 第三次更新
        self.repository.update_four_dim_statistics(
            user_id=self.test_user_id,
            session_id=self.test_session_id,
            dialogue_id=self.test_dialogue_id,
            intensity_value=5.8,
            hedonic_label="中性",
            tension_label="中"
        )
        
        # 验证结果
        insights = self.repository.get_session_insights(
            self.test_user_id, 
            self.test_session_id
        )
        
        # 验证强度值数组
        assert len(insights['intensity_values']) == 3
        assert insights['intensity_values'][0]['value'] == 6.5
        assert insights['intensity_values'][1]['value'] == 7.2
        assert insights['intensity_values'][2]['value'] == 5.8
        
        # 验证计数
        assert insights['hedonic_counts']['负性'] == 2
        assert insights['hedonic_counts']['中性'] == 1
        assert insights['hedonic_counts']['正性'] == 0
        
        assert insights['tension_counts']['中'] == 2
        assert insights['tension_counts']['高'] == 1
        assert insights['tension_counts']['低'] == 0
    
    def test_update_complexity_analysis(self):
        """测试复杂度分析更新"""
        # 准备复杂度分析结果
        complexity_analysis = {
            "type": "复杂",
            "emotions": [
                {"emotion": "忧", "value": 0.6},
                {"emotion": "思", "value": 0.4}
            ]
        }
        
        # 执行更新
        self.repository.update_complexity_analysis(
            user_id=self.test_user_id,
            session_id=self.test_session_id,
            dialogue_id=self.test_dialogue_id,
            complexity_analysis=complexity_analysis
        )
        
        # 验证结果
        insights = self.repository.get_session_insights(
            self.test_user_id, 
            self.test_session_id
        )
        
        assert insights is not None
        assert insights['complexity_analysis'] is not None
        assert insights['complexity_analysis']['type'] == "复杂"
        assert len(insights['complexity_analysis']['emotions']) == 2
        assert insights['complexity_analysis']['emotions'][0]['emotion'] == "忧"
        assert insights['complexity_analysis']['emotions'][0]['value'] == 0.6
    
    def test_mark_insight_completed(self):
        """测试标记洞察为已完成"""
        # 先创建记录
        self.repository.update_four_dim_statistics(
            user_id=self.test_user_id,
            session_id=self.test_session_id,
            dialogue_id=self.test_dialogue_id,
            intensity_value=6.5,
            hedonic_label="负性",
            tension_label="中"
        )
        
        # 标记为已完成
        self.repository.mark_insight_completed(
            self.test_user_id, 
            self.test_session_id
        )
        
        # 验证
        insights = self.repository.get_session_insights(
            self.test_user_id, 
            self.test_session_id
        )
        
        assert insights['is_completed'] == True
    
    def test_mark_insight_migrated(self):
        """测试标记洞察为已迁移"""
        # 先创建记录
        self.repository.update_four_dim_statistics(
            user_id=self.test_user_id,
            session_id=self.test_session_id,
            dialogue_id=self.test_dialogue_id,
            intensity_value=6.5,
            hedonic_label="负性",
            tension_label="中"
        )
        
        # 标记为已迁移
        self.repository.mark_insight_migrated(
            self.test_user_id, 
            self.test_session_id
        )
        
        # 验证
        insights = self.repository.get_session_insights(
            self.test_user_id, 
            self.test_session_id
        )
        
        assert insights['is_migrated'] == True


class TestExtractFourDimData:
    """测试从对话中提取四维数据功能"""
    
    def test_extract_four_dim_data_from_dialogues(self):
        """测试从对话历史中提取四维数据"""
        from backend.api.v1.chat_endpoints import extract_four_dim_data_from_dialogues
        
        # 准备测试数据
        dialogues = [
            {
                "role": "user",
                "content": "我感觉很焦虑",
                "created_at": "2026-04-01T10:00:00",
                "four_dim": {
                    "intensity": 6.5,
                    "hedonic": "负性",
                    "tension": "高",
                    "complexity": None
                }
            },
            {
                "role": "assistant",
                "content": "我理解你的感受",
                "created_at": "2026-04-01T10:00:05",
                "four_dim": None
            },
            {
                "role": "user",
                "content": "工作压力很大",
                "created_at": "2026-04-01T10:00:10",
                "four_dim": {
                    "intensity": 7.2,
                    "hedonic": "负性",
                    "tension": "高",
                    "complexity": None
                }
            }
        ]
        
        # 执行提取
        result = extract_four_dim_data_from_dialogues(dialogues)
        
        # 验证结果
        assert result is not None
        assert len(result['intensity_values']) == 2
        assert result['intensity_values'][0]['value'] == 6.5
        assert result['intensity_values'][1]['value'] == 7.2
        
        # 验证快感度统计
        assert result['hedonic_values'][0]['label'] == "负性"
        assert result['hedonic_values'][0]['value'] == 2
        
        # 验证紧张度统计
        assert result['tension_values'][2]['label'] == "高"
        assert result['tension_values'][2]['value'] == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
