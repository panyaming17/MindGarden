import pandas as pd

df1 = pd.read_csv("data/mydata/merged_data_clean_final.csv")          # 当前干净数据（786条）
df2 = pd.read_csv("data/mydata/train/ai.csv")   # 新过滤数据

# 合并并去重（保留第一条，可按需排序）
df_combined = pd.concat([df1, df2], ignore_index=True)
df_combined = df_combined.drop_duplicates(subset=['text'])
df_combined.to_csv("data/mydata/train/human.csv", index=False, encoding='utf-8-sig')
print(f"合并后总样本数: {len(df_combined)}")