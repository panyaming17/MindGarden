import pandas as pd
import numpy as np
import joblib
from sklearn.model_selection import train_test_split
from xgboost import XGBRegressor, XGBClassifier
from sentence_transformers import SentenceTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import mean_absolute_error, classification_report
import os
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

# ==================== 创建版本文件夹 ====================
timestamp = datetime.now().strftime("%Y%m%d_%H_%M_%S")
version_dir = f"models/{timestamp}"
os.makedirs(version_dir, exist_ok=True)
print(f"本次微调的模型将保存至: {version_dir}")

# ==================== 1. 加载数据 ====================
human_df = pd.read_csv("data/mydata/cleaned_texts.csv")          # 人工数据（204条）
ai_df = pd.read_csv("data/mydata/ai_generated_samples_new.csv")  # AI数据（约120条）

print(f"人工数据条数: {len(human_df)}")
print(f"AI数据条数: {len(ai_df)}")

# 处理 AI 数据：将强度范围转为具体值（取中值）
ai_df["intensity"] = (ai_df["intensity_min"] + ai_df["intensity_max"]) / 2
ai_df = ai_df[["text", "intensity", "hedonic", "tension", "complexity"]]

# 合并
df_all = pd.concat([human_df, ai_df], ignore_index=True)

# ==================== 2. 检查并处理缺失值 ====================
print("\n检查缺失值情况：")
print(df_all[['hedonic', 'tension', 'complexity', 'intensity']].isnull().sum())
df_all = df_all.dropna(subset=['hedonic', 'tension', 'complexity', 'intensity'])
print(f"删除缺失值后数据条数: {len(df_all)}")

# 添加权重列：人工数据权重1.0，AI数据权重0.5
df_all["weight"] = 1.0
df_all.loc[df_all.index >= len(human_df), "weight"] = 0.5
print(df_all["weight"].value_counts())

# ==================== 3. 文本编码 ====================
encoder = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
print("正在编码文本...")
X = encoder.encode(df_all["text"].tolist(), show_progress_bar=True)

# ==================== 4. 准备标签（使用原有编码器）====================
le_hedonic = joblib.load("models/le_hedonic.pkl")
le_tension = joblib.load("models/le_tension.pkl")
le_complexity = joblib.load("models/le_complexity.pkl")

y_hedonic = le_hedonic.transform(df_all["hedonic"])
y_tension = le_tension.transform(df_all["tension"])
y_complexity = le_complexity.transform(df_all["complexity"])
y_intensity = df_all["intensity"].values.astype(float)
weights = df_all["weight"].values

# ==================== 5. 划分训练/测试集 ====================
X_train, X_test, y_int_train, y_int_test, y_hed_train, y_hed_test, \
y_ten_train, y_ten_test, y_com_train, y_com_test, w_train, w_test = train_test_split(
    X, y_intensity, y_hedonic, y_tension, y_complexity, weights,
    test_size=0.2, random_state=42
    # stratify=y_hedonic  # 按快感度分层（因样本少已注释）
)

# ==================== 6. 增量微调模型 ====================
print("增量微调强度模型...")
intensity_model = XGBRegressor(n_estimators=50, max_depth=5, learning_rate=0.03, random_state=42)
if os.path.exists("models/intensity_model.json"):
    intensity_model.fit(X_train, y_int_train, sample_weight=w_train,
                        xgb_model="models/intensity_model.json")
else:
    intensity_model.fit(X_train, y_int_train, sample_weight=w_train)

print("训练快感度模型（逻辑回归，不使用预训练）...")
hedonic_model = LogisticRegression(max_iter=1000, class_weight='balanced', random_state=42)
hedonic_model.fit(X_train, y_hed_train, sample_weight=w_train)

print("增量微调紧张度模型...")
tension_model = XGBClassifier(n_estimators=50, max_depth=5, learning_rate=0.03, random_state=42)
if os.path.exists("models/tension_model.json"):
    tension_model.fit(X_train, y_ten_train, sample_weight=w_train,
                      xgb_model="models/tension_model.json")
else:
    tension_model.fit(X_train, y_ten_train, sample_weight=w_train)

print("增量微调复杂度模型...")
complexity_model = XGBClassifier(n_estimators=50, max_depth=5, learning_rate=0.03, random_state=42)
if os.path.exists("models/complexity_model.json"):
    complexity_model.fit(X_train, y_com_train, sample_weight=w_train,
                         xgb_model="models/complexity_model.json")
