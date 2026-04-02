# 数据库优化方案可行性分析

## 用户提出的两个想法

### 想法 1：链表结构关联
**描述**：`session_reports` 表与 `session_analysis_insights` 表通过链表结构关联

### 想法 2：中转站模式
**描述**：`session_analysis_insights` 作为数据合成中转站，完成后迁移到 `session_reports`

### 疑问：四维数据存储位置
**问题**：四维数据应该存在哪里？

---

## 想法 1 分析：链表结构关联

### 方案设计

```sql
-- session_reports 表
CREATE TABLE session_reports (
    id BIGINT PRIMARY KEY,
    session_id VARCHAR(50),
    user_id VARCHAR(50),
    
    -- 链表头指针：指向第一条洞察
    first_insight_id BIGINT,
    
    -- 链表尾指针：指向最后一条洞察
    last_insight_id BIGINT,
    
    -- 快照指针：指向最近的快照洞察
    snapshot_insight_id BIGINT,
    
    -- 报告 JSON（可选：作为缓存）
    analysis_report_json JSON,
    
    -- 状态
    analysis_status VARCHAR(20),
    created_at TIMESTAMP
);

-- session_analysis_insights 表（链表节点）
CREATE TABLE session_analysis_insights (
    id BIGINT PRIMARY KEY,
    session_id VARCHAR(50),
    user_id VARCHAR(50),
    dialogue_id BIGINT,
    
    -- 链表指针：指向前一条洞察
    prev_insight_id BIGINT,
    
    -- 是否为快照
    is_snapshot BOOLEAN DEFAULT FALSE,
    
    -- 增量数据
    is_incremental BOOLEAN DEFAULT TRUE,
    changed_fields JSON,
    
    -- 完整数据（如果是快照）
    common_automatic_thoughts JSON,
    thinking_traps JSON,
    core_beliefs JSON,
    cognitive_mappings JSON,
    tcm_dominant_emotion VARCHAR(20),
    tcm_related_organs JSON,
    tcm_qi_dynamics VARCHAR(200),
    tcm_interpretation TEXT,
    cbt_perspective TEXT,
    tcm_perspective TEXT,
    emotional_trend TEXT,
    
    -- 四维数据（如果是快照）
    four_dim_snapshot JSON,
    
    created_at TIMESTAMP,
    
    -- 索引
    INDEX idx_prev (prev_insight_id),
    INDEX idx_session (session_id)
);
```

### 数据流转

```
会话开始
    ↓
对话 1 → 洞察 1 (is_snapshot=TRUE, prev=NULL)
    ↓
对话 2 → 洞察 2 (is_snapshot=FALSE, prev=1, changed_fields={...})
    ↓
对话 3 → 洞察 3 (is_snapshot=FALSE, prev=2, changed_fields={...})
    ↓
...
    ↓
对话 10 → 洞察 10 (is_snapshot=TRUE, prev=3, 完整数据)
    ↓
结束会话
    ↓
session_reports:
    - first_insight_id = 1
    - last_insight_id = 10
    - snapshot_insight_id = 10
```

### 查询逻辑

```python
def get_analysis_report(session_id):
    """通过链表获取分析报告"""
    
    # 1. 获取报告记录
    report = db.query(SessionReportDB).filter_by(
        session_id=session_id
    ).first()
    
    # 2. 从最近的快照开始向前遍历
    snapshot = db.query(SessionAnalysisInsightDB).get(
        report.snapshot_insight_id
    )
    
    # 3. 加载快照数据
    merged = {
        "common_automatic_thoughts": set(snapshot.common_automatic_thoughts or []),
        "thinking_traps": set(snapshot.thinking_traps or []),
        "core_beliefs": set(snapshot.core_beliefs or []),
        "cognitive_mappings": snapshot.cognitive_mappings or [],
        "tcm_analysis": {
            "dominant_emotion": snapshot.tcm_dominant_emotion,
            "related_organs": snapshot.tcm_related_organs,
            "qi_dynamics": snapshot.tcm_qi_dynamics,
            "tcm_interpretation": snapshot.tcm_interpretation
        },
        "four_dim_snapshot": snapshot.four_dim_snapshot
    }
    
    # 4. 向后遍历增量记录（如果有）
    current_id = snapshot.id
    while True:
        next_insight = db.query(SessionAnalysisInsightDB).filter_by(
            prev_insight_id=current_id
        ).first()
        
        if not next_insight:
            break
        
        # 应用增量
        if next_insight.is_incremental:
            apply_changes(merged, next_insight.changed_fields)
        
        current_id = next_insight.id
    
    # 5. 构建报告
    analysis_report = {
        "four_dim_summary": merged["four_dim_snapshot"],
        "cognitive_analysis": {
            "mappings": merged["cognitive_mappings"],
            "common_automatic_thoughts": list(merged["common_automatic_thoughts"]),
            "thinking_traps": list(merged["thinking_traps"]),
            "core_beliefs": list(merged["core_beliefs"])
        },
        "tcm_analysis": merged["tcm_analysis"],
        "trends": merged.get("emotional_trend", "")
    }
    
    return analysis_report
```

