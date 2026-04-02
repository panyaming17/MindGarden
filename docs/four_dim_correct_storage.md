# 四维数据正确存储方案分析

## 四维数据的组成结构

根据您的说明，四维数据应该包含：

```json
{
  "intensity_values": [
    {"value": 6.5, "timestamp": "2026-04-01T10:00:00Z"},
    {"value": 7.2, "timestamp": "2026-04-01T10:05:00Z"}
  ],
  "hedonic_distribution": {"负性": 8, "中性": 2, "正性": 0},
  "tension_distribution": {"高": 5, "中": 4, "低": 1},
  "complexity_analysis": {
    "type": "复杂",
    "emotions": [
      {"emotion": "忧", "value": 0.6},
      {"emotion": "思", "value": 0.4}
    ]
  }
}
```

---

## 问题 1：statistics 字段的含义

### 我之前误解的 statistics

```json
// ❌ 我理解的 statistics（不需要）
{
  "avg_intensity": 6.8,  // 平均强度
  "max_intensity": 8.5,  // 最大强度
  "min_intensity": 4.2   // 最小强度
}
```

### 您实际需要的"统计"

```json
// ✅ 您需要的统计（计数）
{
  "hedonic_distribution": {"负性": 8, "中性": 2, "正性": 0},  // ← 这就是统计
  "tension_distribution": {"高": 5, "中": 4, "低": 1}         // ← 这就是统计
}
```

**结论**：
- ✅ `hedonic_distribution` 和 `tension_distribution` **就是统计字段**
- ✅ 需要存储（计数结果）
- ❌ 强度**不需要**统计，只存储原始数组

---

## 问题 2：四维数据的正确存储方案

### 四类数据的存储策略

| 数据类型 | 存储内容 | 是否统计 | 存储方式 |
|---------|---------|---------|---------|
| **强度** | 时间 + 数值数组 | ❌ 不统计 | 存储完整数组 |
| **快感度** | 三个特性的数量 | ✅ 统计 | 存储计数结果 |
| **紧张度** | 三个特性的数量 | ✅ 统计 | 存储计数结果 |
| **复杂度** | LLM 分析结果 | ✅ 分析 | 存储 LLM 分析 JSON |

---

### 详细存储方案

#### 1. 强度（Intensity）- 存储原始数组

```json
"intensity_values": [
  {"value": 6.5, "timestamp": "2026-04-01T10:00:00Z"},
  {"value": 7.2, "timestamp": "2026-04-01T10:05:00Z"},
  {"value": 6.8, "timestamp": "2026-04-01T10:10:00Z"},
  {"value": 8.0, "timestamp": "2026-04-01T10:15:00Z"}
]
```

**特点**：
- ✅ 存储完整时间序列
- ✅ 不计算平均值、最大最小值
- ✅ 前端可以自己决定如何展示

**dialogues 表存储**：
```python
# 每条对话保存原始值
four_dim_intensity = 6.5  # Float 值
```

**聚合后存储**：
```python
# session_reports 中
intensity_values = [
    {"value": d.four_dim_intensity, "timestamp": d.created_at.isoformat()}
    for d in dialogues if d.four_dim_intensity
]
```

---

#### 2. 快感度（Hedonic）- 存储统计计数

```json
"hedonic_distribution": {
  "负性": 8,
  "中性": 2,
  "正性": 0
}
```

**特点**：
- ✅ 存储计数结果（不是原始数组）
- ✅ 每次对话后更新计数
- ✅ 增量累加

**dialogues 表存储**：
```python
# 每条对话保存原始值
four_dim_hedonic = "负性"  # String: "负性"、"中性"、"正性"
```

**聚合后存储**：
```python
# 统计计数
hedonic_counts = {"负性": 0, "中性": 0, "正性": 0}
for d in dialogues:
    if d.four_dim_hedonic:
        hedonic_counts[d.four_dim_hedonic] += 1

# 存储结果
hedonic_distribution = hedonic_counts
```

---

#### 3. 紧张度（Tension）- 存储统计计数

```json
"tension_distribution": {
  "高": 5,
  "中": 4,
  "低": 1
}
```

**特点**：
- ✅ 存储计数结果（不是原始数组）
- ✅ 每次对话后更新计数
- ✅ 增量累加

**dialogues 表存储**：
```python
# 每条对话保存原始值
four_dim_tension = "高"  # String: "低"、"中"、"高"
```

