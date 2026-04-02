# 数据库优化实施进度报告

**更新时间**: 2026-04-01  
**阶段**: Phase Zero & Phase One - 代码清理和表结构修改

## 已完成任务

### ✅ 1. 删除 SessionFourDimDataDB 类

**文件**: `backend/core/database.py`  
**操作**: 删除了 `SessionFourDimDataDB` 类定义（原 line 191-210）

**删除的代码**:
```python
class SessionFourDimDataDB(Base):
    """会话四维数据表（用于存储分析师的四维图表数据）"""
    __tablename__ = "session_four_dim_data"
    # ... (id, session_id, user_id, intensity_values, hedonic_values, tension_values, complexity_values)
```

### ✅ 2. 删除 SessionFourDimDataDB 引用

**文件**: `backend/agents/analyst_agent.py`  
**操作**: 删除了整个 `update_four_dim_data` 方法（line 683-831）

**删除的方法功能**:
- 从对话历史中提取四维数据
- 保存到 `session_four_dim_data` 表
- 使用 LLM 分析中医情志复杂度

### ✅ 3. 修改调用点

#### 3.1 chat_endpoints.py

**文件**: `backend/api/v1/chat_endpoints.py`

**修改内容**:
1. 添加辅助函数 `extract_four_dim_data_from_dialogues()`:
   - 从 dialogues 表的 four_dim 字段直接提取数据
   - 不需要额外的数据库查询
   - 返回格式与原有 API 兼容

2. 修改 end_session 流程:
   ```python
   # 旧代码
   four_dim_data = await analyst_agent.update_four_dim_data(user_id, session_id, dialogue_history)
   
   # 新代码
   four_dim_data = extract_four_dim_data_from_dialogues(dialogue_history)
   ```

#### 3.2 async_report_generator.py

**文件**: `backend/api/v1/async_report_generator.py`

**修改内容**:
```python
# 旧代码
four_dim_data = await analyst_agent.update_four_dim_data(user_id, session_id, dialogue_history)

# 新代码
four_dim_data = extract_four_dim_data_from_dialogues(dialogue_history)
```

### ✅ 4. 修改 session_analysis_insights 表结构

**文件**: `backend/core/database.py`

**新增字段**:

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `intensity_values` | JSON | 强度值数组 `[{"value": 6.5, "timestamp": "..."}, ...]` |
| `hedonic_counts` | JSON | 快感度计数 `{"负性": 3, "中性": 1, "正性": 1}` |
| `tension_counts` | JSON | 紧张度计数 `{"高": 1, "中": 1, "低": 3}` |
| `complexity_analysis` | JSON | 复杂度分析 `{"type": "复杂", "emotions": [...]}` |
| `is_completed` | Boolean | 是否已完成分析 |
| `is_migrated` | Boolean | 是否已迁移到 session_reports |

**设计说明**:
- 支持增量更新（每次对话追加/累加）
- 状态标记用于数据迁移和清理
- 与原有认知分析字段共存

### ✅ 5. 修改 record_repository_new.py

**文件**: `backend/repositories/record_repository_new.py`

**新增方法**:

#### 5.1 `update_four_dim_statistics()`
```python
def update_four_dim_statistics(self, user_id: str, session_id: str,
                               dialogue_id: Optional[int],
                               intensity_value: Optional[float],
                               hedonic_label: Optional[str],
                               tension_label: Optional[str]) -> None
```
**功能**: 增量更新四维数据统计
- 强度值：追加到数组
- 快感度：计数 +1
- 紧张度：计数 +1

#### 5.2 `update_complexity_analysis()`
```python
def update_complexity_analysis(self, user_id: str, session_id: str,
                               dialogue_id: int,
                               complexity_analysis: Dict[str, Any]) -> None
```
**功能**: 更新复杂度分析结果（每 2 轮对话调用一次 LLM）

#### 5.3 `mark_insight_completed()`
```python
def mark_insight_completed(self, user_id: str, session_id: str) -> None
```
**功能**: 标记会话分析为已完成

#### 5.4 `mark_insight_migrated()`
```python
def mark_insight_migrated(self, user_id: str, session_id: str) -> None
```
**功能**: 标记会话分析数据已迁移到 session_reports

#### 5.5 `get_session_insights()`
```python
def get_session_insights(self, user_id: str, session_id: str) -> Optional[Dict]
```
**功能**: 获取会话分析洞察（用于生成报告）

### ✅ 6. 修改 analyst_agent.py

**文件**: `backend/agents/analyst_agent.py`

**修改内容**:

#### 6.1 修改 `_save_realtime_insight()` 方法

**新增逻辑**:
1. 增量更新四维数据统计:
   ```python
   self.repository.update_four_dim_statistics(
       user_id=user_id,
       session_id=session_id,
       dialogue_id=dialogue_id,
       intensity_value=intensity,
       hedonic_label=hedonic,
       tension_label=tension
   )
   ```

2. 每 2 轮对话调用一次 LLM 分析复杂度:
   ```python
   user_dialogues_count = len([d for d in recent_dialogues if d.get("role") == "user"])
   if user_dialogues_count % 2 == 0:  # 每 2 轮对话
       await self._update_complexity_analysis(user_id, session_id, dialogue_id, recent_dialogues)
   ```

#### 6.2 新增 `_update_complexity_analysis()` 方法

**功能**:
- 提取所有用户对话内容
- 调用 LLM 分析中医七种情志占比
- 判断复杂度类型（情绪类型 >= 2 为"复杂"）
- 增量保存到 session_analysis_insights 表

**LLM Prompt**:
```
分析以下用户对话中的情绪，映射到中医七种情志（喜、怒、忧、思、悲、恐、惊），并计算各情志占比。

要求：
1. 识别对话中涉及的所有情志类型
2. 计算各情志的占比（总和为 1）
3. 如果只涉及一种情志，标记为"简单"；如果涉及多种，标记为"复杂"
```

## 数据流程

### 新的四维数据存储流程

```
用户对话
  ↓
记录师分析四维数据
  ↓
保存到 dialogues 表 (four_dim_* 字段)
  ↓
分析师每轮对话增量更新
  ↓
session_analysis_insights 表 (增量统计)
  ↓
结束会话时
  ↓
从 dialogues 提取四维数据 → 生成报告
  ↓
session_reports 表 (最终 JSON)
  ↓
标记 is_migrated = True
```

### 复杂度分析流程

```
第 2 轮对话 → LLM 分析 → 保存到 session_analysis_insights
第 4 轮对话 → LLM 分析 → 更新 session_analysis_insights
第 6 轮对话 → LLM 分析 → 更新 session_analysis_insights
...
结束会话 → 从 session_analysis_insights 读取 → 生成报告
```

## 待完成任务

### ⏳ Phase Two - 删除旧表

1. 创建数据库迁移脚本，删除 3 个表:
   - `session_four_dim_data`
   - `questionnaires`
   - `user_questionnaire_results`

### ⏳ Phase Three - 修改 end_session 逻辑

**文件**: `backend/api/v1/chat_endpoints.py`

**需求**:
- 保存对话后立即响应
- 响应消息：`"结束会话已完成，正在生成报告中"`
- 响应码：`200`
- 异步触发三个报告生成

### ⏳ Phase Four - 数据库迁移

1. 运行 Alembic 迁移脚本
2. 验证表结构
3. 数据迁移（如果需要）

### ⏳ Phase Five - 测试

1. 单元测试
2. 集成测试
3. 性能测试

### ⏳ Phase Six - 部署

1. 备份数据库
2. 应用迁移
3. 监控运行

## 代码清理总结

| 文件 | 删除内容 | 状态 |
|------|----------|------|
| `database.py` | `SessionFourDimDataDB` 类 | ✅ |
| `analyst_agent.py` | `update_four_dim_data` 方法 | ✅ |
| `chat_endpoints.py` | 调用 `update_four_dim_data` | ✅ (已替换) |
| `async_report_generator.py` | 调用 `update_four_dim_data` | ✅ (已替换) |

**旧表引用检查**:
- `session_four_dim_data`: 已清理 ✅
- `questionnaires`: 无引用 ✅
- `user_questionnaire_results`: 无引用 ✅

## 新增代码统计

| 文件 | 新增行数 | 说明 |
|------|----------|------|
| `database.py` | +14 | session_analysis_insights 新字段 |
| `record_repository_new.py` | +192 | 5 个增量更新方法 |
| `analyst_agent.py` | +96 | 复杂度分析逻辑 |
| `chat_endpoints.py` | +73 | 辅助函数 |

**总计**: +375 行新代码

## 下一步行动

1. **修改 end_session 接口** - 实现立即响应 + 异步报告生成
2. **创建数据库迁移脚本** - 删除旧表，应用新字段
3. **测试增量更新逻辑** - 验证每 2 轮对话的复杂度分析
4. **性能优化** - 确保异步任务不会阻塞主流程

---

**报告生成时间**: 2026-04-01  
**下一步**: 修改 end_session 接口逻辑
