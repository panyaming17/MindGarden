"""
分析师智能体 (Analyst Agent)
职责：对记录师提供的结构化情绪信息进行专业分析（CBT + 中医情志），生成诊断报告。
"""
from typing import Dict, Any, List
import time
from datetime import datetime
import uuid

from backend.agents.base_agent import BaseAgent
from backend.core.rule_engine import RuleEngine
from backend.core.data_models import (
    StructuredRecord, DiagnosisReport, RecordReport, AnalysisReport,
    CBTAnalysis, TCMAnalysis, DistortionItem, DominantEmotion, SecondaryEmotion
)
from backend.repositories.record_repository import RecordRepository


class AnalystAgent(BaseAgent):
    """分析师智能体 - 不进行对话，只进行分析"""
    
    def __init__(self, agent_name: str = "analyst_agent"):
        super().__init__(agent_name)
        self.rule_engine = RuleEngine()
        self.repository = RecordRepository()
        
        # 性能监控
        self.analysis_count = 0
        self.total_analysis_time = 0.0
    
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行分析任务"""
        start_time = time.time()
        
        try:
            # 1. 验证输入
            record_id = input_data.get("record_id")
            if not record_id:
                raise ValueError("缺少record_id参数")
            
            # 2. 从数据库获取记录报告
            # 首先尝试获取RecordReport
            record_report = await self.repository.get_record_report_by_id(record_id)
            
            # 如果没有找到RecordReport，尝试获取StructuredRecord
            if not record_report:
                structured_record = await self.repository.get_record_by_id(record_id)
                if not structured_record:
                    raise ValueError(f"未找到ID为{record_id}的记录")
                
                # 将StructuredRecord转换为RecordReport格式
                record_report = RecordReport(
                    record_id=structured_record.record_id,
                    session_id="",
                    user_id=structured_record.user_id,
                    timestamp=structured_record.created_at,
                    duration=0.0,
                    conversation_log=[],
                    situation=structured_record.situation,
                    automatic_thoughts=structured_record.automatic_thoughts,
                    emotions=structured_record.emotions,
                    physical_sensations=structured_record.physical_sensations or [],
                    summary=""
                )
            
            # 3. 执行双通路分析
            analysis_results = await self._perform_dual_path_analysis(record_report)
            
            # 4. 生成分析报告
            analysis_report = await self._generate_analysis_report(
                record_report, analysis_results, start_time
            )
            
            # 5. 保存报告到数据库
            report_id = await self.repository.save_analysis_report(analysis_report)
            
            # 6. 更新性能统计
            elapsed_time = time.time() - start_time
            self._update_performance_stats(elapsed_time)
            
            return {
                "agent": self.agent_name,
                "status": "success",
                "report_id": report_id,
                "analysis_summary": {
                    "cbt_distortions_found": len(analysis_results["cbt"]),
                    "dominant_emotion": analysis_results["tcm"].get("dominant_emotion", {}).get("type"),
                    "confidence_score": analysis_report.confidence_score,
                    "processing_time": elapsed_time
                },
                "diagnosis_preview": {
                    "cbt_summary": self._summarize_cbt_findings(analysis_results["cbt"]),
                    "tcm_summary": self._summarize_tcm_findings(analysis_results["tcm"])
                }
            }
            
        except Exception as e:
            return {
                "agent": self.agent_name,
                "status": "error",
                "error": str(e),
                "processing_time": time.time() - start_time
            }
    
    async def _perform_dual_path_analysis(self, record: RecordReport) -> Dict[str, Any]:
        """执行双通路分析（CBT + 中医情志）"""
        # 并行执行CBT和中医分析
        cbt_results = self.rule_engine.analyze_cbt_patterns(record.automatic_thoughts)
        tcm_results = self.rule_engine.analyze_tcm_patterns(record.emotions)
        
        return {
            "cbt": cbt_results,
            "tcm": tcm_results,
            "record_id": record.record_id
        }
    
    async def _generate_analysis_report(self, record: RecordReport, 
                                        analysis_results: Dict, 
                                        start_time: float) -> AnalysisReport:
        """生成分析报告"""
        # 计算置信度
        confidence = self._calculate_confidence(analysis_results)
        
        # 生成综合干预框架
        framework = self.rule_engine.generate_intervention_framework(
            analysis_results["cbt"], analysis_results["tcm"]
        )
        
        # 计算实际分析耗时
        analysis_duration = time.time() - start_time
        
        # 生成报告ID
        report_id = f"ana_{uuid.uuid4().hex[:8]}"
        
        # 构建CBT分析结果
        cbt_analysis = CBTAnalysis(
            distortions_detected=[
                DistortionItem(
                    distortion_type=distortion.get("type", "未知类型"),
                    matched_thought=thought.get("thought", ""),
                    evidence=distortion.get("evidence", ""),
                    challenge_question=distortion.get("challenge_question")
                )
                for thought in analysis_results["cbt"]
                for distortion in thought.get("distortions", [])
            ],
            summary=self._summarize_cbt_findings(analysis_results["cbt"]),
            challenge_questions=[
                distortion.get("challenge_question")
                for thought in analysis_results["cbt"]
                for distortion in thought.get("distortions", [])
                if distortion.get("challenge_question")
            ]
        )
        
        # 构建中医情志分析结果
        tcm_result = analysis_results["tcm"]
        dominant_emotion = tcm_result.get("dominant_emotion", {})
        tcm_analysis = TCMAnalysis(
            dominant_emotion=DominantEmotion(
                type=dominant_emotion.get("type", "未知"),
                intensity=dominant_emotion.get("intensity", 0),
                affected_zang=dominant_emotion.get("affected_zang", "未知")
            ),
            inhibiting_emotion=tcm_result.get("tcm_relationships", {}).get("inhibiting_emotion", ""),
            secondary_emotions=[
                SecondaryEmotion(
                    type=emotion.get("type", "未知"),
                    intensity=emotion.get("intensity", 0),
                    affected_zang=emotion.get("affected_zang", "未知")
                )
                for emotion in tcm_result.get("secondary_emotions", [])
            ],
            recommended_interventions=tcm_result.get("recommended_interventions", [])
        )
        
        # 确定干预优先级
        priority = self._determine_priority(analysis_results)
        
        return AnalysisReport(
            report_id=report_id,
            record_id=record.record_id,
            user_id=record.user_id,
            timestamp=datetime.utcnow(),
            analysis_duration=analysis_duration,
            confidence_score=confidence,
            cbt_analysis=cbt_analysis,
            tcm_analysis=tcm_analysis,
            integrated_framework=framework,
            priority=priority
        )
    
    def _determine_priority(self, analysis_results: Dict) -> str:
        """确定干预优先级"""
        cbt_results = analysis_results.get("cbt", [])
        tcm_results = analysis_results.get("tcm", {})
        
        # 计算CBT扭曲数量
        cbt_distortions = sum(len(thought.get("distortions", [])) for thought in cbt_results)
        
        # 计算中医情绪强度
        dominant_emotion = tcm_results.get("dominant_emotion", {})
        emotion_intensity = dominant_emotion.get("intensity", 0)
        
        # 根据CBT扭曲数量和情绪强度确定优先级
        if cbt_distortions > 2 and emotion_intensity < 7:
            return "CBT优先"
        elif emotion_intensity >= 7 and cbt_distortions < 2:
            return "情志优先"
        else:
            return "并重"
    
    def _calculate_confidence(self, analysis_results: Dict) -> float:
        """计算分析置信度 (0.0 ~ 0.95)"""
        confidence_factors = []
        
        # CBT置信度因素：基于检测到的扭曲数量
        cbt_results = analysis_results["cbt"]
        if cbt_results:
            # 假设每个检测到的扭曲增加一定置信度
            total_matches = sum(len(item.get("distortions", [])) for item in cbt_results)
            confidence_factors.append(min(total_matches * 0.15, 0.4))  # 每个最多贡献0.15，上限0.4
        
        # 中医置信度因素：基于情绪强度
        tcm_results = analysis_results["tcm"]
        if tcm_results and tcm_results.get("dominant_emotion"):
            intensity = tcm_results["dominant_emotion"].get("intensity", 0)
            # 强度越高，置信度越高
            confidence_factors.append(min(intensity / 10 * 0.4, 0.4))  # 最多贡献40%
        
        # 基础置信度 + 各因素总和
        base_confidence = 0.2
        total_confidence = base_confidence + sum(confidence_factors)
        
        # 设置上限，避免过于绝对
        return min(total_confidence, 0.95)
    
    def _summarize_cbt_findings(self, cbt_results: List) -> str:
        """总结CBT分析发现"""
        if not cbt_results:
            return "未检测到明显的认知扭曲模式。"
        
        # 统计各类认知扭曲的出现次数
        distortion_counts = {}
        for thought_analysis in cbt_results:
            distortions = thought_analysis.get("distortions", [])
            for distortion in distortions:
                # 直接使用字符串类型，假设RuleEngine返回的是字符串
                d_type = distortion.get("type", "未知类型")
                if isinstance(d_type, str):  # 如果是字符串
                    distortion_counts[d_type] = distortion_counts.get(d_type, 0) + 1
                # 如果RuleEngine返回的是枚举，这里可能需要调整
        
        if not distortion_counts:
            return "检测到自动思维，但未明确归类认知扭曲类型。"
        
        # 找出出现最多的扭曲类型
        primary_type, primary_count = max(distortion_counts.items(), key=lambda x: x[1])
        return f"在{len(cbt_results)}个自动思维中识别到认知扭曲，主要类型为「{primary_type}」（出现{primary_count}次）。"
    
    def _summarize_tcm_findings(self, tcm_results: Dict) -> str:
        """总结中医情志分析发现"""
        if not tcm_results or not tcm_results.get("dominant_emotion"):
            return "未识别出主导性情志失调模式。"
        
        dominant = tcm_results["dominant_emotion"]
        emotion_type = dominant.get("type", "未知情志")
        intensity = dominant.get("intensity", 0)
        affected_organ = dominant.get("affected_zang", "相关脏腑")
        
        # 获取相胜关系（如果规则引擎提供）
        inhibiting_emotion = tcm_results.get("tcm_relationships", {}).get("inhibiting_emotion", "")
        
        summary = f"主导情志为「{emotion_type}」（强度{intensity}/10），主要影响「{affected_organ}」。"
        if inhibiting_emotion:
            summary += f" 根据情志相胜理论，可用「{inhibiting_emotion}」进行调理。"
        
        return summary
    
    def _update_performance_stats(self, elapsed_time: float):
        """更新性能统计"""
        self.analysis_count += 1
        self.total_analysis_time += elapsed_time
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """获取性能指标"""
        if self.analysis_count == 0:
            avg_time = 0.0
        else:
            avg_time = self.total_analysis_time / self.analysis_count
        
        return {
            "agent_name": self.agent_name,
            "total_analyses": self.analysis_count,
            "average_time_seconds": round(avg_time, 3),
            "total_analysis_time": round(self.total_analysis_time, 3),
            "status": "active"
        }