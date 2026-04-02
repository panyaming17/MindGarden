# 前端适配指南 - 异步报告生成

## 📋 概述

由于后端实现了**增量保存 + 异步报告生成**机制，前端需要相应调整以提供更好的用户体验。

### 核心变化

**原来的流程**：
```
结束会话 → 等待所有报告生成（30-60 秒） → 一次性显示所有报告
```

**现在的流程**：
```
结束会话 → 立即返回 → 记录报告立即显示 → 分析报告稍后显示 → 调理报告稍后显示
```

---

## 🔧 必须完成的前端改动

### 1. 修改结束会话调用方式

#### 当前代码（同步模式）
```javascript
async function endSession(sessionId) {
  const response = await fetch('/api/v1/chat/end-session', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ 
      user_id: userId, 
      session_id: sessionId 
    })
  });
  
  const result = await response.json();
  
  // 等待所有报告生成完成才显示
  console.log('报告已生成:', result.reports);
  showReports(result.reports);
}
```

#### 修改后（异步模式）
```javascript
async function endSession(sessionId) {
  const response = await fetch('/api/v1/chat/end-session', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ 
      user_id: userId, 
      session_id: sessionId 
    })
  });
  
  const result = await response.json();
  
  // 立即返回，显示"报告生成中"状态
  console.log('报告正在生成:', result);
  
  // 显示状态面板
  showGeneratingStatus(result);
  
  // 启动轮询查询报告状态
  startPollingReportStatus(result.report_id);
}
```

---

### 2. 添加轮询查询函数

```javascript
// 全局轮询定时器
let pollingTimer = null;
let pollingTimeout = null;

/**
 * 启动轮询查询报告状态
 * @param {number} reportId - 报告 ID
 */
function startPollingReportStatus(reportId) {
  // 显示加载状态
  showLoadingSpinner('报告正在生成中，请稍候...');
  
  // 立即查询一次
  queryReportStatus(reportId);
  
  // 每 3 秒查询一次
  pollingTimer = setInterval(() => {
    queryReportStatus(reportId);
  }, 3000);
  
  // 最多轮询 5 分钟（100 次）
  pollingTimeout = setTimeout(() => {
    if (pollingTimer) {
      clearInterval(pollingTimer);
      pollingTimer = null;
    }
    hideLoadingSpinner();
    showTimeoutMessage('报告生成超时，请稍后查看');
  }, 5 * 60 * 1000); // 5 分钟
}

/**
 * 查询报告状态
 * @param {number} reportId - 报告 ID
 */
async function queryReportStatus(reportId) {
  try {
    const response = await fetch(`/api/v1/report/session/${reportId}/status`);
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const status = await response.json();
    console.log('报告状态:', status);
    
    // 更新 UI 显示状态
    updateReportStatusUI(status);
    
    // 检查是否全部完成
    if (isAllReportsCompleted(status)) {
      stopPolling();
      hideLoadingSpinner();
      showCompleteReports(status.data);
      return;
    }
    
    // 检查是否有失败
    if (isAnyReportFailed(status)) {
      stopPolling();
      hideLoadingSpinner();
      showPartialReports(status.data, status.status);
      return;
    }
    
  } catch (error) {
    console.error('查询报告状态失败:', error);
  }
}

/**
 * 停止轮询
 */
function stopPolling() {
  if (pollingTimer) {
    clearInterval(pollingTimer);
    pollingTimer = null;
  }
  if (pollingTimeout) {
    clearTimeout(pollingTimeout);
    pollingTimeout = null;
  }
}

/**
 * 检查是否全部完成
 */
function isAllReportsCompleted(status) {
  return status.status.record_report === 'completed' &&
         status.status.analysis_report === 'completed' &&
         status.status.treatment_report === 'completed';
}

/**
 * 检查是否有失败
 */
function isAnyReportFailed(status) {
  return status.status.analysis_report === 'failed' ||
         status.status.treatment_report === 'failed';
}
```

---

### 3. 更新 UI 显示函数

