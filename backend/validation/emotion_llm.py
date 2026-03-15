"""
LLM情绪识别准确性测试脚本
功能：测试LLM是否能从对话中提取情绪词并将其归类到中医情志（忧、怒、思等）
要求：安装依赖库 openai, pandas, matplotlib, seaborn, scikit-learn
使用方法：
    python test_emotion_recognition.py --test_file test_samples.jsonl --output_dir results
"""

import os
import json
import argparse
import time
from typing import List, Dict, Any, Optional, Tuple
from collections import Counter

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score, precision_recall_fscore_support

# 导入项目的LLM服务
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.llm_service import LLMService

# 定义中医情志类别（可根据需要修改）
AFFECT_CATEGORIES = ["喜", "怒", "忧", "思", "悲", "恐", "惊"]

# 提示词模板（包含few-shot示例）
SYSTEM_PROMPT = """你是一个情感分析专家。请根据用户输入的对话内容，提取其中表达情绪的词（如焦虑、开心、愤怒等），并将其归类到中医情志理论中的七情之一（喜、怒、忧、思、悲、恐、惊）。

注意：
- 焦虑、担心、忧愁、忧郁等词归类为“忧”。
- 害怕、紧张、惊恐等词归类为“恐”。
- 悲伤、难过、伤心等词归类为“悲”。
- 生气、愤怒、恼火等词归类为“怒”。
- 高兴、喜悦、愉快等词归类为“喜”。
- 思念、怀念、思虑等词归类为“思”。
- 惊讶、吃惊等词归类为“惊”。

请以JSON格式输出，包含两个字段：
- "emotion_words": 提取到的情绪词列表（如果没有情绪词则为空列表）
- "affect_category": 主要情志类别（如果没有情绪词则为"无"）

示例：
用户：明天要面试了，我好焦虑啊。
输出：{{"emotion_words": ["焦虑"], "affect_category": "忧"}}

用户：看到老朋友真开心！
输出：{{"emotion_words": ["开心"], "affect_category": "喜"}}

用户：他居然骗了我，气死我了。
输出：{{"emotion_words": ["气"], "affect_category": "怒"}}

用户：今天天气不错。
输出：{{"emotion_words": [], "affect_category": "无"}}
"""

USER_PROMPT_TEMPLATE = "用户：{text}\n输出："

# 解析命令行参数
def parse_args():
    parser = argparse.ArgumentParser(description="测试LLM情绪识别准确性")
    parser.add_argument("--test_file", type=str, required=True,
                        help="测试集文件路径（JSONL格式，每行包含text, expected_emotion_words, expected_affect_category）")
    parser.add_argument("--output_dir", type=str, default="results",
                        help="输出目录，用于保存结果和图表")
    parser.add_argument("--model", type=str, default="gpt-3.5-turbo",
                        help="使用的OpenAI模型名称")
    parser.add_argument("--api_key", type=str, default=None,
                        help="OpenAI API密钥，若不提供则读取环境变量OPENAI_API_KEY")
    parser.add_argument("--max_tokens", type=int, default=100,
                        help="API调用最大生成token数")
    parser.add_argument("--temperature", type=float, default=0.0,
                        help="采样温度，0表示确定性输出")
    parser.add_argument("--delay", type=float, default=0.5,
                        help="请求间隔时间（秒），避免触发限流")
    return parser.parse_args()

# 初始化LLM服务
def init_llm_service() -> LLMService:
    """初始化项目的LLM服务"""
    try:
        # 创建LLMService实例，使用deepseek提供商
        llm_service = LLMService(provider="deepseek")
        return llm_service
    except Exception as e:
        print(f"初始化LLM服务失败：{e}")
        raise

# 调用LLM获取情绪分析结果
async def async_call_llm(llm_service: LLMService, text: str, max_tokens: int, temperature: float) -> Dict[str, Any]:
    try:
        # 构建消息
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": USER_PROMPT_TEMPLATE.format(text=text)}
        ]
        
        # 调用LLM服务，确保只使用deepseek，不尝试其他提供商
        content = await llm_service.chat_completion(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            json_mode=True,  # 强制JSON输出
            try_all_providers=False  # 只使用当前配置的提供商（deepseek）
        )
        
        # 解析JSON
        result = json.loads(content)
        # 确保字段存在
        if "emotion_words" not in result:
            result["emotion_words"] = []
        if "affect_category" not in result:
            result["affect_category"] = "无"
        return result
    except Exception as e:
        print(f"API调用或解析失败：{e}")
        return {"emotion_words": [], "affect_category": "无", "error": str(e)}

# 同步包装函数
def call_llm(llm_service: LLMService, text: str, model: str, max_tokens: int, temperature: float) -> Dict[str, Any]:
    import asyncio
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        # 直接创建LLMService实例并使用deepseek提供商
        async def run_with_service():
            async with LLMService(provider="deepseek") as service:
                # 确保只使用deepseek，不尝试其他提供商
                return await async_call_llm(service, text, max_tokens, temperature)
        return loop.run_until_complete(run_with_service())
    finally:
        loop.close()

# 加载测试集
def load_test_data(file_path: str) -> List[Dict]:
    samples = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            samples.append(json.loads(line))
    return samples

# 评估情绪词提取
def evaluate_emotion_words(predicted: List[str], expected: List[str]) -> Tuple[int, int, int]:
    """
    返回 (TP, FP, FN) 基于词级别的匹配
    如果多个词，采用集合比较：预测词集合与期望词集合的交集为TP，预测多余为FP，期望缺失为FN
    """
    pred_set = set(predicted)
    exp_set = set(expected)
    tp = len(pred_set & exp_set)
    fp = len(pred_set - exp_set)
    fn = len(exp_set - pred_set)
    return tp, fp, fn

