"""
调理师智能体 (Therapist Agent)
职责：根据分析师的分析报告，生成面向用户的最终疏导方案，包含具体可操作的建议。
"""
from typing import Dict, Any, List
import time
from datetime import datetime
import uuid

from backend.agents.base_agent import BaseAgent
from backend.core.rule_engine import RuleEngine
from backend.core.data_models import (
    SuggestionReport, DailySuggestion
)
from backend.repositories.record_repository import RecordRepository


class TherapistAgent(BaseAgent):
    """调理师智能体 - 生成具体可操作的建议"""
    
    def __init__(self, agent_name: str = "therapist_agent"):
        super().__init__(agent_name)
        self.rule_engine = RuleEngine()
        self.repository = RecordRepository()
        
        # 性能监控
        self.suggestion_count = 0
        self.total_suggestion_time = 0.0
    
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行建议生成任务"""
        start_time = time.time()
        
        try:
            # 1. 验证输入
            report_id = input_data.get("report_id")
            if not report_id:
                raise ValueError("缺少report_id参数")
            
            # 2. 从数据库获取分析报告
            analysis_report = await self.repository.get_analysis_report_by_id(report_id)
            if not analysis_report:
                raise ValueError(f"未找到ID为{report_id}的分析报告")
            
            # 3. 生成建议报告
            suggestion_report = await self._generate_suggestion_report(
                analysis_report, start_time
            )
            
            # 4. 保存报告到数据库
            suggestion_id = await self.repository.save_suggestion_report(suggestion_report)
            
            # 5. 更新性能统计
            elapsed_time = time.time() - start_time
            self._update_performance_stats(elapsed_time)
            
            return {
                "agent": self.agent_name,
                "status": "success",
                "suggestion_id": suggestion_id,
                "suggestion_summary": {
                    "target_issues_count": len(suggestion_report.target_issues),
                    "daily_suggestions_count": len(suggestion_report.daily_suggestions),
                    "processing_time": elapsed_time
                }
            }
            
        except Exception as e:
            return {
                "agent": self.agent_name,
                "status": "error",
                "error": str(e),
                "processing_time": time.time() - start_time
            }
    
    async def _generate_suggestion_report(self, analysis_report: Any, start_time: float) -> SuggestionReport:
        """生成建议报告"""
        # 计算实际生成耗时
        generation_duration = time.time() - start_time
        
        # 生成建议报告ID
        suggestion_id = f"sug_{uuid.uuid4().hex[:8]}"
        
        # 从分析报告中提取目标问题
        target_issues = self._extract_target_issues(analysis_report)
        
        # 生成核心理念
        core_principles = self._generate_core_principles(analysis_report)
        
        # 生成每日建议
        daily_suggestions = self._generate_daily_suggestions(analysis_report)
        
        # 生成紧急应对技巧
        emergency_tips = self._generate_emergency_tips(analysis_report)
        
        # 生成鼓励性结语
        encouragement = self._generate_encouragement()
        
        # 生成计划总结
        plan_summary = self._generate_plan_summary(daily_suggestions)
        
        return SuggestionReport(
            suggestion_id=suggestion_id,
            report_id=analysis_report.report_id,
            user_id=analysis_report.user_id,
            timestamp=datetime.utcnow(),
            target_issues=target_issues,
            core_principles=core_principles,
            daily_suggestions=daily_suggestions,
            emergency_tips=emergency_tips,
            encouragement=encouragement,
            plan_summary=plan_summary
        )
    
    def _extract_target_issues(self, analysis_report: Any) -> List[str]:
        """从分析报告中提取目标问题"""
        target_issues = []
        
        # 从CBT分析中提取问题
        cbt_analysis = analysis_report.cbt_analysis
        for distortion in cbt_analysis.distortions_detected:
            target_issues.append(f"{distortion.distortion_type}导致的{distortion.matched_thought}")
        
        # 从中医分析中提取问题
        tcm_analysis = analysis_report.tcm_analysis
        dominant_emotion = tcm_analysis.dominant_emotion
        target_issues.append(f"{dominant_emotion.type}情绪（{dominant_emotion.type}）影响{dominant_emotion.affected_zang}气")
        
        # 从次要情绪中提取问题
        for emotion in tcm_analysis.secondary_emotions:
            target_issues.append(f"{emotion.type}过度影响{emotion.affected_zang}脏")
        
        return target_issues[:3]  # 最多返回3个问题
    
    def _generate_core_principles(self, analysis_report: Any) -> List[str]:
        """生成核心理念"""
        core_principles = []
        
        # 根据CBT分析生成核心理念
        cbt_analysis = analysis_report.cbt_analysis
        if cbt_analysis.distortions_detected:
            core_principles.append("认知重构：挑战极端想法，建立合理认知")
        
        # 根据中医分析生成核心理念
        tcm_analysis = analysis_report.tcm_analysis
        core_principles.append(f"情志相胜：用{tcm_analysis.inhibiting_emotion}能量平衡{ tcm_analysis.dominant_emotion.type}")
        
        # 添加身心同调原则
        core_principles.append("身心同调：通过身体练习改善情绪")
        
        return core_principles
    
    def _generate_daily_suggestions(self, analysis_report: Any) -> List[DailySuggestion]:
        """生成每日可执行建议"""
        daily_suggestions = []
        
        # 认知类建议
        daily_suggestions.append(DailySuggestion(
            title="思维记录练习",
            description="每天出现负面思维时，记录具体情境、自动思维、替代思维，尝试写下至少一个反例。",
            duration=5,
            type="认知"
        ))
        
        # 情志类建议
        tcm_analysis = analysis_report.tcm_analysis
        daily_suggestions.append(DailySuggestion(
            title=f"{tcm_analysis.inhibiting_emotion}能量呼吸法",
            description=f"晨起练习：吸气时想象{self._get_emotion_color(tcm_analysis.inhibiting_emotion)}色能量进入身体，呼气时释放负面情绪，重复5次。",
            duration=3,
            type="情志"
        ))
        
        # 行为类建议
        daily_suggestions.append(DailySuggestion(
            title="积极行动练习",
            description="每天完成一件让自己感到成就的小事情，无论大小，记录下来并感受成就感。",
            duration=10,
            type="行为"
        ))
        
        # 身体类建议
        daily_suggestions.append(DailySuggestion(
            title="经络疏通练习",
            description="每天按摩太冲穴（位于脚背第一、二跖骨结合部前方凹陷处）5分钟，有助于疏解情绪。",
            duration=5,
            type="身体"
        ))
        
        return daily_suggestions
    
    def _generate_emergency_tips(self, analysis_report: Any) -> List[str]:
        """生成紧急应对技巧"""
        emergency_tips = [
            "当情绪突然低落时，立刻做5次深呼吸，将注意力集中在呼气上。",
            "尝试'4-7-8'呼吸法：吸气4秒，屏息7秒，呼气8秒，重复3次。",
            "起身活动一下，喝一杯温水，看看窗外的景色，转移注意力。"
        ]
        
        return emergency_tips
    
    def _generate_encouragement(self) -> str:
        """生成鼓励性结语"""
        encouragements = [
            "每一次觉察和练习，都是在为自己积攒内在的力量。你并不孤单，这个系统会一直陪伴你。",
            "改变需要时间和耐心，你已经迈出了重要的第一步。坚持下去，你会看到自己的成长。",
            "记住，情绪是暂时的，而你的内在力量是永恒的。相信自己，你有能力度过难关。",
            "每一个小进步都值得庆祝，你正在成为更好的自己。"
        ]
        
        # 随机选择一个鼓励语
        import random
        return random.choice(encouragements)
    
    def _generate_plan_summary(self, daily_suggestions: List[DailySuggestion]) -> str:
        """生成计划总结"""
        total_duration = sum(suggestion.duration for suggestion in daily_suggestions)
        
        # 统计各类建议的数量
        type_count = {}
        for suggestion in daily_suggestions:
            type_count[suggestion.type] = type_count.get(suggestion.type, 0) + 1
        
        # 生成总结
        type_str = ", ".join([f"{count}个{type}" for type, count in type_count.items()])
        
        return f"本周重点：{type_str}练习，每日{total_duration}分钟，坚持执行，培养健康的情绪管理习惯。"
    
    def _get_emotion_color(self, emotion: str) -> str:
        """根据情绪类型返回对应的颜色"""
        color_map = {
            "喜": "红",
            "怒": "红",
            "忧": "白",
            "思": "黄",
            "恐": "黑"
        }
        return color_map.get(emotion, "红")
    
    def _update_performance_stats(self, elapsed_time: float):
        """更新性能统计"""
        self.suggestion_count += 1
        self.total_suggestion_time += elapsed_time
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """获取性能指标"""
        if self.suggestion_count == 0:
            avg_time = 0.0
        else:
            avg_time = self.total_suggestion_time / self.suggestion_count
        
        return {
            "agent_name": self.agent_name,
            "total_suggestions": self.suggestion_count,
            "average_time_seconds": round(avg_time, 3),
            "total_suggestion_time": round(self.total_suggestion_time, 3),
            "status": "active"
        }
