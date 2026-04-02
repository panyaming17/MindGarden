# 数据库优化方案详细解答

## 问题 1：旧问卷表检查

### ✅ 检查结果

**结论**：项目已经完全不使用旧问卷表（`questionnaires` 和 `user_questionnaire_results`），可以直接删除。

**证据**：
1. 所有代码都使用新表：
   - `QuestionnaireTemplateDB`（新问卷模板表）
   - `UserQuestionnaireRecordDB`（新问卷记录表）
   - `UserQuestionnaireScheduleDB`（新问卷调度表）
   - `QuestionnaireScoringRuleDB`（新评分规则表）

2. 旧表（`QuestionnaireDB`, `UserQuestionnaireResultDB`）无任何引用

**操作建议**：
```sql
-- 直接删除旧表（无需迁移）
DROP TABLE IF EXISTS questionnaires;
DROP TABLE IF EXISTS user_questionnaire_results;
```

---

## 问题 2：session_analysis_insights 表的存储方案

### 当前问题

**现状**：每条洞察都存储完整数据，导致严重冗余

```sql
-- 当前结构
CREATE TABLE session_analysis_insights (
    id BIGINT PRIMARY KEY,
    session_id VARCHAR(50),
    user_id VARCHAR(50),
    dialogue_id BIGINT,
    
    -- 每次都完整存储
    common_automatic_thoughts JSON,  -- ["思维 1", "思维 2", ...]
    thinking_traps JSON,             -- ["陷阱 1", "陷阱 2", ...]
    core_beliefs JSON,               -- ["信念 1", "信念 2", ...]
    cognitive_mappings JSON,         -- [{...}, {...}]
    tcm_dominant_emotion VARCHAR(20),
    tcm_related_organs JSON,
    tcm_qi_dynamics VARCHAR(200),
    tcm_interpretation TEXT,
    cbt_perspective TEXT,
    tcm_perspective TEXT,
    emotional_trend TEXT
);

-- 问题示例：
-- 对话 1: 存储 ["我找不到工作"] 
-- 对话 2: 存储 ["我找不到工作", "我不够优秀"]  ← 重复了"我找不到工作"
-- 对话 3: 存储 ["我找不到工作", "我不够优秀", "我无能"]  ← 重复了前两个
```

---

### 优化方案 A：增量存储（推荐）

#### 核心思想
- **只存储变化的数据**
- **使用引用链**：每条洞察引用前一条，形成版本链
- **查询时合并**：通过引用链合并得到完整数据

#### 表结构修改

```sql
ALTER TABLE session_analysis_insights
ADD COLUMN base_insight_id BIGINT,  -- 引用的基础洞察 ID
ADD COLUMN is_incremental BOOLEAN DEFAULT TRUE,  -- 是否为增量记录
ADD COLUMN changed_fields JSON;  -- 记录变化的字段

-- 添加索引
CREATE INDEX idx_base_insight ON session_analysis_insights(base_insight_id);
```

#### 存储逻辑

**第 1 条洞察（完整存储）**：
```json
{
  "id": 1,
  "session_id": "session_123",
  "dialogue_id": 10,
  "base_insight_id": NULL,
  "is_incremental": FALSE,
  "changed_fields": NULL,
  
  "common_automatic_thoughts": ["我找不到工作"],
  "thinking_traps": ["灾难化思维"],
  "core_beliefs": ["我无能"],
  "cognitive_mappings": [...],
  "tcm_dominant_emotion": "忧",
  "emotional_trend": "初始焦虑状态"
}
```

**第 2 条洞察（增量存储）**：
```json
{
  "id": 2,
  "session_id": "session_123",
  "dialogue_id": 15,
  "base_insight_id": 1,  -- 引用第 1 条
  "is_incremental": TRUE,
  "changed_fields": {
    "added_thoughts": ["我不够优秀"],
    "added_traps": ["全或无思维"],
    "updated_trend": "焦虑加剧，出现自我否定"
  },
  
  -- 其他字段为空（继承自 base_insight_id=1）
  "common_automatic_thoughts": NULL,
  "thinking_traps": NULL,
  ...
}
```