```javascript
/**
 * 显示报告生成中状态
 */
function showGeneratingStatus(result) {
  const statusPanel = document.getElementById('report-status-panel');
  if (statusPanel) {
    statusPanel.style.display = 'block';
  }
  
  // 隐藏报告内容区域，等待数据
  const reportContent = document.getElementById('report-content');
  if (reportContent) {
    reportContent.style.display = 'none';
  }
}

/**
 * 更新报告状态 UI
 */
function updateReportStatusUI(status) {
  // 更新记录报告状态
  const recordStatus = document.getElementById('record-report-status');
  if (recordStatus) {
    recordStatus.className = `status-badge status-${status.status.record_report}`;
    recordStatus.textContent = getStatusText(status.status.record_report);
  }
  
  // 更新分析报告状态
  const analysisStatus = document.getElementById('analysis-report-status');
  if (analysisStatus) {
    analysisStatus.className = `status-badge status-${status.status.analysis_report}`;
    let text = getStatusText(status.status.analysis_report);
    
    // 显示重试次数
    if (status.retry_counts?.analysis > 0) {
      text += ` (重试${status.retry_counts.analysis}次)`;
    }
    analysisStatus.textContent = text;
  }
  
  // 更新调理报告状态
  const treatmentStatus = document.getElementById('treatment-report-status');
  if (treatmentStatus) {
    treatmentStatus.className = `status-badge status-${status.status.treatment_report}`;
    let text = getStatusText(status.status.treatment_report);
    
    // 显示重试次数
    if (status.retry_counts?.treatment > 0) {
      text += ` (重试${status.retry_counts.treatment}次)`;
    }
    treatmentStatus.textContent = text;
  }
}

/**
 * 获取状态文本
 */
function getStatusText(status) {
  const statusMap = {
    'completed': '✅ 已完成',
    'generating': '⏳ 生成中...',
    'pending': '⏸️ 等待中',
    'failed': '❌ 失败'
  };
  return statusMap[status] || status;
}

/**
 * 显示加载动画
 */
function showLoadingSpinner(message) {
  const spinner = document.getElementById('loading-spinner');
  if (spinner) {
    spinner.style.display = 'block';
    const messageEl = spinner.querySelector('p');
    if (messageEl) {
      messageEl.textContent = message;
    }
  }
}

/**
 * 隐藏加载动画
 */
function hideLoadingSpinner() {
  const spinner = document.getElementById('loading-spinner');
  if (spinner) {
    spinner.style.display = 'none';
  }
}

/**
 * 显示完整报告
 */
function showCompleteReports(reports) {
  // 隐藏状态面板
  const statusPanel = document.getElementById('report-status-panel');
  if (statusPanel) {
    statusPanel.style.display = 'none';
  }
  
  // 显示报告内容区域
  const reportContent = document.getElementById('report-content');
  if (reportContent) {
    reportContent.style.display = 'block';
  }
  
  // 显示记录报告
  if (reports.record_report) {
    renderRecordReport(reports.record_report);
  }
  
  // 显示分析报告
  if (reports.analysis_report) {
    renderAnalysisReport(reports.analysis_report);
  }
  
  // 显示调理报告
  if (reports.treatment_report) {
    renderTreatmentReport(reports.treatment_report);
  }
  
  // 显示成功提示
  showMessage('报告生成完成！', 'success');
}

/**
 * 显示部分报告（有失败）
 */
function showPartialReports(reports, status) {
  // 隐藏状态面板
  const statusPanel = document.getElementById('report-status-panel');
  if (statusPanel) {
    statusPanel.style.display = 'none';
  }
  
  // 显示报告内容区域
  const reportContent = document.getElementById('report-content');
  if (reportContent) {
    reportContent.style.display = 'block';
  }
  
  // 显示成功的报告
  if (status.record_report === 'completed' && reports.record_report) {
    renderRecordReport(reports.record_report);
  }
  
  if (status.analysis_report === 'completed' && reports.analysis_report) {
    renderAnalysisReport(reports.analysis_report);
  }
  
  if (status.treatment_report === 'completed' && reports.treatment_report) {
    renderTreatmentReport(reports.treatment_report);
  }
  
  // 显示失败提示
  if (status.analysis_report === 'failed') {
    showErrorMessage('分析报告生成失败，请稍后重试');
  }
  
  if (status.treatment_report === 'failed') {
    showErrorMessage('调理报告生成失败，请稍后重试');
  }
}

/**
 * 显示报告内容（示例函数）
 */
function renderRecordReport(report) {
  const section = document.getElementById('record-report-section');
  const body = section?.querySelector('.report-body');
  if (body) {
    section.style.display = 'block';
    body.innerHTML = JSON.stringify(report, null, 2);
    // 或者使用更美观的渲染方式
  }
}

function renderAnalysisReport(report) {
  const section = document.getElementById('analysis-report-section');
  const body = section?.querySelector('.report-body');
  if (body) {
    section.style.display = 'block';
    body.innerHTML = JSON.stringify(report, null, 2);
  }
}

function renderTreatmentReport(report) {
  const section = document.getElementById('treatment-report-section');
  const body = section?.querySelector('.report-body');
  if (body) {
    section.style.display = 'block';
    body.innerHTML = JSON.stringify(report, null, 2);
  }
}

/**
 * 显示消息提示
 */
function showMessage(message, type = 'info') {
  // 实现消息提示逻辑（toast、notification 等）
  console.log(`[${type.toUpperCase()}] ${message}`);
}

/**
 * 显示错误提示
 */
function showErrorMessage(message) {
  showMessage(message, 'error');
}

/**
 * 显示超时提示
 */
function showTimeoutMessage(message) {
  showErrorMessage(message);
  // 可以提供手动刷新按钮
}
```

