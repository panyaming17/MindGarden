"""
测试实时分析数据保存功能
"""
import asyncio
import httpx
import json
from datetime import datetime

BASE_URL = "http://localhost:8001"

async def test_realtime_insight():
    """测试实时分析洞察保存功能"""
    
    # 用户凭据
    username = "pym"
    password = "pym123456"
    
    async with httpx.AsyncClient() as client:
        print("=" * 60)
        print("测试实时分析数据保存功能")
        print("=" * 60)
        
        # 1. 登录
        print("\n[步骤 1] 登录...")
        try:
            login_response = await client.post(
                f"{BASE_URL}/api/v1/auth/login",
                json={"username": username, "password": password}
            )
            login_data = login_response.json()
            token = login_data.get("access_token")
            user_id = login_data.get("user", {}).get("id")
            
            if not token:
                print(f"登录失败：{login_data}")
                return
            
            print(f"登录成功！用户 ID: {user_id}, Token: {token[:20]}...")
        except Exception as e:
            print(f"登录异常：{e}")
            return
        
        # 2. 创建新会话
        print("\n[步骤 2] 创建新会话...")
        try:
            headers = {"Authorization": f"Bearer {token}"}
            session_response = await client.post(
                f"{BASE_URL}/api/v1/chat/new-session",
                json={"user_id": user_id},
                headers=headers
            )
            session_data = session_response.json()
            session_id = session_data.get("session_id")
            
            if not session_id:
                print(f"创建会话失败：{session_data}")
                return
            
            print(f"会话创建成功！会话 ID: {session_id}")
        except Exception as e:
            print(f"创建会话异常：{e}")
            return
        
        # 3. 发送多条消息（触发分析师实时保存）
        print("\n[步骤 3] 发送多条消息（触发分析师实时保存分析数据）...")
        test_messages = [
            "最近我感觉很焦虑，工作压力很大",
            "我担心自己无法完成项目，觉得自己能力不够",
            "同事们都很优秀，我总觉得自己不如别人",
            "昨天晚上失眠了，一直在想工作的事情"
        ]
        
        for i, message in enumerate(test_messages, 1):
            print(f"\n  发送第 {i} 条消息...")
            try:
                message_response = await client.post(
                    f"{BASE_URL}/api/v1/chat/message",
                    json={
                        "user_id": user_id,
                        "session_id": session_id,
                        "message": message
                    },
                    headers=headers
                )
                message_data = message_response.json()
                
                if message_response.status_code == 200:
                    is_valuable = message_data.get("is_valuable", False)
                    print(f"  消息发送成功！是否有价值：{is_valuable}")
                    if is_valuable:
                        print(f"  -> 已触发分析师智能体，应已实时保存分析洞察")
                else:
                    print(f"  消息发送失败：{message_data}")
            except Exception as e:
                print(f"  消息发送异常：{e}")
            
            # 等待一下，避免请求太快
            await asyncio.sleep(1)
        
        # 4. 查询实时保存的分析洞察
        print("\n[步骤 4] 查询实时保存的分析洞察...")
        try:
            # 直接从数据库查询
            from backend.core.database import SessionLocal, SessionAnalysisInsightDB
            from sqlalchemy import and_
            
            db = SessionLocal()
            try:
                insights = db.query(SessionAnalysisInsightDB).filter(
                    and_(
                        SessionAnalysisInsightDB.user_id == user_id,
                        SessionAnalysisInsightDB.session_id == session_id
                    )
                ).order_by(SessionAnalysisInsightDB.created_at.asc()).all()
                
                print(f"\n  查询到 {len(insights)} 条实时分析洞察：")
                for i, insight in enumerate(insights, 1):
                    print(f"\n  --- 洞察 {i} ---")
                    print(f"  ID: {insight.id}")
                    print(f"  对话 ID: {insight.dialogue_id}")
                    print(f"  自动思维：{insight.common_automatic_thoughts}")
                    print(f"  思维陷阱：{insight.thinking_traps}")
                    print(f"  核心信念：{insight.core_beliefs}")
                    print(f"  认知映射：{len(insight.cognitive_mappings) if insight.cognitive_mappings else 0} 条")
                    print(f"  主导情志：{insight.tcm_dominant_emotion}")
                    print(f"  相关脏腑：{insight.tcm_related_organs}")
                    print(f"  气机动态：{insight.tcm_qi_dynamics}")
                    print(f"  创建时间：{insight.created_at}")
            finally:
                db.close()
        except Exception as e:
            print(f"查询分析洞察异常：{e}")
            import traceback
            traceback.print_exc()
        
        # 5. 结束会话并生成报告
        print("\n[步骤 5] 结束会话并生成报告...")
        try:
            end_response = await client.post(
                f"{BASE_URL}/api/v1/chat/end-session",
                json={
                    "user_id": user_id,
                    "session_id": session_id
                },
                headers=headers
            )
            end_data = end_response.json()
            
            print(f"\n会话结束响应：")
            print(f"  消息：{end_data.get('message')}")
            print(f"  报告 ID: {end_data.get('report_id')}")
            
            # 检查报告是否使用了实时数据
            reports = end_data.get("reports", {})
            if reports:
                analysis_report = reports.get("analysis_report", {})
                cognitive_analysis = analysis_report.get("cognitive_analysis", {})
                
                print(f"\n分析报告中的认知分析数据：")
                print(f"  自动思维数量：{len(cognitive_analysis.get('common_automatic_thoughts', []))}")
                print(f"  思维陷阱数量：{len(cognitive_analysis.get('thinking_traps', []))}")
                print(f"  核心信念数量：{len(cognitive_analysis.get('core_beliefs', []))}")
                print(f"  认知映射数量：{len(cognitive_analysis.get('mappings', []))}")
                
                tcm_analysis = analysis_report.get("tcm_analysis", {})
                print(f"\n中医分析数据：")
                print(f"  主导情志：{tcm_analysis.get('dominant_emotion', 'N/A')}")
                print(f"  相关脏腑：{tcm_analysis.get('related_organs', [])}")
                print(f"  气机动态：{tcm_analysis.get('qi_dynamics', 'N/A')}")
                
        except Exception as e:
            print(f"结束会话异常：{e}")
            import traceback
            traceback.print_exc()
        
        print("\n" + "=" * 60)
        print("测试完成！")
        print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_realtime_insight())