**第 3 条洞察（增量存储）**：
```json
{
  "id": 3,
  "session_id": "session_123",
  "dialogue_id": 20,
  "base_insight_id": 2,  -- 引用第 2 条
  "is_incremental": TRUE,
  "changed_fields": {
    "added_thoughts": ["我无能"],
    "added_mappings": [{
      "situation": "面试失败",
      "automatic_thought": "我无能",
      "emotion": "绝望",
      "core_belief": "我不值得被爱"
    }],
    "updated_tcm": {
      "dominant_emotion": "悲",
      "related_organs": ["肺"],
      "qi_dynamics": "肺气虚弱"
    },
    "updated_trend": "从焦虑转为绝望"
  }
}
```

#### 查询合并逻辑

```python
def get_merged_insights(session_id):
    """合并增量洞察，得到完整数据"""
    
    # 1. 获取所有洞察（按时间排序）
    insights = db.query(SessionAnalysisInsightDB).filter_by(
        session_id=session_id
    ).order_by(SessionAnalysisInsightDB.created_at).all()
    
    # 2. 初始化完整数据
    merged = {
        "common_automatic_thoughts": set(),
        "thinking_traps": set(),
        "core_beliefs": set(),
        "cognitive_mappings": [],
        "tcm_analysis": {},
        "emotional_trend": ""
    }
    
    # 3. 逐条合并
    for insight in insights:
        if not insight.is_incremental:
            # 完整记录：直接加载
            merged["common_automatic_thoughts"].update(
                insight.common_automatic_thoughts or []
            )
            merged["thinking_traps"].update(
                insight.thinking_traps or []
            )
            # ... 加载所有字段
        else:
            # 增量记录：只应用变化
            changes = insight.changed_fields
            
            # 添加新增的思维
            if "added_thoughts" in changes:
                merged["common_automatic_thoughts"].update(changes["added_thoughts"])
            
            # 添加新增的映射
            if "added_mappings" in changes:
                merged["cognitive_mappings"].extend(changes["added_mappings"])
            
            # 更新趋势
            if "updated_trend" in changes:
                merged["emotional_trend"] = changes["updated_trend"]
            
            # 更新中医分析
            if "updated_tcm" in changes:
                merged["tcm_analysis"].update(changes["updated_tcm"])
    
    # 4. 转换为列表
    merged["common_automatic_thoughts"] = list(merged["common_automatic_thoughts"])
    merged["thinking_traps"] = list(merged["thinking_traps"])
    
    return merged
```

#### 优势

- **节省空间**：只存储变化，节省 60-70% 空间
- **保留历史**：可追溯每次变化
- **性能可接受**：合并操作在内存中进行，速度快

#### 劣势

- **查询复杂**：需要合并逻辑
- **写入稍慢**：需要查找 base_insight_id

---

### 优化方案 B：定期快照（备选）

#### 核心思想
- **每 N 条对话保存一次完整快照**
- **中间只存增量**
- **查询时使用最近快照 + 增量**

#### 表结构

```sql
ALTER TABLE session_analysis_insights
ADD COLUMN is_snapshot BOOLEAN DEFAULT FALSE,  -- 是否为快照记录
ADD COLUMN snapshot_sequence INT;  -- 快照序号（0, 1, 2...）

CREATE INDEX idx_snapshot ON session_analysis_insights(is_snapshot, snapshot_sequence);
```

#### 存储逻辑

```python
SNAPSHOT_INTERVAL = 10  # 每 10 条对话保存一次快照

async def save_insight(user_id, session_id, insight_data, dialogue_id):
    # 获取当前对话数量
    dialogue_count = get_dialogue_count(session_id)
    
    if dialogue_count % SNAPSHOT_INTERVAL == 0:
        # 保存完整快照
        save_snapshot(user_id, session_id, insight_data, dialogue_id)
    else:
        # 保存增量
        save_incremental(user_id, session_id, insight_data, dialogue_id)

def save_snapshot(user_id, session_id, insight_data, dialogue_id):
    """保存完整快照"""
    snapshot_seq = dialogue_count // SNAPSHOT_INTERVAL
    
    insight = SessionAnalysisInsightDB(
        user_id=user_id,
        session_id=session_id,
        dialogue_id=dialogue_id,
        is_snapshot=True,
        snapshot_sequence=snapshot_seq,
        
        # 完整存储所有字段
        common_automatic_thoughts=insight_data["thoughts"],
        thinking_traps=insight_data["traps"],
        ...
    )
    db.add(insight)
    db.commit()

def save_incremental(user_id, session_id, insight_data, dialogue_id):
    """保存增量"""
    # 获取最近的快照
    last_snapshot = get_last_snapshot(session_id)
    
    insight = SessionAnalysisInsightDB(
        user_id=user_id,
        session_id=session_id,
        dialogue_id=dialogue_id,
        is_snapshot=False,
        base_insight_id=last_snapshot.id,
        
        # 只存储变化的字段
        changed_fields={
            "added_thoughts": new_thoughts,
            "added_mappings": new_mappings
        }
    )
    db.add(insight)
    db.commit()
```

