"""
初始化问卷模板和评分规则脚本
"""
import json
from datetime import datetime
from backend.core.database import SessionLocal, QuestionnaireTemplateDB, QuestionnaireScoringRuleDB

# PHQ-9 抑郁量表题目
PHQ9_QUESTIONS = [
    {
        "id": "phq-1",
        "type": "phq9",
        "text": "对做事提不起劲或没有兴趣",
        "options": [
            {"id": "o0", "label": "完全没有", "desc": "0天", "score": 0},
            {"id": "o1", "label": "有几天", "desc": "1～4天", "score": 1},
            {"id": "o2", "label": "一半以上天数", "desc": "5～9天", "score": 2},
            {"id": "o3", "label": "几乎每天", "desc": "10～14天", "score": 3}
        ]
    },
    {
        "id": "phq-2",
        "type": "phq9",
        "text": "感到心情低落、沮丧或绝望",
        "options": [
            {"id": "o0", "label": "完全没有", "desc": "0天", "score": 0},
            {"id": "o1", "label": "有几天", "desc": "1～4天", "score": 1},
            {"id": "o2", "label": "一半以上天数", "desc": "5～9天", "score": 2},
            {"id": "o3", "label": "几乎每天", "desc": "10～14天", "score": 3}
        ]
    },
    {
        "id": "phq-3",
        "type": "phq9",
        "text": "入睡困难、睡不安稳或睡眠过多",
        "options": [
            {"id": "o0", "label": "完全没有", "desc": "0天", "score": 0},
            {"id": "o1", "label": "有几天", "desc": "1～4天", "score": 1},
            {"id": "o2", "label": "一半以上天数", "desc": "5～9天", "score": 2},
            {"id": "o3", "label": "几乎每天", "desc": "10～14天", "score": 3}
        ]
    },
    {
        "id": "phq-4",
        "type": "phq9",
        "text": "感觉疲倦或没有活力",
        "options": [
            {"id": "o0", "label": "完全没有", "desc": "0天", "score": 0},
            {"id": "o1", "label": "有几天", "desc": "1～4天", "score": 1},
            {"id": "o2", "label": "一半以上天数", "desc": "5～9天", "score": 2},
            {"id": "o3", "label": "几乎每天", "desc": "10～14天", "score": 3}
        ]
    },
    {
        "id": "phq-5",
        "type": "phq9",
        "text": "食欲不振或吃太多",
        "options": [
            {"id": "o0", "label": "完全没有", "desc": "0天", "score": 0},
            {"id": "o1", "label": "有几天", "desc": "1～4天", "score": 1},
            {"id": "o2", "label": "一半以上天数", "desc": "5～9天", "score": 2},
            {"id": "o3", "label": "几乎每天", "desc": "10～14天", "score": 3}
        ]
    },
    {
        "id": "phq-6",
        "type": "phq9",
        "text": "觉得自己很糟，或觉得自己很失败，让自己或家人失望",
        "options": [
            {"id": "o0", "label": "完全没有", "desc": "0天", "score": 0},
            {"id": "o1", "label": "有几天", "desc": "1～4天", "score": 1},
            {"id": "o2", "label": "一半以上天数", "desc": "5～9天", "score": 2},
            {"id": "o3", "label": "几乎每天", "desc": "10～14天", "score": 3}
        ]
    },
    {
        "id": "phq-7",
        "type": "phq9",
        "text": "对事物专注有困难（例如阅读、看手机、看电视）",
        "options": [
            {"id": "o0", "label": "完全没有", "desc": "0天", "score": 0},
            {"id": "o1", "label": "有几天", "desc": "1～4天", "score": 1},
            {"id": "o2", "label": "一半以上天数", "desc": "5～9天", "score": 2},
            {"id": "o3", "label": "几乎每天", "desc": "10～14天", "score": 3}
        ]
    },
    {
        "id": "phq-8",
        "type": "phq9",
        "text": "动作或说话速度特别缓慢，或相反：烦躁、坐立不安",
        "options": [
            {"id": "o0", "label": "完全没有", "desc": "0天", "score": 0},
            {"id": "o1", "label": "有几天", "desc": "1～4天", "score": 1},
            {"id": "o2", "label": "一半以上天数", "desc": "5～9天", "score": 2},
            {"id": "o3", "label": "几乎每天", "desc": "10～14天", "score": 3}
        ]
    },
    {
        "id": "phq-9",
        "type": "phq9",
        "text": "有不如死掉或用某种方式伤害自己的念头",
        "options": [
            {"id": "o0", "label": "完全没有", "desc": "0天", "score": 0},
            {"id": "o1", "label": "有几天", "desc": "1～4天", "score": 1},
            {"id": "o2", "label": "一半以上天数", "desc": "5～9天", "score": 2},
            {"id": "o3", "label": "几乎每天", "desc": "10～14天", "score": 3}
        ]
    }
]

