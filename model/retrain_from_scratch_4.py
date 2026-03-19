import pandas as pd
import numpy as np
import joblib
from sklearn.model_selection import train_test_split
from xgboost import XGBRegressor, XGBClassifier
from sentence_transformers import SentenceTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import mean_absolute_error, classification_report, accuracy_score
from sklearn.metrics import confusion_matrix
import matplotlib.pyplot as plt
import seaborn as sns
import os
from datetime import datetime

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

# ==================== 创建版本文件夹 ====================
timestamp = datetime.now().strftime("%Y%m%d_%H_%M_%S")
version_dir = f"models/{timestamp}"
os.makedirs(version_dir, exist_ok=True)
print(f"本次微调的模型将保存至: {version_dir}")

# ==================== 1. 加载原有数据 ====================
print("加载原有数据...")
human_df = pd.read_csv("data/mydata/cleaned_texts.csv")                # 人工数据（204条）
ai_df = pd.read_csv("data/mydata/ai_generated_samples_new.csv")        # AI生成数据（含正/中样本）
# 处理 AI 数据：将强度范围转为具体值（取中值），如果已经处理过可跳过
if 'intensity_min' in ai_df.columns:
    ai_df["intensity"] = (ai_df["intensity_min"] + ai_df["intensity_max"]) / 2
    ai_df = ai_df[["text", "intensity", "hedonic", "tension", "complexity"]]

# ==================== 2. 加载新预测数据 ====================
print("加载新预测数据...")
new_df = pd.read_csv("data/mydata/predicted_data.csv")              # 新预测数据（几万条）
# 确保列名一致，必要时重命名
# 假设新数据包含 text, hedonic, intensity, tension, complexity
# 如果列名不同，请在此处调整
# new_df = new_df.rename(columns={...})

print(f"人工数据条数: {len(human_df)}")
print(f"AI生成数据条数: {len(ai_df)}")
print(f"新预测数据条数: {len(new_df)}")

# ==================== 3. 合并所有数据 ====================
df_all = pd.concat([human_df, ai_df], ignore_index=True)
print(f"总数据条数: {len(df_all)}")

# 检查并处理缺失值
print("\n检查缺失值情况：")
print(df_all[['hedonic', 'tension', 'complexity', 'intensity']].isnull().sum())
df_all = df_all.dropna(subset=['hedonic', 'tension', 'complexity', 'intensity'])
print(f"删除缺失值后数据条数: {len(df_all)}")

# ==================== 4. 设置样本权重 ====================
# 基础权重：人工数据1.0，AI数据0.5，新预测数据0.3
df_all["weight"] = 1.0
df_all.loc[df_all.index >= len(human_df), "weight"] = 0.5               # AI数据
df_all.loc[df_all.index >= len(human_df) + len(ai_df), "weight"] = 0.3 # 新预测数据

# 针对紧张度中的低紧张度类别，进一步提高权重（可选）
# 假设我们想强化低紧张度（tension=="低"）的学习
low_tension_mask = (df_all["tension"] == "低")
df_all.loc[low_tension_mask, "weight"] *= 2.0   # 低紧张度样本权重翻倍
print("各类别样本权重统计（加权后）：")
print(df_all.groupby("tension")["weight"].describe())

# ==================== 5. 文本编码 ====================
encoder = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
print("正在编码文本...")
# 分批编码以防内存溢出（数据量大时建议分批，此处直接整体编码，如内存不足可修改）
X = encoder.encode(df_all["text"].tolist(), show_progress_bar=True)

# ==================== 6. 准备标签（使用原有编码器）====================
le_hedonic = joblib.load("models/le_hedonic.pkl")
le_tension = joblib.load("models/le_tension.pkl")
le_complexity = joblib.load("models/le_complexity.pkl")

y_hedonic = le_hedonic.transform(df_all["hedonic"])
y_tension = le_tension.transform(df_all["tension"])
y_complexity = le_complexity.transform(df_all["complexity"])
y_intensity = df_all["intensity"].values.astype(float)
weights = df_all["weight"].values

# ==================== 7. 划分训练/测试集 ====================
# 按复杂度分层，确保训练集中包含两类
X_train, X_test, y_int_train, y_int_test, y_hed_train, y_hed_test, \
y_ten_train, y_ten_test, y_com_train, y_com_test, w_train, w_test = train_test_split(
    X, y_intensity, y_hedonic, y_tension, y_complexity, weights,
    test_size=0.2, random_state=42, stratify=y_complexity
)
# ==================== 8. 增量微调模型 ====================
print("增量微调强度模型...")
intensity_model = XGBRegressor(n_estimators=100, max_depth=6, learning_rate=0.02, 
                               random_state=42, early_stopping_rounds=20, eval_metric='mae')
intensity_model.fit(X_train, y_int_train, sample_weight=w_train,
                    eval_set=[(X_test, y_int_test)], 
                    sample_weight_eval_set=[w_test],
                    xgb_model="models/latest_intensity_model.json")   # 从最新版继续

print("训练快感度模型（逻辑回归，从头训练）...")
hedonic_model = LogisticRegression(max_iter=1000, class_weight='balanced', random_state=42)
hedonic_model.fit(X_train, y_hed_train, sample_weight=w_train)