### ✅ 可行性评估

| 维度 | 评分 | 说明 |
|------|------|------|
| **可行性** | ✅ 9/10 | 技术上完全可行 |
| **性能** | ✅ 8/10 | 查询效率高（从快照开始） |
| **空间效率** | ✅ 9/10 | 增量存储节省空间 |
| **复杂度** | ⚠️ 6/10 | 链表管理较复杂 |
| **维护成本** | ⚠️ 6/10 | 需要维护指针一致性 |

### 优势

1. ✅ **查询高效**：从快照开始，只需遍历少量增量
2. ✅ **空间节省**：增量存储，避免重复
3. ✅ **历史可追溯**：完整保留每次变化
4. ✅ **灵活**：支持多个快照

### 劣势

1. ⚠️ **链表维护复杂**：需要维护 prev_insight_id
2. ⚠️ **指针一致性**：删除中间节点需要更新指针
3. ⚠️ **事务复杂**：需要保证链表完整性

### 改进建议

**双向链表**（增加 next 指针）：
```sql
ALTER TABLE session_analysis_insights
ADD COLUMN next_insight_id BIGINT;  -- 指向下一条

-- 优势：可以向前和向后遍历
-- 劣势：维护更复杂
```

**推荐指数**：⭐⭐⭐⭐ (4/5)

---

## 想法 2 分析：中转站模式

### 方案设计

```sql
-- session_analysis_insights 表（中转站）
-- 临时存储，会话结束后清空

CREATE TABLE session_analysis_insights (
    id BIGINT PRIMARY KEY,
    session_id VARCHAR(50),
    user_id VARCHAR(50),
    dialogue_id BIGINT,
    
    -- 过程数据
    common_automatic_thoughts JSON,
    thinking_traps JSON,
    core_beliefs JSON,
    cognitive_mappings JSON,
    tcm_dominant_emotion VARCHAR(20),
    tcm_related_organs JSON,
    tcm_qi_dynamics VARCHAR(200),
    tcm_interpretation TEXT,
    cbt_perspective TEXT,
    tcm_perspective TEXT,
    emotional_trend TEXT,
    
    -- 四维数据
    four_dim_data JSON,
    
    -- 状态标记
    is_completed BOOLEAN DEFAULT FALSE,  -- 是否已完成合成
    migrated_to_report BOOLEAN DEFAULT FALSE,  -- 是否已迁移到 reports
    
    created_at TIMESTAMP,
    completed_at TIMESTAMP
);

-- session_reports 表（最终存储）
CREATE TABLE session_reports (
    id BIGINT PRIMARY KEY,
    session_id VARCHAR(50),
    user_id VARCHAR(50),
    
    -- 完整分析报告 JSON（最终版本）
    analysis_report_json JSON,
    
    -- 状态
    analysis_status VARCHAR(20) DEFAULT 'completed',
    completed_at TIMESTAMP,
    
    -- 其他报告
    record_report_json JSON,
    treatment_report_json JSON
);
```

### 数据流转

```
对话过程中：
对话 1 → 更新 insights (累积数据)
对话 2 → 更新 insights (累积数据)
对话 3 → 更新 insights (累积数据)
...
对话 N → 更新 insights (累积数据)

结束会话：
1. 从 insights 读取完整数据
2. 组装分析报告
3. 保存到 session_reports.analysis_report_json
4. 标记 insights.is_completed = TRUE
5. 标记 insights.migrated_to_report = TRUE

定期清理：
DELETE FROM session_analysis_insights
WHERE migrated_to_report = TRUE 
  AND completed_at < DATE_SUB(NOW(), INTERVAL 30 DAY);
```

### 实现逻辑