# GAD-7 焦虑量表题目
GAD7_QUESTIONS = [
    {
        "id": "gad-1",
        "type": "gad7",
        "text": "感觉紧张、焦虑或烦躁",
        "options": [
            {"id": "o0", "label": "完全没有", "desc": "0天", "score": 0},
            {"id": "o1", "label": "有几天", "desc": "1～4天", "score": 1},
            {"id": "o2", "label": "一半以上天数", "desc": "5～9天", "score": 2},
            {"id": "o3", "label": "几乎每天", "desc": "10～14天", "score": 3}
        ]
    },
    {
        "id": "gad-2",
        "type": "gad7",
        "text": "不能停止或控制担忧",
        "options": [
            {"id": "o0", "label": "完全没有", "desc": "0天", "score": 0},
            {"id": "o1", "label": "有几天", "desc": "1～4天", "score": 1},
            {"id": "o2", "label": "一半以上天数", "desc": "5～9天", "score": 2},
            {"id": "o3", "label": "几乎每天", "desc": "10～14天", "score": 3}
        ]
    },
    {
        "id": "gad-3",
        "type": "gad7",
        "text": "对各种事情过分担忧",
        "options": [
            {"id": "o0", "label": "完全没有", "desc": "0天", "score": 0},
            {"id": "o1", "label": "有几天", "desc": "1～4天", "score": 1},
            {"id": "o2", "label": "一半以上天数", "desc": "5～9天", "score": 2},
            {"id": "o3", "label": "几乎每天", "desc": "10～14天", "score": 3}
        ]
    },
    {
        "id": "gad-4",
        "type": "gad7",
        "text": "很难放松下来",
        "options": [
            {"id": "o0", "label": "完全没有", "desc": "0天", "score": 0},
            {"id": "o1", "label": "有几天", "desc": "1～4天", "score": 1},
            {"id": "o2", "label": "一半以上天数", "desc": "5～9天", "score": 2},
            {"id": "o3", "label": "几乎每天", "desc": "10～14天", "score": 3}
        ]
    },
    {
        "id": "gad-5",
        "type": "gad7",
        "text": "由于不安而无法静坐",
        "options": [
            {"id": "o0", "label": "完全没有", "desc": "0天", "score": 0},
            {"id": "o1", "label": "有几天", "desc": "1～4天", "score": 1},
            {"id": "o2", "label": "一半以上天数", "desc": "5～9天", "score": 2},
            {"id": "o3", "label": "几乎每天", "desc": "10～14天", "score": 3}
        ]
    },
    {
        "id": "gad-6",
        "type": "gad7",
        "text": "容易生气或发怒",
        "options": [
            {"id": "o0", "label": "完全没有", "desc": "0天", "score": 0},
            {"id": "o1", "label": "有几天", "desc": "1～4天", "score": 1},
            {"id": "o2", "label": "一半以上天数", "desc": "5～9天", "score": 2},
            {"id": "o3", "label": "几乎每天", "desc": "10～14天", "score": 3}
        ]
    },
    {
        "id": "gad-7",
        "type": "gad7",
        "text": "感到害怕，似乎有可怕的事情即将发生",
        "options": [
            {"id": "o0", "label": "完全没有", "desc": "0天", "score": 0},
            {"id": "o1", "label": "有几天", "desc": "1～4天", "score": 1},
            {"id": "o2", "label": "一半以上天数", "desc": "5～9天", "score": 2},
            {"id": "o3", "label": "几乎每天", "desc": "10～14天", "score": 3}
        ]
    }
]

# PHQ-9 评分规则
PHQ9_SCORING_RULES = [
    # 等级规则
    {"type": "level", "config": {"min": 0, "max": 4, "level": "none", "text": "无抑郁", "color": "green"}, "priority": 1},
    {"type": "level", "config": {"min": 5, "max": 9, "level": "mild", "text": "轻度抑郁", "color": "yellow"}, "priority": 2},
    {"type": "level", "config": {"min": 10, "max": 14, "level": "moderate", "text": "中度抑郁", "color": "orange"}, "priority": 3},
    {"type": "level", "config": {"min": 15, "max": 19, "level": "moderately_severe", "text": "中重度抑郁", "color": "red"}, "priority": 4},
    {"type": "level", "config": {"min": 20, "max": 27, "level": "severe", "text": "重度抑郁", "color": "darkred"}, "priority": 5},
    # 间隔规则
    {"type": "interval", "config": {"days": 3, "skip_max": 3}, "priority": 0},
]