---

### 4. 添加 HTML 模板

```html
<!-- 报告生成状态面板 -->
<div id="report-status-panel" class="status-panel" style="display: none;">
  <h3>📊 报告生成状态</h3>
  
  <div class="status-item">
    <span class="status-label">📝 记录报告:</span>
    <span id="record-report-status" class="status-badge status-completed">
      ✅ 已完成
    </span>
  </div>
  
  <div class="status-item">
    <span class="status-label">📈 分析报告:</span>
    <span id="analysis-report-status" class="status-badge status-generating">
      ⏳ 生成中...
    </span>
  </div>
  
  <div class="status-item">
    <span class="status-label">💊 调理报告:</span>
    <span id="treatment-report-status" class="status-badge status-pending">
      ⏸️ 等待中
    </span>
  </div>
  
  <!-- 加载动画 -->
  <div id="loading-spinner" class="loading-spinner">
    <div class="spinner"></div>
    <p>报告正在生成中，请稍候...</p>
  </div>
</div>

<!-- 报告内容区域 -->
<div id="report-content" class="report-content">
  <!-- 记录报告 -->
  <div id="record-report-section" class="report-section" style="display: none;">
    <h3>📝 记录报告</h3>
    <div class="report-body"></div>
  </div>
  
  <!-- 分析报告 -->
  <div id="analysis-report-section" class="report-section" style="display: none;">
    <h3>📈 分析报告</h3>
    <div class="report-body"></div>
  </div>
  
  <!-- 调理报告 -->
  <div id="treatment-report-section" class="report-section" style="display: none;">
    <h3>💊 调理报告</h3>
    <div class="report-body"></div>
  </div>
</div>
```

---

### 5. 添加 CSS 样式

