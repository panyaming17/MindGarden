# session_reports 表状态字段添加完成

**完成时间**: 2026-04-01  
**需求**: 添加报告状态标识字段，支持前端轮询查询

## 📊 新增字段

为 `session_reports` 表添加了 4 个状态字段：

| 字段名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `record_report_status` | VARCHAR(20) | 'pending' | 记录报告状态 |
| `analysis_report_status` | VARCHAR(20) | 'pending' | 分析报告状态 |
| `treatment_report_status` | VARCHAR(20) | 'pending' | 调理报告状态 |
| `status_updated_at` | TIMESTAMP | CURRENT_TIMESTAMP | 状态更新时间 |

### 状态值说明

| 状态值 | 说明 |
|--------|------|
| `pending` | 等待中（初始状态） |
| `generating` | 生成中 |
| `completed` | 已完成 |
| `failed` | 失败（预留） |

## ✅ 已完成的修改

### 1. 数据库迁移

执行成功：
```
✓ 已添加字段：record_report_status
✓ 已添加字段：analysis_report_status
✓ 已添加字段：treatment_report_status
✓ 已添加字段：status_updated_at
```

### 2. 异步任务状态更新

在 `generate_all_reports_async()` 函数中添加了状态更新逻辑：

**记录报告生成流程**：
```python
# 更新状态：记录报告生成中
existing_report.record_report_status = 'generating'
db.commit()

record_report = await recorder_agent.finalize_record_report(...)

# 更新状态：记录报告完成
existing_report.record_report_status = 'completed'
db.commit()
```

**分析报告生成流程**：
```python
# 更新状态：分析报告生成中
existing_report.analysis_report_status = 'generating'
db.commit()

analysis_report = await analyst_agent.generate_analysis_report_from_archive(...)

# 更新状态：分析报告完成
existing_report.analysis_report_status = 'completed'
db.commit()
```

**调理报告生成流程**：
```python
# 更新状态：调理报告生成中
existing_report.treatment_report_status = 'generating'
db.commit()

treatment_report = await therapist_agent.generate_treatment_report(...)

# 更新状态：调理报告完成
existing_report.treatment_report_status = 'completed'
db.commit()
```

### 3. 新增查询报告状态接口

**接口地址**: `GET /api/v1/chat/report-status/{session_id}`

**响应示例**：
```json
{
  "session_id": "session_12345",
  "status": {
    "record_report": "completed",
    "analysis_report": "generating",
    "treatment_report": "pending"
  },
  "status_updated_at": "2026-04-01T21:30:00",
  "reports_available": {
    "record_report": true,
    "analysis_report": false,
    "treatment_report": false
  }
}
```

**字段说明**：
- `status`: 三个报告的状态
- `status_updated_at`: 最后状态更新时间
- `reports_available`: 报告是否已生成（JSON 字段是否为 NULL）

## 🧪 测试步骤

### 1. 测试 end_session 接口

**操作步骤**：
1. 前端创建会话并进行 2-3 轮对话
2. 点击"结束会话"
3. 观察响应

**预期响应**：
```json
{
  "message": "结束会话已完成，正在生成报告中",
  "code": 200,
  "session_id": "xxx",
  "dialogue_count": 3,
  "status": {
    "record_report": "pending",
    "analysis_report": "pending",
    "treatment_report": "pending"
  }
}
```

### 2. 测试报告状态查询

**操作步骤**：
1. 结束会话后立即调用 `GET /api/v1/chat/report-status/{session_id}`
2. 每隔 2 秒调用一次，观察状态变化

**预期状态变化**：
```
时间 0 秒:  {record: "pending", analysis: "pending", treatment: "pending"}
时间 2 秒:  {record: "generating", analysis: "pending", treatment: "pending"}
时间 5 秒:  {record: "completed", analysis: "generating", treatment: "pending"}
时间 10 秒: {record: "completed", analysis: "completed", treatment: "generating"}
时间 15 秒: {record: "completed", analysis: "completed", treatment: "completed"}
```

### 3. 查看后端日志