print("增量微调紧张度模型...")
tension_model = XGBClassifier(n_estimators=100, max_depth=6, learning_rate=0.02,
                              random_state=42, early_stopping_rounds=20, eval_metric='mlogloss')
tension_model.fit(X_train, y_ten_train, sample_weight=w_train,
                  eval_set=[(X_test, y_ten_test)],
                  sample_weight_eval_set=[w_test],
                  xgb_model="models/latest_tension_model.json")

print("增量微调复杂度模型...")
complexity_model = XGBClassifier(n_estimators=100, max_depth=6, learning_rate=0.02,
                                 random_state=42, early_stopping_rounds=20, eval_metric='mlogloss')
complexity_model.fit(X_train, y_com_train, sample_weight=w_train,
                     eval_set=[(X_test, y_com_test)],
                     sample_weight_eval_set=[w_test],
                     xgb_model="models/latest_complexity_model.json")

# ==================== 9. 评估 ====================
print("\n===== 测试集评估 =====")

y_int_pred = intensity_model.predict(X_test)
print(f"强度 MAE: {mean_absolute_error(y_int_test, y_int_pred):.2f}")

y_hed_pred = hedonic_model.predict(X_test)
present_hed_labels = sorted(set(y_hed_test))
present_hed_names = le_hedonic.inverse_transform(present_hed_labels)
print("\n快感度分类报告:")
print(classification_report(y_hed_test, y_hed_pred, labels=present_hed_labels,
                            target_names=present_hed_names, zero_division=0))

y_ten_pred = tension_model.predict(X_test)
present_ten_labels = sorted(set(y_ten_test))
present_ten_names = le_tension.inverse_transform(present_ten_labels)
print("\n紧张度分类报告:")
print(classification_report(y_ten_test, y_ten_pred, labels=present_ten_labels,
                            target_names=present_ten_names, zero_division=0))

y_com_pred = complexity_model.predict(X_test)
present_com_labels = sorted(set(y_com_test))
present_com_names = le_complexity.inverse_transform(present_com_labels)
print("\n复杂度分类报告:")
print(classification_report(y_com_test, y_com_pred, labels=present_com_labels,
                            target_names=present_com_names, zero_division=0))

# ==================== 10. 保存模型到版本文件夹 ====================
print(f"\n正在保存模型到 {version_dir} ...")
joblib.dump(intensity_model, f"{version_dir}/intensity_model.pkl")
joblib.dump(hedonic_model, f"{version_dir}/hedonic_model.pkl")
joblib.dump(tension_model, f"{version_dir}/tension_model.pkl")
joblib.dump(complexity_model, f"{version_dir}/complexity_model.pkl")
joblib.dump(le_hedonic, f"{version_dir}/le_hedonic.pkl")
joblib.dump(le_tension, f"{version_dir}/le_tension.pkl")
joblib.dump(le_complexity, f"{version_dir}/le_complexity.pkl")

# XGBoost模型保存json格式
intensity_model.save_model(f"{version_dir}/intensity_model.json")
tension_model.save_model(f"{version_dir}/tension_model.json")
complexity_model.save_model(f"{version_dir}/complexity_model.json")

# 更新latest版本
joblib.dump(intensity_model, "models/latest_intensity_model.pkl")
joblib.dump(hedonic_model, "models/latest_hedonic_model.pkl")
joblib.dump(tension_model, "models/latest_tension_model.pkl")
joblib.dump(complexity_model, "models/latest_complexity_model.pkl")
intensity_model.save_model("models/latest_intensity_model.json")
tension_model.save_model("models/latest_tension_model.json")
complexity_model.save_model("models/latest_complexity_model.json")

print("保存完成。")

# ==================== 11. 生成评估报告和图表 ====================
result_dir = version_dir
md_path = os.path.join(result_dir, "evaluation_report.md")

with open(md_path, "w", encoding="utf-8") as f:
    f.write(f"# 模型评估报告（含新数据）\n\n")
    f.write(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
    f.write(f"**训练数据构成**: 人工 {len(human_df)} 条, AI生成 {len(ai_df)} 条, 新预测 {len(new_df)} 条\n\n")
    
    f.write(f"## 强度回归\n")
    f.write(f"- **MAE**: {mean_absolute_error(y_int_test, y_int_pred):.2f}\n\n")
    # 强度散点图
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

    # 快感度
    f.write(f"## 快感度分类\n")
    f.write("```\n")
    f.write(classification_report(y_hed_test, y_hed_pred, labels=present_hed_labels,
                                  target_names=present_hed_names, zero_division=0))
    f.write("\n```\n\n")
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

    # 紧张度
    f.write(f"## 紧张度分类\n")
    f.write("```\n")
    f.write(classification_report(y_ten_test, y_ten_pred, labels=present_ten_labels,
                                  target_names=present_ten_names, zero_division=0))
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

    # 复杂度
    f.write(f"## 复杂度分类\n")
    f.write("```\n")
    f.write(classification_report(y_com_test, y_com_pred, labels=present_com_labels,
                                  target_names=present_com_names, zero_division=0))
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

print(f"评估报告已保存至: {md_path}")