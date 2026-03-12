########     规则引擎       ###########
from typing import Dict, List, Optional, Tuple
from .data_models import CBTDistortionType, EmotionType
import jieba  # 用于中文分词分析
import re

class RuleEngine:
    """双通路规则引擎"""
    
    def __init__(self):
        self._init_cbt_rules()
        self._init_tcm_rules()
        self._init_keyword_patterns()
    
    def _init_cbt_rules(self):
        """初始化CBT认知扭曲规则库"""
        self.cbt_rules = {
            CBTDistortionType.ALL_OR_NOTHING: {
                "keywords": ["总是", "从不", "完全", "绝对", "彻底失败", "一无是处"],
                "challenge_template": "事情是否真的非黑即白？有没有中间状态或部分成功的情况？",
                "behavior_experiment": "尝试记录一周内该情境的灰色地带实例",
                "reframe_template": "虽然不完美，但我在...方面有所进步"
            },
            CBTDistortionType.OVERGENERALIZATION: {
                "keywords": ["每次", "所有人", "总是这样", "从来没", "任何事"],
                "challenge_template": "一次经历能代表所有情况吗？有哪些反例？",
                "behavior_experiment": "收集与这个概括相反的三个具体证据",
                "reframe_template": "这次的情况是特定的，不代表所有情况"
            }
            # 其他认知扭曲类型...
        }
    
    def _init_tcm_rules(self):
        """初始化中医情志相胜规则库"""
        self.tcm_rules = {
            EmotionType.ANGER: {
                "dominant_emotion": "怒",
                "keywords": ["生气", "愤怒", "暴怒", "恼火", "气愤"],
                "affected_zang": "肝",
                "common_patterns": ["肝郁气滞", "肝火上炎", "肝阳上亢"],
                "inhibiting_emotion": "悲",  # 悲胜怒
                "behavioral_adjustment": ["听商音（属金）音乐", "6秒吸气，8秒呼气法", "舒展肝胆经的拉伸"],
                "other_suggestions": ["避免辛辣刺激食物", "保持充足睡眠"]
            },
            EmotionType.WORRY: {
                "dominant_emotion": "忧",
                "keywords": ["担忧", "焦虑", "忧虑", "担心", "发愁"],
                "affected_zang": "肺",
                "common_patterns": ["肺气虚", "肺气郁", "肺阴虚"],
                "inhibiting_emotion": "喜",  # 喜胜忧
                "behavioral_adjustment": ["听徵音（属火）音乐", "腹式呼吸，想象红色能量", "开怀大笑练习"],
                "other_suggestions": ["多吃润肺食物", "适当运动"]
            },
            EmotionType.PENSIVE: {
                "dominant_emotion": "思",
                "keywords": ["思考", "思虑", "沉思", "冥想", "琢磨"],
                "affected_zang": "脾",
                "common_patterns": ["脾虚", "心脾两虚", "脾胃不和"],
                "inhibiting_emotion": "怒",  # 怒胜思
                "behavioral_adjustment": ["听角音（属木）音乐", "轻度运动", "户外活动"],
                "other_suggestions": ["饮食规律", "避免过度思虑"]
            },
            EmotionType.JOY: {
                "dominant_emotion": "喜",
                "keywords": ["高兴", "快乐", "喜悦", "开心", "兴奋"],
                "affected_zang": "心",
                "common_patterns": ["心火亢盛", "心阴不足", "心脾两虚"],
                "inhibiting_emotion": "恐",  # 恐胜喜
                "behavioral_adjustment": ["听羽音（属水）音乐", "平静呼吸", "避免过度兴奋"],
                "other_suggestions": ["保持情绪稳定", "充足休息"]
            },
            EmotionType.FEAR: {
                "dominant_emotion": "恐",
                "keywords": ["害怕", "恐惧", "担忧", "惊慌", "紧张"],
                "affected_zang": "肾",
                "common_patterns": ["肾虚", "肾阴不足", "肾阳虚"],
                "inhibiting_emotion": "思",  # 思胜恐
                "behavioral_adjustment": ["听宫音（属土）音乐", "深呼吸", "冥想放松"],
                "other_suggestions": ["适当补肾食物", "规律作息"]
            }
        }
    
    def _init_keyword_patterns(self):
        """初始化关键词匹配模式"""
        self.intensity_patterns = {
            "极度": 9, "非常": 8, "很": 7, "比较": 6, "有点": 5, "稍微": 4
        }
    
    def analyze_cbt_patterns(self, automatic_thoughts: List[str]) -> List[Dict]:
        """分析认知扭曲模式"""
        results = []
        
        for thought in automatic_thoughts:
            detected_distortions = []
            
            # 1. 关键词匹配
            for distortion_type, rule in self.cbt_rules.items():
                for keyword in rule["keywords"]:
                    if keyword in thought:
                        detected_distortions.append({
                            "type": distortion_type,
                            "matched_keyword": keyword,
                            "confidence": 0.8,
                            "evidence": thought
                        })
                        break
            
            # 2. 模式匹配（使用简单正则）
            if len(detected_distortions) == 0:
                # 匹配"全或无"模式：包含极端词汇
                if re.search(r'(完全|绝对|彻底|一点也).*(不|没有)', thought):
                    detected_distortions.append({
                        "type": CBTDistortionType.ALL_OR_NOTHING,
                        "matched_pattern": "极端词汇模式",
                        "confidence": 0.7,
                        "evidence": thought
                    })
            
            if detected_distortions:
                results.append({
                    "original_thought": thought,
                    "distortions": detected_distortions,
                    "primary_distortion": detected_distortions[0]  # 取置信度最高的
                })
        
        return results
    
    def analyze_tcm_patterns(self, emotions: List[Dict]) -> Dict:
        """分析中医情志模式"""
        if not emotions:
            return {"dominant_emotion": None, "patterns": []}
        
        # 找出主导情绪（强度最高的）
        dominant_emotion = max(emotions, key=lambda x: x.get("intensity", 0))
        emotion_type = EmotionType(dominant_emotion["type"])
        
        # 获取对应规则
        rule = self.tcm_rules.get(emotion_type, {})
        
        # 分析相生相克关系
        generating_cycle = self._get_generating_cycle(emotion_type)
        controlling_cycle = self._get_controlling_cycle(emotion_type)
        
        return {
            "dominant_emotion": {
                "type": emotion_type.value,
                "intensity": dominant_emotion["intensity"],
                "affected_zang": rule.get("affected_zang", ""),
                "common_patterns": rule.get("common_patterns", [])
            },
            "tcm_relationships": {
                "generating": generating_cycle,   # 相生
                "controlling": controlling_cycle, # 相克
                "inhibiting_emotion": rule.get("inhibiting_emotion", "")  # 相胜
            },
            "recommended_interventions": {
                "behavioral_adjustment": rule.get("behavioral_adjustment", []),
                "other_suggestions": rule.get("other_suggestions", [])
            },
            "keywords": rule.get("keywords", [])
        }
    
    def _get_generating_cycle(self, emotion: EmotionType) -> Dict:
        """获取相生关系（五行相生）"""
        cycles = {
            "怒": {"generates": "喜", "element": "木生火"},
            "喜": {"generates": "思", "element": "火生土"},
            "思": {"generates": "忧", "element": "土生金"},
            "忧": {"generates": "恐", "element": "金生水"},
            "恐": {"generates": "怒", "element": "水生木"}
        }
        return cycles.get(emotion.value, {})
    
    def _get_controlling_cycle(self, emotion: EmotionType) -> Dict:
        """获取相克关系（五行相克）"""
        cycles = {
            "怒": {"controls": "思", "controlled_by": "忧", "element": "木克土"},
            "喜": {"controls": "忧", "controlled_by": "恐", "element": "火克金"},
            "思": {"controls": "恐", "controlled_by": "怒", "element": "土克水"},
            "忧": {"controls": "怒", "controlled_by": "喜", "element": "金克木"},
            "恐": {"controls": "喜", "controlled_by": "思", "element": "水克火"}
        }
        return cycles.get(emotion.value, {})
    
    async def apply_cbt_rules(self, record):
        """应用CBT规则分析记录"""
        return self.analyze_cbt_patterns(record.automatic_thoughts)
    
    async def apply_tcm_rules(self, record):
        """应用中医情志规则分析记录"""
        return self.analyze_tcm_patterns(record.emotions)
    
    def generate_intervention_framework(self, cbt_results: List, tcm_results: Dict) -> str:
        """生成综合干预框架"""
        framework_parts = []
        
        # CBT部分
        if cbt_results:
            primary_distortion = cbt_results[0]["primary_distortion"]["type"]
            framework_parts.append(f"认知调整：针对{primary_distortion.value}，建议进行认知重构")
        
        # 中医部分
        if tcm_results.get("dominant_emotion"):
            emotion = tcm_results["dominant_emotion"]["type"]
            zang = tcm_results["dominant_emotion"]["affected_zang"]
            inhibiting = tcm_results["tcm_relationships"]["inhibiting_emotion"]
            framework_parts.append(f"情志调理：主导情志为{emotion}，伤及{zang}，适用{inhibiting}胜{emotion}原则")
        
        # 融合建议
        if framework_parts:
            return "；".join(framework_parts) + "。建议先处理急性认知扭曲，再配合情志能量调理。"
        
        return "未检测到明显的认知扭曲或情志失调模式。"