**聚合后存储**：
```python
# 统计计数
tension_counts = {"低": 0, "中": 0, "高": 0}
for d in dialogues:
    if d.four_dim_tension:
        tension_counts[d.four_dim_tension] += 1

# 存储结果
tension_distribution = tension_counts
```

---

#### 4. 复杂度（Complexity）- LLM 分析结果

```json
"complexity_analysis": {
  "type": "复杂",  // 或 "简单"
  "emotions": [     // 复杂时才有
    {"emotion": "忧", "value": 0.6},
    {"emotion": "思", "value": 0.4}
  ],
  "analysis": "用户情绪呈现复杂特征，主要表现为忧思交织...",
  "llm_version": "2026-04-01"  // LLM 分析版本
}
```

**特点**：
- ✅ LLM 分析结果（不是简单计数）
- ✅ 需要增量分析（每次对话后重新分析）
- ✅ 可能随对话深入而变化

**存储策略**：
```python
# 方案 A：每次对话后 LLM 实时分析（推荐）
async def analyze_complexity(dialogue_history):
    """LLM 分析复杂度"""
    prompt = f"""基于以下对话，分析用户情绪的复杂度：
    {dialogue_history}
    
    请返回：
    1. type: "简单" 或 "复杂"
    2. 如果是复杂，列出主要情绪及其占比
    3. 分析说明
    """
    
    result = await llm_service.chat_completion(...)
    return {
        "type": result["type"],
        "emotions": result.get("emotions", []),
        "analysis": result.get("analysis", "")
    }

# 方案 B：只在会话结束时分析
def finalize_complexity_analysis(session_id):
    """会话结束时分析复杂度"""
    dialogues = get_all_dialogues(session_id)
    dialogue_history = "\n".join([d.content for d in dialogues])
    
    complexity = analyze_complexity(dialogue_history)
    return complexity
```

---

## 问题 3：复杂度的增量分析保存

### 您的需求

> 复杂度分析是分析师 LLM 分析的，也需要增量分析保存

### 实现方案

#### 方案 A：每次对话后增量分析（推荐）⭐

**数据流**：
```
对话 1 → LLM 分析 → complexity_v1
对话 2 → LLM 分析 → complexity_v2（基于对话 1+2）
对话 3 → LLM 分析 → complexity_v3（基于对话 1+2+3）
...
```

**存储结构**：
```python
class SessionAnalysisInsightDB(Base):
    # 复杂度分析（每次增量更新）
    complexity_analysis = Column(JSON, nullable=True)
    complexity_version = Column(Integer, default=1)
    last_complexity_update = Column(TIMESTAMP)
```

**实现逻辑**：
```python
async def update_complexity_analysis(user_id, session_id, new_dialogue):
    """增量更新复杂度分析"""
    
    # 获取历史洞察
    insight = get_or_create_insight(session_id)
    
    # 获取所有对话历史
    dialogues = db.query(DialogueDB).filter_by(
        session_id=session_id
    ).order_by(DialogueDB.created_at).all()
    
    # 构建对话文本
    dialogue_history = "\n".join([
        f"{d.role}: {d.content}" 
        for d in dialogues
    ])
    
    # LLM 分析复杂度
    complexity = await analyze_complexity_llm(dialogue_history)
    
    # 更新洞察
    insight.complexity_analysis = complexity
    insight.complexity_version += 1
    insight.last_complexity_update = datetime.utcnow()
    
    db.commit()
```

**优点**：
- ✅ 实时反映情绪复杂度变化
- ✅ 可以看到复杂度演变过程
- ✅ 会话结束时无需重新分析

**缺点**：
- ⚠️ LLM 调用频繁（每次对话都调用）
- ⚠️ API 成本较高

---

#### 方案 B：定期增量分析（折中）⭐⭐⭐

**数据流**：
```
对话 1-5  → 使用初始分析
对话 6    → LLM 分析 → complexity_v1
对话 7-10 → 使用 v1
对话 11   → LLM 分析 → complexity_v2
...
```

**实现逻辑**：
```python
async def update_complexity_analysis_periodic(user_id, session_id, dialogue_count):
    """定期增量更新复杂度分析"""
    
    # 每 5 条对话分析一次
    if dialogue_count % 5 == 0:
        # 获取所有对话
        dialogues = get_all_dialogues(session_id)
        dialogue_history = build_dialogue_text(dialogues)
        
        # LLM 分析
        complexity = await analyze_complexity_llm(dialogue_history)
        
        # 保存
        insight = get_insight(session_id)
        insight.complexity_analysis = complexity
        insight.complexity_version += 1
        db.commit()
```