# PHQ-9 建议规则
PHQ9_SUGGESTIONS = {
    "none": {
        "suggestions": [
            "您的情绪状态良好，请继续保持健康的生活方式",
            "建议定期进行自我评估，关注情绪变化"
        ],
        "resources": [
            {"name": "心理健康知识", "type": "article", "url": "/article/mental-health"}
        ]
    },
    "mild": {
        "suggestions": [
            "您可能有轻度抑郁症状，建议关注情绪变化",
            "可以尝试放松训练、运动等方式调节情绪",
            "建议与家人朋友多交流，寻求社会支持"
        ],
        "resources": [
            {"name": "抑郁自测详解", "type": "article", "url": "/article/depression-guide"},
            {"name": "放松训练音频", "type": "audio", "url": "/resource/relaxation"}
        ]
    },
    "moderate": {
        "suggestions": [
            "您可能有中度抑郁症状，建议寻求专业心理咨询",
            "可以考虑预约心理咨询师进行面对面咨询",
            "保持规律作息，适当运动，避免过度压力"
        ],
        "resources": [
            {"name": "心理咨询预约", "type": "internal", "url": "/booking"},
            {"name": "抑郁应对指南", "type": "article", "url": "/article/depression-help"}
        ]
    },
    "moderately_severe": {
        "suggestions": [
            "您可能有中重度抑郁症状，建议尽快寻求专业帮助",
            "强烈建议预约精神科医生或心理咨询师",
            "如有自伤念头，请立即联系危机干预热线"
        ],
        "resources": [
            {"name": "心理咨询预约", "type": "internal", "url": "/booking"},
            {"name": "危机干预热线", "type": "hotline", "url": "tel:400-161-9995"}
        ]
    },
    "severe": {
        "suggestions": [
            "您可能有重度抑郁症状，请立即寻求专业帮助",
            "强烈建议尽快就医，接受专业治疗",
            "如有自伤或自杀念头，请立即拨打危机干预热线或前往医院"
        ],
        "resources": [
            {"name": "紧急求助", "type": "hotline", "url": "tel:400-161-9995"},
            {"name": "就近医院", "type": "map", "url": "/map/hospitals"}
        ]
    }
}

# GAD-7 评分规则
GAD7_SCORING_RULES = [
    # 等级规则
    {"type": "level", "config": {"min": 0, "max": 4, "level": "none", "text": "无焦虑", "color": "green"}, "priority": 1},
    {"type": "level", "config": {"min": 5, "max": 9, "level": "mild", "text": "轻度焦虑", "color": "yellow"}, "priority": 2},
    {"type": "level", "config": {"min": 10, "max": 14, "level": "moderate", "text": "中度焦虑", "color": "orange"}, "priority": 3},
    {"type": "level", "config": {"min": 15, "max": 21, "level": "severe", "text": "重度焦虑", "color": "red"}, "priority": 4},
    # 间隔规则
    {"type": "interval", "config": {"days": 3, "skip_max": 3}, "priority": 0},
]

# GAD-7 建议规则
GAD7_SUGGESTIONS = {
    "none": {
        "suggestions": [
            "您的焦虑水平正常，请继续保持",
            "建议定期进行自我评估"
        ],
        "resources": [
            {"name": "焦虑管理技巧", "type": "article", "url": "/article/anxiety-management"}
        ]
    },
    "mild": {
        "suggestions": [
            "您可能有轻度焦虑，建议学习放松技巧",
            "尝试深呼吸、冥想等放松方法",
            "保持规律运动，有助于缓解焦虑"
        ],
        "resources": [
            {"name": "放松训练", "type": "audio", "url": "/resource/relaxation"},
            {"name": "焦虑自测详解", "type": "article", "url": "/article/anxiety-guide"}
        ]
    },
    "moderate": {
        "suggestions": [
            "您可能有中度焦虑，建议寻求专业帮助",
            "可以考虑预约心理咨询师",
            "学习认知行为疗法技巧，挑战焦虑思维"
        ],
        "resources": [
            {"name": "心理咨询预约", "type": "internal", "url": "/booking"},
            {"name": "CBT自助指南", "type": "article", "url": "/article/cbt-guide"}
        ]
    },
    "severe": {
        "suggestions": [
            "您可能有重度焦虑，建议尽快寻求专业帮助",
            "强烈建议预约精神科医生或心理咨询师",
            "如焦虑严重影响生活，请及时就医"
        ],
        "resources": [
            {"name": "心理咨询预约", "type": "internal", "url": "/booking"},
            {"name": "紧急求助", "type": "hotline", "url": "tel:400-161-9995"}
        ]
    }
}


