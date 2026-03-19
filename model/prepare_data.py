import pandas as pd
import re
import os

# ==================== 配置路径 ====================
# 输入文件路径（相对于当前工作目录）
input_file = 'data/mydata/unmarked_data.txt'
# 输出文件路径
output_file = 'data/mydata/cleaned_texts.csv'

# ==================== 清洗函数 ====================
def clean_text(text):
    """清洗单条文本：合并换行、去除多余空格、可选添加句号"""
    # 将连续的空白字符（包括换行）替换为一个空格
    text = re.sub(r'\s+', ' ', text)
    # 去除首尾空格
    text = text.strip()
    # 如果最后一个字符不是常见的结束标点，添加句号（可选，不影响模型理解）
    if text and text[-1] not in '。！？；':
        text += '。'
    return text

def split_entries(filepath):
    """按空行分割文件，返回每条文本的列表"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    # 按两个及以上换行符分割（即空行）
    entries = re.split(r'\n\s*\n', content)
    # 过滤掉空字符串
    entries = [e.strip() for e in entries if e.strip()]
    return entries

# ==================== 主流程 ====================
def main():
    # 1. 检查输入文件是否存在
    if not os.path.exists(input_file):
        print(f"错误：文件 {input_file} 不存在，请检查路径。")
        return

    # 2. 分割条目
    print(f"正在读取 {input_file} ...")
    entries = split_entries(input_file)
    print(f"共找到 {len(entries)} 条自述")

    # 3. 清洗每条文本
    cleaned = [clean_text(entry) for entry in entries]

    # 4. 保存为 CSV
    df = pd.DataFrame({'text': cleaned})
    # 确保输出目录存在
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    df.to_csv(output_file, index=False, encoding='utf-8-sig')
    print(f"已保存到 {output_file}")

if __name__ == '__main__':
    main()