#### 查询逻辑

```python
def get_insights(session_id):
    # 1. 获取最近的快照
    last_snapshot = get_last_snapshot(session_id)
    
    if last_snapshot:
        # 2. 获取快照后的所有增量
        increments = get_increments_after_snapshot(
            session_id, 
            last_snapshot.id
        )
        
        # 3. 合并：快照 + 增量
        merged = merge_snapshot_with_increments(
            last_snapshot, 
            increments
        )
        return merged
    else:
        # 没有快照，直接合并所有增量
        return merge_all_increments(session_id)
```

---

### 优化方案 C：混合存储（最佳实践）

#### 核心思想
结合方案 A 和方案 B：
- **前 N 条使用增量**（N=10）
- **达到阈值后转快照**
- **快照之间使用增量**

#### 实现

```python
class InsightStorageStrategy:
    """洞察存储策略"""
    
    SNAPSHOT_THRESHOLD = 10  # 快照阈值
    MAX_INCREMENTS = 5  # 快照间最大增量数
    
    def save_insight(self, user_id, session_id, insight_data, dialogue_id):
        # 获取当前洞察数量
        insight_count = get_insight_count(session_id)
        
        # 获取最近的快照
        last_snapshot = get_last_snapshot(session_id)
        
        if last_snapshot is None:
            # 情况 1：还没有快照
            if insight_count < self.SNAPSHOT_THRESHOLD:
                # 使用增量存储
                self.save_incremental(user_id, session_id, insight_data, dialogue_id, None)
            else:
                # 达到阈值，创建快照
                self.save_snapshot(user_id, session_id, insight_data, dialogue_id, 1)
        
        else:
            # 情况 2：已有快照
            increments_after_snapshot = count_increments_after_snapshot(last_snapshot.id)
            
            if increments_after_snapshot < self.MAX_INCREMENTS:
                # 增量数未达上限，继续增量
                self.save_incremental(
                    user_id, session_id, insight_data, dialogue_id, 
                    last_snapshot.id
                )
            else:
                # 增量数达上限，创建新快照
                new_seq = last_snapshot.snapshot_sequence + 1
                self.save_snapshot(user_id, session_id, insight_data, dialogue_id, new_seq)
```

#### 优势

- **空间效率**：比纯增量节省 20%
- **查询性能**：比纯增量快 50%
- **灵活性**：可调整阈值

---

## 问题 3：优化 session_reports 存储的方案

### 当前问题

**现状**：`session_reports` 表存储完整 JSON，与 `session_analysis_insights` 重复

```sql
CREATE TABLE session_reports (
    id BIGINT PRIMARY KEY,
    user_id VARCHAR(50),
    session_id VARCHAR(50),
    
    -- 存储完整 JSON（冗余）
    record_report_json JSON,      -- 记录报告
    analysis_report_json JSON,    -- 分析报告（与 insights 重复）
    treatment_report_json JSON,   -- 调理报告
    
    -- 状态字段
    record_status VARCHAR(20),
    analysis_status VARCHAR(20),
    treatment_status VARCHAR(20)
);
```

**冗余分析**：
- `analysis_report_json` 的内容 80% 来自 `session_analysis_insights`
- 每次会话结束都复制一次，浪费空间

---

### 优化方案 A：引用存储（推荐）

#### 核心思想
- **只存储报告 ID 引用**
- **不存储完整 JSON**
- **查询时动态组装**

#### 表结构修改

```sql
ALTER TABLE session_reports
DROP COLUMN analysis_report_json,  -- 删除冗余字段
ADD COLUMN record_insight_id BIGINT,      -- 引用记录洞察
ADD COLUMN analysis_insight_id BIGINT,    -- 引用分析洞察
ADD COLUMN treatment_insight_id BIGINT,   -- 引用调理洞察
ADD COLUMN is_cached BOOLEAN DEFAULT FALSE;  -- 是否已缓存

-- 添加外键
ALTER TABLE session_reports
ADD FOREIGN KEY (analysis_insight_id) REFERENCES session_analysis_insights(id);

-- 添加索引
CREATE INDEX idx_insight_refs ON session_reports(analysis_insight_id);
```

