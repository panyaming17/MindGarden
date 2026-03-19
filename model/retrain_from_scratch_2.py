import pandas as pd
import numpy as np
import joblib
from sklearn.model_selection import train_test_split
from xgboost import XGBRegressor, XGBClassifier
from sentence_transformers import SentenceTransformer
from sklearn.linear_model import LogisticRegression
import os



# ==================== 1. 加载数据 ====================
human_df = pd.read_csv("data/mydata/cleaned_texts.csv")          # 人工数据（204条）
ai_df = pd.read_csv("data/mydata/ai_generated_samples_new.csv")      # AI数据（约120条）

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
# 删除包含缺失值的行
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
    # stratify=y_hedonic  # 按快感度分层
)

# ==================== 6. 增量微调模型 ====================
print("增量微调强度模型...")
intensity_model = XGBRegressor(n_estimators=50, max_depth=5, learning_rate=0.05, random_state=42)
# 加载预训练json（如果存在）
if os.path.exists("models/intensity_model.json"):
    intensity_model.fit(X_train, y_int_train, sample_weight=w_train,
                        xgb_model="models/intensity_model.json")
else:
    intensity_model.fit(X_train, y_int_train, sample_weight=w_train)

print("训练快感度模型（逻辑回归，不使用预训练）...")
hedonic_model = LogisticRegression(max_iter=1000, class_weight='balanced', random_state=42)
hedonic_model.fit(X_train, y_hed_train, sample_weight=w_train)   # 逻辑回归也支持样本权重

print("增量微调紧张度模型...")
tension_model = XGBClassifier(n_estimators=50, max_depth=5, learning_rate=0.05, random_state=42)
if os.path.exists("models/tension_model.json"):
    tension_model.fit(X_train, y_ten_train, sample_weight=w_train,
                      xgb_model="models/tension_model.json")
else:
    tension_model.fit(X_train, y_ten_train, sample_weight=w_train)

print("增量微调复杂度模型...")
complexity_model = XGBClassifier(n_estimators=50, max_depth=5, learning_rate=0.05, random_state=42)
if os.path.exists("models/complexity_model.json"):
    complexity_model.fit(X_train, y_com_train, sample_weight=w_train,
                         xgb_model="models/complexity_model.json")
else:
    complexity_model.fit(X_train, y_com_train, sample_weight=w_train)

# ==================== 7. 评估 ====================
from sklearn.metrics import mean_absolute_error, accuracy_score, classification_report

print("\n===== 测试集评估 =====")

# 强度
y_int_pred = intensity_model.predict(X_test)
print(f"强度 MAE: {mean_absolute_error(y_int_test, y_int_pred):.2f}")

# 快感度
y_hed_pred = hedonic_model.predict(X_test)
# 获取测试集中实际出现的类别
present_hed_labels = sorted(set(y_hed_test))
present_hed_names = le_hedonic.inverse_transform(present_hed_labels)
print("\n快感度分类报告 (仅测试集出现的类别):")
print(classification_report(y_hed_test, y_hed_pred, 
                            labels=present_hed_labels, 
                            target_names=present_hed_names,
                            zero_division=0))  # 避免除零警告

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