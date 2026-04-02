# 数据库优化实施工作流（v2 修订版）

## 概述

本文档详细列出数据库优化的所有修改步骤，包括删除表、修改表结构、实现新功能等。

**修订说明**：
- 新增：检查并删除 `SessionFourDimDataDB` 相关代码
- 修改：复杂度分析逻辑（≥2 种情绪=复杂，每 2 轮对话调用 LLM）
- 修改：end_session 接口响应逻辑（立即响应，异步生成报告）
- 新增：全面检索并删除旧代码引用

---

## 阶段零：代码检查与清理（新增，1 天）

### 0.1 全面检索 SessionFourDimDataDB 引用

**目标**：找出所有引用 `SessionFourDimDataDB` 的代码

**检索范围**：
```bash
# 搜索 Python 文件
grep -r "SessionFourDimDataDB" backend/
grep -r "session_four_dim_data" backend/
grep -r "four_dim_data" backend/

# 搜索导入语句
grep -r "from.*session_four_dim_data" backend/
grep -r "import.*SessionFourDimDataDB" backend/
```

**待删除的代码**（示例）：
```python
# ❌ 删除这些引用
from backend.core.database import SessionFourDimDataDB

# ❌ 删除查询逻辑
four_dim_data = db.query(SessionFourDimDataDB).filter_by(
    session_id=session_id
).first()

# ❌ 删除保存逻辑
new_four_dim = SessionFourDimDataDB(
    session_id=session_id,
    intensity_values=...,
    ...
)
```

---

### 0.2 全面检索旧问卷表引用

**目标**：找出所有引用旧问卷表的代码

**检索范围**：
```bash
# 搜索旧表引用
grep -r "QuestionnaireDB" backend/
grep -r "UserQuestionnaireResultDB" backend/
grep -r "questionnaires" backend/ --include="*.py"
grep -r "user_questionnaire_results" backend/ --include="*.py"
```

**待删除的代码**（示例）：
```python
# ❌ 删除这些引用
from backend.core.database import QuestionnaireDB, UserQuestionnaireResultDB

# ❌ 删除查询逻辑
questionnaires = db.query(QuestionnaireDB).all()
results = db.query(UserQuestionnaireResultDB).filter_by(user_id=user_id).all()
```

---

### 0.3 创建代码清理报告

**文件**：`docs/code_cleanup_report.md`（新建）

**内容**：
```markdown
# 代码清理报告

## 删除的引用

### SessionFourDimDataDB 相关
1. backend/api/v1/xxx.py - 第 X 行
2. backend/agents/xxx.py - 第 X 行
...

### 旧问卷表相关
1. backend/api/v1/xxx.py - 第 X 行
2. backend/repositories/xxx.py - 第 X 行
...

## 删除的文件
- backend/api/v1/old_questionnaire.py（如有）
- backend/repositories/old_questionnaire_repo.py（如有）

## 验证
- [ ] 运行 grep 搜索确认无残留
- [ ] 运行测试确认无报错
```

---

## 阶段一：清理旧表（0.5 天）

### 1.1 删除旧问卷表

**目标**：删除不再使用的旧问卷表

**操作**：
```sql
-- 检查是否有数据
SELECT COUNT(*) FROM questionnaires;
SELECT COUNT(*) FROM user_questionnaire_results;

-- 删除表
DROP TABLE IF EXISTS questionnaires;
DROP TABLE IF EXISTS user_questionnaire_results;
```

**前提条件**：
- [ ] 阶段零已完成，所有代码引用已删除
- [ ] 已运行测试验证无报错

---

### 1.2 删除 session_four_dim_data 表

**目标**：删除冗余的四维数据表

**操作**：
```sql
-- 检查是否有数据
SELECT COUNT(*) FROM session_four_dim_data;

-- 删除表
DROP TABLE IF EXISTS session_four_dim_data;
```

**前提条件**：
- [ ] 阶段零已完成，所有代码引用已删除
- [ ] 已验证四维数据从 dialogues 表获取

---

## 阶段二：修改 session_analysis_insights 表结构（1 天）

### 2.1 添加状态字段

**目标**：将 insights 表改造为"中转站"

