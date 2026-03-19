import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
from datetime import datetime

# ==================== 配置 ====================
DATA_FILE = "data/mydata/merged_data_clean_final.csv"  # 合并后的数据集
OUTPUT_DIR = "data_quality_report"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

# ==================== 读取数据 ====================
print("=" * 60)
print("数据集质量评估报告")
print("=" * 60)
df = pd.read_csv(DATA_FILE)
print(f"数据文件: {DATA_FILE}")
print(f"总样本数: {len(df)}")
print(f"数据列: {list(df.columns)}")

# 确保强度列为数值类型
print("\n【强度列转换】")
df['intensity'] = pd.to_numeric(df['intensity'], errors='coerce')
# 检查转换后是否有缺失
if df['intensity'].isnull().any():
    print(f"警告：强度列转换后产生了 {df['intensity'].isnull().sum()} 个缺失值（可能是非数字内容），这些样本将被删除。")
    df = df.dropna(subset=['intensity'])
    print(f"删除后样本数: {len(df)}")

# ==================== 缺失值检查 ====================
print("\n【1】缺失值检查")
missing = df[['text', 'intensity', 'hedonic', 'tension', 'complexity']].isnull().sum()
if missing.sum() == 0:
    print("✅ 无缺失值")
else:
    print("❌ 存在缺失值：")
    print(missing[missing > 0])
    df = df.dropna(subset=['text', 'intensity', 'hedonic', 'tension', 'complexity'])
    print(f"删除缺失值后样本数: {len(df)}")

# ==================== 重复文本检查 ====================
print("\n【2】重复文本检查")
duplicate_count = df['text'].duplicated().sum()
if duplicate_count == 0:
    print("✅ 无重复文本")
else:
    print(f"⚠️ 发现 {duplicate_count} 条重复文本（占总样本 {duplicate_count/len(df)*100:.2f}%）")
    df = df.drop_duplicates(subset=['text'])
    print(f"去重后样本数: {len(df)}")

# ==================== 文本长度分布 ====================
print("\n【3】文本长度分布")
df['text_len'] = df['text'].astype(str).apply(len)
print(f"平均长度: {df['text_len'].mean():.1f} 字符")
print(f"中位数长度: {df['text_len'].median():.1f} 字符")
print(f"最短: {df['text_len'].min()} 字符, 最长: {df['text_len'].max()} 字符")

plt.figure(figsize=(8, 4))
plt.hist(df['text_len'], bins=50, alpha=0.7)
plt.xlabel("文本长度（字符数）")
plt.ylabel("频数")
plt.title("文本长度分布")
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, "text_length_dist.png"), dpi=150)
plt.close()

# ==================== 强度分布 ====================
print("\n【4】强度分布（1-10）")
# 检查强度是否在1-10范围内
if (df['intensity'] < 1).any() or (df['intensity'] > 10).any():
    print("⚠️ 存在超出 1-10 范围的强度值")
else:
    print("✅ 强度值均在 1-10 范围内")
intensity_stats = df['intensity'].describe()
print(intensity_stats.to_string())

plt.figure(figsize=(8, 4))
plt.hist(df['intensity'], bins=20, alpha=0.7, edgecolor='black')
plt.xlabel("强度值")
plt.ylabel("频数")
plt.title("强度分布")
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, "intensity_dist.png"), dpi=150)
plt.close()

# ==================== 分类变量分布 ====================
print("\n【5】分类变量分布")

# 快感度
print("\n快感度 (hedonic):")
hedonic_counts = df['hedonic'].value_counts()
print(hedonic_counts.to_string())
if len(hedonic_counts) != 3:
    print("⚠️ 快感度类别数不是3，可能缺失某些类别")
# 检查是否严重不平衡
min_hedonic_ratio = hedonic_counts.min() / len(df)
if min_hedonic_ratio < 0.05:
    print(f"⚠️ 快感度最小类占比 {min_hedonic_ratio:.2%}，存在严重不平衡")

# 紧张度
print("\n紧张度 (tension):")
tension_counts = df['tension'].value_counts()
print(tension_counts.to_string())
if set(tension_counts.index) != {'低', '中', '高'}:
    print("⚠️ 紧张度类别可能缺失")
min_tension_ratio = tension_counts.min() / len(df)
if min_tension_ratio < 0.05:
    print(f"⚠️ 紧张度最小类占比 {min_tension_ratio:.2%}，存在严重不平衡")

# 复杂度
print("\n复杂度 (complexity):")
complexity_counts = df['complexity'].value_counts()
print(complexity_counts.to_string())
if set(complexity_counts.index) != {'简单', '复杂'}:
    print("⚠️ 复杂度类别可能缺失")