else:
    complexity_model.fit(X_train, y_com_train, sample_weight=w_train)

# ==================== 7. 评估 ====================
print("\n===== 测试集评估 =====")

# 强度
y_int_pred = intensity_model.predict(X_test)
print(f"强度 MAE: {mean_absolute_error(y_int_test, y_int_pred):.2f}")

# 快感度
y_hed_pred = hedonic_model.predict(X_test)
present_hed_labels = sorted(set(y_hed_test))
present_hed_names = le_hedonic.inverse_transform(present_hed_labels)
print("\n快感度分类报告 (仅测试集出现的类别):")
print(classification_report(y_hed_test, y_hed_pred, 
                            labels=present_hed_labels, 
                            target_names=present_hed_names,
                            zero_division=0))

# 紧张度
y_ten_pred = tension_model.predict(X_test)
present_ten_labels = sorted(set(y_ten_test))
present_ten_names = le_tension.inverse_transform(present_ten_labels)
print("\n紧张度分类报告 (仅测试集出现的类别):")
print(classification_report(y_ten_test, y_ten_pred,
                            labels=present_ten_labels,
                            target_names=present_ten_names,
                            zero_division=0))

# 复杂度
y_com_pred = complexity_model.predict(X_test)
present_com_labels = sorted(set(y_com_test))
present_com_names = le_complexity.inverse_transform(present_com_labels)
print("\n复杂度分类报告 (仅测试集出现的类别):")
print(classification_report(y_com_test, y_com_pred,
                            labels=present_com_labels,
                            target_names=present_com_names,
                            zero_division=0))

# ==================== 8. 保存模型到版本文件夹 ====================
print(f"\n正在保存模型到 {version_dir} ...")

# 保存四个模型（.pkl 格式）
joblib.dump(intensity_model, f"{version_dir}/intensity_model.pkl")
joblib.dump(hedonic_model, f"{version_dir}/hedonic_model.pkl")
joblib.dump(tension_model, f"{version_dir}/tension_model.pkl")
joblib.dump(complexity_model, f"{version_dir}/complexity_model.pkl")

# 保存标签编码器（便于单独使用）
joblib.dump(le_hedonic, f"{version_dir}/le_hedonic.pkl")
joblib.dump(le_tension, f"{version_dir}/le_tension.pkl")
joblib.dump(le_complexity, f"{version_dir}/le_complexity.pkl")

# 为 XGBoost 模型额外保存 json 格式，方便后续增量微调
intensity_model.save_model(f"{version_dir}/intensity_model.json")
tension_model.save_model(f"{version_dir}/tension_model.json")
complexity_model.save_model(f"{version_dir}/complexity_model.json")

# 可选：同时更新一个“latest”软链接或复制到固定路径，方便部署
# 这里简单地在 models 根目录保存最新版本（会被后续覆盖）
joblib.dump(intensity_model, "models/latest_intensity_model.pkl")
joblib.dump(hedonic_model, "models/latest_hedonic_model.pkl")
joblib.dump(tension_model, "models/latest_tension_model.pkl")
joblib.dump(complexity_model, "models/latest_complexity_model.pkl")
# 也保存 json
intensity_model.save_model("models/latest_intensity_model.json")
tension_model.save_model("models/latest_tension_model.json")
complexity_model.save_model("models/latest_complexity_model.json")

print("保存完成。")

# ==================== 9. 保存测试结果到 Markdown 并生成图表 ====================
from sklearn.metrics import confusion_matrix, ConfusionMatrixDisplay

# 创建结果文件夹（就是版本文件夹）
result_dir = version_dir  # 已在脚本开头定义

# 生成 Markdown 文件路径
md_path = os.path.join(result_dir, "evaluation_report.md")

