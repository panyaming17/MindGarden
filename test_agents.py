# test_agents.py
import asyncio
import sys
import os

# 添加项目根目录到路径（根据你的实际结构调整）
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.agents.recorder_agent import RecorderAgent
from backend.agents.analyst_agent import AnalystAgent
from backend.agents.therapist_agent import TherapistAgent
from backend.core.llm_service import LLMService
from backend.core.database import DBConfig, UserDB

async def main():
    # 初始化 LLM 服务（根据你的实际实现调整）
    llm = LLMService(provider="deepseek")  # 这里需要替换为你的 LLM 服务实例

    # 创建数据库会话并检查/创建测试用户
    db = next(DBConfig.get_db())
    user_id = "test_user_001"
    existing_user = db.query(UserDB).filter(UserDB.id == user_id).first()
    if not existing_user:
        new_user = UserDB(
            id=user_id,
            username="test_user",
            email="test@example.com",
            password_hash="test_password",
            role="user"
        )
        db.add(new_user)
        db.commit()
        print(f"创建测试用户: {user_id}")
    db.close()

    # 创建三个智能体
    recorder = RecorderAgent(llm_service=llm)
    analyst = AnalystAgent(llm_service=llm)
    therapist = TherapistAgent(llm_service=llm)

    session_id = "test_session_001"

    test_messages = [
        "我明天要答辩，紧张得睡不着觉，脑子一片空白。",
        "我觉得自己肯定搞砸，老师会觉得我很差劲。",
        "其实我准备了很多，但还是害怕。"
    ]

    for user_input in test_messages:
        print("\n" + "="*60)
        print(f"👤 用户: {user_input}")

        # 1. 记录师
        recorder_result = await recorder.execute({
            "user_id": user_id,
            "message": user_input,
            "session_id": session_id
        })
        print(f"📝 记录师: 强度={recorder_result['intensity']}, "
              f"快感度={recorder_result['hedonic']}, "
              f"紧张度={recorder_result['tension']}, "
              f"复杂度={recorder_result['complexity']}, "
              f"有价值={recorder_result['is_valuable']}")

        four_dim = {
            "intensity": recorder_result["intensity"],
            "hedonic": recorder_result["hedonic"],
            "tension": recorder_result["tension"],
            "complexity": recorder_result["complexity"]
        }

        # 2. 如果有价值，调用分析师
        advice = None
        if recorder_result["is_valuable"]:
            analyst_result = await analyst.execute({
                "user_id": user_id,
                "user_input": user_input,
                "four_dim": four_dim,
                "dialogue_id": None,  # 暂不关联对话ID
                "session_id": session_id
            })
            if analyst_result["status"] == "success":
                advice = analyst_result["data"]
                print(f"🧠 分析师: 融合模式={advice.get('fusion_mode')}, "
                      f"当前焦点={advice.get('current_focus')}")
            else:
                print(f"⚠️ 分析师失败: {analyst_result['message']}")

        # 3. 调理师生成回复
        therapist_result = await therapist.execute({
            "user_id": user_id,
            "user_input": user_input,
            "advice": advice,  # 传递本次建议
            "session_id": session_id
        })
        if therapist_result["status"] == "success":
            print(f"💬 调理师: {therapist_result['data']['reply']}")
        else:
            print(f"⚠️ 调理师失败: {therapist_result['message']}")

    print("\n✅ 测试完成。")

if __name__ == "__main__":
    asyncio.run(main())