**修改内容**：
```sql
ALTER TABLE session_analysis_insights
ADD COLUMN is_completed BOOLEAN DEFAULT FALSE COMMENT '是否已完成',
ADD COLUMN migrated_to_report BOOLEAN DEFAULT FALSE COMMENT '是否已迁移到 reports',
ADD COLUMN completed_at TIMESTAMP NULL COMMENT '完成时间';
```

---

### 2.2 添加复杂度版本追踪字段

**目标**：支持复杂度的增量版本管理

**修改内容**：
```sql
ALTER TABLE session_analysis_insights
ADD COLUMN complexity_version INT DEFAULT 1 COMMENT '复杂度分析版本',
ADD COLUMN last_complexity_update TIMESTAMP NULL COMMENT '最后复杂度更新时间';
```

---

### 2.3 添加四维数据字段

**目标**：存储四维数据的增量统计

**修改内容**：
```sql
ALTER TABLE session_analysis_insights
ADD COLUMN intensity_values JSON COMMENT '强度时间序列 [{"value": 6.5, "timestamp": "..."}]',
ADD COLUMN hedonic_distribution JSON COMMENT '快感度分布统计 {"负性": 8, "中性": 2, "正性": 0}',
ADD COLUMN tension_distribution JSON COMMENT '紧张度分布统计 {"高": 5, "中": 4, "低": 1}',
ADD COLUMN complexity_analysis JSON COMMENT '复杂度 LLM 分析结果 {type, emotions, analysis}';
```

---

## 阶段三：修改 Python 代码（3 天）

### 3.1 修改 database.py

**文件**：`backend/core/database.py`

**修改内容**：

#### 删除 SessionFourDimDataDB 类
```python
# ❌ 删除整个类
class SessionFourDimDataDB(Base):
    """会话四维数据表（用于存储分析师的四维图表数据）"""
    __tablename__ = "session_four_dim_data"
    ...
```

#### 修改 SessionAnalysisInsightDB 类
```python
class SessionAnalysisInsightDB(Base):
    """会话分析洞察表（中转站）"""
    __tablename__ = "session_analysis_insights"
    
    # ... 现有字段 ...
    
    # 新增：状态字段
    is_completed = Column(Boolean, default=False, comment='是否已完成')
    migrated_to_report = Column(Boolean, default=False, comment='是否已迁移到 reports')
    completed_at = Column(TIMESTAMP, nullable=True, comment='完成时间')
    
    # 新增：复杂度版本追踪
    complexity_version = Column(Integer, default=1, comment='复杂度分析版本')
    last_complexity_update = Column(TIMESTAMP, nullable=True, comment='最后复杂度更新时间')
    
    # 新增：四维数据字段
    intensity_values = Column(JSON, nullable=True, comment='强度时间序列')
    hedonic_distribution = Column(JSON, nullable=True, comment='快感度分布统计')
    tension_distribution = Column(JSON, nullable=True, comment='紧张度分布统计')
    complexity_analysis = Column(JSON, nullable=True, comment='复杂度 LLM 分析结果')
```

---

### 3.2 修改 record_repository_new.py

**文件**：`backend/repositories/record_repository_new.py`

**删除内容**：
```python
# ❌ 删除所有引用 SessionFourDimDataDB 的方法
def get_four_dim_data(session_id):
    four_dim_data = db.query(SessionFourDimDataDB)...
    return four_dim_data
```

**新增方法**：

#### 3.2.1 更新四维统计数据
```python
def update_four_dim_statistics(self, session_id: str, four_dim: Dict[str, Any]):
    """
    增量更新四维数据统计
    :param session_id: 会话 ID
    :param four_dim: 四维数据 {intensity, hedonic, tension, complexity}
    """
    insight = self.get_or_create_insight(session_id)
    
    # 1. 强度：追加到数组
    if insight.intensity_values is None:
        insight.intensity_values = []
    
    insight.intensity_values.append({
        "value": four_dim.get("intensity"),
        "timestamp": datetime.utcnow().isoformat()
    })
    
    # 2. 快感度：计数 +1
    if insight.hedonic_distribution is None:
        insight.hedonic_distribution = {"负性": 0, "中性": 0, "正性": 0}
    
    hedonic = four_dim.get("hedonic")
    if hedonic and hedonic in insight.hedonic_distribution:
        insight.hedonic_distribution[hedonic] += 1
    
    # 3. 紧张度：计数 +1
    if insight.tension_distribution is None:
        insight.tension_distribution = {"低": 0, "中": 0, "高": 0}
    
    tension = four_dim.get("tension")
    if tension and tension in insight.tension_distribution:
        insight.tension_distribution[tension] += 1
    
    db.commit()
```

