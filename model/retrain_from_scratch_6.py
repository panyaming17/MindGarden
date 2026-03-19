import pandas as pd
import numpy as np
import joblib
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from xgboost import XGBRegressor, XGBClassifier
from sentence_transformers import SentenceTransformer
from sklearn.metrics import mean_absolute_error, classification_report, confusion_matrix
import matplotlib.pyplot as plt
import seaborn as sns
import os
from datetime import datetime

# ==================== 设置中文字体 ====================
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

# ==================== 创建版本文件夹 ====================
timestamp = datetime.now().strftime("%Y%m%d_%H_%M_%S")
version_dir = f"models/{timestamp}"
os.makedirs(version_dir, exist_ok=True)
print(f"本次微调的模型将保存至: {version_dir}")

# ==================== 1. 加载数据 ====================
human_df = pd.read_csv("data/mydata/human_labeled.csv")          # 人工数据
ai_df = pd.read_csv("data/mydata/ai_generated_samples_new.csv")  # 旧 AI 数据
new_df = pd.read_csv("data/mydata/predicted_data.csv")           # 新预测数据

print(f"人工数据条数: {len(human_df)}")
print(f"旧 AI 数据条数: {len(ai_df)}")
print(f"新预测数据条数: {len(new_df)}")

# 处理旧 AI 数据：将强度范围转为具体值
if 'intensity_min' in ai_df.columns and 'intensity_max' in ai_df.columns:
    ai_df["intensity"] = (ai_df["intensity_min"] + ai_df["intensity_max"]) / 2
    ai_df = ai_df[["text", "intensity", "hedonic", "tension", "complexity"]]
else:
    ai_df = ai_df[["text", "intensity", "hedonic", "tension", "complexity"]]

# ==================== 2. 从人工数据中划分训练/测试 ====================
# 先给人工数据添加权重列
human_df = human_df.copy()
human_df["weight"] = 1.0

# 随机划分，不按分层（因为正性样本太少）
human_train, human_test = train_test_split(
    human_df, test_size=0.2, random_state=42
)
print(f"人工数据 - 训练集: {len(human_train)} 条, 测试集: {len(human_test)} 条")

# ==================== 3. 构建训练集（合并） ====================
# 训练集中的人工部分已有 weight=1.0
ai_df = ai_df.copy()
ai_df["weight"] = 0.5

new_df = new_df.copy()
new_df["weight"] = 0.3

train_df = pd.concat([human_train, ai_df, new_df], ignore_index=True)
test_df = human_test.copy()

# 检查缺失值
print("\n检查训练集缺失值情况：")
print(train_df[['hedonic', 'tension', 'complexity', 'intensity']].isnull().sum())
train_df = train_df.dropna(subset=['hedonic', 'tension', 'complexity', 'intensity'])
test_df = test_df.dropna(subset=['hedonic', 'tension', 'complexity', 'intensity'])
print(f"删除缺失值后训练集: {len(train_df)} 条, 测试集: {len(test_df)} 条")

# ==================== 4. 检查训练集类别完整性，必要时从测试集迁移样本 ====================
print("\n训练集分类分布检查：")
print("快感度分布：", train_df['hedonic'].value_counts().to_dict())
print("紧张度分布：", train_df['tension'].value_counts().to_dict())
print("复杂度分布：", train_df['complexity'].value_counts().to_dict())

expected_tension = {'低', '中', '高'}
expected_complexity = {'简单', '复杂'}

def ensure_classes_in_train(df_train, df_test, column, expected_classes):
    """
    确保训练集中包含所有预期的类别。如果缺失，则从测试集中借样本。
    返回更新后的 train_df 和 test_df。
    """
    missing = expected_classes - set(df_train[column].unique())
    if missing:
        print(f"警告：训练集中缺少 {column} 类别 {missing}，将从测试集中补充。")
        for cls in missing:
            # 从测试集中取出属于该类别的样本
            cls_samples = df_test[df_test[column] == cls]
            if len(cls_samples) == 0:
                raise ValueError(f"测试集中也没有类别 {cls}，无法补充。")
            # 随机选择最多5个样本加入训练集
            n_to_move = min(5, len(cls_samples))
            moved = cls_samples.sample(n=n_to_move, random_state=42)
            df_train = pd.concat([df_train, moved], ignore_index=True)
            # 从测试集中删除这些样本
            df_test = df_test.drop(moved.index)
            print(f"已将 {n_to_move} 个 {cls} 样本从测试集移到训练集。")
    return df_train, df_test

