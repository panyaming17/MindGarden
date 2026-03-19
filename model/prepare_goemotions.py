import pandas as pd
import numpy as np
from glob import glob

# ==================== 1. 数据加载与聚合 ====================
# 1. 读取所有分片
files = glob('data/goemotions/goemotions_*.csv')
df_list = []
for f in files:
    df = pd.read_csv(f)
    df_list.append(df)
df_raw = pd.concat(df_list, ignore_index=True)

print(f"原始数据行数: {len(df_raw)}")

# 情绪列列表（GoEmotions 的 27 种情绪 + neutral）
emotion_cols = ['admiration', 'amusement', 'anger', 'annoyance', 'approval',
                'caring', 'confusion', 'curiosity', 'desire', 'disappointment',
                'disapproval', 'disgust', 'embarrassment', 'excitement', 'fear',
                'gratitude', 'grief', 'joy', 'love', 'nervousness', 'optimism',
                'pride', 'realization', 'relief', 'remorse', 'sadness', 'surprise',
                'neutral']

# 确保所有情绪列存在
emotion_cols = [c for c in emotion_cols if c in df_raw.columns]

# 2. 按 id 聚合（每个 id 对应一段文本）
def aggregate_annotations(group):
    """对同一个文本的多个标注进行聚合"""
    # 统计每个情绪被标注的次数
    counts = group[emotion_cols].sum()
    # 选取至少被 2 个标注者标记的情绪（避免单个人噪声）
    final_emotions = counts[counts >= 2].index.tolist()
    # 如果没有情绪达到 2 次，则取次数最多的情绪（但排除 neutral 优先？）
    if len(final_emotions) == 0:
        # 取次数最多的（若有多个并列，取第一个）
        max_count = counts.max()
        if max_count > 0:
            final_emotions = counts[counts == max_count].index.tolist()
        else:
            final_emotions = ['neutral']
    # 如果 neutral 和其他情绪同时存在，移除 neutral（因为 neutral 意味着无情绪）
    if 'neutral' in final_emotions and len(final_emotions) > 1:
        final_emotions.remove('neutral')
    return pd.Series({
        'text': group['text'].iloc[0],
        'emotions': final_emotions
    })

df_agg = df_raw.groupby('id').apply(aggregate_annotations).reset_index(drop=True)
print(f"聚合后数据条数: {len(df_agg)}")
print(df_agg.head())

# ==================== 2. 情绪到四维的映射 ====================
# 3. 定义情绪分类
positive_emotions = ['admiration', 'amusement', 'approval', 'caring', 'excitement',
                     'gratitude', 'joy', 'love', 'optimism', 'pride', 'relief']
negative_emotions = ['anger', 'annoyance', 'disappointment', 'disapproval', 'disgust',
                     'embarrassment', 'fear', 'grief', 'nervousness', 'remorse', 'sadness']
neutral_emotions = ['confusion', 'curiosity', 'desire', 'realization', 'surprise']

# 强度基准（每个情绪的基础强度值，1-10）
intensity_map = {
    'anger': 8, 'fear': 8, 'grief': 8, 'joy': 7, 'sadness': 7,
    'annoyance': 5, 'disappointment': 5, 'nervousness': 6,
    'admiration': 6, 'gratitude': 6, 'love': 8, 'surprise': 6,
    'amusement': 6, 'approval': 5, 'caring': 6, 'excitement': 7,
    'optimism': 6, 'pride': 7, 'relief': 5, 'confusion': 5,
    'curiosity': 5, 'desire': 6, 'realization': 5, 'remorse': 7,
    'disgust': 7, 'embarrassment': 7, 'disapproval': 5
}

def emotions_to_fourdim(emotion_list):
    # 快感度
    if any(e in positive_emotions for e in emotion_list):
        hedonic = '正性'
    elif any(e in negative_emotions for e in emotion_list):
        hedonic = '负性'
    else:
        hedonic = '中性'
    
    # 强度：取所有情绪的强度平均值（如果不在映射里，默认5）
    intensities = [intensity_map.get(e, 5) for e in emotion_list]
    intensity = np.mean(intensities) if intensities else 5.0
    
    # 紧张度：简单规则，有 fear/nervousness/anger 为高；有 sadness/grief 为中；其他为低
    if any(e in ['fear', 'nervousness', 'anger'] for e in emotion_list):
        tension = '高'
    elif any(e in ['sadness', 'grief'] for e in emotion_list):
        tension = '中'
    else:
        tension = '低'
    
    # 复杂度：情绪种类数 >= 2 为复杂
    complexity = '复杂' if len(emotion_list) >= 2 else '简单'
    
    return intensity, hedonic, tension, complexity

# 应用映射
df_agg[['intensity', 'hedonic', 'tension', 'complexity']] = df_agg['emotions'].apply(
    lambda x: pd.Series(emotions_to_fourdim(x))
)

# ==================== 3. 保存结果 ====================
# 保存预处理后的数据
df_agg[['text', 'intensity', 'hedonic', 'tension', 'complexity']].to_csv(
    'data/goemotions_four_dim.csv', index=False, encoding='utf-8-sig'
)
print("预处理完成，已保存到 data/goemotions_four_dim.csv")
