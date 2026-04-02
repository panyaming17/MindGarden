# 项目API接口详细文档

## 1. 基础信息

- **服务地址**: `http://localhost:8000`
- **API文档**: `http://localhost:8000/docs` (Swagger UI)
- **项目结构**: 模块化设计，包含记录师、分析师和调理师三个主要模块

## 2. 记录师模块 (Recorder)

### 2.1 对话接口

**路径**: `/recorder/converse`
**方法**: `POST`
**功能**: 与记录师智能体对话，支持新会话和继续会话

**请求参数**:
```json
{
  "user_input": "用户输入内容",
  "session_id": "可选，会话ID，不提供则创建新会话",
  "user_id": "可选，用户标识"
}
```

**响应格式**:
```json
{
  "session_id": "会话ID",
  "success": true,
  "message": "操作结果消息",
  "llm_response": "给用户的自然语言回应",
  "record_id": "可选，记录完成时返回的记录ID",
  "next_action": "continue_dialogue 或 trigger_analyst",
  "structured_data": "可选，结构化数据"
}
```

### 2.2 会话信息接口

**路径**: `/recorder/session/{session_id}`
**方法**: `GET`
**功能**: 获取会话状态信息（用于调试）

**响应格式**:
```json
{
  "session_id": "会话ID",
  "status": "active",
  "agent": "recorder_agent"
}
```

## 3. 分析师模块 (Analyst)

### 3.1 分析请求接口

**路径**: `/analyst/analyze`
**方法**: `POST`
**功能**: 请求分析（支持同步/异步处理）

**请求参数**:
```json
{
  "record_id": "记录ID",
  "priority": "可选，优先级：low, normal, high，默认normal",
  "callback_url": "可选，异步回调地址"
}
```

**响应格式**:
```json
{
  "request_id": "请求ID",
  "status": "状态：completed, failed, queued",
  "message": "操作结果消息",
  "report_id": "可选，分析完成时返回的报告ID",
  "estimated_completion_time": "可选，预估完成时间（秒）"
}
```

### 3.2 报告获取接口

**路径**: `/analyst/report/{report_id}`
**方法**: `GET`
**功能**: 获取分析报告

**响应格式**:
```json
{
  "report_id": "报告ID",
  "status": "available",
  "content": {
    "cbt_summary": "认知行为分析摘要",
    "tcm_summary": "中医情志分析摘要"
  }
}
```

### 3.3 性能指标接口

**路径**: `/analyst/performance`
**方法**: `GET`
**功能**: 获取分析师性能指标

**响应格式**:
```json
{
  "agent_name": "分析师智能体名称",
  "metrics": "性能指标数据",
  "timestamp": "时间戳"
}
```

## 4. 调理师模块 (Therapist)

### 4.1 生成疏导方案接口

**路径**: `/therapist/generate-plan`
**方法**: `POST`
**功能**: 根据分析报告生成疏导方案

**请求参数**:
```json
{
  "report_id": "报告ID",
  "user_preference": "可选，用户偏好：cbt_focus, tcm_focus, balanced"
}
```

**响应格式**:
```json
{
  "status": "success",
  "therapy_plan": "疏导方案内容",
  "therapist_summary": "调理师摘要信息",
  "processing_time": "处理时间（秒）",
  "report_id": "报告ID"
}
```

### 4.2 策略模板接口

**路径**: `/therapist/strategies`
**方法**: `GET`
**功能**: 获取可用的干预策略模板（用于前端展示）

**响应格式**:
```json
{
  "cbt_strategies": ["认知重构", "行为激活", "思维记录"],
  "tcm_strategies": ["情志相胜", "五行音乐", "导引按跷"],
  "integrated_approaches": ["认知-情志双通路疏导"]
}
```

## 5. 系统接口

### 5.1 根路径接口

**路径**: `/`
**方法**: `GET`
**功能**: 系统根路径，返回服务状态信息

**响应格式**:
```json
{
  "service": "analyst_module",
  "status": "active",
  "description": "双通路情绪分析服务"
}
```

### 5.2 健康检查接口

**路径**: `/health`
**方法**: `GET`
**功能**: 健康检查接口，返回服务状态和时间戳

**响应格式**:
```json
{
  "status": "healthy",
  "timestamp": "时间戳"
}
```

## 6. 接口调用流程

前端应用可以按照以下流程调用API：

1. **开始对话**: 调用 `/recorder/converse` 接口开始与记录师对话
2. **获取记录ID**: 当 `next_action` 为 `trigger_analyst` 时，获取 `record_id`
3. **请求分析**: 调用 `/analyst/analyze` 接口请求分析
4. **获取报告**: 分析完成后，调用 `/analyst/report/{report_id}` 获取分析报告
5. **生成疏导方案**: 调用 `/therapist/generate-plan` 生成疏导方案
6. **获取策略模板**: 调用 `/therapist/strategies` 获取可用的干预策略模板

## 7. 错误处理

所有API接口都可能返回以下错误格式：

```json
{
  "detail": "错误描述"
}
```

常见错误状态码：
- `400`: 请求参数错误
- `500`: 服务器内部错误

## 8. 示例代码

### 8.1 开始新会话示例

```javascript
// 开始新会话
const response = await fetch('http://localhost:8000/recorder/converse', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    user_input: '我最近感到心情低落'
  })
});

const data = await response.json();
console.log('会话ID:', data.session_id);
console.log('记录师回应:', data.llm_response);
```

### 8.2 请求分析示例

```javascript
// 请求分析
const response = await fetch('http://localhost:8000/analyst/analyze', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    record_id: '记录ID',
    priority: 'high'
  })
});

const data = await response.json();
console.log('分析请求ID:', data.request_id);
console.log('分析状态:', data.status);
console.log('报告ID:', data.report_id);
```

### 8.3 生成疏导方案示例

```javascript
// 生成疏导方案
const response = await fetch('http://localhost:8000/therapist/generate-plan', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    report_id: '报告ID',
    user_preference: 'balanced'
  })
});

const data = await response.json();
console.log('疏导方案:', data.therapy_plan);
console.log('调理师摘要:', data.therapist_summary);
```

## 9. 注意事项

1. **会话管理**: 前端需要保存会话ID以继续对话
2. **异步处理**: 对于非高优先级的分析请求，使用后台任务处理，需要通过回调或轮询获取结果
3. **错误处理**: 前端需要处理可能的错误响应
4. **参数验证**: 所有请求参数都会经过Pydantic模型验证，请确保参数格式正确
5. **数据格式**: 响应数据会按照定义的模型格式返回，请参考响应格式示例