min_complexity_ratio = complexity_counts.min() / len(df)
if min_complexity_ratio < 0.05:
    print(f"⚠️ 复杂度最小类占比 {min_complexity_ratio:.2%}，存在严重不平衡")

# 绘制分类变量分布图
fig, axes = plt.subplots(1, 3, figsize=(12, 4))
hedonic_counts.plot(kind='bar', ax=axes[0], color=['green', 'blue', 'red'])
axes[0].set_title("快感度分布")
axes[0].set_xlabel("类别")
axes[0].set_ylabel("频数")
tension_counts.plot(kind='bar', ax=axes[1], color=['orange', 'purple', 'cyan'])
axes[1].set_title("紧张度分布")
axes[1].set_xlabel("类别")
complexity_counts.plot(kind='bar', ax=axes[2], color=['pink', 'gray'])
axes[2].set_title("复杂度分布")
axes[2].set_xlabel("类别")
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, "categorical_dist.png"), dpi=150)
plt.close()

# ==================== 类别组合分布 ====================
print("\n【6】类别组合分布（快感度×紧张度）")
cross = pd.crosstab(df['hedonic'], df['tension'])
print(cross)
# 可以检查是否有某些组合样本极少
print("\n类别组合分布（快感度×复杂度）")
cross2 = pd.crosstab(df['hedonic'], df['complexity'])
print(cross2)

# ==================== 总体评估 ====================
print("\n" + "=" * 60)
print("【7】总体评估结论")
print("=" * 60)

warnings = []
if len(df) < 1000:
    warnings.append(f"样本量较小（{len(df)}条），可能影响模型泛化能力，建议扩充数据。")
if min_hedonic_ratio < 0.05:
    warnings.append(f"快感度类别严重不平衡（最小类占比 {min_hedonic_ratio:.2%}），训练时需使用类别权重或过采样。")
if min_tension_ratio < 0.05:
    warnings.append(f"紧张度类别严重不平衡（最小类占比 {min_tension_ratio:.2%}），训练时需使用类别权重或过采样。")
if min_complexity_ratio < 0.05:
    warnings.append(f"复杂度类别严重不平衡（最小类占比 {min_complexity_ratio:.2%}），训练时需使用类别权重或过采样。")
if duplicate_count > 0:
    warnings.append(f"存在重复文本（{duplicate_count}条），已去重。")
if missing.sum() > 0:
    warnings.append(f"存在缺失值（{missing.sum()}条），已删除。")
if df['text_len'].min() < 10:
    warnings.append("存在极短文本（少于10字符），可能影响语义理解。")
if df['text_len'].max() > 500:
    warnings.append("存在超长文本（超过500字符），可能超出模型处理能力，建议截断或分段。")
if (df['intensity'] < 1).any() or (df['intensity'] > 10).any():
    warnings.append("强度值存在超出1-10范围的情况，需检查数据。")

if not warnings:
    print("✅ 数据集质量较好，适合用于训练。")
else:
    print("⚠️ 数据集存在以下问题，建议处理后再训练：")
    for w in warnings:
        print(f"  - {w}")

# 保存报告文本
with open(os.path.join(OUTPUT_DIR, "data_quality_report.txt"), "w", encoding="utf-8") as f:
    f.write("数据集质量评估报告\n")
    f.write("=" * 50 + "\n")
    f.write(f"数据文件: {DATA_FILE}\n")
    f.write(f"总样本数: {len(df)}\n\n")
    f.write("【1】缺失值检查\n")
    f.write(f"缺失值情况: {missing.to_string()}\n\n")
    f.write("【2】重复文本检查\n")
    f.write(f"重复文本数: {duplicate_count}\n\n")
    f.write("【3】文本长度分布\n")
    f.write(f"平均长度: {df['text_len'].mean():.1f} 字符\n")
    f.write(f"中位数: {df['text_len'].median():.1f} 字符\n")
    f.write(f"范围: {df['text_len'].min()} - {df['text_len'].max()}\n\n")
    f.write("【4】强度分布\n")
    f.write(intensity_stats.to_string() + "\n\n")
    f.write("【5】分类变量分布\n")
    f.write("快感度:\n")
    f.write(hedonic_counts.to_string() + "\n")
    f.write("紧张度:\n")
    f.write(tension_counts.to_string() + "\n")
    f.write("复杂度:\n")
    f.write(complexity_counts.to_string() + "\n\n")
    f.write("【6】总体结论\n")
    if warnings:
        f.write("存在问题：\n")
        for w in warnings:
            f.write(f"  - {w}\n")
    else:
        f.write("数据集质量良好，适合训练。\n")

print(f"\n报告已保存至: {OUTPUT_DIR}/")
print("图表已保存至相同目录。")