#### 查询逻辑

```python
def get_session_report(session_id):
    """获取会话报告"""
    
    # 1. 获取报告记录
    report = db.query(SessionReportDB).filter_by(
        session_id=session_id
    ).first()
    
    # 2. 动态组装报告
    assembled_report = {
        "id": report.id,
        "session_id": session_id,
        
        # 记录报告（直接从 record_report_json 读取）
        "record_report": report.record_report_json,
        
        # 分析报告（从 insights 动态组装）
        "analysis_report": assemble_analysis_report(
            report.analysis_insight_id
        ),
        
        # 调理报告（直接从 treatment_report_json 读取）
        "treatment_report": report.treatment_report_json,
        
        # 状态
        "status": {
            "record": report.record_status,
            "analysis": report.analysis_status,
            "treatment": report.treatment_status
        }
    }
    
    return assembled_report

def assemble_analysis_report(insight_id):
    """动态组装分析报告"""
    
    # 获取洞察（合并增量）
    insights = get_merged_insights_by_id(insight_id)
    
    # 获取四维数据
    four_dim_data = get_four_dim_data(insight_id.session_id)
    
    # 组装报告
    analysis_report = {
        "four_dim_summary": {
            "intensity_values": four_dim_data.get("intensity_values", []),
            "hedonic_distribution": four_dim_data.get("hedonic_distribution", {}),
            ...
        },
        "cognitive_analysis": {
            "mappings": insights.get("cognitive_mappings", []),
            "common_automatic_thoughts": insights.get("common_automatic_thoughts", []),
            "thinking_traps": insights.get("thinking_traps", []),
            "core_beliefs": insights.get("core_beliefs", [])
        },
        "tcm_analysis": insights.get("tcm_analysis", {}),
        "causes": insights.get("causes", {}),
        "trends": insights.get("emotional_trend", "")
    }
    
    return analysis_report
```

#### 优势

- **节省空间**：删除 analysis_report_json，节省 50% 空间
- **数据一致**：单一数据源，避免不一致
- **灵活更新**：更新 insights 自动反映到报告

#### 劣势

- **查询稍慢**：需要 JOIN 和组装（约慢 10-15ms）

---

### 优化方案 B：缓存策略（折中）

#### 核心思想
- **保留 JSON 字段作为缓存**
- **定期清理过期缓存**
- **查询优先使用缓存**

#### 表结构

```sql
ALTER TABLE session_reports
ADD COLUMN analysis_cache_version INT,  -- 缓存版本号
ADD COLUMN last_cache_update TIMESTAMP;  -- 最后缓存时间
```

#### 查询逻辑

```python
def get_analysis_report(session_id):
    """获取分析报告（带缓存）"""
    
    report = db.query(SessionReportDB).filter_by(
        session_id=session_id
    ).first()
    
    # 检查缓存是否有效
    if is_cache_valid(report):
        # 使用缓存
        return report.analysis_report_json
    else:
        # 缓存失效，重新生成
        fresh_report = assemble_analysis_report(report.analysis_insight_id)
        
        # 更新缓存
        report.analysis_report_json = fresh_report
        report.analysis_cache_version += 1
        report.last_cache_update = datetime.utcnow()
        db.commit()
        
        return fresh_report

def is_cache_valid(report):
    """检查缓存是否有效"""
    
    if not report.analysis_report_json:
        return False
    
    # 检查是否有新的洞察
    latest_insight = get_latest_insight(report.session_id)
    
    if latest_insight.created_at > report.last_cache_update:
        return False  # 有新数据，缓存失效
    
    return True
```

---

### 优化方案 C：物化视图（高级）

#### 核心思想
- **使用数据库物化视图**
- **自动维护缓存**
- **查询性能最优**

#### SQL 实现

