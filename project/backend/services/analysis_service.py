########     分析师智能体       ###########
from typing import Dict, Any
import time
from .base_agent import BaseAgent
from core.rule_engine import RuleEngine
from core.data_models import StructuredRecord, DiagnosisReport
from repositories.record_repository import RecordRepository

class AnalystAgent(BaseAgent):
    """分析师智能体 - 不进行对话，只进行分析"""
    
    def __init__(self, agent_name: str = "analyst_agent"):
        super().__init__(agent_name)
        self.rule_engine = RuleEngine()
        self.repository = RecordRepository()
        
        # 性能监控
        self.analysis_count = 0
        self.total_analysis_time = 0
    
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行分析任务"""
        start_time = time.time()
        
        try:
            # 1. 验证输入
            record_id = input_data.get("record_id")
            if not record_id:
                raise ValueError("缺少record_id参数")
            
            # 2. 从数据库获取结构化记录
            structured_record = await self.repository.get_record_by_id(record_id)
            if not structured_record:
                raise ValueError(f"未找到ID为{record_id}的记录")
            
            # 3. 执行双通路分析
            analysis_results = await self._perform_dual_path_analysis(structured_record)
            
            # 4. 生成诊断报告
            diagnosis_report = await self._generate_diagnosis_report(
                structured_record, analysis_results
            )
            
            # 5. 保存报告到数据库
            report_id = await self.repository.save_diagnosis_report(diagnosis_report)
            
            # 6. 更新性能统计
            elapsed_time = time.time() - start_time
            self._update_performance_stats(elapsed_time)
            
            return {
                "status": "success",
                "report_id": report_id,
                "analysis_summary": {
                    "cbt_distortions_found": len(analysis_results["cbt"]),
                    "dominant_emotion": analysis_results["tcm"].get("dominant_emotion", {}).get("type"),
                    "confidence_score": diagnosis_report.confidence_score,
                    "processing_time": elapsed_time
                }
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "processing_time": time.time() - start_time
            }
    
    async def _perform_dual_path_analysis(self, record: StructuredRecord) -> Dict[str, Any]:
        """执行双通路分析"""
        # 并行执行CBT和中医分析
        cbt_results = self.rule_engine.analyze_cbt_patterns(record.automatic_thoughts)
        tcm_results = self.rule_engine.analyze_tcm_patterns(record.emotions)
        
        return {
            "cbt": cbt_results,
            "tcm": tcm_results,
            "record_id": record.record_id
        }
    
    async def _generate_diagnosis_report(self, record: StructuredRecord, analysis_results: Dict) -> DiagnosisReport:
        """生成诊断报告"""
        # 计算置信度
        confidence = self._calculate_confidence(analysis_results)
        
        # 生成综合框架
        framework = self.rule_engine.generate_intervention_framework(
            analysis_results["cbt"], analysis_results["tcm"]
        )
        
        return DiagnosisReport(
            id=f"report_{record.record_id}_{int(time.time())}",
            record_id=record.record_id,
            user_id=record.user_id,
            cbt_analysis={
                "distortions_detected": analysis_results["cbt"],
                "summary": self._summarize_cbt_findings(analysis_results["cbt"])
            },
            tcm_analysis={
                "patterns_detected": analysis_results["tcm"],
                "summary": self._summarize_tcm_findings(analysis_results["tcm"])
            },
            comprehensive_framework=framework,
            confidence_score=confidence,
            analysis_duration=time.time(),  # 会在execute中修正
            created_at=time.time()
        )
    
    def _calculate_confidence(self, analysis_results: Dict) -> float:
        """计算分析置信度"""
        confidence_factors = []
        
        # CBT置信度因素
        cbt_results = analysis_results["cbt"]
        if cbt_results:
            # 基于匹配的关键词数量和类型
            total_matches = sum(len(item["distortions"]) for item in cbt_results)
            confidence_factors.append(min(total_matches * 0.2, 0.4))  # 最多贡献40%
        
        # 中医置信度因素
        tcm_results = analysis_results["tcm"]
        if tcm_results.get("dominant_emotion"):
            intensity = tcm_results["dominant_emotion"].get("intensity", 0)
            confidence_factors.append(min(intensity / 10 * 0.4, 0.4))  # 最多贡献40%
        
        # 基础置信度
        base_confidence = 0.2
        
        return min(base_confidence + sum(confidence_factors), 0.95)  # 上限95%
    
    def _summarize_cbt_findings(self, cbt_results: List) -> str:
        """总结CBT发现"""
        if not cbt_results:
            return "未检测到明显的认知扭曲模式。"
        
        distortion_counts = {}
        for result in cbt_results:
            for distortion in result["distortions"]:
                d_type = distortion["type"].value
                distortion_counts[d_type] = distortion_counts.get(d_type, 0) + 1
        
        primary = max(distortion_counts.items(), key=lambda x: x[1]) if distortion_counts else ("", 0)
        return f"检测到{len(cbt_results)}个自动思维中存在认知扭曲，主要类型为'{primary[0]}'（出现{primary[1]}次）。"
    
    def _summarize_tcm_findings(self, tcm_results: Dict) -> str:
        """总结中医发现"""
        if not tcm_results.get("dominant_emotion"):
            return "未识别出主导性情志失调。"
        
        emotion = tcm_results["dominant_emotion"]["type"]
        intensity = tcm_results["dominant_emotion"]["intensity"]
        organ = tcm_results["dominant_emotion"]["affected_zang"]
        
        return f"主导情志为{emotion}（强度{intensity}/10），主要影响{organ}脏功能。"
    
    def _update_performance_stats(self, elapsed_time: float):
        """更新性能统计"""
        self.analysis_count += 1
        self.total_analysis_time += elapsed_time
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """获取性能指标"""
        avg_time = self.total_analysis_time / self.analysis_count if self.analysis_count > 0 else 0
        return {
            "total_analyses": self.analysis_count,
            "average_time_seconds": avg_time,
            "status": "active"
        }