train_df, test_df = ensure_classes_in_train(train_df, test_df, 'tension', expected_tension)
train_df, test_df = ensure_classes_in_train(train_df, test_df, 'complexity', expected_complexity)

print("\n补充后训练集分布：")
print("紧张度分布：", train_df['tension'].value_counts().to_dict())
print("复杂度分布：", train_df['complexity'].value_counts().to_dict())

# ==================== 5. 针对低紧张度提高权重 ====================
low_tension_mask = (train_df["tension"] == "低")
train_df.loc[low_tension_mask, "weight"] *= 2.0
print("\n训练集紧张度权重统计（加权后）：")
print(train_df.groupby("tension")["weight"].describe())

# ==================== 6. 文本编码 ====================
encoder = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
print("\n正在编码训练集文本...")
X_train = encoder.encode(train_df["text"].tolist(), show_progress_bar=True)
print("正在编码测试集文本...")
X_test = encoder.encode(test_df["text"].tolist(), show_progress_bar=True)

# ==================== 7. 准备标签和权重 ====================
le_hedonic = joblib.load("models/le_hedonic.pkl")
le_tension = joblib.load("models/le_tension.pkl")
le_complexity = joblib.load("models/le_complexity.pkl")

# 训练集
y_int_train = train_df["intensity"].values.astype(float)
y_hed_train = le_hedonic.transform(train_df["hedonic"])
y_ten_train = le_tension.transform(train_df["tension"])
y_com_train = le_complexity.transform(train_df["complexity"])
w_train = train_df["weight"].values

# 测试集
y_int_test = test_df["intensity"].values.astype(float)
y_hed_test = le_hedonic.transform(test_df["hedonic"])
y_ten_test = le_tension.transform(test_df["tension"])
y_com_test = le_complexity.transform(test_df["complexity"])
w_test = test_df["weight"].values  # 测试集权重均为1.0

# ==================== 8. 增量微调模型 ====================
print("\n开始微调模型...")

# 强度模型
print("增量微调强度模型...")
intensity_model = XGBRegressor(
    n_estimators=200, max_depth=6, learning_rate=0.02,
    random_state=42, early_stopping_rounds=20, eval_metric='mae'
)
if os.path.exists("models/latest_intensity_model.json"):
    intensity_model.fit(
        X_train, y_int_train, sample_weight=w_train,
        eval_set=[(X_test, y_int_test)],
        sample_weight_eval_set=[w_test],
        xgb_model="models/latest_intensity_model.json"
    )
else:
    intensity_model.fit(
        X_train, y_int_train, sample_weight=w_train,
        eval_set=[(X_test, y_int_test)],
        sample_weight_eval_set=[w_test]
    )

# 快感度模型（逻辑回归）
print("训练快感度模型（逻辑回归）...")
hedonic_model = LogisticRegression(max_iter=1000, class_weight='balanced', random_state=42)
hedonic_model.fit(X_train, y_hed_train, sample_weight=w_train)

# 紧张度模型
print("增量微调紧张度模型...")
tension_model = XGBClassifier(
    n_estimators=200, max_depth=6, learning_rate=0.02,
    random_state=42, early_stopping_rounds=20, eval_metric='mlogloss'
)
if os.path.exists("models/latest_tension_model.json"):
    tension_model.fit(
        X_train, y_ten_train, sample_weight=w_train,
        eval_set=[(X_test, y_ten_test)],
        sample_weight_eval_set=[w_test],
        xgb_model="models/latest_tension_model.json"
    )
