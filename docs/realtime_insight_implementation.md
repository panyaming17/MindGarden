# 实时分析数据保存功能实现文档

## 概述

本功能实现了在对话过程中实时保存分析师智能体的分析字段到数据库，减少对 LLM 的依赖，加快会话结束时的报告生成速度。

## 核心设计思想

1. **实时保存**：在每次有价值对话触发分析师智能体时，实时保存分析字段
2. **增量聚合**：会话结束时聚合所有实时保存的分析数据
3. **降级处理**：如果实时数据不完整，使用 LLM 补充生成
4. **性能优化**：减少会话结束时的 LLM 调用，加快响应速度

## 数据库设计

### 新增表：`session_analysis_insights`

用于存储实时分析洞察数据：

```sql
CREATE TABLE session_analysis_insights (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    session_id VARCHAR(50) NOT NULL,
    user_id VARCHAR(50) NOT NULL,
    dialogue_id BIGINT,  -- 触发该洞察的对话 ID
    
    -- 认知分析字段
    common_automatic_thoughts JSON,  -- 常见自动思维列表
    thinking_traps JSON,  -- 思维陷阱列表
    core_beliefs JSON,  -- 核心信念列表
    cognitive_mappings JSON,  -- 认知映射关系
    
    -- 中医分析字段
    tcm_dominant_emotion VARCHAR(20),  -- 主导情志
    tcm_related_organs JSON,  -- 相关脏腑
    tcm_qi_dynamics VARCHAR(200),  -- 气机动态
    tcm_interpretation TEXT,  -- 中医解读
    
    -- 原因分析
    cbt_perspective TEXT,  -- CBT 视角分析
    tcm_perspective TEXT,  -- 中医视角分析
    
    -- 情绪趋势
    emotional_trend TEXT,  -- 情绪趋势总结
    
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    
    INDEX idx_session_insight (session_id, user_id),
    INDEX idx_dialogue_insight (dialogue_id)
);
```

## 实现细节

### 1. 数据模型 (database.py)

```python
class SessionAnalysisInsightDB(Base):
    """会话分析洞察表（用于实时保存分析师的分析字段）"""
    __tablename__ = "session_analysis_insights"
    
    # 字段定义...
```

### 2. 存储库方法 (record_repository_new.py)

#### save_analysis_insight()
保存实时分析洞察数据：
```python
def save_analysis_insight(self, user_id: str, session_id: str, 
                         insight_data: Dict[str, Any],
                         dialogue_id: Optional[int] = None) -> int
```

#### aggregate_session_insights()
聚合会话的所有分析洞察，生成汇总数据：
```python
def aggregate_session_insights(self, user_id: str, session_id: str) -> Dict[str, Any]
```

该方法会：
- 查询会话的所有洞察记录
- 合并所有自动思维、思维陷阱、核心信念（去重）
- 使用最新的中医分析数据
- 使用最新的原因分析数据
- 使用最新的情绪趋势

### 3. 分析师智能体 (analyst_agent.py)

#### _save_realtime_insight()
在每次 analyze_process 调用时实时保存基础分析数据：
```python
async def _save_realtime_insight(self, user_id: str, session_id: str, 
                                archive: Dict[str, Any], four_dim: Dict[str, Any],
                                dialogue_id: Optional[int] = None)
```

保存的数据包括：
- `common_automatic_thoughts`: 从档案中提取
- `thinking_traps`: 从档案中提取
- `core_beliefs`: 从档案中提取
- `emotional_trend`: 从档案的情绪时间线提取
- 其他字段暂时为空（可通过 LLM 补充）

#### _generate_complete_insight()
生成完整的分析洞察（包括认知映射和中医分析）：
```python
async def _generate_complete_insight(self, user_id: str, session_id: str,
                                    archive: Dict[str, Any], 
                                    dialogue_history: List[Dict[str, Any]]) -> Dict[str, Any]
```

该方法调用 LLM 生成：
- 认知映射关系（情景 -> 自动化思维 -> 情绪 -> 核心信念）
- 中医主导情志、相关脏腑、气机动态
- CBT 和中医视角的原因分析
- 情绪趋势总结

#### save_complete_insight()
公开方法，用于定期生成并保存完整洞察：
```python
async def save_complete_insight(self, user_id: str, session_id: str, 
                               dialogue_history: List[Dict[str, Any]])
```

### 4. 结束会话接口 (chat_endpoints.py)

修改后的 end_session 逻辑：