```python
# 对话过程中：累积更新
async def update_insight_during_dialogue(user_id, session_id, new_data):
    """对话过程中累积更新"""
    
    # 获取或创建洞察记录
    insight = db.query(SessionAnalysisInsightDB).filter_by(
        session_id=session_id
    ).first()
    
    if not insight:
        # 创建新记录
        insight = SessionAnalysisInsightDB(
            user_id=user_id,
            session_id=session_id,
            common_automatic_thoughts=[],
            thinking_traps=[],
            core_beliefs=[],
            cognitive_mappings=[],
            four_dim_data={}
        )
        db.add(insight)
    
    # 累积更新（合并数据）
    insight.common_automatic_thoughts = merge_lists(
        insight.common_automatic_thoughts,
        new_data.get("thoughts", [])
    )
    insight.thinking_traps = merge_lists(
        insight.thinking_traps,
        new_data.get("traps", [])
    )
    # ... 更新其他字段
    
    db.commit()

# 结束会话：迁移到 reports
def finalize_session_report(session_id):
    """结束会话，迁移数据到 reports"""
    
    # 1. 获取洞察数据
    insight = db.query(SessionAnalysisInsightDB).filter_by(
        session_id=session_id
    ).first()
    
    # 2. 组装分析报告
    analysis_report = {
        "four_dim_summary": insight.four_dim_data,
        "cognitive_analysis": {
            "mappings": insight.cognitive_mappings,
            "common_automatic_thoughts": insight.common_automatic_thoughts,
            "thinking_traps": insight.thinking_traps,
            "core_beliefs": insight.core_beliefs
        },
        "tcm_analysis": {
            "dominant_emotion": insight.tcm_dominant_emotion,
            "related_organs": insight.tcm_related_organs,
            "qi_dynamics": insight.tcm_qi_dynamics,
            "tcm_interpretation": insight.tcm_interpretation
        },
        "causes": {
            "cbt_perspective": insight.cbt_perspective,
            "tcm_perspective": insight.tcm_perspective
        },
        "trends": insight.emotional_trend
    }
    
    # 3. 获取或创建报告记录
    report = db.query(SessionReportDB).filter_by(
        session_id=session_id
    ).first()
    
    if not report:
        report = SessionReportDB(
            user_id=insight.user_id,
            session_id=session_id
        )
        db.add(report)
    
    # 4. 保存分析报告
    report.analysis_report_json = analysis_report
    report.analysis_status = "completed"
    report.completed_at = datetime.utcnow()
    
    # 5. 标记洞察记录
    insight.is_completed = True
    insight.migrated_to_report = True
    insight.completed_at = datetime.utcnow()
    
    db.commit()
    
    # 6. 定期清理（异步任务）
    schedule_cleanup_old_insights()
```

### ✅ 可行性评估

| 维度 | 评分 | 说明 |
|------|------|------|
| **可行性** | ✅ 10/10 | 技术上完全可行，简单直接 |
| **性能** | ✅ 9/10 | 查询极快（直接读 JSON） |
| **空间效率** | ⚠️ 6/10 | 有冗余（insights + reports） |
| **复杂度** | ✅ 9/10 | 逻辑简单清晰 |
| **维护成本** | ✅ 9/10 | 易于维护 |

### 优势

1. ✅ **简单直接**：逻辑清晰，易于理解
2. ✅ **查询性能最优**：直接读 JSON，无需 JOIN
3. ✅ **数据独立**：reports 不依赖 insights
4. ✅ **易于清理**：insights 可定期删除
5. ✅ **适合报告场景**：报告是最终版本，不需要历史追溯

### 劣势

1. ⚠️ **空间冗余**：数据在两个表都存储
2. ⚠️ **历史丢失**：清理 insights 后无法追溯过程
3. ⚠️ **同步风险**：需要保证 insights 和 reports 一致

### 空间优化方案

**方案 A：延迟清理**
```python
# 保留 30 天后再清理
def cleanup_old_insights():
    cutoff_date = datetime.utcnow() - timedelta(days=30)
    
    db.execute("""
        DELETE FROM session_analysis_insights
        WHERE migrated_to_report = TRUE
          AND completed_at < :cutoff
    """, {"cutoff": cutoff_date})
    
    db.commit()
```

**方案 B：压缩存储**
```python
# 迁移后压缩 insights
def compress_insight_after_migration(insight_id):
    insight = db.query(SessionAnalysisInsightDB).get(insight_id)
    
    # 只保留关键字段（删除冗余数据）
    compressed = {
        "summary": {
            "thought_count": len(insight.common_automatic_thoughts),
            "trap_count": len(insight.thinking_traps),
            "dominant_emotion": insight.tcm_dominant_emotion
        },
        "migrated_at": datetime.utcnow().isoformat()
    }
    
    # 清空详细数据
    insight.common_automatic_thoughts = None
    insight.thinking_traps = None
    insight.core_beliefs = None
    insight.cognitive_mappings = None
    insight.tcm_dominant_emotion = None
    # ... 清空其他字段
    
    # 保存压缩摘要
    insight.compressed_summary = compressed
    
    db.commit()
```

