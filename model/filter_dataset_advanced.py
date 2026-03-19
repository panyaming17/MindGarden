import pandas as pd
import argparse
import os

def filter_dataset(input_file, output_file=None, min_length=5, protect_minority=True):
    """
    过滤数据集：去除短文本和重复文本，可选择保护少数类样本
    :param input_file: 输入 CSV 文件路径
    :param output_file: 输出 CSV 文件路径（可选）
    :param min_length: 最小文本长度（字符数）
    :param protect_minority: 是否保护少数类（复杂、高紧张度、正性）不被短文本过滤删除
    """
    # 读取数据
    print(f"读取数据文件: {input_file}")
    df = pd.read_csv(input_file)
    original_count = len(df)
    print(f"原始数据条数: {original_count}")

    # 添加文本长度列
    df['text_len'] = df['text'].astype(str).apply(len)

    # 1. 短文本过滤
    if protect_minority:
        # 定义少数类条件（可根据需要调整）
        minority_condition = (
            (df['complexity'] == '复杂') |
            (df['tension'] == '高') |
            (df['hedonic'] == '正性')
        )
        # 保留长度足够 或 属于少数类的样本
        df = df[(df['text_len'] >= min_length) | minority_condition]
        removed = original_count - len(df)
        print(f"短文本过滤（保护少数类）：保留 {len(df)} 条，删除了 {removed} 条（其中 {removed} 条可能是短文本且不属于少数类）")
    else:
        df = df[df['text_len'] >= min_length]
        print(f"短文本过滤（无保护）：保留 {len(df)} 条，删除了 {original_count - len(df)} 条")

    # 2. 去除重复文本
    before_dup = len(df)
    # 如果有 source 列，可以按优先级去重（这里简单去重，保留第一条）
    df = df.drop_duplicates(subset=['text'])
    after_dup = len(df)
    print(f"去重：删除了 {before_dup - after_dup} 条重复")

    # 删除临时列
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
    parser = argparse.ArgumentParser(description="过滤数据集：去除短文本和重复文本，可选择保护少数类")
    parser.add_argument("input_file", help="输入的 CSV 文件路径")
    parser.add_argument("--output_file", help="输出的 CSV 文件路径（可选）")
    parser.add_argument("--min_length", type=int, default=5, help="最小文本长度（字符数），默认5")
    parser.add_argument("--no_protect", action="store_false", dest="protect_minority",
                        help="禁用保护少数类模式，即所有短文本一律删除")
    args = parser.parse_args()

    filter_dataset(args.input_file, args.output_file, args.min_length, args.protect_minority)