**优点**：
- ✅ 减少 LLM 调用次数
- ✅ 降低成本
- ✅ 仍然有增量更新

**缺点**：
- ⚠️ 两次分析之间可能错过重要变化

---

#### 方案 C：只在会话结束时分析（简化）⭐⭐

**数据流**：
```
对话 1, 2, 3, ... N
    ↓
结束会话
    ↓
LLM 分析完整对话历史 → complexity_final
```

**实现逻辑**：
```python
def finalize_complexity_analysis(session_id):
    """会话结束时分析复杂度"""
    
    # 获取所有对话
    dialogues = db.query(DialogueDB).filter_by(
        session_id=session_id
    ).order_by(DialogueDB.created_at).all()
    
    # 构建完整对话历史
    dialogue_history = "\n".join([
        f"{d.role}: {d.content}" 
        for d in dialogues
    ])
    
    # LLM 分析
    complexity = analyze_complexity_llm(dialogue_history)
    
    return complexity
```

**优点**：
- ✅ 只需调用一次 LLM
- ✅ 成本最低
- ✅ 基于完整对话历史

**缺点**：
- ❌ 无法看到复杂度变化过程
- ❌ 对话过程中无法获取复杂度分析

---

#### 方案 D：混合策略（最佳实践）⭐⭐⭐⭐⭐

**核心思想**：
- 对话过程中：简单规则判断（不调用 LLM）
- 会话结束时：LLM 深度分析

**实现逻辑**：
```python
# 对话过程中：使用简单规则
def update_complexity_simple(new_dialogue):
    """简单规则判断复杂度"""
    
    # 规则 1：检查情绪关键词数量
    emotion_keywords = count_emotion_keywords(new_dialogue.content)
    
    if emotion_keywords >= 3:
        return {
            "type": "复杂",
            "reason": "检测到多种情绪关键词",
            "is_llm_analysis": False
        }
    else:
        return {
            "type": "简单",
            "reason": "情绪表达单一",
            "is_llm_analysis": False
        }

# 会话结束时：LLM 深度分析
def finalize_complexity_llm(session_id):
    """LLM 深度分析"""
    
    dialogues = get_all_dialogues(session_id)
    dialogue_history = build_dialogue_text(dialogues)
    
    complexity = analyze_complexity_llm(dialogue_history)
    complexity["is_llm_analysis"] = True
    
    return complexity
```

**存储**：
```python
# session_analysis_insights 表
complexity_analysis = Column(JSON)
# 包含：
# {
#   "type": "复杂",
#   "emotions": [...],
#   "analysis": "...",
#   "is_llm_analysis": True/False
# }
```

**优点**：
- ✅ 对话过程中有实时反馈
- ✅ 会话结束有深度分析
- ✅ 成本可控

---

## 完整的四维数据存储架构

### dialogues 表（原始数据）

```python
class DialogueDB(Base):
    # 四维原始数据
    four_dim_intensity = Column(Float)        # 强度值：6.5
    four_dim_hedonic = Column(String(10))     # 快感度："负性"
    four_dim_tension = Column(String(10))     # 紧张度："高"
    four_dim_complexity = Column(String(10))  # 复杂度："简单"（可选）
```

### session_analysis_insights 表（中转站 - 增量更新）

```python
class SessionAnalysisInsightDB(Base):
    # 四维数据统计（增量更新）
    intensity_values = Column(JSON)           # [{"value": 6.5, "timestamp": "..."}]
    hedonic_distribution = Column(JSON)       # {"负性": 8, "中性": 2, "正性": 0}
    tension_distribution = Column(JSON)       # {"高": 5, "中": 4, "低": 1}
    complexity_analysis = Column(JSON)        # LLM 分析结果
    
    # 复杂度版本追踪
    complexity_version = Column(Integer, default=1)
    last_complexity_update = Column(TIMESTAMP)
```

### session_reports 表（最终存储）

```python
# session_reports.analysis_report_json
{
  "four_dim_summary": {
    "intensity_values": [
      {"value": 6.5, "timestamp": "2026-04-01T10:00:00Z"},
      {"value": 7.2, "timestamp": "2026-04-01T10:05:00Z"}
      // ... 完整数组（不统计）
    ],
    
    "hedonic_distribution": {
      "负性": 8,
      "中性": 2,
      "正性": 0
    },  // ← 统计计数
    
    "tension_distribution": {
      "高": 5,
      "中": 4,
      "低": 1
    },  // ← 统计计数
    
    "complexity_analysis": {
      "type": "复杂",
      "emotions": [
        {"emotion": "忧", "value": 0.6},
        {"emotion": "思", "value": 0.4}
      ],
      "analysis": "用户情绪呈现复杂特征...",
      "is_llm_analysis": True
    }  // ← LLM 分析结果
  }
}
```

