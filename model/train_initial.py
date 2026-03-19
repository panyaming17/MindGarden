import pandas as pd
import numpy as np
import joblib
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from xgboost import XGBRegressor, XGBClassifier
from sentence_transformers import SentenceTransformer
import os

# 1. 加载预处理后的数据
df = pd.read_csv('data/goemotions_four_dim.csv')
texts = df['text'].tolist()

# 2. 提取句子向量
print("Loading SentenceTransformer model...")
encoder = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
print("Encoding texts...")
X = encoder.encode(texts, show_progress_bar=True)

# 3. 准备标签
y_intensity = df['intensity'].values.astype(float)

le_hedonic = LabelEncoder()
y_hedonic = le_hedonic.fit_transform(df['hedonic'])

le_tension = LabelEncoder()
y_tension = le_tension.fit_transform(df['tension'])

le_complexity = LabelEncoder()
y_complexity = le_complexity.fit_transform(df['complexity'])

# 4. 划分训练/测试集
X_train, X_test, y_int_train, y_int_test, y_hed_train, y_hed_test, y_ten_train, y_ten_test, y_com_train, y_com_test = train_test_split(
    X, y_intensity, y_hedonic, y_tension, y_complexity, test_size=0.2, random_state=42
)

# 5. 训练模型
print("Training intensity regressor (XGBoost)...")
intensity_model = XGBRegressor(n_estimators=100, max_depth=5, learning_rate=0.1, random_state=42)
intensity_model.fit(X_train, y_int_train)

print("Training hedonic classifier (Logistic Regression)...")
hedonic_model = LogisticRegression(max_iter=1000, class_weight='balanced', random_state=42)
hedonic_model.fit(X_train, y_hed_train)

print("Training tension classifier (XGBoost)...")
tension_model = XGBClassifier(n_estimators=100, max_depth=5, learning_rate=0.1, random_state=42)
tension_model.fit(X_train, y_ten_train)

print("Training complexity classifier (XGBoost)...")
complexity_model = XGBClassifier(n_estimators=100, max_depth=5, learning_rate=0.1, random_state=42)
complexity_model.fit(X_train, y_com_train)

# 6. 评估（可选）
from sklearn.metrics import mean_absolute_error, accuracy_score, classification_report

y_int_pred = intensity_model.predict(X_test)
print(f"Intensity MAE: {mean_absolute_error(y_int_test, y_int_pred):.2f}")

for name, model, y_true, le in [
    ("Hedonic", hedonic_model, y_hed_test, le_hedonic),
    ("Tension", tension_model, y_ten_test, le_tension),
    ("Complexity", complexity_model, y_com_test, le_complexity)
]:
    y_pred = model.predict(X_test)
    acc = accuracy_score(y_true, y_pred)
    print(f"{name} Accuracy: {acc:.2f}")
    print(classification_report(y_true, y_pred, target_names=le.classes_))

# 7. 保存模型
os.makedirs('models', exist_ok=True)
joblib.dump(intensity_model, 'models/intensity_model.pkl')
joblib.dump(hedonic_model, 'models/hedonic_model.pkl')
joblib.dump(tension_model, 'models/tension_model.pkl')
joblib.dump(complexity_model, 'models/complexity_model.pkl')
joblib.dump(le_hedonic, 'models/le_hedonic.pkl')
joblib.dump(le_tension, 'models/le_tension.pkl')
joblib.dump(le_complexity, 'models/le_complexity.pkl')
print("All models saved to ./models/")