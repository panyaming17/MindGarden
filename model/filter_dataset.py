import pandas as pd
import argparse
import os

def filter_dataset(input_file, output_file=None, min_length=10):
    """
    过滤数据集：去除短文本和重复文本
    :param input_file: 输入 CSV 文件路径
    :param output_file: 输出 CSV 文件路径（若为 None，则自动在原文件名后加 _filtered）
    :param min_length: 最小文本长度（字符数），短于此长度的文本将被删除
    """
    # 读取数据
    print(f"读取数据文件: {input_file}")
    df = pd.read_csv(input_file)
    original_count = len(df)
    print(f"原始数据条数: {original_count}")

    # 检查必要列是否存在
    required_cols = ['text', 'intensity', 'hedonic', 'tension', 'complexity']
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"数据文件中缺少必要的列: {col}")

    # 1. 去除文本长度过短的样本
    df['text_len'] = df['text'].astype(str).apply(len)
    before_len = len(df)
    df = df[df['text_len'] >= min_length]
    after_len = len(df)
    print(f"去除长度 < {min_length} 的文本: 删除了 {before_len - after_len} 条")

    # 2. 去除重复文本
    before_dup = len(df)
    df = df.drop_duplicates(subset=['text'])
    after_dup = len(df)
    print(f"去除重复文本: 删除了 {before_dup - after_dup} 条")

    # 删除临时长度列
    df.drop(columns=['text_len'], inplace=True)

    # 最终统计
    final_count = len(df)
    print(f"过滤后数据条数: {final_count}")
    print(f"共删除 {original_count - final_count} 条数据")

    # 保存文件
    if output_file is None:
        base, ext = os.path.splitext(input_file)
        output_file = f"{base}_filtered{ext}"
    df.to_csv(output_file, index=False, encoding='utf-8-sig')
    print(f"过滤后数据已保存至: {output_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="过滤数据集：去除短文本和重复文本")
    parser.add_argument("input_file", help="输入的 CSV 文件路径")
    parser.add_argument("--output_file", help="输出的 CSV 文件路径（可选）")
    parser.add_argument("--min_length", type=int, default=10, help="最小文本长度（字符数），默认10")
    args = parser.parse_args()

    filter_dataset(args.input_file, args.output_file, args.min_length)