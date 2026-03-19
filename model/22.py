import pandas as pd

# 读取CSV，假设列名是 text, hedonic, intensity, tension, complexity
df = pd.read_csv("data/mydata/train/11.csv", header=None, names=['text','hedonic','intensity','tension','complexity'])
# 重新排列为 text, intensity, hedonic, tension, complexity
df = df[['text','intensity','hedonic','tension','complexity']]
# 保存为新文件
df.to_csv("data/mydata/train/human2.csv", index=False, encoding='utf-8-sig')