```css
/* ========== 状态面板样式 ========== */
.status-panel {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 25px;
  border-radius: 12px;
  margin: 20px 0;
  color: white;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.status-panel h3 {
  margin: 0 0 20px 0;
  font-size: 20px;
  font-weight: 600;
}

.status-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.2);
}

.status-item:last-child {
  border-bottom: none;
}

.status-label {
  font-size: 16px;
  font-weight: 500;
}

/* ========== 状态徽章样式 ========== */
.status-badge {
  padding: 6px 16px;
  border-radius: 20px;
  font-size: 14px;
  font-weight: 600;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  transition: all 0.3s ease;
}

.status-completed {
  background: rgba(76, 175, 80, 0.9);
  color: white;
}

.status-generating {
  background: rgba(33, 150, 243, 0.9);
  color: white;
  animation: pulse 1.5s ease-in-out infinite;
}

.status-pending {
  background: rgba(255, 152, 0, 0.9);
  color: white;
}

.status-failed {
  background: rgba(244, 67, 54, 0.9);
  color: white;
}

/* ========== 加载动画样式 ========== */
.loading-spinner {
  text-align: center;
  padding: 30px 20px;
}

.loading-spinner p {
  margin-top: 15px;
  font-size: 16px;
  color: #666;
}

.spinner {
  border: 4px solid #f3f3f3;
  border-top: 4px solid #667eea;
  border-radius: 50%;
  width: 50px;
  height: 50px;
  animation: spin 1s linear infinite;
  margin: 0 auto;
}

@keyframes pulse {
  0%, 100% { 
    opacity: 1;
    transform: scale(1);
  }
  50% { 
    opacity: 0.6;
    transform: scale(1.05);
  }
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

/* ========== 报告内容区域样式 ========== */
.report-content {
  margin-top: 30px;
}

.report-section {
  margin: 20px 0;
  padding: 25px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
}

.report-section:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.report-section h3 {
  margin: 0 0 20px 0;
  color: #333;
  font-size: 18px;
  font-weight: 600;
  border-bottom: 2px solid #667eea;
  padding-bottom: 10px;
}

.report-body {
  line-height: 1.6;
  color: #555;
}

/* ========== 响应式设计 ========== */
@media (max-width: 768px) {
  .status-panel {
    padding: 20px 15px;
  }
  
  .status-item {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }
  
  .status-badge {
    width: 100%;
    justify-content: center;
  }
  
  .report-section {
    padding: 20px 15px;
  }
}
```

---

## 🚀 可选的高级功能

### 1. WebSocket 实时推送（推荐）

#### 后端支持
```python
# backend/main.py
from fastapi import WebSocket

@app.websocket("/ws/report-status/{report_id}")
async def websocket_report_status(websocket: WebSocket, report_id: int):
    await websocket.accept()
    
    while True:
        # 查询报告状态
        status = get_report_status_from_db(report_id)
        await websocket.send_json(status)
        
        if is_all_completed(status):
            await websocket.send_json({"type": "completed"})
            break
        
        await asyncio.sleep(2)
```

#### 前端使用
```javascript
/**
 * 使用 WebSocket 监听报告状态
 */
function watchReportStatusViaWebSocket(reportId) {
  const ws = new WebSocket(`ws://localhost:8000/ws/report-status/${reportId}`);
  
  ws.onopen = () => {
    console.log('WebSocket 连接已建立');
  };
  
  ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    
    if (data.type === 'completed') {
      ws.close();
      return;
    }
    
    updateReportStatusUI(data);
    
    if (isAllReportsCompleted(data)) {
      showCompleteReports(data.data);
      ws.close();
    }
  };
  
  ws.onerror = (error) => {
    console.error('WebSocket 错误:', error);
    // 降级到轮询
    startPollingReportStatus(reportId);
  };
  
  ws.onclose = () => {
    console.log('WebSocket 连接已关闭');
  };
}
```

---

### 2. 手动重试功能

```javascript
/**
 * 手动重试生成失败的报告
 */
async function retryFailedReport(reportId, reportType) {
  try {
    const response = await fetch(`/api/v1/report/${reportId}/retry`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ report_type: reportType })
    });
    
    if (response.ok) {
      showMessage('重试已启动', 'success');
      startPollingReportStatus(reportId);
    } else {
      throw new Error('重试失败');
    }
  } catch (error) {
    showErrorMessage('重试失败：' + error.message);
  }
}
```

HTML 按钮：
```html
<button onclick="retryFailedReport(reportId, 'analysis')">
  重试分析报告