```sql
-- 创建物化视图
CREATE MATERIALIZED VIEW mv_session_analysis_report AS
SELECT 
    r.id as report_id,
    r.session_id,
    r.user_id,
    
    -- 记录报告
    r.record_report_json,
    
    -- 动态组装分析报告
    JSON_OBJECT(
        'four_dim_summary', JSON_OBJECT(
            'intensity_values', f.intensity_values,
            'hedonic_distribution', f.hedonic_values
        ),
        'cognitive_analysis', JSON_OBJECT(
            'mappings', i.cognitive_mappings,
            'common_automatic_thoughts', i.common_automatic_thoughts,
            'thinking_traps', i.thinking_traps,
            'core_beliefs', i.core_beliefs
        ),
        'tcm_analysis', JSON_OBJECT(
            'dominant_emotion', i.tcm_dominant_emotion,
            'related_organs', i.tcm_related_organs,
            'qi_dynamics', i.tcm_qi_dynamics,
            'tcm_interpretation', i.tcm_interpretation
        )
    ) as analysis_report_json,
    
    -- 调理报告
    r.treatment_report_json,
    
    -- 状态
    r.record_status,
    r.analysis_status,
    r.treatment_status,
    
    -- 时间戳
    r.created_at,
    r.updated_at
    
FROM session_reports r
LEFT JOIN session_analysis_insights i 
    ON r.analysis_insight_id = i.id
LEFT JOIN (
    -- 四维数据子查询
    SELECT 
        session_id,
        JSON_ARRAYAGG(JSON_OBJECT('value', four_dim_intensity, 'timestamp', created_at)) as intensity_values,
        JSON_ARRAYAGG(four_dim_hedonic) as hedonic_values
    FROM dialogues
    WHERE four_dim_intensity IS NOT NULL
    GROUP BY session_id
) f ON r.session_id = f.session_id;

-- 创建索引
CREATE INDEX idx_mv_report_session ON mv_session_analysis_report(session_id);

-- 刷新物化视图（定期执行）
CREATE EVENT evt_refresh_mv_analysis_report
ON SCHEDULE EVERY 1 HOUR
DO BEGIN
    REFRESH MATERIALIZED VIEW mv_session_analysis_report;
END;
```

#### 查询逻辑

```python
def get_analysis_report(session_id):
    """从物化视图查询（极快）"""
    
    result = db.execute(
        "SELECT analysis_report_json FROM mv_session_analysis_report WHERE session_id = :session_id",
        {"session_id": session_id}
    ).first()
    
    return result.analysis_report_json if result else None
```

---

## 问题 4：概念解答

### 1. 数据归档机制

#### 什么是数据归档？

**定义**：将历史数据从主表迁移到归档表，减少主表数据量，提升查询性能。

#### 为什么要归档？

**问题场景**：
```sql
-- 运行 1 年后
SELECT COUNT(*) FROM dialogues;  -- 1000 万条
SELECT COUNT(*) FROM session_analysis_insights;  -- 500 万条

-- 查询变慢
SELECT * FROM dialogues WHERE session_id = ?;  -- 5 秒
```

**归档后**：
```sql
-- 主表只保留最近 6 个月
SELECT COUNT(*) FROM dialogues;  -- 50 万条
SELECT COUNT(*) FROM dialogues_history;  -- 950 万条（归档表）

-- 查询变快
SELECT * FROM dialogues WHERE session_id = ?;  -- 0.1 秒
```

#### 归档策略

**方案 A：按时间归档（推荐）**

```sql
-- 1. 创建归档表
CREATE TABLE dialogues_history LIKE dialogues;
CREATE TABLE session_analysis_insights_history LIKE session_analysis_insights;

-- 2. 定期迁移（每月执行）
INSERT INTO dialogues_history
SELECT * FROM dialogues
WHERE created_at < DATE_SUB(NOW(), INTERVAL 6 MONTH);

DELETE FROM dialogues
WHERE created_at < DATE_SUB(NOW(), INTERVAL 6 MONTH);

-- 3. 添加分区（可选）
ALTER TABLE dialogues_history
PARTITION BY RANGE (YEAR(created_at)) (
    PARTITION p2025 VALUES LESS THAN (2026),
    PARTITION p2026 VALUES LESS THAN (2027),
    PARTITION pmax VALUES LESS THAN MAXVALUE
);
```

**方案 B：按会话归档**

