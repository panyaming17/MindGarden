import joblib
from sentence_transformers import SentenceTransformer
import os

# 确定模型目录（根据你的实际结构调整）
current_dir = os.path.dirname(os.path.abspath(__file__))
model_dir = os.path.join(current_dir, "backend", "checkpoints", "models")
model_dir = os.path.abspath(model_dir)
print(f"模型目录: {model_dir}")

# 检查文件是否存在
for f in ["latest_intensity_model.pkl", "latest_hedonic_model.pkl", "latest_tension_model.pkl",
          "latest_complexity_model.pkl", "le_hedonic.pkl", "le_tension.pkl", "le_complexity.pkl"]:
    path = os.path.join(model_dir, f)
    print(f"{f}: {'存在' if os.path.exists(path) else '不存在'}")

# 加载编码器
encoder = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')

# 加载模型
try:
    intensity_model = joblib.load(os.path.join(model_dir, "latest_intensity_model.pkl"))
    hedonic_model = joblib.load(os.path.join(model_dir, "latest_hedonic_model.pkl"))
    tension_model = joblib.load(os.path.join(model_dir, "latest_tension_model.pkl"))
    complexity_model = joblib.load(os.path.join(model_dir, "latest_complexity_model.pkl"))
    le_hedonic = joblib.load(os.path.join(model_dir, "le_hedonic.pkl"))
    le_tension = joblib.load(os.path.join(model_dir, "le_tension.pkl"))
    le_complexity = joblib.load(os.path.join(model_dir, "le_complexity.pkl"))
    print("模型加载成功")
except Exception as e:
    print(f"模型加载失败: {e}")
    exit()

# 测试文本
texts = ["我明天要答辩，紧张得睡不着觉，脑子一片空白。"]

# 编码
emb = encoder.encode(texts)
print("编码成功，形状:", emb.shape)

# 预测强度
intensity = intensity_model.predict(emb)
print("强度预测:", intensity)

# 预测快感度
hedonic = le_hedonic.inverse_transform(hedonic_model.predict(emb))
print("快感度预测:", hedonic)

# 预测紧张度
tension = le_tension.inverse_transform(tension_model.predict(emb))
print("紧张度预测:", tension)

# 预测复杂度
complexity = le_complexity.inverse_transform(complexity_model.predict(emb))
print("复杂度预测:", complexity)