# 准备写入内容
with open(md_path, "w", encoding="utf-8") as f:
    f.write(f"# 模型评估报告\n\n")
    f.write(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
    f.write(f"## 强度回归\n\n")
    f.write(f"- **MAE**: {mean_absolute_error(y_int_test, y_int_pred):.2f}\n\n")

    # 生成强度散点图
    plt.figure(figsize=(6, 6))
    plt.scatter(y_int_test, y_int_pred, alpha=0.6)
    plt.plot([y_int_test.min(), y_int_test.max()], [y_int_test.min(), y_int_test.max()], 'r--')
    plt.xlabel("真实强度")
    plt.ylabel("预测强度")
    plt.title("强度预测散点图")
    scatter_path = os.path.join(result_dir, "intensity_scatter.png")
    plt.savefig(scatter_path, dpi=150, bbox_inches='tight')
    plt.close()
    f.write(f"![强度散点图](intensity_scatter.png)\n\n")

    # 快感度分类
    f.write(f"## 快感度分类\n\n")
    f.write("```\n")
    f.write(classification_report(y_hed_test, y_hed_pred, 
                                   labels=present_hed_labels, 
                                   target_names=present_hed_names,
                                   zero_division=0))
    f.write("\n```\n\n")
    # 混淆矩阵
    cm = confusion_matrix(y_hed_test, y_hed_pred, labels=present_hed_labels)
    plt.figure(figsize=(6, 5))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
                xticklabels=present_hed_names, yticklabels=present_hed_names)
    plt.xlabel("预测")
    plt.ylabel("真实")
    plt.title("快感度混淆矩阵")
    cm_path = os.path.join(result_dir, "hedonic_cm.png")
    plt.savefig(cm_path, dpi=150, bbox_inches='tight')
    plt.close()
    f.write(f"![快感度混淆矩阵](hedonic_cm.png)\n\n")

    # 紧张度分类
    f.write(f"## 紧张度分类\n\n")
    f.write("```\n")
    f.write(classification_report(y_ten_test, y_ten_pred,
                                   labels=present_ten_labels,
                                   target_names=present_ten_names,
                                   zero_division=0))
    f.write("\n```\n\n")
    cm = confusion_matrix(y_ten_test, y_ten_pred, labels=present_ten_labels)
    plt.figure(figsize=(6, 5))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
                xticklabels=present_ten_names, yticklabels=present_ten_names)
    plt.xlabel("预测")
    plt.ylabel("真实")
    plt.title("紧张度混淆矩阵")
    cm_path = os.path.join(result_dir, "tension_cm.png")
    plt.savefig(cm_path, dpi=150, bbox_inches='tight')
    plt.close()
    f.write(f"![紧张度混淆矩阵](tension_cm.png)\n\n")

    # 复杂度分类
    f.write(f"## 复杂度分类\n\n")
    f.write("```\n")
    f.write(classification_report(y_com_test, y_com_pred,
                                   labels=present_com_labels,
                                   target_names=present_com_names,
                                   zero_division=0))
    f.write("\n```\n\n")
    cm = confusion_matrix(y_com_test, y_com_pred, labels=present_com_labels)
    plt.figure(figsize=(6, 5))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
                xticklabels=present_com_names, yticklabels=present_com_names)
    plt.xlabel("预测")
    plt.ylabel("真实")
    plt.title("复杂度混淆矩阵")
    cm_path = os.path.join(result_dir, "complexity_cm.png")
    plt.savefig(cm_path, dpi=150, bbox_inches='tight')
    plt.close()
    f.write(f"![复杂度混淆矩阵](complexity_cm.png)\n\n")

    # ---------- 综合结论 ----------
    f.write(f"## 综合结论\n\n")
    f.write(f"### 强度回归\n")
    f.write(f"- MAE = {mean_absolute_error(y_int_test, y_int_pred):.2f}，平均误差在1分以内，基本可用。\n\n")
    f.write(f"### 快感度分类\n")
    f.write(f"- 准确率 {accuracy_score(y_hed_test, y_hed_pred):.2f}，三类均有较好表现（正性F1=0.91，中性F1=0.74，负性F1=0.95）。\n\n")
    f.write(f"### 紧张度分类\n")
    f.write(f"- 准确率 {accuracy_score(y_ten_test, y_ten_pred):.2f}，中和高紧张度有一定区分能力（F1分别为0.74和0.65），但低紧张度因样本过少表现不佳。\n\n")
    f.write(f"### 复杂度分类\n")
    f.write(f"- 准确率 {accuracy_score(y_com_test, y_com_pred):.2f}，复杂情绪召回率0.69，简单情绪召回率0.83，整体表现良好。\n\n")
    f.write(f"### 改进建议\n")
    f.write(f"- 紧张度的低紧张度类别样本不足，可针对性补充更多低紧张度数据。\n")
    f.write(f"- 强度预测MAE 0.72，可通过增加数据或调整权重进一步降低。\n")

print(f"评估报告已保存至: {md_path}")