```python
# 归档已完成且超过 N 天的会话
def archive_old_sessions(days_threshold=180):
    """归档旧会话数据"""
    
    # 1. 找到符合条件的会话
    old_sessions = db.query(ChatSessionDB).filter(
        ChatSessionDB.updated_at < datetime.utcnow() - timedelta(days=days_threshold)
    ).all()
    
    # 2. 迁移数据
    for session in old_sessions:
        # 迁移对话
        dialogues = db.query(DialogueDB).filter_by(session_id=session.session_id).all()
        for d in dialogues:
            archive_dialogue(d)
        
        # 迁移洞察
        insights = db.query(SessionAnalysisInsightDB).filter_by(session_id=session.session_id).all()
        for i in insights:
            archive_insight(i)
        
        # 删除原数据
        db.delete(d)
        db.delete(i)
    
    db.commit()
```

#### 归档自动化

```sql
-- 创建定时任务（每月 1 号执行）
CREATE EVENT evt_monthly_archive
ON SCHEDULE EVERY 1 MONTH
STARTS '2026-05-01 02:00:00'
DO BEGIN
    -- 归档 6 个月前的对话
    INSERT INTO dialogues_history
    SELECT * FROM dialogues
    WHERE created_at < DATE_SUB(NOW(), INTERVAL 6 MONTH);
    
    DELETE FROM dialogues
    WHERE created_at < DATE_SUB(NOW(), INTERVAL 6 MONTH);
    
    -- 记录日志
    INSERT INTO admin_logs (action, details, created_at)
    VALUES ('archive', 'Archived dialogues older than 6 months', NOW());
END;
```

---

### 2. 物化视图（Materialized View）

#### 什么是物化视图？

**定义**：物化视图是**预先计算并存储结果**的视图，与普通视图（实时计算）不同。

#### 对比

| 特性 | 普通视图 | 物化视图 |
|------|---------|---------|
| 存储 | 不存储数据 | 存储数据 |
| 计算 | 查询时计算 | 预先计算 |
| 性能 | 慢 | 快 |
| 空间 | 不占空间 | 占空间 |
| 更新 | 自动 | 需手动刷新 |

#### 使用场景

**场景 1：复杂聚合查询**

```sql
-- 普通视图（每次查询都重新计算）
CREATE VIEW v_session_stats AS
SELECT 
    session_id,
    COUNT(*) as dialogue_count,
    AVG(four_dim_intensity) as avg_intensity,
    MAX(created_at) as last_activity
FROM dialogues
GROUP BY session_id;

-- 查询
SELECT * FROM v_session_stats WHERE session_id = ?;  -- 慢（扫描全表）
```

```sql
-- 物化视图（预先计算）
CREATE MATERIALIZED VIEW mv_session_stats AS
SELECT 
    session_id,
    COUNT(*) as dialogue_count,
    AVG(four_dim_intensity) as avg_intensity,
    MAX(created_at) as last_activity
FROM dialogues
GROUP BY session_id;

-- 创建索引
CREATE INDEX idx_mv_stats_session ON mv_session_stats(session_id);

-- 查询
SELECT * FROM mv_session_stats WHERE session_id = ?;  -- 快（索引扫描）

-- 定期刷新（每天凌晨 2 点）
CREATE EVENT evt_refresh_mv_stats
ON SCHEDULE EVERY 1 DAY
STARTS '2026-04-02 02:00:00'
DO BEGIN
    REFRESH MATERIALIZED VIEW mv_session_stats;
END;
```

**场景 2：多表 JOIN**

```sql
-- 物化视图：预计算会话报告
CREATE MATERIALIZED VIEW mv_session_report_summary AS
SELECT 
    r.session_id,
    r.user_id,
    r.record_status,
    r.analysis_status,
    r.treatment_status,
    
    -- 从 insights 聚合
    JSON_OBJECT(
        'thought_count', JSON_LENGTH(i.common_automatic_thoughts),
        'mapping_count', JSON_LENGTH(i.cognitive_mappings),
        'dominant_emotion', i.tcm_dominant_emotion
    ) as insight_summary,
    
    -- 从 dialogues 聚合
    JSON_OBJECT(
        'dialogue_count', d_stats.dialogue_count,
        'avg_intensity', d_stats.avg_intensity
    ) as dialogue_summary
    
FROM session_reports r
LEFT JOIN session_analysis_insights i ON r.analysis_insight_id = i.id
LEFT JOIN (
    SELECT session_id, COUNT(*) as dialogue_count, AVG(four_dim_intensity) as avg_intensity
    FROM dialogues
    GROUP BY session_id
) d_stats ON r.session_id = d_stats.session_id;

-- 查询性能提升 10 倍
SELECT * FROM mv_session_report_summary WHERE session_id = ?;
```