#### 3.2.2 更新复杂度分析（修订版）
```python
async def update_complexity_analysis(self, session_id: str, 
                                     dialogue_history: List[Dict],
                                     force_llm: bool = False):
    """
    更新复杂度分析（修订版：每 2 轮对话调用 LLM）
    :param session_id: 会话 ID
    :param dialogue_history: 对话历史
    :param force_llm: 是否强制调用 LLM
    """
    insight = self.get_or_create_insight(session_id)
    dialogue_count = len(dialogue_history)
    
    # 策略：每 2 条对话调用一次 LLM
    if force_llm or dialogue_count % 2 == 0:
        # 调用 LLM 分析
        complexity = await self.llm_analyze_complexity(dialogue_history)
        
        # 判断情绪种类数量
        emotion_count = len(complexity.get("emotions", []))
        
        # 情绪类>=2 时就是复杂
        if emotion_count >= 2:
            complexity["type"] = "复杂"
        else:
            complexity["type"] = "简单"
        
        insight.complexity_analysis = complexity
        insight.complexity_version += 1
        insight.last_complexity_update = datetime.utcnow()
    else:
        # 简单规则判断（不调用 LLM）
        if insight.complexity_analysis is None:
            # 初始化为简单
            insight.complexity_analysis = {
                "type": "简单",
                "emotions": [],
                "analysis": "等待 LLM 分析...",
                "is_llm_analysis": False
            }
    
    db.commit()
```

#### 3.2.3 标记完成和迁移
```python
def mark_insight_completed(self, session_id: str):
    """标记洞察记录已完成"""
    insight = self.get_insight(session_id)
    if insight:
        insight.is_completed = True
        insight.completed_at = datetime.utcnow()
        db.commit()

def mark_insight_migrated(self, session_id: str):
    """标记洞察记录已迁移"""
    insight = self.get_insight(session_id)
    if insight:
        insight.migrated_to_report = True
        db.commit()
```

---

### 3.3 修改 analyst_agent.py

**文件**：`backend/agents/analyst_agent.py`

**删除内容**：
```python
# ❌ 删除所有引用 SessionFourDimDataDB 的代码
from backend.core.database import SessionFourDimDataDB
```

**修改内容**：

#### 3.3.1 修改 analyze_process 方法
```python
async def analyze_process(self, user_id: str, user_input: str, 
                         four_dim: Dict[str, Any], 
                         dialogue_id: int = None, 
                         session_id: str = None) -> Dict[str, Any]:
    """处理分析的主入口"""
    
    # ... 现有逻辑 ...
    
    # 新增：实时更新四维统计
    try:
        self.repository.update_four_dim_statistics(session_id, four_dim)
        print(f"DEBUG: 四维统计更新成功，会话 ID: {session_id}")
    except Exception as e:
        print(f"ERROR: 更新四维统计失败：{e}")
    
    # 新增：定期更新复杂度分析（每 2 轮对话）
    try:
        dialogue_history = self.repository.get_recent_dialogues(
            user_id, limit=50, session_id=session_id
        )
        await self.repository.update_complexity_analysis(
            session_id, dialogue_history, force_llm=False
        )
        print(f"DEBUG: 复杂度分析更新成功，版本：{self.repository.get_insight(session_id).complexity_version}")
    except Exception as e:
        print(f"ERROR: 更新复杂度分析失败：{e}")
    
    return advice
```

---

### 3.4 修改 chat_endpoints.py（修订版）

**文件**：`backend/api/v1/chat_endpoints.py`

**删除内容**：
```python
# ❌ 删除所有引用 SessionFourDimDataDB 的代码
from backend.core.database import SessionFourDimDataDB
```

**修改内容**：

#### 3.4.1 修订 end_session 方法（立即响应，异步生成）