# 生成混淆矩阵并保存
def plot_confusion_matrix(cm, classes, save_path):
    plt.figure(figsize=(8, 6))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', xticklabels=classes, yticklabels=classes)
    plt.xlabel('预测类别')
    plt.ylabel('真实类别')
    plt.title('情志分类混淆矩阵')
    plt.tight_layout()
    plt.savefig(save_path)
    plt.close()

def main():
    args = parse_args()
    
    # 初始化LLM服务
    llm_service = init_llm_service()
    
    try:
        # 初始化异步上下文
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(llm_service.__aenter__())
        
        # 创建输出目录
        os.makedirs(args.output_dir, exist_ok=True)

        # 加载测试数据
        samples = load_test_data(args.test_file)
        print(f"加载了 {len(samples)} 个测试样本")

        # 存储结果
        results = []
        tp_word_total = 0
        fp_word_total = 0
        fn_word_total = 0
        y_true = []   # 真实情志类别
        y_pred = []   # 预测情志类别
        affect_categories_with_none = AFFECT_CATEGORIES + ["无"]

        for idx, sample in enumerate(samples):
            text = sample["text"]
            expected_words = sample.get("expected_emotion_words", [])
            expected_affect = sample.get("expected_affect_category", "无")

            print(f"处理样本 {idx+1}/{len(samples)}: {text[:50]}...")

            # 调用LLM
            pred = call_llm(llm_service, text, args.model, args.max_tokens, args.temperature)
            pred_words = pred.get("emotion_words", [])
            pred_affect = pred.get("affect_category", "无")

            # 记录
            sample_result = {
                "text": text,
                "expected_words": expected_words,
                "expected_affect": expected_affect,
                "predicted_words": pred_words,
                "predicted_affect": pred_affect,
                "error": pred.get("error", "")
            }
            results.append(sample_result)

            # 更新词级别统计
            tp, fp, fn = evaluate_emotion_words(pred_words, expected_words)
            tp_word_total += tp
            fp_word_total += fp
            fn_word_total += fn

            # 更新情志分类统计（只考虑有情绪的情况？这里我们包括所有样本）
            y_true.append(expected_affect)
            y_pred.append(pred_affect)

            # 延迟，避免限流
            time.sleep(args.delay)

        # 保存详细结果到CSV
        df = pd.DataFrame(results)
        df.to_csv(os.path.join(args.output_dir, "detailed_results.csv"), index=False, encoding='utf-8-sig')

        # 计算词级别指标
        precision_word = tp_word_total / (tp_word_total + fp_word_total) if (tp_word_total + fp_word_total) > 0 else 0
        recall_word = tp_word_total / (tp_word_total + fn_word_total) if (tp_word_total + fn_word_total) > 0 else 0
        f1_word = 2 * precision_word * recall_word / (precision_word + recall_word) if (precision_word + recall_word) > 0 else 0

        print("\n===== 情绪词提取评估 =====")
        print(f"精确率 (Precision): {precision_word:.4f}")
        print(f"召回率 (Recall): {recall_word:.4f}")
        print(f"F1分数: {f1_word:.4f}")

        # 计算情志分类指标（所有类别，包括"无"）
        # 使用sklearn的classification_report
        # 注意：y_true和y_pred中可能包含不在预定义类别中的值，需要处理
        # 收集实际出现的所有类别
        all_labels = set(y_true + y_pred)
        # 确保"无"类别存在
        if "无" not in all_labels:
            all_labels.add("无")
        # 按预定义顺序排序，确保一致性
        valid_labels = [label for label in AFFECT_CATEGORIES if label in all_labels] + (["无"] if "无" in all_labels else [])
        
        # 将标签转换为数字编码
        label_to_id = {label: i for i, label in enumerate(valid_labels)}
        y_true_ids = [label_to_id.get(l, -1) for l in y_true]
        y_pred_ids = [label_to_id.get(l, -1) for l in y_pred]
        # 移除无效标签（-1）
        valid_indices = [i for i, (t, p) in enumerate(zip(y_true_ids, y_pred_ids)) if t != -1 and p != -1]
        y_true_filtered = [y_true_ids[i] for i in valid_indices]
        y_pred_filtered = [y_pred_ids[i] for i in valid_indices]

        if len(y_true_filtered) > 0:
            # 计算准确率
            acc = accuracy_score(y_true_filtered, y_pred_filtered)
            print("\n===== 情志分类评估 =====")
            print(f"准确率 (Accuracy): {acc:.4f}")

            # 生成分类报告
            report = classification_report(y_true_filtered, y_pred_filtered,
                                           target_names=valid_labels, zero_division=0, output_dict=True)
            df_report = pd.DataFrame(report).transpose()
            df_report.to_csv(os.path.join(args.output_dir, "classification_report.csv"), encoding='utf-8-sig')
            print(classification_report(y_true_filtered, y_pred_filtered,
                                        target_names=valid_labels, zero_division=0))

            # 混淆矩阵
            cm = confusion_matrix(y_true_filtered, y_pred_filtered, labels=range(len(valid_labels)))
            plot_confusion_matrix(cm, valid_labels, os.path.join(args.output_dir, "confusion_matrix.png"))
            print(f"混淆矩阵已保存到 {args.output_dir}/confusion_matrix.png")
        else:
            print("没有有效的分类结果用于计算情志分类指标")

        print(f"\n详细结果已保存到 {args.output_dir}/detailed_results.csv")
    finally:
        # 关闭LLM服务
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(llm_service.__aexit__(None, None, None))

if __name__ == "__main__":
    main()