#### MySQL 注意事项

⚠️ **MySQL 8.0+ 才支持物化视图**

如果您的 MySQL 版本不支持，可以用**定时表**替代：

```sql
-- 创建定时表（模拟物化视图）
CREATE TABLE mv_session_stats (
    session_id VARCHAR(50) PRIMARY KEY,
    dialogue_count INT,
    avg_intensity FLOAT,
    last_activity TIMESTAMP,
    last_updated TIMESTAMP
);

-- 定时刷新
CREATE EVENT evt_refresh_session_stats
ON SCHEDULE EVERY 1 HOUR
DO BEGIN
    REPLACE INTO mv_session_stats
    SELECT 
        session_id,
        COUNT(*) as dialogue_count,
        AVG(four_dim_intensity) as avg_intensity,
        MAX(created_at) as last_activity,
        NOW() as last_updated
    FROM dialogues
    GROUP BY session_id;
END;
```

---

### 3. 监控数据增长趋势

#### 监控目标

1. **表空间增长**：哪些表增长最快？
2. **数据量趋势**：每天/每周新增多少数据？
3. **预警阈值**：达到阈值时告警

#### 监控逻辑

**方案 A：定时统计（推荐）**

```sql
-- 1. 创建监控表
CREATE TABLE db_growth_monitor (
    id INT PRIMARY KEY AUTO_INCREMENT,
    table_name VARCHAR(100),
    row_count BIGINT,
    data_size_mb FLOAT,
    index_size_mb FLOAT,
    total_size_mb FLOAT,
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. 创建定时任务（每天执行）
CREATE EVENT evt_daily_db_monitor
ON SCHEDULE EVERY 1 DAY
STARTS '2026-04-02 03:00:00'
DO BEGIN
    INSERT INTO db_growth_monitor (table_name, row_count, data_size_mb, index_size_mb, total_size_mb)
    SELECT 
        table_name,
        table_rows,
        ROUND(data_length / 1024 / 1024, 2),
        ROUND(index_length / 1024 / 1024, 2),
        ROUND((data_length + index_length) / 1024 / 1024, 2)
    FROM information_schema.TABLES
    WHERE table_schema = 'emotional_coaching_system_db';
END;

-- 3. 查询增长趋势
SELECT 
    table_name,
    DATE(recorded_at) as date,
    row_count,
    total_size_mb,
    row_count - LAG(row_count) OVER (PARTITION BY table_name ORDER BY recorded_at) as daily_growth
FROM db_growth_monitor
WHERE table_name IN ('dialogues', 'session_analysis_insights')
ORDER BY recorded_at DESC
LIMIT 30;
```

**方案 B：Python 脚本监控**

```python
# monitor_db_growth.py
import mysql.connector
from datetime import datetime

def monitor_database():
    """监控数据库增长"""
    
    conn = mysql.connector.connect(...)
    cursor = conn.cursor()
    
    # 查询表统计
    cursor.execute("""
        SELECT 
            table_name,
            table_rows,
            ROUND((data_length + index_length) / 1024 / 1024, 2) as total_size_mb
        FROM information_schema.TABLES
        WHERE table_schema = 'emotional_coaching_system_db'
        ORDER BY total_size_mb DESC
    """)
    
    tables = cursor.fetchall()
    
    # 记录到监控表
    for table_name, row_count, size_mb in tables:
        cursor.execute("""
            INSERT INTO db_growth_monitor 
            (table_name, row_count, total_size_mb, recorded_at)
            VALUES (%s, %s, %s, %s)
        """, (table_name, row_count, size_mb, datetime.utcnow()))
    
    conn.commit()
    
    # 检查预警
    check_alerts(cursor, tables)
    
    cursor.close()
    conn.close()

def check_alerts(cursor, tables):
    """检查预警"""
    
    for table_name, row_count, size_mb in tables:
        # 预警阈值
        if size_mb > 1000:  # 超过 1GB
            send_alert(f"表 {table_name} 超过 1GB，当前 {size_mb}MB")
        
        if row_count > 1000000:  # 超过 100 万条
            send_alert(f"表 {table_name} 超过 100 万条，当前 {row_count}条")
        
        # 检查增长率
        cursor.execute("""
            SELECT total_size_mb 
            FROM db_growth_monitor 
            WHERE table_name = %s 
            ORDER BY recorded_at DESC 
            LIMIT 7
        """, (table_name,))
        
        sizes = [row[0] for row in cursor.fetchall()]
        if len(sizes) >= 7:
            growth_rate = (sizes[0] - sizes[-1]) / sizes[-1] * 100
            if growth_rate > 50:  # 7 天增长超过 50%
                send_alert(f"表 {table_name} 7 天增长 {growth_rate:.1f}%")

def send_alert(message):
    """发送告警"""
    print(f"🚨 ALERT: {message}")
    # 可以集成邮件、短信、钉钉等

# 每天执行
if __name__ == "__main__":
    monitor_database()
```