</button>
<button onclick="retryFailedReport(reportId, 'treatment')">
  重试调理报告
</button>
```

---

### 3. 进度条显示

```javascript
/**
 * 显示生成进度条
 */
function updateProgress(status) {
  const total = 3; // 3 个报告
  let completed = 0;
  
  if (status.status.record_report === 'completed') completed++;
  if (status.status.analysis_report === 'completed') completed++;
  if (status.status.treatment_report === 'completed') completed++;
  
  const progress = (completed / total) * 100;
  
  const progressBar = document.getElementById('progress-bar');
  if (progressBar) {
    progressBar.style.width = `${progress}%`;
    progressBar.textContent = `${Math.round(progress)}%`;
  }
}
```

HTML：
```html
<div class="progress-container">
  <div id="progress-bar" class="progress-bar" style="width: 0%;">0%</div>
</div>
```

---

## 📊 API 接口说明

### 1. 结束会话接口

**请求**：
```http
POST /api/v1/chat/end-session
Content-Type: application/json

{
  "user_id": "user_123",
  "session_id": "session_abc"
}
```

**响应**：
```json
{
  "message": "会话已结束，报告正在生成中",
  "session_id": "session_abc",
  "report_id": 123,
  "status": {
    "record_report": "completed",
    "analysis_report": "generating",
    "treatment_report": "pending"
  },
  "data": {
    "record_report": { ... },
    "analysis_report": null,
    "treatment_report": null
  }
}
```

---

### 2. 查询报告状态接口

**请求**：
```http
GET /api/v1/report/session/{session_id}/status
```

**响应**：
```json
{
  "report_id": 123,
  "session_id": "session_abc",
  "status": {
    "record_report": "completed",
    "analysis_report": "generating",
    "treatment_report": "pending"
  },
  "retry_counts": {
    "analysis": 1,
    "treatment": 0
  },
  "data": {
    "record_report": { ... },
    "analysis_report": null,
    "treatment_report": null
  },
  "created_at": "2026-03-31T14:28:27.862132",
  "updated_at": "2026-03-31T14:30:17.531172"
}
```

---

## ✅ 测试清单

完成前端适配后，请测试以下场景：

- [ ] 结束会话后立即显示"生成中"状态
- [ ] 记录报告立即显示
- [ ] 分析报告生成完成后自动显示
- [ ] 调理报告生成完成后自动显示
- [ ] 轮询在全部完成后停止
- [ ] 5 分钟超时后显示提示
- [ ] 报告生成失败时显示错误信息
- [ ] 页面刷新后能继续查看报告
- [ ] 移动端响应式显示正常

---

## 🎯 用户体验流程

```
1. 用户点击"结束会话"
   ↓
2. 显示状态面板："报告正在生成中"
   ↓
3. 记录报告立即显示（✅ 已完成）
   ↓
4. 分析报告生成中...（⏳ 2-5 秒）
   ↓
5. 分析报告显示（✅ 已完成）
   ↓
6. 调理报告生成中...（⏳ 2-5 秒）
   ↓
7. 调理报告显示（✅ 已完成）
   ↓
8. 隐藏状态面板，显示完整报告
```

---

## 📝 总结

### 必须完成
1. ✅ 修改结束会话调用方式
2. ✅ 添加轮询查询函数
3. ✅ 更新 UI 显示状态
4. ✅ 添加状态查询接口

### 推荐完成
- ⭐ WebSocket 实时推送
- ⭐ 手动重试功能
- ⭐ 进度条显示

### 好处
- ✅ 用户不再需要等待 30-60 秒
- ✅ 实时看到生成进度
- ✅ 即使部分失败也能看到已完成的报告
- ✅ 更好的用户体验

---

**文档版本**: v1.0  
**更新日期**: 2026-03-31  
**适用后端版本**: 异步报告生成机制（方案 A）