```python
@router.post("/end-session")
async def end_session(request_data: dict, db: Session = Depends(get_db)):
    """
    结束会话（修订版：立即响应，异步生成报告）
    
    流程：
    1. 保存所有对话到 dialogues 表
    2. 立即响应"结束会话已完成，正在生成报告中"
    3. 异步触发三个报告生成任务
    """
    user_id = request_data.get("user_id")
    session_id = request_data.get("session_id")
    
    # 验证用户和会话
    user = db.query(UserDB).filter(UserDB.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="用户不存在")
    
    session = db.query(ChatSessionDB).filter(
        ChatSessionDB.session_id == session_id,
        ChatSessionDB.user_id == user_id
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    # 步骤 1：保存所有对话（确保已保存）
    dialogues = db.query(DialogueDB).filter_by(
        session_id=session_id
    ).all()
    
    if not dialogues:
        raise HTTPException(status_code=400, detail="会话中没有对话记录")
    
    # 步骤 2：立即响应
    response_data = {
        "message": "结束会话已完成，正在生成报告中",
        "code": 200,
        "session_id": session_id,
        "dialogue_count": len(dialogues),
        "status": {
            "record_report": "pending",
            "analysis_report": "pending",
            "treatment_report": "pending"
        }
    }
    
    # 步骤 3：异步触发三个报告生成（后台任务）
    asyncio.create_task(
        generate_all_reports_async(user_id, session_id, dialogues, db)
    )
    
    return response_data


async def generate_all_reports_async(user_id: str, session_id: str, 
                                     dialogues: List, db: Session):
    """
    异步生成三个报告（后台任务）
    """
    try:
        # 获取 LLM 服务
        llm_service = await get_llm_service()
        
        # 初始化三个智能体
        recorder_agent = get_recorder_agent()
        recorder_agent.llm_service = llm_service
        
        analyst_agent = get_analyst_agent()
        analyst_agent.llm_service = llm_service
        
        therapist_agent = get_therapist_agent()
        therapist_agent.llm_service = llm_service
        
        # 构建对话历史
        dialogue_history = [
            {"role": d.role, "content": d.content, "four_dim": {
                "intensity": d.four_dim_intensity,
                "hedonic": d.four_dim_hedonic,
                "tension": d.four_dim_tension,
                "complexity": d.four_dim_complexity
            }}
            for d in dialogues
        ]
        
        # ========== 报告 1：记录报告 ==========
        print(f"DEBUG: 开始生成记录报告，会话 ID: {session_id}")
        record_report = await recorder_agent.finalize_record_report(user_id, session_id)
        
        # ========== 报告 2：分析报告 ==========
        print(f"DEBUG: 开始生成分析报告，会话 ID: {session_id}")
        
        # 从 insights 读取四维数据和分析数据
        insight = analyst_agent.repository.get_insight(session_id)
        
        four_dim_summary = {
            "intensity_values": insight.intensity_values or [],
            "hedonic_distribution": insight.hedonic_distribution or {},
            "tension_distribution": insight.tension_distribution or {},
            "complexity_analysis": insight.complexity_analysis or {}
        }
        
        analysis_report = {
            "four_dim_summary": four_dim_summary,
            "cognitive_analysis": {
                "mappings": insight.cognitive_mappings or [],
                "common_automatic_thoughts": insight.common_automatic_thoughts or [],
                "thinking_traps": insight.thinking_traps or [],
                "core_beliefs": insight.core_beliefs or []
            },
            "tcm_analysis": {
                "dominant_emotion": insight.tcm_dominant_emotion,
                "related_organs": insight.tcm_related_organs or [],
                "qi_dynamics": insight.tcm_qi_dynamics,
                "tcm_interpretation": insight.tcm_interpretation
            },
            "causes": {
                "cbt_perspective": insight.cbt_perspective,
                "tcm_perspective": insight.tcm_perspective
            },
            "trends": insight.emotional_trend
        }
        
        # ========== 报告 3：调理报告 ==========
        print(f"DEBUG: 开始生成调理报告，会话 ID: {session_id}")
        treatment_report = await therapist_agent.generate_treatment_report(
            user_id, session_id, analysis_report
        )
        
        # 保存到 session_reports 表
        report = SessionReportDB(
            user_id=user_id,
            session_id=session_id,
            record_report_json=record_report,
            analysis_report_json=analysis_report,
            treatment_report_json=treatment_report,
            record_status="completed",
            analysis_status="completed",
            treatment_status="completed"
        )
        db.add(report)
        db.commit()
        
        # 标记 insights
        analyst_agent.repository.mark_insight_completed(session_id)
        analyst_agent.repository.mark_insight_migrated(session_id)
        
        print(f"DEBUG: 报告生成完成，会话 ID: {session_id}, 报告 ID: {report.id}")
        
    except Exception as e:
        print(f"ERROR: 生成报告失败：{e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        
        # 更新状态为失败
        report = db.query(SessionReportDB).filter_by(session_id=session_id).first()
        if report:
            report.analysis_status = "failed"
            db.commit()
```