**预期日志**：
```
DEBUG: 结束会话，对话数量：3
DEBUG: 已启动异步报告生成任务，用户 ID: xxx, 会话 ID: xxx
DEBUG: [异步任务] 开始生成报告，用户 ID: xxx, 会话 ID: xxx
DEBUG: [异步任务] 调用记录师最终确定记录报告
DEBUG: [异步任务] 记录报告生成完成
DEBUG: [异步任务] 从 dialogues 中提取四维数据
DEBUG: [异步任务] 从实时分析数据生成分析报告
DEBUG: [异步任务] 分析报告生成完成
DEBUG: [异步任务] 调用调理师生成调理报告
DEBUG: [异步任务] 调理报告生成完成
DEBUG: [异步任务] 创建新报告，ID: xxx
DEBUG: [异步任务] 报告生成完成
```

### 4. 验证数据库状态

**SQL 查询**：
```sql
SELECT 
    session_id,
    record_report_status,
    analysis_report_status,
    treatment_report_status,
    status_updated_at,
    CASE WHEN record_report_json IS NOT NULL THEN '✓' ELSE '✗' END as has_record,
    CASE WHEN analysis_report_json IS NOT NULL THEN '✓' ELSE '✗' END as has_analysis,
    CASE WHEN treatment_report_json IS NOT NULL THEN '✓' ELSE '✗' END as has_treatment
FROM session_reports
WHERE session_id = '你的会话 ID'
ORDER BY created_at DESC;
```

**预期结果**：
- 三个状态字段都为 `'completed'`
- 三个报告 JSON 字段都不为 NULL
- `status_updated_at` 有值

## 📝 前端适配建议

### 轮询查询状态

```javascript
// 结束会话后开始轮询
function startPolling(sessionId) {
  const pollInterval = setInterval(async () => {
    const response = await fetch(`/api/v1/chat/report-status/${sessionId}`);
    const status = await response.json();
    
    // 更新 UI 显示状态
    updateStatusUI(status);
    
    // 如果三个报告都完成了，停止轮询
    if (
      status.status.record_report === 'completed' &&
      status.status.analysis_report === 'completed' &&
      status.status.treatment_report === 'completed'
    ) {
      clearInterval(pollInterval);
      // 加载完整报告
      loadFullReport(sessionId);
    }
  }, 2000); // 每 2 秒查询一次
}
```

### 状态显示 UI

```javascript
function getStatusText(status) {
  const statusMap = {
    'pending': '⏸️ 等待中',
    'generating': '⏳ 生成中...',
    'completed': '✅ 已完成',
    'failed': '❌ 失败'
  };
  return statusMap[status] || status;
}

function getStatusClass(status) {
  const classMap = {
    'pending': 'status-pending',
    'generating': 'status-generating',
    'completed': 'status-completed',
    'failed': 'status-failed'
  };
  return classMap[status] || '';
}
```

## 🎯 完整流程

```
用户点击"结束会话"
  ↓
end_session 接口立即响应（<1 秒）
{
  "message": "结束会话已完成，正在生成报告中",
  "status": {
    "record_report": "pending",
    "analysis_report": "pending",
    "treatment_report": "pending"
  }
}
  ↓
后台异步任务启动
  ↓
[异步任务] 开始生成报告
  ↓
记录报告生成中 → status = "generating"
  ↓
记录报告完成 → status = "completed"
  ↓
分析报告生成中 → status = "generating"
  ↓
分析报告完成 → status = "completed"
  ↓
调理报告生成中 → status = "generating"
  ↓
调理报告完成 → status = "completed"
  ↓
报告生成完成，前端轮询检测到全部完成
  ↓
前端加载完整报告内容
```

## ✅ 完成清单

- [x] 为 `session_reports` 表添加 4 个状态字段
- [x] 修改异步任务，在生成报告时更新状态
- [x] 新增查询报告状态接口
- [x] 数据库迁移成功执行
- [x] 代码逻辑完整

---

**完成时间**: 2026-04-01  
**下一步**: 重启后端服务并进行前端测试