---

## 数据流转完整示例

### 对话过程中的增量更新

```python
# 对话 1
dialogue_1 = {
    "content": "我很焦虑",
    "four_dim": {
        "intensity": 7.5,
        "hedonic": "负性",
        "tension": "高",
        "complexity": "简单"
    }
}

# 保存到 dialogues 表
save_to_dialogues(dialogue_1)

# 更新 insights（增量）
insight = get_or_create_insight(session_id)

# 1. 强度：追加到数组
insight.intensity_values.append({
    "value": 7.5,
    "timestamp": datetime.utcnow().isoformat()
})

# 2. 快感度：计数 +1
insight.hedonic_distribution["负性"] += 1  # {"负性": 1, "中性": 0, "正性": 0}

# 3. 紧张度：计数 +1
insight.tension_distribution["高"] += 1  # {"高": 1, "中": 0, "低": 0}

# 4. 复杂度：简单规则判断
insight.complexity_analysis = {
    "type": "简单",
    "reason": "单一情绪表达",
    "is_llm_analysis": False
}

db.commit()
```

```python
# 对话 2
dialogue_2 = {
    "content": "但又有点期待",
    "four_dim": {
        "intensity": 6.0,
        "hedonic": "中性",
        "tension": "中",
        "complexity": "简单"
    }
}

# 保存到 dialogues 表
save_to_dialogues(dialogue_2)

# 更新 insights（增量）
insight = get_insight(session_id)

# 1. 强度：追加到数组
insight.intensity_values.append({
    "value": 6.0,
    "timestamp": datetime.utcnow().isoformat()
})

# 2. 快感度：计数 +1
insight.hedonic_distribution["中性"] += 1  # {"负性": 1, "中性": 1, "正性": 0}

# 3. 紧张度：计数 +1
insight.tension_distribution["中"] += 1  # {"高": 1, "中": 1, "低": 0}

# 4. 复杂度：检测到两种情绪，调用 LLM 分析
if dialogue_count % 5 == 0:  # 每 5 条对话调用一次 LLM
    insight.complexity_analysis = await analyze_complexity_llm(...)
    insight.complexity_version += 1

db.commit()
```

### 会话结束时的数据迁移

```python
def finalize_session_report(session_id):
    """结束会话，迁移数据到 reports"""
    
    # 1. 从 insights 读取数据
    insight = get_insight(session_id)
    
    # 2. 构建四维总结
    four_dim_summary = {
        "intensity_values": insight.intensity_values,  # 完整数组
        "hedonic_distribution": insight.hedonic_distribution,  # 计数
        "tension_distribution": insight.tension_distribution,  # 计数
        "complexity_analysis": insight.complexity_analysis  # LLM 分析
    }
    
    # 3. 保存到 reports
    report = get_or_create_report(session_id)
    report.analysis_report_json["four_dim_summary"] = four_dim_summary
    report.analysis_status = "completed"
    
    # 4. 标记 insights
    insight.is_completed = True
    insight.migrated_to_report = True
    
    db.commit()
```

---

## 总结

### 四维数据的正确理解

| 维度 | 存储内容 | 是否统计 | 说明 |
|------|---------|---------|------|
| **强度** | 时间 + 数值数组 | ❌ 不统计 | 完整时间序列 |
| **快感度** | 三个特性的数量 | ✅ 统计 | 计数：负性/中性/正性 |
| **紧张度** | 三个特性的数量 | ✅ 统计 | 计数：低/中/高 |
| **复杂度** | LLM 分析结果 | ✅ 分析 | 类型 + 情绪占比 + 分析说明 |

### 存储策略

1. **dialogues 表**：存储原始值（每条对话）
2. **session_analysis_insights 表**：增量更新（中转站）
3. **session_reports 表**：完整存储（最终版本）

### 复杂度增量分析

**推荐方案 D（混合策略）**：
- 对话过程中：简单规则判断
- 每 5 条对话：LLM 分析一次
- 会话结束：LLM 最终分析

---

**文档版本**：v1.0  
**创建日期**：2026-04-01  
**分析师**：系统架构师