---

### 3.5 创建清理任务脚本

**文件**：`backend/tasks/cleanup_insights.py`（新建）

**内容**：
```python
"""
定期清理已迁移的洞察数据
"""
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from backend.core.database import SessionLocal, SessionAnalysisInsightDB

def cleanup_old_insights(days_to_keep: int = 30):
    """
    清理 30 天前的已迁移洞察数据
    :param days_to_keep: 保留天数
    """
    db = SessionLocal()
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
        
        # 删除已迁移且超过 30 天的记录
        result = db.query(SessionAnalysisInsightDB).filter(
            SessionAnalysisInsightDB.migrated_to_report == True,
            SessionAnalysisInsightDB.completed_at < cutoff_date
        ).delete()
        
        db.commit()
        
        print(f"清理了 {result} 条洞察记录")
        return result
        
    except Exception as e:
        db.rollback()
        print(f"清理失败：{e}")
        raise e
    finally:
        db.close()

if __name__ == "__main__":
    cleanup_old_insights()
```

---

### 3.6 添加定时任务配置

**文件**：`backend/main.py`（或定时任务配置文件）

**内容**：
```python
from apscheduler.schedulers.background import BackgroundScheduler
from backend.tasks.cleanup_insights import cleanup_old_insights

# 创建后台调度器
scheduler = BackgroundScheduler()

# 每天凌晨 2 点执行清理
scheduler.add_job(
    cleanup_old_insights,
    'cron',
    hour=2,
    minute=0,
    id='cleanup_insights'
)

# 启动调度器
scheduler.start()
```

---

## 阶段四：数据库迁移脚本（0.5 天）

### 4.1 创建迁移脚本

**文件**：`backend/migrations/add_insight_fields.py`（新建）

**内容**：
```python
"""
数据库迁移：添加 insight 表新字段
"""
from sqlalchemy import text
from backend.core.database import engine

def upgrade():
    """升级数据库"""
    
    with engine.connect() as conn:
        # 添加状态字段
        conn.execute(text("""
            ALTER TABLE session_analysis_insights
            ADD COLUMN is_completed BOOLEAN DEFAULT FALSE COMMENT '是否已完成'
        """))
        
        conn.execute(text("""
            ALTER TABLE session_analysis_insights
            ADD COLUMN migrated_to_report BOOLEAN DEFAULT FALSE COMMENT '是否已迁移到 reports'
        """))
        
        conn.execute(text("""
            ALTER TABLE session_analysis_insights
            ADD COLUMN completed_at TIMESTAMP NULL COMMENT '完成时间'
        """))
        
        # 添加复杂度版本字段
        conn.execute(text("""
            ALTER TABLE session_analysis_insights
            ADD COLUMN complexity_version INT DEFAULT 1 COMMENT '复杂度分析版本'
        """))
        
        conn.execute(text("""
            ALTER TABLE session_analysis_insights
            ADD COLUMN last_complexity_update TIMESTAMP NULL COMMENT '最后复杂度更新时间'
        """))
        
        # 添加四维数据字段
        conn.execute(text("""
            ALTER TABLE session_analysis_insights
            ADD COLUMN intensity_values JSON COMMENT '强度时间序列'
        """))
        
        conn.execute(text("""
            ALTER TABLE session_analysis_insights
            ADD COLUMN hedonic_distribution JSON COMMENT '快感度分布统计'
        """))
        
        conn.execute(text("""
            ALTER TABLE session_analysis_insights
            ADD COLUMN tension_distribution JSON COMMENT '紧张度分布统计'
        """))
        
        conn.execute(text("""
            ALTER TABLE session_analysis_insights
            ADD COLUMN complexity_analysis JSON COMMENT '复杂度 LLM 分析结果'
        """))
        
        conn.commit()
        
    print("数据库迁移完成")

def downgrade():
    """回滚迁移"""
    
    with engine.connect() as conn:
        # 删除所有新增字段
        conn.execute(text("""
            ALTER TABLE session_analysis_insights
            DROP COLUMN is_completed,
            DROP COLUMN migrated_to_report,
            DROP COLUMN completed_at,
            DROP COLUMN complexity_version,
            DROP COLUMN last_complexity_update,
            DROP COLUMN intensity_values,
            DROP COLUMN hedonic_distribution,
            DROP COLUMN tension_distribution,
            DROP COLUMN complexity_analysis
        """))
        
        conn.commit()
        
    print("数据库回滚完成")

if __name__ == "__main__":
    upgrade()
```

