#!/usr/bin/env python3
"""
更新数据库中的中医规则库数据，使其与新的结构匹配
"""

import sys
from sqlalchemy.orm import Session
from backend.core.database import SessionLocal, RuleDB

def update_tcm_rules():
    """更新中医规则库数据"""
    db = SessionLocal()
    try:
        # 获取所有中医类型的规则
        tcm_rules = db.query(RuleDB).filter(RuleDB.type == "tcm").all()
        
        print(f"找到 {len(tcm_rules)} 条中医规则")
        
        # 定义新的中医情志规则结构
        new_tcm_rules = {
            "怒": {
                "dominant_emotion": "怒",
                "keywords": ["生气", "愤怒", "暴怒", "恼火", "气愤"],
                "affected_zang": "肝",
                "common_patterns": ["肝郁气滞", "肝火上炎", "肝阳上亢"],
                "inhibiting_emotion": "悲",  # 悲胜怒
                "behavioral_adjustment": ["听商音（属金）音乐", "6秒吸气，8秒呼气法", "舒展肝胆经的拉伸"],
                "other_suggestions": ["避免辛辣刺激食物", "保持充足睡眠"]
            },
            "喜": {
                "dominant_emotion": "喜",
                "keywords": ["高兴", "快乐", "喜悦", "开心", "兴奋"],
                "affected_zang": "心",
                "common_patterns": ["心火亢盛", "心阴不足", "心脾两虚"],
                "inhibiting_emotion": "恐",  # 恐胜喜
                "behavioral_adjustment": ["听羽音（属水）音乐", "平静呼吸", "避免过度兴奋"],
                "other_suggestions": ["保持情绪稳定", "充足休息"]
            },
            "忧": {
                "dominant_emotion": "忧",
                "keywords": ["担忧", "焦虑", "忧虑", "担心", "发愁"],
                "affected_zang": "肺",
                "common_patterns": ["肺气虚", "肺气郁", "肺阴虚"],
                "inhibiting_emotion": "喜",  # 喜胜忧
                "behavioral_adjustment": ["听徵音（属火）音乐", "腹式呼吸，想象红色能量", "开怀大笑练习"],
                "other_suggestions": ["多吃润肺食物", "适当运动"]
            },
            "思": {
                "dominant_emotion": "思",
                "keywords": ["思考", "思虑", "沉思", "冥想", "琢磨"],
                "affected_zang": "脾",
                "common_patterns": ["脾虚", "心脾两虚", "脾胃不和"],
                "inhibiting_emotion": "怒",  # 怒胜思
                "behavioral_adjustment": ["听角音（属木）音乐", "轻度运动", "户外活动"],
                "other_suggestions": ["饮食规律", "避免过度思虑"]
            },
            "恐": {
                "dominant_emotion": "恐",
                "keywords": ["害怕", "恐惧", "担忧", "惊慌", "紧张"],
                "affected_zang": "肾",
                "common_patterns": ["肾虚", "肾阴不足", "肾阳虚"],
                "inhibiting_emotion": "思",  # 思胜恐
                "behavioral_adjustment": ["听宫音（属土）音乐", "深呼吸", "冥想放松"],
                "other_suggestions": ["适当补肾食物", "规律作息"]
            }
        }
        
        # 更新或创建规则
        for emotion, rule_data in new_tcm_rules.items():
            # 查找现有规则
            existing_rule = db.query(RuleDB).filter(
                RuleDB.type == "tcm",
                RuleDB.name == emotion
            ).first()
            
            if existing_rule:
                # 更新现有规则
                existing_rule.content = rule_data
                existing_rule.version = "2.0"
                print(f"更新规则: {emotion}")
            else:
                # 创建新规则
                new_rule = RuleDB(
                    type="tcm",
                    name=emotion,
                    content=rule_data,
                    version="2.0",
                    is_active=True
                )
                db.add(new_rule)
                print(f"创建规则: {emotion}")
        
        # 提交更改
        db.commit()
        print("\n中医规则库更新完成")
        
    except Exception as e:
        print(f"错误: {str(e)}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    update_tcm_rules()
