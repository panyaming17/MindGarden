"""
记录师智能体 (Recorder Agent)
职责：与用户进行初步共情对话，提取并结构化关键情绪信息。
"""
from typing import Dict, Any, Optional
import json
import time
import re
from datetime import datetime
import uuid

from backend.agents.base_agent import BaseAgent
from backend.core.data_models import StructuredRecord
from backend.repositories.record_repository import RecordRepository

from backend.core.llm_service import LLMService

class RecorderAgent(BaseAgent):
    """记录师智能体 - 负责情绪信息收集与结构化"""
    
    def __init__(self, agent_name: str = "recorder_agent", llm_service: Optional[LLMService] = None):
        super().__init__(agent_name)
        self.repository = RecordRepository()  # 数据存储层
        self.llm_service = llm_service  # 注入的LLM服务
        self._init_prompts()  # 初始化提示词模板
        
        # 会话状态跟踪（可选，用于多轮对话）
        self.active_sessions = {}  # {session_id: {state, history}}
    
    def _init_prompts(self):
        """初始化记录师专用的提示词模板（融合中医情志安抚与智能推进）"""
        self.system_prompt = """你是一位专业的心理记录师，负责情绪疏导初始阶段的倾听与信息采集。你的核心任务是：通过共情式对话，引导用户描述引发情绪的具体情境、当时的想法、身体感受和情绪状态，并将这些信息结构化输出给分析师。同时，你可以运用中医“五情相胜”的智慧，在用户情绪强烈时给予简短的即时安抚，但你的主要职责仍是记录而非干预。
    ## 一、信息收集清单（记录报告字段）
    你需要从对话中提取以下关键信息，形成结构化的“情绪标本”：
    - **situation**：引发情绪的具体事件或情境（例如：“昨天和同事吵架了”、“早上醒来想到工作就难受”）
    - **automatic_thoughts**：用户脑海中自动浮现的想法（列表形式，至少1条，例如：“我什么都做不好”、“没人理解我”）
    - **emotions**：情绪类型及强度（情绪类型必须从中医五情中选择：怒、喜、忧、思、恐；强度为1-10的整数，可参考下文的量化指南）
    - **physical_sensations**：身体感受（列表形式，例如：胸闷、头痛、失眠、食欲不振等，用户若说“没有”也算收集）

    ## 二、对话策略：分阶段灵活引导

    ### 第一阶段：共情与开放探索（对话初期）
    - 先共情，用温暖的语言接纳用户的情绪，避免机械重复。
    - 使用开放式问题引导用户开始表达：“今天是什么事情让你想聊聊呢？可以告诉我发生了什么，以及你当时的感受吗？”

    ### 第二阶段：聚焦与结构化收集（当用户开始表达后）
    - 每次回应至少引导用户补充1-2个缺失字段。引导方式应多样化，可围绕以下四个维度切换：
    * **情境**：“当时具体发生了什么？在哪里？和谁？”
    * **想法**：“当那件事发生时，你脑海里闪过了哪些念头？”
    * **情绪**：“那种情绪如果用1-10打分，10分最强烈，你感觉是几分？”（可结合量化选项帮助用户定位）
    * **身体**：“身体上有什么感觉吗？比如哪里紧绷、沉重、或者不舒服？”

    **情绪强度量化辅助**（供你生成选项时使用）：
    当用户表达某种情绪但未给出强度时，可根据情绪类型提供典型场景选项，例如：
    - 对于“忧”：
    - 轻度：听到一个不太好的消息，心里有点闷（强度3）
    - 中度：和朋友闹矛盾，一直想着这事，吃饭不香（强度6）
    - 重度：失去了重要的人，感觉未来没有希望（强度9）
    其他情绪（怒、喜、思、恐）可参考类似描述。用户选择后，你可以根据选项对应的强度值（3/6/9）填入JSON，也可根据对话细节微调。

    ### 第三阶段：中医情志即时安抚（当用户情绪强烈时）
    如果你觉察到用户情绪非常强烈（例如强度≥7，或表达出明显的痛苦），可以在记录的同时，运用中医“五情相胜”理论给予简短的情绪安抚，帮助用户稳定状态，以便继续对话。**注意：安抚只是辅助，切勿喧宾夺主，记录仍是首要任务。**

    **五情相胜关系**：
    - 悲（忧）胜怒  →  对愤怒的用户，可以引导其想一些悲伤的事（但需谨慎使用）
    - 恐胜喜      →  对过度兴奋的用户，引导其考虑潜在风险
    - 怒胜思      →  对思虑过度的用户，引导其表达愤怒或不满
    - **喜胜忧**  →  对忧虑的用户，引导其回忆开心的事、听欢快的音乐、看喜剧等（本项目重点）
    - 思胜恐      →  对恐惧的用户，引导其理性分析

    **应用示例**：
    - 如果用户深陷“忧”中：“我感受到你现在被忧虑包围着。在中医里，有一种‘喜胜忧’的说法，意思是适当的心情愉悦可以帮助缓解忧愁。也许你可以试着回忆一件最近让你感到温暖或开心的小事，哪怕只有一分钟，或者听一段欢快的音乐。当然，我们不需要立刻好起来，只是给自己一个小小的缓冲。”
    - 如果用户“思虑过度”：“你反复琢磨这件事，一定很累。中医认为‘怒胜思’，有时候适度地表达自己的不满，反而能让思绪停下来。你可以想想，这件事里有没有让你感到不公平的地方？”

    **使用原则**：
    - 简短、自然，不强行说教。
    - 安抚后仍需回到信息收集主线：“谢谢你和我说这些，我们继续聊聊当时的情况好吗？”

    ### 第四阶段：信息收集完成与流程推进
    **信息收集完成标准**（满足以下任意一种情况即可生成JSON推进）：
    1. **基本完整**：已收集到具体情境、至少1条自动思维、至少一种情绪及其强度，且已尝试询问身体感受（无论用户是否提供）。
    2. **最小可行**：用户始终无法提供具体情境或想法，但情绪类型和强度已明确（例如用户反复说“没力气”、“就是难受”），且对话已进行至少4轮。此时可生成JSON，将缺失字段设为合理默认值：
    - situation：可设为“用户未明确具体事件，但表达了持续的情绪困扰”
    - automatic_thoughts：可设为[]或[“用户未表达具体想法”]
    - physical_sensations：根据已有信息填写，若无则设为[]

    **推进时的行动**：
    当你判断信息足够时，应：
    1. 用共情的语言总结你收集到的信息，并请用户确认：“我试着整理一下：你最近因为……（情境），脑海里反复出现……（想法），情绪上感到……（情绪类型+强度），身体上也有……（身体感受）。是这样吗？”
    2. 告知用户即将进入分析阶段：“好的，感谢你的分享。接下来我会把这些信息交给分析师，从专业角度帮你梳理一下，请稍等。”
    3. 输出包裹在 ```json 中的结构化JSON数据。

    ### 第五阶段：处理僵局与重复（关键！防止对话循环）
    当用户反复重复同一句话（如“我没力气”、“我就是控制不了”）时，**不要重复提问**，而应采取以下策略之一：
    - **切换维度**：从当前卡住的维度转向其他维度。例如，用户一直说“没力气”（可能属于身体感受），你可以问：“这种没力气的感受，如果用一个画面或比喻来形容，会是什么？”（切换到认知/隐喻），或者问：“如果0是完全没力气，10是充满能量，你现在在几分？”（量化）。
    - **承认并总结**：直接承认用户的重复，并表达理解，然后尝试推进：“我听到你反复提到‘没力气’，这种持续的疲惫感一定很消耗你。也许我们不需要立刻找到原因，你可以先告诉我，当这种没力气的感觉最明显的时候，通常是在一天的哪个时刻？”
    - **给出有限选项**：当用户难以描述时，提供几个可能的选项供其选择：“你更倾向于觉得是‘身体被掏空’，还是‘心里压着石头’，或者是‘什么都不想做’？”
    - **如果多次尝试后仍无进展**：直接进入信息收集完成的最小可行模式，生成JSON推进。

    ## 三、输出格式
    - **正常对话中**：只输出自然语言文本（可包含情绪安抚语句），不要输出JSON。
    - **信息收集完成时**：先输出自然语言总结和推进语，然后另起一行输出包裹在 ```json 和 ``` 中的JSON数据。
    - **JSON格式必须严格遵循以下结构**（字段顺序不限）：
    ```json
    {
    "situation": "简要描述事件或情境",
    "automatic_thoughts": ["想法1", "想法2"],
    "emotions": [{"type": "忧", "intensity": 7}],
    "physical_sensations": ["头痛", "失眠"],
    "conversation_summary": "本次对话的简要总结，用于分析师参考"
    }
    ```
    """

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行记录师的核心流程。
        输入格式：
        {
            "session_id": "唯一会话ID",  # 可选，用于多轮对话
            "user_input": "用户本次输入文本",
            "is_new_session": true/false  # 是否是新会话
        }
        """
        start_time = time.time()
        
        try:
            # 1. 提取输入参数
            session_id = input_data.get("session_id") or f"session_{uuid.uuid4().hex[:8]}"
            user_input = input_data.get("user_input", "").strip()
            is_new_session = input_data.get("is_new_session", True)
            
            if not user_input:
                return self._create_response(
                    success=False,
                    message="用户输入不能为空",
                    session_id=session_id
                )
            
            # 2. 管理会话状态（用于多轮对话上下文）
            await self._update_session_state(session_id, user_input, is_new_session)
            
            # 打印当前对话的关键信息
            print(f"\n[对话关键信息]")
            print(f"会话ID: {session_id}")
            print(f"用户输入: {user_input}")
            print(f"是否新会话: {is_new_session}")
            
            # 3. 构建对话历史上下文（用于LLM调用）
            conversation_context = await self._build_conversation_context(session_id)
            
            # 打印对话上下文
            print(f"\n[对话上下文]")
            print(conversation_context)
            print("\n")
            
            # 4. 调用LLM进行共情回应并尝试提取结构化信息
            llm_response = await self._call_llm_with_structured_output(
                conversation_context, user_input, session_id
            )
            
            # 缓存LLM响应中的情绪程度场景内容
            self._cache_emotion_scenarios(session_id, llm_response)
            
            # 打印LLM原始响应
            print(f"[LLM原始响应]")
            print(llm_response)
            print("\n")
            
            # 5. 尝试从LLM响应中解析结构化数据
            structured_data, llm_text_response = self._parse_llm_response(llm_response)
            
            # 尝试从用户输入中提取情绪程度
            emotion_type, intensity = self._extract_emotion_intensity(session_id, user_input)
            if emotion_type and intensity:
                print(f"[自动提取情绪程度] 情绪类型: {emotion_type}, 强度: {intensity}")
                # 如果提取到情绪程度，可以在这里更新已收集的数据
                if session_id in self.active_sessions:
                    # 确保情绪数据结构存在
                    if "emotions" not in self.active_sessions[session_id]["collected_data"]:
                        self.active_sessions[session_id]["collected_data"]["emotions"] = []
                    # 添加或更新情绪数据
                    emotion_data = {"type": emotion_type, "intensity": intensity}
                    self.active_sessions[session_id]["collected_data"]["emotions"].append(emotion_data)
                    self.active_sessions[session_id]["collected_fields"].add("emotions")
            
            # 如果提取到结构化数据，更新已收集的字段和数据
            if structured_data:
                # 更新已收集的字段
                if session_id in self.active_sessions:
                    # 添加已收集的字段
                    for field in structured_data:
                        if structured_data[field]:  # 确保字段有值
                            self.active_sessions[session_id]["collected_fields"].add(field)
                            self.active_sessions[session_id]["collected_data"][field] = structured_data[field]
            
            # 打印当前已收集的字段和数据
            if session_id in self.active_sessions:
                print(f"[已收集信息]")
                print(f"已收集字段: {self.active_sessions[session_id]['collected_fields']}")
                print(f"已收集数据: {json.dumps(self.active_sessions[session_id]['collected_data'], ensure_ascii=False, indent=2)}")
                print("\n")
            
            # 打印解析结果
            print(f"[解析结果]")
            print(f"提取到结构化数据: {structured_data is not None}")
            print(f"LLM文本回应: {llm_text_response}")
            print("\n")
            
            # 6. 如果成功提取结构化数据，则保存记录并结束本轮
            if structured_data:
                # 打印从前端获取到的结构化数据
                print("\n[前端获取的结构化数据]")
                print(json.dumps(structured_data, ensure_ascii=False, indent=2))
                print("\n")
                
                # 创建结构化记录对象
                structured_record = await self._create_structured_record(
                    session_id, structured_data, conversation_context
                )
                
                # 保存到数据库
                record_id = await self.repository.save_record(structured_record)
                
                # 清理会话状态（本轮记录完成）
                self._cleanup_session(session_id)
                
                return self._create_response(
                    success=True,
                    message="已成功完成情绪记录",
                    session_id=session_id,
                    record_id=record_id,
                    structured_data=structured_data,
                    llm_response=llm_text_response,  # LLM最后的共情总结
                    next_action="trigger_analyst",  # 触发下一个智能体
                    processing_time=time.time() - start_time
                )
            else:
                # 7. 如果未提取到结构化数据，则继续对话
                # 确保返回的响应中包含structured_data字段，未获取到时返回空值
                return self._create_response(
                    success=True,
                    message="继续对话以收集更多信息",
                    session_id=session_id,
                    llm_response=llm_text_response,  # LLM的引导性问题
                    next_action="continue_dialogue",
                    structured_data=None,  # 未获取到结构化数据时返回空值
                    processing_time=time.time() - start_time
                )
                
        except Exception as e:
            return self._create_response(
                success=False,
                message=f"记录过程发生错误: {str(e)}",
                session_id=input_data.get("session_id", "unknown"),
                structured_data=None,  # 异常情况下返回空值
                processing_time=time.time() - start_time
            )
    
    async def _call_llm_with_structured_output(self, context: str, user_input: str, session_id: str) -> str:
        """
        调用LLM，特别设计提示词以鼓励结构化JSON输出。
        这里集成了你的文心一言/DeepSeek/OpenAI API调用。
        """
        # 1. 构建给大模型的完整“系统指令”和“用户消息”
        system_message = {
            "role": "system",
            "content": self.system_prompt  # 使用你初始化好的详细系统提示词
        }
        # 构建完整的对话提示
        full_prompt = f"""对话历史上下文：
{context}

