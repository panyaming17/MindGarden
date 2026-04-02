# 对话相关API接口参数和传递信息总结

## 1. 发送消息接口

### 接口信息

- **路径**: `/api/v1/chat/message`
- **方法**: `POST`
- **响应模型**: `ChatMessageResponse`

### 请求参数

```json
{
  "user_id": "用户ID",
  "session_id": "会话ID",
  "message": "消息内容"
}
```

### 响应格式

```json
{
  "reply": "助手回复内容",
  "four_dim": {
    "intensity": 0.0,
    "hedonic": "中性",
    "tension": "低",
    "complexity": "简单"
  },
  "is_valuable": false
}
```

### 处理流程

1. 检查用户是否存在，不存在则创建新用户
2. 获取LLM服务实例
3. 调用记录师智能体处理用户消息
4. 异步触发分析师智能体（如果消息有价值）
5. 调用调理师智能体生成回复
6. 构建并返回响应

## 2. 创建新会话接口

### 接口信息

- **路径**: `/api/v1/chat/new-session`
- **方法**: `POST`
- **响应模型**: `NewSessionResponse`

### 请求参数

```json
{
  "user_id": "用户ID"
}
```

### 响应格式

```json
{
  "session_id": "会话ID",
  "message": "会话创建成功"
}
```

### 处理流程

1. 从请求体中获取user\_id
2. 检查用户是否存在
3. 创建对话会话记录
4. 构建并返回响应

## 3. 结束会话接口

### 接口信息

- **路径**: `/api/v1/chat/end-session`
- **方法**: `POST`
- **响应**: 自定义响应

### 请求参数

```json
{
  "user_id": "用户ID",
  "session_id": "会话ID"
}
```

### 响应格式

成功时：

```json
{
  "message": "会话已结束，报告已生成",
  "session_id": "会话ID",
  "report_id": "报告ID",
  "reports": {
    "record_report": {...},  // 记录报告
    "analysis_report": {...},  // 分析报告
    "treatment_report": {...}  // 调理报告
  }
}
```

失败时：

```json
{
  "message": "会话已结束，但报告生成失败",
  "session_id": "会话ID",
  "error": "错误信息"
}
```

### 处理流程

1. 从请求体中获取user\_id和session\_id
2. 检查用户和会话是否存在
3. 获取会话的对话记录、用户认知档案和分析师建议
4. 调用三个智能体生成报告
5. 保存报告到数据库
6. 构建并返回响应

## 4. 获取用户会话列表接口

### 接口信息

- **路径**: `/api/v1/chat/sessions`
- **方法**: `POST`
- **响应模型**: `SessionList`

### 请求参数

```json
{
  "user_id": "用户ID"
}
```

### 响应格式

```json
{
  "sessions": [
    {
      "session_id": "会话ID",
      "title": "会话标题",
      "last_message": "最后一条消息",
      "created_at": "创建时间",
      "thinking_traps": ["思维陷阱1", "思维陷阱2"],
      "emotional_response": "情绪反应"
    }
  ]
}
```

### 处理流程

1. 从请求体中获取user\_id
2. 检查用户是否存在
3. 从UserArchiveDB中获取用户的所有会话
4. 构建会话列表，包含会话信息、最后一条消息、思维陷阱和情绪反应
5. 按创建时间降序排序
6. 构建并返回响应

## 5. 获取会话对话记录接口

### 接口信息

- **路径**: `/api/v1/chat/history`
- **方法**: `POST`
- **响应模型**: `ChatHistoryResponse`

### 请求参数

```json
{
  "user_id": "用户ID",
  "session_id": "会话ID",
  "limit": 50  // 可选，默认50，最大100
}
```

### 响应格式

```json
{
  "dialogues": [
    {
      "id": "对话ID",
      "user_id": "用户ID",
      "session_id": "会话ID",
      "role": "user或assistant",
      "content": "对话内容",
      "four_dim_intensity": 0.0,
      "four_dim_hedonic": "中性",
      "four_dim_tension": "低",
      "four_dim_complexity": "简单",
      "is_valuable": false,
      "created_at": "创建时间"
    }
  ]
}
```

### 处理流程

1. 从请求体中获取user\_id、session\_id和limit参数
2. 检查参数是否完整
3. 查询对话记录
4. 转换为响应模型
5. 构建并返回响应

## 6. 编辑会话标题接口

### 接口信息

- **路径**: `/api/v1/chat/edit-session-title  这个接口不实现，可以忽略`
- **方法**: `POST`
- **响应**: 自定义响应

### 请求参数

```json
{
  "user_id": "用户ID",
  "session_id": "会话ID",
  "title": "新标题"
}
```

### 响应格式

```json
{
  "message": "会话标题更新成功",
  "session_id": "会话ID",
  "new_title": "新标题"
}
```

### 处理流程

1. 从请求体中获取user\_id、session\_id和new\_title
2. 检查参数是否完整
3. 检查用户和会话是否存在
4. 更新会话标题
5. 同时更新用户认知档案中的标题（如果存在）
6. 构建并返回响应

## 7. 删除会话接口

### 接口信息

- **路径**: `/api/v1/chat/delete-session`
- **方法**: `POST`
- **响应**: 自定义响应

### 请求参数

```json
{
  "user_id": "用户ID",
  "session_id": "会话ID"
}
```

### 响应格式

```json
{
  "message": "会话删除成功",
  "session_id": "会话ID"
}
```

### 处理流程

1. 从请求体中获取user\_id和session\_id
2. 检查参数是否完整
3. 检查用户和会话是否存在，且会话属于该用户
4. 删除关联的建议记录、用户认知档案、会话报告和对话记录
5. 删除会话本身
6. 构建并返回响应

## 数据传递说明

### 1. 用户认证

- 所有接口都需要传递user\_id参数
- 接口会检查用户是否存在，不存在则创建新用户

### 2. 会话管理

- 创建会话时生成唯一的session\_id
- 所有会话相关操作都需要传递session\_id
- 会话删除会级联删除相关数据

### 3. 智能体调用

- 记录师智能体：处理用户消息，进行情绪分析
- 分析师智能体：对有价值的消息进行深度分析
- 调理师智能体：生成助手回复

### 4. 报告生成

- 结束会话时会调用三个智能体生成报告
- 报告包括记录报告、分析报告和调理报告
- 报告会保存到数据库中

### 5. 错误处理

- 参数缺失：返回422 Unprocessable Content
- 用户不存在：返回404 Not Found
- 会话不存在：返回404 Not Found
- 服务器内部错误：返回500 Internal Server Error

## 注意事项

1. 所有API接口都使用POST方法
2. 所有请求参数都通过JSON请求体传递
3. 响应格式统一为JSON格式
4. 接口会自动处理用户创建和会话管理
5. 智能体会自动处理消息分析和回复生成