else:
    tension_model.fit(
        X_train, y_ten_train, sample_weight=w_train,
        eval_set=[(X_test, y_ten_test)],
        sample_weight_eval_set=[w_test]
    )

# 复杂度模型
print("增量微调复杂度模型...")
complexity_model = XGBClassifier(
    n_estimators=200, max_depth=6, learning_rate=0.02,
    random_state=42, early_stopping_rounds=20, eval_metric='mlogloss'
)
if os.path.exists("models/latest_complexity_model.json"):
    complexity_model.fit(
        X_train, y_com_train, sample_weight=w_train,
        eval_set=[(X_test, y_com_test)],
        sample_weight_eval_set=[w_test],
        xgb_model="models/latest_complexity_model.json"
    )
else:
    complexity_model.fit(
        X_train, y_com_train, sample_weight=w_train,
        eval_set=[(X_test, y_com_test)],
        sample_weight_eval_set=[w_test]
    )

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

# ==================== 10. 保存模型 ====================
print(f"\n正在保存模型到 {version_dir} ...")
joblib.dump(intensity_model, f"{version_dir}/intensity_model.pkl")
joblib.dump(hedonic_model, f"{version_dir}/hedonic_model.pkl")
joblib.dump(tension_model, f"{version_dir}/tension_model.pkl")
joblib.dump(complexity_model, f"{version_dir}/complexity_model.pkl")
joblib.dump(le_hedonic, f"{version_dir}/le_hedonic.pkl")
joblib.dump(le_tension, f"{version_dir}/le_tension.pkl")
joblib.dump(le_complexity, f"{version_dir}/le_complexity.pkl")

intensity_model.save_model(f"{version_dir}/intensity_model.json")
tension_model.save_model(f"{version_dir}/tension_model.json")
complexity_model.save_model(f"{version_dir}/complexity_model.json")

# 更新 latest 版本
joblib.dump(intensity_model, "models/latest_intensity_model.pkl")
joblib.dump(hedonic_model, "models/latest_hedonic_model.pkl")
joblib.dump(tension_model, "models/latest_tension_model.pkl")
joblib.dump(complexity_model, "models/latest_complexity_model.pkl")
intensity_model.save_model("models/latest_intensity_model.json")
tension_model.save_model("models/latest_tension_model.json")
complexity_model.save_model("models/latest_complexity_model.json")

print("保存完成。")

# ==================== 11. 生成评估报告 ====================
md_path = os.path.join(version_dir, "evaluation_report.md")
with open(md_path, "w", encoding="utf-8") as f:
    f.write(f"# 模型评估报告（含新数据）\n\n")
    f.write(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
    f.write(f"**训练数据构成**: 人工 {len(human_df)} 条, 旧 AI {len(ai_df)} 条, 新预测 {len(new_df)} 条\n")
    f.write(f"**测试集**: 人工数据中的 {len(test_df)} 条（20%）\n\n")

    # 强度
    f.write(f"## 强度回归\n")
    f.write(f"- **MAE**: {mean_absolute_error(y_int_test, y_int_pred):.2f}\n\n")
    plt.figure(figsize=(6, 6))
    plt.scatter(y_int_test, y_int_pred, alpha=0.6)
    plt.plot([y_int_test.min(), y_int_test.max()], [y_int_test.min(), y_int_test.max()], 'r--')
    plt.xlabel("真实强度")
    plt.ylabel("预测强度")
    plt.title("强度预测散点图")
    scatter_path = os.path.join(version_dir, "intensity_scatter.png")
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
    cm_path = os.path.join(version_dir, "hedonic_cm.png")
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
    cm_path = os.path.join(version_dir, "tension_cm.png")
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
    cm_path = os.path.join(version_dir, "complexity_cm.png")
    plt.savefig(cm_path, dpi=150, bbox_inches='tight')
    plt.close()
    f.write(f"![复杂度混淆矩阵](complexity_cm.png)\n\n")

print(f"评估报告已保存至: {md_path}")