```python
# 步骤 1: 记录师生成记录报告
record_report = await recorder_agent.finalize_record_report(user_id, session_id)

# 步骤 2: 更新四维数据
four_dim_data = await analyst_agent.update_four_dim_data(user_id, session_id, dialogue_history)

# 步骤 3: 从实时分析数据生成分析报告
aggregated_insights = analyst_agent.repository.aggregate_session_insights(user_id, session_id)

if aggregated_insights:
    # 使用已保存的分析数据构建报告
    analysis_report = {
        "cognitive_analysis": {
            "mappings": aggregated_insights.get("cognitive_mappings", []),
            "common_automatic_thoughts": aggregated_insights.get("common_automatic_thoughts", []),
            ...
        },
        "tcm_analysis": aggregated_insights.get("tcm_analysis", {}),
        ...
    }
    
    # 如果实时数据不完整，使用 LLM 补充
    if not analysis_report["cognitive_analysis"]["mappings"] or \
       not analysis_report["tcm_analysis"]["dominant_emotion"]:
        analysis_report = await analyst_agent.generate_analysis_report_from_archive(...)
else:
    # 没有实时数据，使用 LLM 生成完整报告
    analysis_report = await analyst_agent.generate_analysis_report_from_archive(...)

# 步骤 4: 调理师生成调理报告
treatment_report = await therapist_agent.generate_treatment_report(user_id, session_id, analysis_report)
```

## 工作流程

### 对话过程中的实时保存

```
用户发送消息
    ↓
记录师智能体分析情绪（四维数据）
    ↓
判断是否有价值（is_valuable）
    ↓
如果有价值 → 触发分析师智能体
    ↓
分析师智能体：
    1. 更新用户档案（增量更新）
    2. 提取认知分析数据（自动思维、思维陷阱、核心信念）
    3. 实时保存到 session_analysis_insights 表
    4. 保存干预建议到 advices 表
    ↓
调理师智能体生成回复
```

### 会话结束时的报告生成

```
用户结束会话
    ↓
1. 记录师生成记录报告（同步）
    ↓
2. 更新四维数据（同步）
    ↓
3. 聚合实时分析洞察（从 session_analysis_insights）
    ↓
4. 检查数据完整性：
    - 如果完整：直接使用实时数据构建报告
    - 如果不完整：调用 LLM 补充缺失字段
    ↓
5. 调理师生成调理报告
    ↓
6. 保存完整报告到 session_reports 表
    ↓
返回响应（< 5 秒）
```

## 优势

1. **减少 LLM 依赖**：大部分分析数据已在对话过程中保存
2. **加快响应速度**：会话结束时无需等待 LLM 生成完整报告
3. **增量更新**：分析数据随对话进行不断丰富
4. **容错机制**：实时数据不完整时自动降级到 LLM 生成
5. **数据可追溯**：每条洞察关联到具体的对话 ID

## 使用场景

### 场景 1：短会话（< 10 条对话）
- 实时数据可能不够完整
- 会话结束时可能需要 LLM 补充
- 但仍比完全依赖 LLM 快

### 场景 2：中等会话（10-30 条对话）
- 实时数据相对完整
- 可能只需要 LLM 补充认知映射和中医分析
- 响应速度显著提升

### 场景 3：长会话（> 30 条对话）
- 实时数据非常完整
- 可能完全不需要 LLM 补充
- 响应速度最快（< 3 秒）

## 测试方法

运行测试脚本：
```bash
cd d:\GP\Projects
python test_realtime_insight.py
```

测试脚本会：
1. 登录用户账号
2. 创建新会话
3. 发送多条消息（触发实时保存）
4. 查询数据库中的实时分析洞察
5. 结束会话并检查报告是否使用了实时数据

## 后续优化方向

1. **定期完整洞察生成**：
   - 每 10 条对话调用一次 `save_complete_insight()`
   - 生成认知映射和中医分析

2. **智能降级策略**：
   - 根据实时数据完整度评分
   - 决定是否需要 LLM 补充

3. **缓存机制**：
   - 缓存聚合的洞察数据
   - 避免重复查询数据库

4. **异步生成**：
   - 完整洞察生成异步执行
   - 不影响对话响应速度

## 注意事项

1. **数据库迁移**：
   - 需要先运行数据库表创建脚本
   - 确保 `session_analysis_insights` 表存在

2. **性能考虑**：
   - 实时保存不应影响对话响应时间
   - 数据库查询应使用索引

3. **数据一致性**：
   - 实时数据与档案数据应保持一致
   - 定期校验数据完整性

## 相关文件

- `backend/core/database.py`: 数据模型定义
- `backend/repositories/record_repository_new.py`: 存储库方法
- `backend/agents/analyst_agent.py`: 分析师智能体逻辑
- `backend/api/v1/chat_endpoints.py`: 结束会话接口
- `test_realtime_insight.py`: 测试脚本