---

## 阶段五：测试验证（2 天）

### 5.1 单元测试

**文件**：`tests/test_four_dim_storage.py`（新建）

**测试内容**：
```python
def test_update_four_dim_statistics():
    """测试四维统计更新"""
    # 测试强度追加
    # 测试快感度计数
    # 测试紧张度计数

def test_complexity_analysis_update():
    """测试复杂度分析更新（每 2 轮对话）"""
    # 测试第 1 条对话：不调用 LLM
    # 测试第 2 条对话：调用 LLM
    # 测试情绪>=2 时标记为"复杂"

def test_end_session_immediate_response():
    """测试结束会话立即响应"""
    # 测试响应消息
    # 测试 code=200
    # 测试异步生成报告
```

### 5.2 集成测试

**测试流程**：
1. 创建会话
2. 发送 10 条消息
3. 验证 insights 表数据增量更新
4. 发送结束会话请求
5. 验证立即响应（message 和 code=200）
6. 验证异步生成报告
7. 验证 reports 表数据完整
8. 验证 insights 表标记正确

---

## 阶段六：实施时间表（修订版）

### 第 1 天：代码检查与清理
- [ ] 0.1 检索 SessionFourDimDataDB 引用
- [ ] 0.2 检索旧问卷表引用
- [ ] 0.3 创建代码清理报告
- [ ] 删除所有旧代码引用

### 第 2 天：清理旧表 + 修改表结构
- [ ] 1.1 删除旧问卷表
- [ ] 1.2 删除 session_four_dim_data 表
- [ ] 2.1-2.3 修改 session_analysis_insights 表

### 第 3-5 天：修改代码
- [ ] 3.1 修改 database.py（删除旧类）
- [ ] 3.2 修改 record_repository_new.py
- [ ] 3.3 修改 analyst_agent.py
- [ ] 3.4 修改 chat_endpoints.py（end_session 逻辑）
- [ ] 3.5-3.6 创建清理任务和定时配置

### 第 6 天：数据库迁移
- [ ] 4.1 运行迁移脚本
- [ ] 验证表结构

### 第 7-8 天：测试
- [ ] 5.1 单元测试
- [ ] 5.2 集成测试
- [ ] 修复 bug

### 第 9 天：部署
- [ ] 部署到开发环境
- [ ] 验证功能
- [ ] 部署到生产环境

---

## 风险评估与回滚方案（修订版）

### 风险 1：旧代码未完全删除

**风险**：删除表后，残留代码报错

**缓解措施**：
- 阶段零全面检索所有引用
- 创建代码清理报告
- 运行 grep 验证无残留

**回滚方案**：
```bash
# 回滚代码
git checkout <previous_version>

# 恢复表
source /path/to/backup.sql
```

---

### 风险 2：end_session 异步生成失败

**风险**：立即响应后，后台任务失败

**缓解措施**：
- 添加异常处理
- 记录详细日志
- 添加重试机制

**回滚方案**：
```python
# 如果异步任务失败，可以手动触发
async def manual_generate_reports(session_id):
    """手动生成报告"""
    # 重新执行 generate_all_reports_async
```

---

### 风险 3：复杂度分析逻辑错误