**推荐指数**：⭐⭐⭐⭐⭐ (5/5)

---

## 四维数据存储位置分析

### 方案对比

#### 方案 A：存在 session_reports（推荐）⭐⭐⭐⭐⭐

```json
// session_reports.analysis_report_json
{
  "four_dim_summary": {
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
    },
    "statistics": {
      "avg_intensity": 6.8,
      "max_intensity": 8.5,
      "min_intensity": 4.2,
      "trend": "上升"
    }
  },
  ...
}
```

**优势**：
- ✅ 报告完整性：报告包含所有必要数据
- ✅ 查询性能：一次查询获取全部数据
- ✅ 数据独立：不依赖其他表
- ✅ 适合归档：报告是最终版本

**劣势**：
- ⚠️ 与 dialogues 表有冗余（但报告需要聚合数据）

---

#### 方案 B：存在 session_analysis_insights

```json
// session_analysis_insights.four_dim_data
{
  "intensity_values": [...],
  "hedonic_distribution": {...},
  "tension_distribution": {...},
  "complexity_analysis": {...}
}
```

**优势**：
- ✅ 对话过程中实时更新
- ✅ 与认知分析数据在一起

**劣势**：
- ❌ 报告需要 JOIN 才能获取四维数据
- ❌ insights 清理后数据丢失
- ❌ 报告不完整

---

#### 方案 C：混合存储（最佳实践）⭐⭐⭐⭐

**核心思想**：
- **对话过程**：四维数据存在 `dialogues` 表（原始数据）
- **会话结束**：聚合到 `session_reports`（聚合数据）
- **不单独存储**：删除 `session_four_dim_data` 表

**数据流**：
```
对话 1: dialogues.four_dim_intensity = 6.5
对话 2: dialogues.four_dim_intensity = 7.2
对话 3: dialogues.four_dim_intensity = 6.8
...
结束会话:
  - 从 dialogues 聚合数据
  - 保存到 session_reports.analysis_report_json.four_dim_summary
  - 完成
```

**实现**：
```python
def aggregate_four_dim_data(session_id):
    """从 dialogues 聚合四维数据"""
    
    # 查询会话的所有对话
    dialogues = db.query(DialogueDB).filter_by(
        session_id=session_id
    ).order_by(DialogueDB.created_at).all()
    
    # 聚合
    intensity_values = []
    hedonic_stats = {"负性": 0, "中性": 0, "正性": 0}
    tension_stats = {"低": 0, "中": 0, "高": 0}
    
    for d in dialogues:
        if d.four_dim_intensity:
            intensity_values.append({
                "value": d.four_dim_intensity,
                "timestamp": d.created_at.isoformat()
            })
        
        if d.four_dim_hedonic:
            hedonic_stats[d.four_dim_hedonic] += 1
        
        if d.four_dim_tension:
            tension_stats[d.four_dim_tension] += 1
    
    # 构建四维总结
    four_dim_summary = {
        "intensity_values": intensity_values,
        "hedonic_distribution": hedonic_stats,
        "tension_distribution": tension_stats,
        "statistics": {
            "avg_intensity": sum(d.four_dim_intensity for d in dialogues if d.four_dim_intensity) / len([d for d in dialogues if d.four_dim_intensity]),
            "max_intensity": max(d.four_dim_intensity for d in dialogues if d.four_dim_intensity),
            "min_intensity": min(d.four_dim_intensity for d in dialogues if d.four_dim_intensity)
        }
    }
    
    return four_dim_summary
```

**推荐指数**：⭐⭐⭐⭐⭐ (5/5)

---

## 综合推荐方案

### 最佳组合

**采用想法 2（中转站模式） + 四维数据混合存储**

### 最终架构

