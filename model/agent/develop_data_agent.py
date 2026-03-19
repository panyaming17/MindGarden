import pandas as pd
import time
import random
import os

from backend.core.llm_service import LLMService

# 输出文件路径
OUTPUT_CSV = "data/mydata/ai_generated_samples_new.csv"

# 生成计划（列表形式，每个元素是一个字典，包含维度范围和目标数量）
GENERATION_PLAN = [
    # 原有负性样本（保持数量，继续补充少数类）
    {"intensity_min": 7, "intensity_max": 9, "hedonic": "负性", "tension": "高", "complexity": "简单", "count": 30},
    {"intensity_min": 6, "intensity_max": 8, "hedonic": "负性", "tension": "中", "complexity": "复杂", "count": 30},
    {"intensity_min": 8, "intensity_max": 9, "hedonic": "负性", "tension": "高", "complexity": "复杂", "count": 20},
    {"intensity_min": 5, "intensity_max": 7, "hedonic": "负性", "tension": "中", "complexity": "简单", "count": 20},
    {"intensity_min": 4, "intensity_max": 6, "hedonic": "负性", "tension": "低", "complexity": "简单", "count": 20},

    # 新增正性样本（强度可稍低，紧张度低，复杂度简单为主）
    {"intensity_min": 3, "intensity_max": 6, "hedonic": "正性", "tension": "低", "complexity": "简单", "count": 20},
    {"intensity_min": 4, "intensity_max": 7, "hedonic": "正性", "tension": "中", "complexity": "简单", "count": 10},
    {"intensity_min": 5, "intensity_max": 8, "hedonic": "正性", "tension": "低", "complexity": "复杂", "count": 5},  # 复杂正性（如喜忧参半）

    # 新增中性样本（情绪平淡，强度低，紧张度低）
    {"intensity_min": 2, "intensity_max": 4, "hedonic": "中性", "tension": "低", "complexity": "简单", "count": 20},
    {"intensity_min": 3, "intensity_max": 5, "hedonic": "中性", "tension": "低", "complexity": "简单", "count": 10},
    {"intensity_min": 4, "intensity_max": 6, "hedonic": "中性", "tension": "中", "complexity": "简单", "count": 5},  # 略带焦虑的中性
]

async def generate_one(intensity_range, hedonic, tension, complexity, temperature=0.8):
    """
    生成一条符合指定维度要求的学生自述文本。
    intensity_range: (min, max) 强度范围
    hedonic: 快感度（正性/负性/中性）
    tension: 紧张度（高/中/低）
    complexity: 复杂度（简单/复杂）
    temperature: 生成温度（越高多样性越大）
    """
    intensity_desc = f"{intensity_range[0]}-{intensity_range[1]}"

    # 紧张度详细说明
    tension_instruction = {
        "高": "紧张度为“高”，请体现生理反应（如心跳加速、大脑空白、手抖）或迫切感（如“当时真的急疯了”“感觉天要塌了”）。",
        "中": "紧张度为“中”，请体现一定的焦虑或压力感，但未到失控程度。",
        "低": "紧张度为“低”，请体现情绪平淡、无力感或长久的低落，而非剧烈冲动。",
    }.get(tension, "")

    # 复杂度详细说明
    complexity_instruction = {
        "复杂": "复杂度为“复杂”，请体现多种情绪交织，例如既愤怒又委屈、既悲伤又担忧、既害怕又自责等。",
        "简单": "复杂度为“简单”，请聚焦于一种主导情绪，不要夹杂多种情绪。",
    }.get(complexity, "")

# 根据快感度添加额外指导
    if hedonic == "正性":
        extra = "请确保文本传递出积极、开心的情绪，如满足、欣慰、期待等。"
    elif hedonic == "中性":
        extra = "请确保文本情绪平淡，无明显的正面或负面色彩，如描述日常学习生活。"
    else:
        extra = ""  # 负性无需额外说明，已有 tension_instruction 等覆盖

    # 构建提示词
    prompt = f"""请根据以下情绪维度要求，生成一段学生自述文本：

- 强度（1-10，10最强）：{intensity_desc}
- 快感度：{hedonic}
- 紧张度：{tension}
- 复杂度：{complexity}

要求：
1. 文本长度约 50-150 字。
2. 围绕学业压力、人际关系、就业焦虑、家庭矛盾等大学生常见烦恼展开。
3. 语言自然真实，像学生本人诉说，可适当使用口语词（如“真的”“简直了”）。
4. {tension_instruction}
5. {complexity_instruction}
{f'6. {extra}' if extra else ''}

只输出文本内容，不要任何解释。"""

    try:
        # 使用项目的 LLMService
        llm_service = LLMService(provider="deepseek")
        response = await llm_service.chat_completion(
            messages=[
                {"role": "system", "content": "你是一位专业的心理学语料生成助手，擅长以第一人称口吻生成真实自然的学生心理自述文本。"},
                {"role": "user", "content": prompt}
            ],
            temperature=temperature,
            max_tokens=300
        )
        return response.strip()
    except Exception as e:
        print(f"生成出错: {e}")
        return None

async def main():
    """主函数"""
    generated_data = []

    for plan in GENERATION_PLAN:
        intensity_min = plan["intensity_min"]
        intensity_max = plan["intensity_max"]
        hedonic = plan["hedonic"]
        tension = plan["tension"]
        complexity = plan["complexity"]
        target_count = plan["count"]

        print(f"正在生成 {tension}紧张度/{complexity}复杂度 共 {target_count} 条...")

        success = 0
        while success < target_count:
            # 随机温度增加多样性
            temp = random.uniform(0.7, 1.0)
            text = await generate_one(
                intensity_range=(intensity_min, intensity_max),
                hedonic=hedonic,
                tension=tension,
                complexity=complexity,
                temperature=temp
            )
            if text:
                # 可选：在这里加入模型验证步骤（例如用你的预训练模型预测并对比标签）
                generated_data.append({
                    "text": text,
                    "intensity": f"{intensity_min}-{intensity_max}",
                    "intensity_min": intensity_min,
                    "intensity_max": intensity_max,
                    "hedonic": hedonic,
                    "tension": tension,
                    "complexity": complexity,
                    "source": "ai_generated"
                })
                success += 1
                print(f"  [{success}/{target_count}] 成功")
            else:
                print("  生成失败，重试...")
            time.sleep(1)  # 控制请求频率，避免触发限流

    # 保存为 CSV
    os.makedirs(os.path.dirname(OUTPUT_CSV), exist_ok=True)
    df = pd.DataFrame(generated_data)
    df.to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")
    print(f"\n生成完成！共生成 {len(df)} 条数据，已保存至 {OUTPUT_CSV}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())