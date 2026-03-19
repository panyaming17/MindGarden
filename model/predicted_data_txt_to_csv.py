import pandas as pd
import joblib
import numpy as np
from sentence_transformers import SentenceTransformer
import os

# ==================== 配置 ====================
input_file = "data/mydata/train.txt"                 # 输入文件路径
output_file = "data/mydata/predicted_data.csv"       # 输出CSV路径
batch_size = 500                         # 每批处理的文本数量（根据内存调整）
model_dir = "models"                      # 模型文件夹

# 标签映射（0:负性, 1:中性, 2:正性）
hedonic_map = {0: "负性", 1: "中性", 2: "正性"}

# ==================== 加载模型和编码器 ====================
print("加载模型和编码器...")
encoder = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')

# 强度模型（回归）
intensity_model = joblib.load(os.path.join(model_dir, "latest_intensity_model.pkl"))
# 紧张度模型（分类）
tension_model = joblib.load(os.path.join(model_dir, "latest_tension_model.pkl"))
# 复杂度模型（分类）
complexity_model = joblib.load(os.path.join(model_dir, "latest_complexity_model.pkl"))
# 标签编码器
le_tension = joblib.load(os.path.join(model_dir, "le_tension.pkl"))
le_complexity = joblib.load(os.path.join(model_dir, "le_complexity.pkl"))

print("模型加载完成。")

# ==================== 读取数据 ====================
print("读取数据文件...")
texts = []
hedonic_labels = []
with open(input_file, "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        # 假设标签和文本之间由空格分隔（也可能是制表符，根据实际情况修改）
        parts = line.split(maxsplit=1)
        if len(parts) == 2:
            label_str, text = parts
            try:
                label = int(label_str)
                if label in hedonic_map:
                    hedonic_labels.append(hedonic_map[label])
                    texts.append(text)
                else:
                    print(f"警告: 忽略无效标签 {label_str}")
            except ValueError:
                print(f"警告: 忽略无法解析的行: {line}")
        else:
            print(f"警告: 忽略格式错误行: {line}")

print(f"共读取 {len(texts)} 条有效数据。")

# ==================== 分批编码和预测 ====================
print("开始编码和预测...")
pred_intensity = []
pred_tension = []
pred_complexity = []

for i in range(0, len(texts), batch_size):
    batch_texts = texts[i:i+batch_size]
    print(f"正在处理第 {i+1} 到 {min(i+batch_size, len(texts))} 条...")
    embeddings = encoder.encode(batch_texts, show_progress_bar=False)  # 可设置显示进度条
    pred_intensity.extend(intensity_model.predict(embeddings))
    pred_tension.extend(tension_model.predict(embeddings))
    pred_complexity.extend(complexity_model.predict(embeddings))

# 将分类数字标签转换回字符串
tension_str = le_tension.inverse_transform(pred_tension)
complexity_str = le_complexity.inverse_transform(pred_complexity)

# ==================== 保存结果 ====================
df = pd.DataFrame({
    "text": texts,
    "hedonic": hedonic_labels,
    "intensity": pred_intensity,
    "tension": tension_str,
    "complexity": complexity_str
})
df.to_csv(output_file, index=False, encoding="utf-8-sig")
print(f"预测完成，结果已保存至 {output_file}")