def init_questionnaires():
    """初始化问卷模板和评分规则"""
    db = SessionLocal()
    try:
        print("开始初始化问卷数据...")
        
        # 1. 创建 PHQ-9 模板
        phq9_template = db.query(QuestionnaireTemplateDB).filter(
            QuestionnaireTemplateDB.code == "PHQ9"
        ).first()
        
        if not phq9_template:
            phq9_template = QuestionnaireTemplateDB(
                code="PHQ9",
                name="PHQ-9 抑郁量表",
                description="患者健康问卷抑郁量表，用于评估抑郁症状的严重程度。共9题，总分0-27分。",
                questions=PHQ9_QUESTIONS,
                scoring_rules={"calculation": "sum", "total_questions": 9},
                is_active=True
            )
            db.add(phq9_template)
            print("✓ 创建 PHQ-9 模板")
        else:
            print("✓ PHQ-9 模板已存在")
        
        # 2. 创建 GAD-7 模板
        gad7_template = db.query(QuestionnaireTemplateDB).filter(
            QuestionnaireTemplateDB.code == "GAD7"
        ).first()
        
        if not gad7_template:
            gad7_template = QuestionnaireTemplateDB(
                code="GAD7",
                name="GAD-7 焦虑量表",
                description="广泛性焦虑障碍7项量表，用于评估焦虑症状的严重程度。共7题，总分0-21分。",
                questions=GAD7_QUESTIONS,
                scoring_rules={"calculation": "sum", "total_questions": 7},
                is_active=True
            )
            db.add(gad7_template)
            print("✓ 创建 GAD-7 模板")
        else:
            print("✓ GAD-7 模板已存在")
        
        db.commit()
        
        # 3. 创建 PHQ-9 评分规则
        for rule in PHQ9_SCORING_RULES:
            existing = db.query(QuestionnaireScoringRuleDB).filter(
                QuestionnaireScoringRuleDB.template_code == "PHQ9",
                QuestionnaireScoringRuleDB.rule_type == rule["type"],
                QuestionnaireScoringRuleDB.rule_config == rule["config"]
            ).first()
            
            if not existing:
                new_rule = QuestionnaireScoringRuleDB(
                    template_code="PHQ9",
                    rule_type=rule["type"],
                    rule_config=rule["config"],
                    priority=rule["priority"],
                    is_active=True
                )
                db.add(new_rule)
        
        print("✓ 创建 PHQ-9 评分规则")
        
        # 4. 创建 PHQ-9 建议规则
        for level, content in PHQ9_SUGGESTIONS.items():
            existing = db.query(QuestionnaireScoringRuleDB).filter(
                QuestionnaireScoringRuleDB.template_code == "PHQ9",
                QuestionnaireScoringRuleDB.rule_type == "suggestion",
                QuestionnaireScoringRuleDB.rule_config["level"].as_string() == level
            ).first()
            
            if not existing:
                new_rule = QuestionnaireScoringRuleDB(
                    template_code="PHQ9",
                    rule_type="suggestion",
                    rule_config={"level": level, **content},
                    priority=0,
                    is_active=True
                )
                db.add(new_rule)
        
        print("✓ 创建 PHQ-9 建议规则")
        
        # 5. 创建 GAD-7 评分规则
        for rule in GAD7_SCORING_RULES:
            existing = db.query(QuestionnaireScoringRuleDB).filter(
                QuestionnaireScoringRuleDB.template_code == "GAD7",
                QuestionnaireScoringRuleDB.rule_type == rule["type"],
                QuestionnaireScoringRuleDB.rule_config == rule["config"]
            ).first()
            
            if not existing:
                new_rule = QuestionnaireScoringRuleDB(
                    template_code="GAD7",
                    rule_type=rule["type"],
                    rule_config=rule["config"],
                    priority=rule["priority"],
                    is_active=True
                )
                db.add(new_rule)
        
        print("✓ 创建 GAD-7 评分规则")
        
        # 6. 创建 GAD-7 建议规则
        for level, content in GAD7_SUGGESTIONS.items():
            existing = db.query(QuestionnaireScoringRuleDB).filter(
                QuestionnaireScoringRuleDB.template_code == "GAD7",
                QuestionnaireScoringRuleDB.rule_type == "suggestion",
                QuestionnaireScoringRuleDB.rule_config["level"].as_string() == level
            ).first()
            
            if not existing:
                new_rule = QuestionnaireScoringRuleDB(
                    template_code="GAD7",
                    rule_type="suggestion",
                    rule_config={"level": level, **content},
                    priority=0,
                    is_active=True
                )
                db.add(new_rule)
        
        print("✓ 创建 GAD-7 建议规则")
        
        db.commit()
        print("\n问卷数据初始化完成！")
        
    except Exception as e:
        db.rollback()
        print(f"初始化失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    init_questionnaires()