用户本次输入：
{user_input}

请你严格遵循系统指令：
1. 首先进行1-2句共情回应。
2. 然后，**当且仅当**你认为已经收集到【情境】、【自动思维】和【情绪】这三类完整信息时，才输出一个JSON对象。
3. 如果信息不足，请只输出一个开放式的引导问题来追问。

你的回应："""
        user_message = {
            "role": "user",
            "content": full_prompt
        }
    
        messages = [system_message, user_message]
    
        # 2. 调用统一的LLM服务
        try:
            if self.llm_service:
                # 注意：为增加JSON输出稳定性，可启用 json_mode (如果提供商支持)
                llm_raw_response = await self.llm_service.chat_completion(
                    messages=messages,
                    temperature=0.5,  # 适当提高温度，增加输出多样性
                    max_tokens=1500,
                    json_mode=False,  # DeepSeek等支持，百度可能不支持
                    try_all_providers=True  # 当一个模型调用失败时，自动尝试下一个模型
                )
                return llm_raw_response
            else:
                # 备用：如果没有注入服务，回落到你已有的配置加载方式
                from backend.core.llm_service import get_llm_service
                service = await get_llm_service()
                return await service.chat_completion(
                    messages,
                    temperature=0.3,
                    try_all_providers=True  # 确保全局实例也使用try_all_providers功能
                )
        except Exception as e:
            # 3. 异常处理：记录日志并返回友好的降级回应
            print(f"[记录师Agent] LLM调用失败: {e}")
            # 降级策略：返回一个引导性问题，保证对话不中断
            return "我这边暂时遇到了一点技术问题。不过没关系，我们可以继续。你刚才说到的感受，身体上有什么特别的觉知吗？"
    
    def _parse_llm_response(self, llm_response: str) -> tuple[Optional[Dict], str]:
        """
        从LLM响应中尝试解析JSON结构化数据。
        返回：(structured_data, text_response)
        """
        # 匹配 ```json ... ``` 或 {...} 模式
        json_pattern = r'```json\s*(.*?)\s*```|({.*})'
        matches = re.findall(json_pattern, llm_response, re.DOTALL)
        
        for match in matches:
            json_str = match[0] or match[1]  # 两种模式取非空的那个
            if json_str:
                try:
                    structured_data = json.loads(json_str)
                    
                    # 验证必要字段
                    required_fields = ['situation', 'automatic_thoughts', 'emotions']
                    if all(field in structured_data for field in required_fields):
                        # 提取JSON之外的文本作为LLM的共情回应
                        text_response = llm_response.replace(f"```json\n{json_str}\n```", "").strip()
                        text_response = text_response.replace(json_str, "").strip()
                        
                        # 如果文本回应为空，使用一个默认的共情总结
                        if not text_response:
                            situation = structured_data.get('situation', '这个情况')
                            text_response = f"感谢你的分享。我已经记录了关于「{situation}」的情绪信息。"
                        
                        return structured_data, text_response
                except json.JSONDecodeError:
                    continue
        
        # 方法2：如果没有找到完整JSON，检查响应是否看起来像引导性问题（而不是JSON）
        if '?' in llm_response and len(llm_response) < 150:
            return None, llm_response  # 纯文本引导问题
        
        # 方法3：默认情况，返回原始响应作为文本
        return None, llm_response
    
    async def _create_structured_record(self, session_id: str, 
                                       structured_data: Dict[str, Any],
                                       conversation_context: str) -> StructuredRecord:
        """创建结构化记录对象"""
        # 从会话状态中获取用户ID（在实际系统中应从认证获取）
        session_state = self.active_sessions.get(session_id, {})
        
        # 生成唯一记录ID
        record_id = f"rec_{uuid.uuid4().hex[:8]}"
        
        return StructuredRecord(
            record_id=record_id,
            user_id=session_state.get("user_id", "anonymous_user"),
            raw_text=conversation_context,  # 原始对话历史
            situation=structured_data.get("situation", ""),
            automatic_thoughts=structured_data.get("automatic_thoughts", []),
            emotions=structured_data.get("emotions", []),
            physical_sensations=structured_data.get("physical_sensations", []),
            created_at=datetime.now()
        )
    
    async def _update_session_state(self, session_id: str, user_input: str, is_new_session: bool):
        """更新和管理会话状态"""
        if is_new_session or session_id not in self.active_sessions:
            self.active_sessions[session_id] = {
                "user_id": f"user_{uuid.uuid4().hex[:6]}",  # 模拟用户ID
                "history": [],
                "start_time": time.time(),
                "state": "collecting_info",
                "collected_fields": set(),  # 已收集的字段集合
                "collected_data": {},  # 已收集的具体数据
                "emotion_scenarios": {}  # 缓存的情绪程度场景内容 {情绪类型: {强度: 场景描述}}
            }
        
        # 将本次交互加入历史
        self.active_sessions[session_id]["history"].append({
            "role": "user",
            "content": user_input,
            "timestamp": time.time()
        })
    
    async def _build_conversation_context(self, session_id: str) -> str:
        """构建对话历史上下文，用于LLM调用"""
        if session_id not in self.active_sessions:
            return "这是对话的开始。"
        
        history = self.active_sessions[session_id]["history"]
        
        # 只保留最近N轮对话以避免上下文过长
        max_turns = 6
        recent_history = history[-max_turns:] if len(history) > max_turns else history
        
        context_lines = []
        for i, turn in enumerate(recent_history):
            role = "用户" if turn["role"] == "user" else "记录员"
            context_lines.append(f"{role}: {turn['content']}")
        
        return "\n".join(context_lines)
    
    def _cleanup_session(self, session_id: str):
        """清理会话状态（一轮记录完成）"""
        if session_id in self.active_sessions:
            # 可以将会话历史存档或清理
            del self.active_sessions[session_id]
    
    def _extract_emotion_intensity(self, session_id: str, user_input: str) -> tuple[Optional[str], Optional[int]]:
        """
        从用户输入中提取情绪程度
        如果用户使用了之前LLM提供的场景内容回答，自动提取对应的情绪程度
        
        返回：(情绪类型, 强度值) 或 (None, None)
        """
        if session_id not in self.active_sessions:
            return None, None
        
        emotion_scenarios = self.active_sessions[session_id].get("emotion_scenarios", {})
        
        # 遍历缓存的情绪场景
        for emotion_type, scenarios in emotion_scenarios.items():
            for intensity, scenario in scenarios.items():
                # 检查用户输入是否包含场景描述的关键词
                if any(keyword in user_input for keyword in scenario.split()):
                    return emotion_type, intensity
        
        return None, None
    
    def _cache_emotion_scenarios(self, session_id: str, llm_response: str):
        """
        从LLM响应中缓存情绪程度场景内容
        当LLM生成情绪程度场景供用户选择时，缓存这些场景
        """
        if session_id not in self.active_sessions:
            return
        
        # 简单的场景提取逻辑，实际实现可能需要更复杂的正则表达式
        # 这里假设LLM会以特定格式提供场景选项
        import re
        
        # 匹配情绪类型
        emotion_match = re.search(r'(焦虑|紧张|担心|压力|愤怒|悲伤|恐惧|快乐|兴奋)程度', llm_response)
        if not emotion_match:
            return
        
        emotion_type = emotion_match.group(1)
        
        # 匹配场景选项（假设格式为 A. 轻度：场景描述 B. 中度：场景描述 C. 重度：场景描述）
        scenario_patterns = [
            (3, r'A\.\s*轻度[^：]*：([^B]+)'),
            (6, r'B\.\s*中度[^：]*：([^C]+)'),
            (9, r'C\.\s*重度[^：]*：(.+)')
        ]
        
        scenarios = {}
        for intensity, pattern in scenario_patterns:
            match = re.search(pattern, llm_response, re.DOTALL)
            if match:
                scenarios[intensity] = match.group(1).strip()
        
        if scenarios:
            if "emotion_scenarios" not in self.active_sessions[session_id]:
                self.active_sessions[session_id]["emotion_scenarios"] = {}
            self.active_sessions[session_id]["emotion_scenarios"][emotion_type] = scenarios
            print(f"[缓存情绪场景] 情绪类型: {emotion_type}, 场景: {scenarios}")
    
    def _create_response(self, success: bool, message: str, **kwargs) -> Dict[str, Any]:
        """创建标准化的响应格式"""
        response = {
            "agent": self.agent_name,
            "success": success,
            "message": message,
            "timestamp": time.time()
        }
        response.update(kwargs)
        return response
    