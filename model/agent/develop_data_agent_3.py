import pandas as pd
import time
import random
import os
import asyncio
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from backend.core.llm_service import LLMService

# 输出文件路径
OUTPUT_CSV = "data/mydata/ai_generated_samples_new2.csv"

# 生成计划（根据数据质量报告，优先补充少数类）
GENERATION_PLAN = [
    # ==================== 正性样本（共150条）====================
    # 正性 - 高紧张度 - 简单
    {"intensity_min": 6, "intensity_max": 9, "hedonic": "正性", "tension": "高", "complexity": "简单", "count": 25},
    # 正性 - 高紧张度 - 复杂
    {"intensity_min": 6, "intensity_max": 9, "hedonic": "正性", "tension": "高", "complexity": "复杂", "count": 25},
    # 正性 - 中紧张度 - 简单
    {"intensity_min": 5, "intensity_max": 8, "hedonic": "正性", "tension": "中", "complexity": "简单", "count": 25},
    # 正性 - 中紧张度 - 复杂
    {"intensity_min": 5, "intensity_max": 8, "hedonic": "正性", "tension": "中", "complexity": "复杂", "count": 25},
    # 正性 - 低紧张度 - 简单
    {"intensity_min": 3, "intensity_max": 6, "hedonic": "正性", "tension": "低", "complexity": "简单", "count": 25},
    # 正性 - 低紧张度 - 复杂
    {"intensity_min": 3, "intensity_max": 6, "hedonic": "正性", "tension": "低", "complexity": "复杂", "count": 25},

    # ==================== 中性样本（共80条）====================
    # 中性 - 高紧张度 - 简单
    {"intensity_min": 5, "intensity_max": 8, "hedonic": "中性", "tension": "高", "complexity": "简单", "count": 15},
    # 中性 - 高紧张度 - 复杂
    {"intensity_min": 5, "intensity_max": 8, "hedonic": "中性", "tension": "高", "complexity": "复杂", "count": 15},
    # 中性 - 中紧张度 - 简单
    {"intensity_min": 4, "intensity_max": 7, "hedonic": "中性", "tension": "中", "complexity": "简单", "count": 15},
    # 中性 - 中紧张度 - 复杂
    {"intensity_min": 4, "intensity_max": 7, "hedonic": "中性", "tension": "中", "complexity": "复杂", "count": 15},
    # 中性 - 低紧张度 - 简单
    {"intensity_min": 2, "intensity_max": 5, "hedonic": "中性", "tension": "低", "complexity": "简单", "count": 10},
    # 中性 - 低紧张度 - 复杂
    {"intensity_min": 2, "intensity_max": 5, "hedonic": "中性", "tension": "低", "complexity": "复杂", "count": 10},

    # ==================== 补充复杂情绪和高紧张度（结合负性，共100条）====================
    # 负性 - 高紧张度 - 复杂
    {"intensity_min": 6, "intensity_max": 9, "hedonic": "负性", "tension": "高", "complexity": "复杂", "count": 50},
    # 负性 - 中紧张度 - 复杂
    {"intensity_min": 5, "intensity_max": 8, "hedonic": "负性", "tension": "中", "complexity": "复杂", "count": 50},
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

    # 紧张度详细说明（增强描述）
    tension_instruction = {
        "高": "紧张度为“高”，请体现强烈的生理反应（如心跳加速、大脑空白、手抖、呼吸困难）或失控感、迫切感（如“当时真的急疯了”“感觉天要塌了”“完全不知道该怎么办”）。",
        "中": "紧张度为“中”，请体现一定的焦虑或压力感，但尚能控制，如“心里有点慌”“压力很大但还能应付”。",
        "低": "紧张度为“低”，请体现情绪平淡、无力感或长久的低落，而非剧烈冲动，如“没什么感觉”“就是有点提不起劲”。",
    }.get(tension, "")

    # 复杂度详细说明（增强描述）
    complexity_instruction = {
        "复杂": "复杂度为“复杂”，必须体现多种情绪的交织，例如既愤怒又委屈、既悲伤又担忧、既害怕又自责、又开心又失落等。请确保文本包含两种或以上不同的情绪。",
        "简单": "复杂度为“简单”，请聚焦于一种主导情绪，不要夹杂多种情绪。",
    }.get(complexity, "")

    # 根据快感度添加额外指导
    extra = ""
    if hedonic == "正性":
        extra = "请确保文本传递出积极、开心的情绪，如满足、欣慰、期待、兴奋等。"
    elif hedonic == "中性":
        extra = "请确保文本情绪平淡，无明显的正面或负面色彩，如描述日常学习生活、客观事实等。"
    # 负性无需额外说明，已有紧张度和复杂度指导

    # 构建提示词
    prompt = f"""请根据以下情绪维度要求，生成一段学生自述文本：

- 强度（1-10，10最强）：{intensity_desc}
- 快感度：{hedonic}
- 紧张度：{tension}
- 复杂度：{complexity}

要求：
1. 文本长度约 50-150 字。
2. 围绕学业压力、人际关系、就业焦虑、家庭矛盾等大学生常见烦恼展开（正性可围绕学业/生活的小确幸、期待等）。
3. 语言自然真实，像学生本人诉说，可适当使用口语词（如“真的”“简直了”“崩溃”“无语”等）。
4. {tension_instruction}
5. {complexity_instruction}
{f'6. {extra}' if extra else ''}

只输出文本内容，不要任何解释。"""

    try:
        # 使用项目的 LLMService，通过上下文管理器确保会话被关闭
        async with LLMService(provider="deepseek") as llm_service:
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

        print(f"正在生成 {hedonic}-{tension}紧张度-{complexity}复杂度 共 {target_count} 条...")

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
                # 在范围内随机选择一个具体的强度值作为标签
                intensity_value = random.uniform(intensity_min, intensity_max)
                generated_data.append({
                    "text": text,
                    "intensity": round(intensity_value, 2),  # 保留两位小数
                    "hedonic": hedonic,
                    "tension": tension,
                    "complexity": complexity,
                    "source": "ai_generated"
                })
                success += 1
                print(f"  [{success}/{target_count}] 成功")
            else:
                print("  生成失败，重试...")
            # 控制请求频率，避免触发限流
            await asyncio.sleep(1)

    # 保存为 CSV，只保留需要的列
    df = pd.DataFrame(generated_data)
    df = df[["text", "intensity", "hedonic", "tension", "complexity"]]  # 确保列顺序
    os.makedirs(os.path.dirname(OUTPUT_CSV), exist_ok=True)
    df.to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")
    print(f"\n生成完成！共生成 {len(df)} 条数据，已保存至 {OUTPUT_CSV}")

if __name__ == "__main__":
    asyncio.run(main())