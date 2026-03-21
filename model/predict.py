import joblib
from sentence_transformers import SentenceTransformer

# 加载模型和编码器（只需加载一次）
encoder = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
intensity_model = joblib.load("models/latest_intensity_model.pkl")
hedonic_model = joblib.load("models/latest_hedonic_model.pkl")
tension_model = joblib.load("models/latest_tension_model.pkl")
complexity_model = joblib.load("models/latest_complexity_model.pkl")
le_hedonic = joblib.load("models/le_hedonic.pkl")
le_tension = joblib.load("models/le_tension.pkl")
le_complexity = joblib.load("models/le_complexity.pkl")

def predict_four_dim(text):
    emb = encoder.encode([text])
    intensity = intensity_model.predict(emb)[0]
    hedonic = le_hedonic.inverse_transform(hedonic_model.predict(emb))[0]
    tension = le_tension.inverse_transform(tension_model.predict(emb))[0]
    complexity = le_complexity.inverse_transform(complexity_model.predict(emb))[0]
    return {
        "intensity": round(intensity, 2),
        "hedonic": hedonic,
        "tension": tension,
        "complexity": complexity
    }