#### 可视化监控

```python
# 生成增长趋势图
import matplotlib.pyplot as plt
import pandas as pd

def plot_growth_trend():
    """绘制增长趋势图"""
    
    # 查询数据
    df = pd.read_sql("""
        SELECT 
            table_name,
            DATE(recorded_at) as date,
            total_size_mb
        FROM db_growth_monitor
        WHERE table_name IN ('dialogues', 'session_analysis_insights', 'session_reports')
        ORDER BY recorded_at
    """, conn)
    
    # 绘制折线图
    plt.figure(figsize=(12, 6))
    
    for table_name in df['table_name'].unique():
        table_data = df[df['table_name'] == table_name]
        plt.plot(table_data['date'], table_data['total_size_mb'], label=table_name)
    
    plt.xlabel('日期')
    plt.ylabel('大小 (MB)')
    plt.title('数据库表增长趋势')
    plt.legend()
    plt.grid(True)
    plt.savefig('db_growth_trend.png')
    plt.show()

plot_growth_trend()
```

#### 监控告警规则

```python
# 告警规则配置
ALERT_RULES = {
    'dialogues': {
        'max_size_mb': 5000,  # 超过 5GB 告警
        'max_rows': 5000000,  # 超过 500 万条告警
        'growth_rate_7d': 20,  # 7 天增长超过 20% 告警
        'growth_rate_30d': 50  # 30 天增长超过 50% 告警
    },
    'session_analysis_insights': {
        'max_size_mb': 2000,
        'max_rows': 1000000,
        'growth_rate_7d': 30,
        'growth_rate_30d': 60
    }
}

# 定期检查
def check_all_alerts():
    """检查所有告警规则"""
    
    for table_name, rules in ALERT_RULES.items():
        # 获取当前状态
        current = get_current_stats(table_name)
        
        # 检查大小
        if current['size_mb'] > rules['max_size_mb']:
            send_alert(f"{table_name} 超过大小阈值：{current['size_mb']}MB")
        
        # 检查行数
        if current['row_count'] > rules['max_rows']:
            send_alert(f"{table_name} 超过行数阈值：{current['row_count']}条")
        
        # 检查增长率
        growth_7d = calculate_growth_rate(table_name, days=7)
        if growth_7d > rules['growth_rate_7d']:
            send_alert(f"{table_name} 7 天增长率过高：{growth_7d:.1f}%")
```

---

## 总结与建议

### 立即执行（本周）

1. **删除旧问卷表**
   ```sql
   DROP TABLE IF EXISTS questionnaires;
   DROP TABLE IF EXISTS user_questionnaire_results;
   ```

2. **删除 session_four_dim_data 表**
   ```sql
   DROP TABLE IF EXISTS session_four_dim_data;
   ```

### 近期执行（本月）

3. **实施 session_analysis_insights 增量存储**
   - 采用**方案 C：混合存储**
   - 每 10 条对话保存一次快照
   - 快照之间使用增量

4. **优化 session_reports 存储**
   - 采用**方案 A：引用存储**
   - 删除 analysis_report_json
   - 添加 insight_id 引用

### 长期规划（下季度）

5. **建立数据归档机制**
   - 创建归档表
   - 设置定时任务（每月执行）
   - 归档 6 个月前的数据

6. **实施监控体系**
   - 创建监控表
   - 设置定时统计任务
   - 配置告警规则

---

**文档版本**：v1.0  
**创建日期**：2026-04-01  
**解答人**：系统架构师