```sql
-- 1. dialogues 表（原始四维数据）
CREATE TABLE dialogues (
    id BIGINT PRIMARY KEY,
    session_id VARCHAR(50),
    four_dim_intensity FLOAT,
    four_dim_hedonic VARCHAR(10),
    four_dim_tension VARCHAR(10),
    four_dim_complexity VARCHAR(10)
);

-- 2. session_analysis_insights 表（中转站）
CREATE TABLE session_analysis_insights (
    id BIGINT PRIMARY KEY,
    session_id VARCHAR(50),
    user_id VARCHAR(50),
    dialogue_id BIGINT,
    
    -- 过程数据（对话过程中累积）
    common_automatic_thoughts JSON,
    thinking_traps JSON,
    core_beliefs JSON,
    cognitive_mappings JSON,
    tcm_dominant_emotion VARCHAR(20),
    tcm_related_organs JSON,
    tcm_qi_dynamics VARCHAR(200),
    tcm_interpretation TEXT,
    cbt_perspective TEXT,
    tcm_perspective TEXT,
    emotional_trend TEXT,
    
    -- 状态
    is_completed BOOLEAN DEFAULT FALSE,
    migrated_to_report BOOLEAN DEFAULT FALSE,
    
    created_at TIMESTAMP
);

-- 3. session_reports 表（最终存储）
CREATE TABLE session_reports (
    id BIGINT PRIMARY KEY,
    session_id VARCHAR(50),
    user_id VARCHAR(50),
    
    -- 完整分析报告（包含四维数据）
    analysis_report_json JSON,  -- 包含 four_dim_summary
    
    -- 其他报告
    record_report_json JSON,
    treatment_report_json JSON,
    
    -- 状态
    analysis_status VARCHAR(20),
    completed_at TIMESTAMP
);
```

### 数据流转图

```
┌─────────────────────────────────────────────────────────┐
│                    对话过程中                            │
└─────────────────────────────────────────────────────────┘
                          ↓
    ┌────────────────────────────────────────┐
    │  dialogues 表                          │
    │  - 存储原始四维数据                     │
    │  - four_dim_intensity, hedonic...      │
    └────────────────────────────────────────┘
                          ↓
    ┌────────────────────────────────────────┐
    │  session_analysis_insights 表（中转站） │
    │  - 累积认知分析数据                     │
    │  - 累积中医分析数据                     │
    │  - 不存储四维数据（实时从 dialogues 读）  │
    └────────────────────────────────────────┘
                          ↓
    ┌────────────────────────────────────────┐
    │           结束会话触发                  │
    └────────────────────────────────────────┘
                          ↓
    ┌────────────────────────────────────────┐
    │  1. 从 dialogues 聚合四维数据            │
    │  2. 从 insights 读取认知分析数据         │
    │  3. 组装完整分析报告                     │
    └────────────────────────────────────────┘
                          ↓
    ┌────────────────────────────────────────┐
    │  session_reports 表（最终存储）         │
    │  - analysis_report_json                │
    │    ├─ four_dim_summary (聚合数据)       │
    │    ├─ cognitive_analysis (来自 insights)│
    │    ├─ tcm_analysis (来自 insights)      │
    │    └─ trends (来自 insights)            │
    └────────────────────────────────────────┘
                          ↓
    ┌────────────────────────────────────────┐
    │  标记 insights.migrated_to_report=TRUE  │
    │  定期清理 insights（30 天后）             │
    └────────────────────────────────────────┘
```

### 优势总结

1. ✅ **架构清晰**：中转站 + 最终存储，职责分明
2. ✅ **性能最优**：报告查询无需 JOIN
3. ✅ **空间节省**：清理 insights 后无冗余
4. ✅ **数据完整**：报告包含所有必要数据
5. ✅ **易于维护**：逻辑简单，易于理解

### 实施步骤

1. **删除** `session_four_dim_data` 表
2. **修改** `session_analysis_insights` 表（添加状态字段）
3. **修改** `session_reports` 表（保留 analysis_report_json）
4. **实现** 数据聚合和迁移逻辑
5. **实现** 定期清理任务

---

## 结论

### 想法 1（链表结构）
- **可行性**：✅ 可行
- **推荐度**：⭐⭐⭐⭐ (4/5)
- **适用场景**：需要完整历史追溯
- **不适用**：报告场景（不需要追溯每次变化）

### 想法 2（中转站模式）
- **可行性**：✅ 完全可行
- **推荐度**：⭐⭐⭐⭐⭐ (5/5)
- **适用场景**：报告生成场景
- **优势**：简单、高效、易维护

### 四维数据存储
- **推荐方案**：混合存储
- **原始数据**：`dialogues` 表
- **聚合数据**：`session_reports.analysis_report_json`
- **不单独存储**：删除 `session_four_dim_data` 表

### 最终建议
**采用想法 2（中转站模式）+ 四维数据混合存储方案**

---

**文档版本**：v1.0  
**创建日期**：2026-04-01  
**分析师**：系统架构师