**风险**：情绪判断逻辑不正确

**缓解措施**：
- 单元测试覆盖
- 添加调试日志
- 人工验证结果

**回滚方案**：
```python
# 临时改回每 5 条对话调用 LLM
if dialogue_count % 5 == 0:  # 临时改回 5
    ...
```

---

## 待确认事项（修订版）

### 需要您确认的内容：

1. **代码检索**：
   - [ ] 确认已检索所有 SessionFourDimDataDB 引用
   - [ ] 确认已检索所有旧问卷表引用
   - [ ] 确认代码清理报告完整

2. **删除表确认**：
   - [ ] 确认可以删除 `questionnaires` 表
   - [ ] 确认可以删除 `user_questionnaire_results` 表
   - [ ] 确认可以删除 `session_four_dim_data` 表

3. **end_session 逻辑确认**：
   - [ ] 确认立即响应（不等待报告生成）
   - [ ] 确认响应 message："结束会话已完成，正在生成报告中"
   - [ ] 确认 code=200
   - [ ] 确认异步触发三个报告生成

4. **复杂度分析逻辑确认**：
   - [ ] 确认情绪类>=2 时标记为"复杂"
   - [ ] 确认每 2 轮对话调用一次 LLM
   - [ ] 确认第 1 条对话不调用 LLM（使用默认简单）

5. **实施时间确认**：
   - [ ] 确认实施时间表（9 天）
   - [ ] 确认部署时间（低峰期）

6. **备份确认**：
   - [ ] 确认已备份数据库
   - [ ] 确认已备份代码

---

## 总结（修订版）

### 修改内容汇总

| 阶段 | 修改项 | 文件数 | 预计时间 |
|------|-------|--------|---------|
| 零：代码检查 | 检索 + 删除旧代码 | 全部 | 1 天 |
| 一：清理旧表 | 3 个表 | 0 | 0.5 天 |
| 二：修改表结构 | 4 个 ALTER | 0 | 1 天 |
| 三：修改代码 | 4 个文件 + 2 个新建 | 6 | 3 天 |
| 四：数据库迁移 | 1 个脚本 | 1 | 0.5 天 |
| 五：测试 | 测试脚本 | 2 | 2 天 |
| 六：部署 | 生产环境 | - | 1 天 |
| **总计** | - | **13** | **9 天** |

---

### 核心变更点

1. **新增阶段零**：全面检索并删除旧代码引用
2. **修改复杂度逻辑**：情绪≥2=复杂，每 2 轮对话调用 LLM
3. **修改 end_session**：立即响应 + 异步生成报告
4. **删除旧表**：3 个表（questionnaires, user_questionnaire_results, session_four_dim_data）

---

**文档版本**：v2.0  
**创建日期**：2026-04-01  
**修订日期**：2026-04-01  
**制定人**：系统架构师  
**状态**：待确认

---

## 请您确认以下内容：

### ✅ 需要您确认的事项（修订版）

1. **代码检索与删除**：
   - [ ] 确认阶段零会全面检索所有旧代码引用
   - [ ] 确认会删除所有 SessionFourDimDataDB 相关代码
   - [ ] 确认会删除所有旧问卷表相关代码
   - [ ] 确认会创建代码清理报告

2. **删除表确认**：
   - [ ] 确认可以删除 `questionnaires` 表
   - [ ] 确认可以删除 `user_questionnaire_results` 表
   - [ ] 确认可以删除 `session_four_dim_data` 表

3. **复杂度分析逻辑**：
   - [ ] 确认情绪种类≥2 时标记为"复杂"
   - [ ] 确认每 2 轮对话调用一次 LLM 分析
   - [ ] 确认第 1 条对话使用默认"简单"

4. **end_session 接口逻辑**：
   - [ ] 确认保存对话后立即响应
   - [ ] 确认响应 message："结束会话已完成，正在生成报告中"
   - [ ] 确认 code=200
   - [ ] 确认异步触发三个报告生成

5. **实施时间确认**：
   - [ ] 确认总时间：9 天
   - [ ] 确认部署时间窗口

6. **备份确认**：
   - [ ] 确认已备份数据库
   - [ ] 确认已备份代码

---

**请您逐项确认，确认完成后我将开始执行修改！** 🙏
