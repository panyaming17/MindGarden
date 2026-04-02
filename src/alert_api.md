# 预警提醒功能 - 后端API接口文档

## 概述

本文档描述了预警提醒功能所需的后端API接口，包括RESTful API和WebSocket实时推送。

---

## 一、RESTful API 接口

### 1. 获取预警列表

**接口地址**: `GET /api/alerts`

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| user_id | string | 是 | 用户ID |
| type | string | 否 | 预警类型筛选：questionnaire/emotion/conversation |
| level | string | 否 | 预警等级筛选：info/warning/danger |
| status | string | 否 | 状态筛选：acknowledged/unacknowledged |
| start_date | string | 否 | 开始日期，格式：YYYY-MM-DD |
| end_date | string | 否 | 结束日期，格式：YYYY-MM-DD |
| page | number | 否 | 页码，默认1 |
| page_size | number | 否 | 每页数量，默认20 |

**响应示例**:

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "total": 45,
    "page": 1,
    "page_size": 20,
    "alerts": [
      {
        "id": "alert_001",
        "type": "questionnaire",
        "level": "warning",
        "title": "PHQ-9评分异常",
        "message": "您的PHQ-9评分为15分，显示中度抑郁倾向，建议关注心理健康状况",
        "source_data": {
          "template_code": "PHQ9",
          "template_name": "PHQ-9抑郁量表",
          "score": 15,
          "result": "中度抑郁",
          "result_level": "moderate",
          "date": "2026-03-30",
          "record_id": "record_001"
        },
        "is_acknowledged": false,
        "created_at": "2026-03-30T10:30:00",
        "acknowledged_at": null,
        "acknowledged_by": null
      },
      {
        "id": "alert_002",
        "type": "emotion",
        "level": "danger",
        "title": "连续负面情绪预警",
        "message": "您已连续7天记录负面情绪，系统检测到情绪状态异常",
        "source_data": {
          "consecutive_days": 7,
          "emotion_records": [
            {"date": "2026-03-24", "emotion": "难过", "intensity": 8},
            {"date": "2026-03-25", "emotion": "焦虑", "intensity": 7},
            {"date": "2026-03-26", "emotion": "疲惫", "intensity": 6},
            {"date": "2026-03-27", "emotion": "担忧", "intensity": 8},
            {"date": "2026-03-28", "emotion": "焦虑", "intensity": 9},
            {"date": "2026-03-29", "emotion": "难过", "intensity": 7},
            {"date": "2026-03-30", "emotion": "愤怒", "intensity": 8}
          ],
          "summary": "连续一周负面情绪，焦虑情绪占主导"
        },
        "is_acknowledged": false,
        "created_at": "2026-03-30T08:00:00",
        "acknowledged_at": null,
        "acknowledged_by": null
      },
      {
        "id": "alert_003",
        "type": "conversation",
        "level": "danger",
        "title": "对话危机信号检测",
        "message": "AI检测到对话内容中存在潜在危机信号词汇，需要特别关注",
        "source_data": {
          "session_id": "session_001",
          "preview": "用户：我觉得活着没什么意义了...",
          "emotion_intensity": 0.92,
          "crisis_detected": true,
          "crisis_keywords": ["活着没意义", "想结束", "不想活"],
          "risk_level": "high"
        },
        "is_acknowledged": true,
        "created_at": "2026-03-29T15:20:00",
        "acknowledged_at": "2026-03-29T16:00:00",
        "acknowledged_by": "admin_001"
      }
    ]
  }
}
```

---

### 2. 确认预警

**接口地址**: `POST /api/alerts/{alert_id}/acknowledge`

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| alert_id | string | 是 | 预警ID（路径参数） |
| user_id | string | 是 | 确认人ID（请求体） |
| notes | string | 否 | 处理备注（请求体） |

**请求示例**:

```json
{
  "user_id": "user_001",
  "notes": "已联系用户进行心理疏导"
}
```

**响应示例**:

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": "alert_001",
    "is_acknowledged": true,
    "acknowledged_at": "2026-03-30T14:30:00",
    "acknowledged_by": "user_001"
  }
}
```

---

### 3. 批量确认预警

**接口地址**: `POST /api/alerts/batch/acknowledge`

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| alert_ids | array | 是 | 预警ID列表 |
| user_id | string | 是 | 确认人ID |

**请求示例**:

```json
{
  "alert_ids": ["alert_001", "alert_002", "alert_003"],
  "user_id": "user_001"
}
```

**响应示例**:

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "success_count": 3,
    "failed_count": 0,
    "failed_ids": []
  }
}
```

---

### 4. 获取预警统计

**接口地址**: `GET /api/alerts/stats`

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| user_id | string | 是 | 用户ID |
| start_date | string | 否 | 开始日期 |
| end_date | string | 否 | 结束日期 |

**响应示例**:

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "total": 45,
    "unacknowledged": 8,
    "acknowledged": 37,
    "by_type": {
      "questionnaire": 15,
      "emotion": 20,
      "conversation": 10
    },
    "by_level": {
      "info": 20,
      "warning": 18,
      "danger": 7
    },
    "by_date": {
      "2026-03-28": 3,
      "2026-03-29": 5,
      "2026-03-30": 2
    }
  }
}
```

---

## 二、WebSocket 实时推送

### 连接地址

```
ws://localhost:8000/ws/alerts/{user_id}
```

### 连接说明

1. 建立WebSocket连接时需要携带用户认证token
2. 连接成功后，服务端会推送该用户的新预警消息
3. 断线后需要客户端自动重连

### 消息格式

WebSocket支持多种消息类型，前端会根据不同类型进行增量更新：

#### 1. 新增预警 - `new_alert`

当有新预警产生时推送，前端会增量添加到列表头部。

```json
{
  "type": "new_alert",
  "timestamp": "2026-03-30T16:45:00",
  "data": {
    "id": "alert_004",
    "type": "questionnaire",
    "level": "danger",
    "title": "GAD-7评分严重异常",
    "message": "您的GAD-7评分为19分，显示重度焦虑倾向，建议尽快寻求专业帮助",
    "source_data": {
      "template_code": "GAD7",
      "template_name": "GAD-7焦虑量表",
      "score": 19,
      "result": "重度焦虑",
      "result_level": "severe",
      "date": "2026-03-30",
      "record_id": "record_002"
    },
    "is_acknowledged": false,
    "created_at": "2026-03-30T16:45:00"
  }
}
```

#### 2. 更新预警 - `update_alert`

当预警状态发生变化时推送（如被其他设备确认），前端会更新对应预警。

```json
{
  "type": "update_alert",
  "timestamp": "2026-03-30T16:50:00",
  "data": {
    "id": "alert_004",
    "is_acknowledged": true,
    "acknowledged_at": "2026-03-30T16:50:00",
    "acknowledged_by": "admin_001"
  }
}
```

#### 3. 删除预警 - `delete_alert`

当预警被删除时推送，前端会从列表中移除。

```json
{
  "type": "delete_alert",
  "timestamp": "2026-03-30T17:00:00",
  "data": {
    "id": "alert_004"
  }
}
```

#### 4. 批量更新 - `batch_update`

当需要全量刷新数据时推送（如同步操作），前端会智能合并数据，保留本地确认状态。

```json
{
  "type": "batch_update",
  "timestamp": "2026-03-30T17:00:00",
  "data": {
    "alerts": [
      {
        "id": "alert_001",
        "type": "questionnaire",
        "level": "warning",
        "title": "PHQ-9评分异常",
        "message": "您的PHQ-9评分为15分，显示中度抑郁倾向",
        "is_acknowledged": false,
        "created_at": "2026-03-30T10:30:00"
      }
      // ... 其他预警
    ]
  }
}
```

#### 5. 连接成功 - `connected`

```json
{
  "type": "connected",
  "timestamp": "2026-03-30T16:00:00",
  "message": "WebSocket连接成功"
}
```

#### 6. 心跳 - `ping`

```json
{
  "type": "ping",
  "timestamp": "2026-03-30T16:01:00"
}
```

### 客户端响应

收到心跳后，客户端应发送pong响应：

```json
{
  "type": "pong",
  "timestamp": "2026-03-30T16:01:00"
}
```

---

## 三、预警触发规则

### 1. 问卷测评预警规则

| 问卷类型 | 触发条件 | 预警等级 | 预警标题 | 预警内容模板 |
|----------|----------|----------|----------|--------------|
| PHQ-9 | score >= 20 | danger | PHQ-9评分严重异常 | 您的PHQ-9评分为{score}分，显示重度抑郁倾向，建议尽快寻求专业帮助 |
| PHQ-9 | score >= 15 | warning | PHQ-9评分异常 | 您的PHQ-9评分为{score}分，显示中度抑郁倾向，建议关注心理健康状况 |
| PHQ-9 | score >= 10 | info | PHQ-9评分提示 | 您的PHQ-9评分为{score}分，显示轻度抑郁倾向，建议适当调节情绪 |
| GAD-7 | score >= 15 | danger | GAD-7评分严重异常 | 您的GAD-7评分为{score}分，显示重度焦虑倾向，建议尽快寻求专业帮助 |
| GAD-7 | score >= 10 | warning | GAD-7评分异常 | 您的GAD-7评分为{score}分，显示中度焦虑倾向，建议关注心理健康状况 |
| GAD-7 | score >= 5 | info | GAD-7评分提示 | 您的GAD-7评分为{score}分，显示轻度焦虑倾向，建议适当放松身心 |

### 2. 情绪记录预警规则

| 触发条件 | 预警等级 | 预警标题 | 预警内容模板 |
|----------|----------|----------|--------------|
| 连续7天负面情绪 | danger | 连续负面情绪预警 | 您已连续7天记录负面情绪，系统检测到情绪状态异常 |
| 连续3天负面情绪 | warning | 连续负面情绪提醒 | 您已连续3天记录负面情绪，建议关注情绪变化 |
| 单日情绪强度 >= 8 | warning | 高强度情绪预警 | 您今日记录的{emotion}情绪强度较高，建议适当调节 |
| 一周内负面情绪 >= 5天 | info | 负面情绪趋势提醒 | 本周负面情绪占比较高，建议关注心理健康 |

**负面情绪定义**: 难过、焦虑、愤怒、担忧、疲惫、孤独

### 3. 对话内容预警规则

| 触发条件 | 预警等级 | 预警标题 | 预警内容模板 |
|----------|----------|----------|--------------|
| 检测到危机关键词 | danger | 对话危机信号检测 | AI检测到对话内容中存在潜在危机信号词汇，需要特别关注 |
| 情绪强度 >= 0.85 | warning | 对话情绪异常 | AI检测到对话中情绪强度异常，建议关注用户状态 |
| 连续3轮负面情绪 | info | 对话情绪趋势提醒 | 对话中连续多轮检测到负面情绪 |

**危机关键词列表**:
- 自杀相关：自杀、想死、不想活、结束生命、了结
- 自伤相关：自残、割腕、伤害自己
- 绝望相关：活着没意义、绝望、没希望、撑不下去
- 极端情绪：受不了、崩溃、疯了、控制不住

---

## 四、数据库表结构

### alerts 表

| 字段名 | 类型 | 说明 |
|--------|------|------|
| id | VARCHAR(64) | 主键，预警ID |
| user_id | VARCHAR(64) | 用户ID，索引 |
| type | ENUM | 预警类型：questionnaire/emotion/conversation |
| level | ENUM | 预警等级：info/warning/danger |
| title | VARCHAR(255) | 预警标题 |
| message | TEXT | 预警内容 |
| source_data | JSON | 关联数据 |
| is_acknowledged | BOOLEAN | 是否已确认，默认false |
| acknowledged_at | DATETIME | 确认时间 |
| acknowledged_by | VARCHAR(64) | 确认人ID |
| created_at | DATETIME | 创建时间，索引 |
| updated_at | DATETIME | 更新时间 |

### alert_rules 表（可选，用于动态配置规则）

| 字段名 | 类型 | 说明 |
|--------|------|------|
| id | VARCHAR(64) | 主键 |
| type | VARCHAR(32) | 规则类型 |
| name | VARCHAR(128) | 规则名称 |
| condition | TEXT | 触发条件（JSON格式） |
| level | ENUM | 预警等级 |
| title_template | VARCHAR(255) | 标题模板 |
| message_template | TEXT | 内容模板 |
| is_active | BOOLEAN | 是否启用 |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 更新时间 |

---

## 五、实现建议

### 1. 预警生成时机

- **问卷预警**: 用户提交问卷后，根据评分立即生成
- **情绪预警**: 
  - 用户记录情绪后，检查当日情绪强度
  - 每日定时任务检查连续负面情绪
- **对话预警**: 
  - 实时分析对话内容（使用AI情感分析）
  - 检测到危机信号立即生成

### 2. 性能优化

- 对 `user_id` 和 `created_at` 字段建立联合索引
- 预警列表查询支持分页，避免大数据量查询
- WebSocket连接使用连接池管理
- 定期清理已确认的历史预警数据（如3个月前）

### 3. 安全性考虑

- 所有API接口需要JWT认证
- WebSocket连接需要验证token
- 用户只能查看自己的预警数据
- 敏感预警（danger级别）建议发送邮件/短信通知

### 4. 监控告警

- 监控WebSocket连接数
- 监控预警生成频率
- 对danger级别预警进行日志记录
- 设置异常预警阈值（如某用户短时间内大量预警）

---

## 六、后端实现逻辑

### 1. 预警生成逻辑

#### 1.1 问卷测评预警生成

```python
# 在用户提交问卷后调用
async def create_questionnaire_alert(user_id: str, template_code: str, score: int, record_id: str):
    """
    根据问卷评分创建预警
    """
    alert_config = {
        "PHQ9": [
            {"min_score": 20, "level": "danger", "title": "PHQ-9评分严重异常", 
             "message": "您的PHQ-9评分为{score}分，显示重度抑郁倾向，建议尽快寻求专业帮助"},
            {"min_score": 15, "level": "warning", "title": "PHQ-9评分异常", 
             "message": "您的PHQ-9评分为{score}分，显示中度抑郁倾向，建议关注心理健康状况"},
            {"min_score": 10, "level": "info", "title": "PHQ-9评分提示", 
             "message": "您的PHQ-9评分为{score}分，显示轻度抑郁倾向，建议适当调节情绪"}
        ],
        "GAD7": [
            {"min_score": 15, "level": "danger", "title": "GAD-7评分严重异常", 
             "message": "您的GAD-7评分为{score}分，显示重度焦虑倾向，建议尽快寻求专业帮助"},
            {"min_score": 10, "level": "warning", "title": "GAD-7评分异常", 
             "message": "您的GAD-7评分为{score}分，显示中度焦虑倾向，建议关注心理健康状况"},
            {"min_score": 5, "level": "info", "title": "GAD-7评分提示", 
             "message": "您的GAD-7评分为{score}分，显示轻度焦虑倾向，建议适当放松身心"}
        ]
    }
    
    template_names = {"PHQ9": "PHQ-9抑郁量表", "GAD7": "GAD-7焦虑量表"}
    result_levels = {
        "PHQ9": {10: "轻度", 15: "中度", 20: "重度"},
        "GAD7": {5: "轻度", 10: "中度", 15: "重度"}
    }
    
    if template_code not in alert_config:
        return None
    
    # 找出匹配的预警等级（从高到低）
    matched_alert = None
    for config in alert_config[template_code]:
        if score >= config["min_score"]:
            matched_alert = config
            break
    
    if not matched_alert:
        return None
    
    # 确定结果等级
    result_level = "normal"
    result_name = "正常"
    for threshold, name in sorted(result_levels[template_code].items(), reverse=True):
        if score >= threshold:
            result_level = name
            result_name = f"{name}抑郁" if template_code == "PHQ9" else f"{name}焦虑"
            break
    
    # 创建预警
    alert = {
        "id": f"alert_{uuid.uuid4().hex[:12]}",
        "user_id": user_id,
        "type": "questionnaire",
        "level": matched_alert["level"],
        "title": matched_alert["title"],
        "message": matched_alert["message"].format(score=score),
        "source_data": {
            "template_code": template_code,
            "template_name": template_names.get(template_code, "心理测评"),
            "score": score,
            "result": result_name,
            "result_level": result_level,
            "date": datetime.now().isoformat(),
            "record_id": record_id
        },
        "is_acknowledged": False,
        "created_at": datetime.now().isoformat()
    }
    
    # 保存到数据库
    await save_alert(alert)
    
    # 推送到前端
    await push_alert_to_user(user_id, alert)
    
    return alert
```

#### 1.2 情绪记录预警生成

```python
# 在用户记录情绪后调用
async def create_emotion_alert(user_id: str, emotion_record: dict):
    """
    根据情绪记录创建预警
    """
    negative_emotions = ["难过", "焦虑", "愤怒", "担忧", "疲惫", "孤独"]
    emotion = emotion_record.get("emotion")
    intensity = emotion_record.get("intensity", 0)
    
    # 检查单日高强度情绪
    if emotion in negative_emotions and intensity >= 8:
        alert = {
            "id": f"alert_{uuid.uuid4().hex[:12]}",
            "user_id": user_id,
            "type": "emotion",
            "level": "warning",
            "title": "高强度情绪预警",
            "message": f"您今日记录的{emotion}情绪强度较高，建议适当调节",
            "source_data": {
                "emotion": emotion,
                "intensity": intensity,
                "date": emotion_record.get("date")
            },
            "is_acknowledged": False,
            "created_at": datetime.now().isoformat()
        }
        await save_alert(alert)
        await push_alert_to_user(user_id, alert)
        return alert
    
    # 检查连续负面情绪
    consecutive_days = await get_consecutive_negative_days(user_id)
    if consecutive_days >= 7:
        # 获取最近7天的情绪记录
        recent_records = await get_recent_emotion_records(user_id, days=7)
        alert = {
            "id": f"alert_{uuid.uuid4().hex[:12]}",
            "user_id": user_id,
            "type": "emotion",
            "level": "danger",
            "title": "连续负面情绪预警",
            "message": "您已连续7天记录负面情绪，系统检测到情绪状态异常",
            "source_data": {
                "consecutive_days": consecutive_days,
                "emotion_records": recent_records,
                "summary": f"连续一周负面情绪，{recent_records[0]['emotion']}情绪占主导"
            },
            "is_acknowledged": False,
            "created_at": datetime.now().isoformat()
        }
        await save_alert(alert)
        await push_alert_to_user(user_id, alert)
        return alert
    elif consecutive_days >= 3:
        recent_records = await get_recent_emotion_records(user_id, days=3)
        alert = {
            "id": f"alert_{uuid.uuid4().hex[:12]}",
            "user_id": user_id,
            "type": "emotion",
            "level": "warning",
            "title": "连续负面情绪提醒",
            "message": "您已连续3天记录负面情绪，建议关注情绪变化",
            "source_data": {
                "consecutive_days": consecutive_days,
                "emotion_records": recent_records
            },
            "is_acknowledged": False,
            "created_at": datetime.now().isoformat()
        }
        await save_alert(alert)
        await push_alert_to_user(user_id, alert)
        return alert
    
    return None

async def get_consecutive_negative_days(user_id: str) -> int:
    """
    获取连续记录负面情绪的天数
    """
    negative_emotions = ["难过", "焦虑", "愤怒", "担忧", "疲惫", "孤独"]
    records = await get_user_emotion_records(user_id, days=30)
    
    consecutive = 0
    for record in reversed(records):  # 从最近开始
        if record["emotion"] in negative_emotions:
            consecutive += 1
        else:
            break
    
    return consecutive
```

#### 1.3 对话内容预警生成

```python
# 在AI分析对话内容后调用
async def create_conversation_alert(user_id: str, session_id: str, analysis_result: dict):
    """
    根据对话分析结果创建预警
    """
    crisis_keywords = ["自杀", "想死", "不想活", "结束生命", "了结", 
                       "自残", "割腕", "伤害自己", "活着没意义", "绝望", 
                       "没希望", "撑不下去", "受不了", "崩溃", "疯了", "控制不住"]
    
    # 检查危机关键词
    conversation_text = analysis_result.get("text", "")
    detected_keywords = [kw for kw in crisis_keywords if kw in conversation_text]
    
    if detected_keywords:
        alert = {
            "id": f"alert_{uuid.uuid4().hex[:12]}",
            "user_id": user_id,
            "type": "conversation",
            "level": "danger",
            "title": "对话危机信号检测",
            "message": "AI检测到对话内容中存在潜在危机信号词汇，需要特别关注",
            "source_data": {
                "session_id": session_id,
                "preview": conversation_text[:100] + "..." if len(conversation_text) > 100 else conversation_text,
                "emotion_intensity": analysis_result.get("emotion_intensity", 0),
                "crisis_detected": True,
                "crisis_keywords": detected_keywords[:5],  # 最多5个关键词
                "risk_level": "high"
            },
            "is_acknowledged": False,
            "created_at": datetime.now().isoformat()
        }
        await save_alert(alert)
        await push_alert_to_user(user_id, alert)
        
        # 危险预警发送额外通知（邮件/短信）
        await send_urgent_notification(user_id, alert)
        
        return alert
    
    # 检查情绪强度
    emotion_intensity = analysis_result.get("emotion_intensity", 0)
    if emotion_intensity >= 0.85:
        alert = {
            "id": f"alert_{uuid.uuid4().hex[:12]}",
            "user_id": user_id,
            "type": "conversation",
            "level": "warning",
            "title": "对话情绪异常",
            "message": "AI检测到对话中情绪强度异常，建议关注用户状态",
            "source_data": {
                "session_id": session_id,
                "preview": conversation_text[:100] + "..." if len(conversation_text) > 100 else conversation_text,
                "emotion_intensity": emotion_intensity,
                "crisis_detected": False,
                "risk_level": "medium"
            },
            "is_acknowledged": False,
            "created_at": datetime.now().isoformat()
        }
        await save_alert(alert)
        await push_alert_to_user(user_id, alert)
        return alert
    
    return None
```

### 2. WebSocket 推送逻辑

```python
# WebSocket连接管理器
class AlertWebSocketManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, user_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[user_id] = websocket
        # 发送连接成功消息
        await websocket.send_json({
            "type": "connected",
            "timestamp": datetime.now().isoformat(),
            "message": "WebSocket连接成功"
        })
    
    async def disconnect(self, user_id: str):
        if user_id in self.active_connections:
            del self.active_connections[user_id]
    
    async def push_alert(self, user_id: str, alert: dict):
        """
        向指定用户推送预警
        """
        if user_id in self.active_connections:
            websocket = self.active_connections[user_id]
            try:
                await websocket.send_json({
                    "type": "new_alert",
                    "timestamp": datetime.now().isoformat(),
                    "data": alert
                })
            except Exception as e:
                print(f"推送预警失败: {e}")
    
    async def push_alert_update(self, user_id: str, alert_id: str, update_data: dict):
        """
        推送预警状态更新
        """
        if user_id in self.active_connections:
            websocket = self.active_connections[user_id]
            try:
                await websocket.send_json({
                    "type": "update_alert",
                    "timestamp": datetime.now().isoformat(),
                    "data": {
                        "id": alert_id,
                        **update_data
                    }
                })
            except Exception as e:
                print(f"推送更新失败: {e}")

# 全局WebSocket管理器
alert_ws_manager = AlertWebSocketManager()

# FastAPI WebSocket端点
@app.websocket("/ws/alerts/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    # 验证用户token
    token = websocket.query_params.get("token")
    if not verify_token(token):
        await websocket.close(code=1008)
        return
    
    await alert_ws_manager.connect(user_id, websocket)
    
    try:
        while True:
            # 接收心跳响应
            data = await websocket.receive_json()
            if data.get("type") == "pong":
                # 更新最后活跃时间
                pass
    except WebSocketDisconnect:
        await alert_ws_manager.disconnect(user_id)

# 推送预警的辅助函数
async def push_alert_to_user(user_id: str, alert: dict):
    await alert_ws_manager.push_alert(user_id, alert)
```

### 3. 定时任务（情绪预警检查）

```python
# 使用APScheduler或Celery实现定时任务
from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler()

@scheduler.scheduled_job("cron", hour=0, minute=0)
async def daily_emotion_check():
    """
    每日检查所有用户的情绪记录，生成预警
    """
    users = await get_all_active_users()
    
    for user in users:
        user_id = user["id"]
        
        # 检查连续负面情绪
        consecutive_days = await get_consecutive_negative_days(user_id)
        if consecutive_days >= 3:
            # 检查是否已存在未确认的连续情绪预警
            existing_alert = await get_unacknowledged_alert(
                user_id, "emotion", "连续负面情绪"
            )
            if not existing_alert:
                await create_emotion_alert(user_id, {"emotion": "", "intensity": 0})

# 启动定时任务
scheduler.start()
```

### 4. 确认预警时的WebSocket推送

```python
@app.post("/api/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: str, request: AcknowledgeRequest):
    """
    确认预警，并推送给其他设备
    """
    # 更新数据库
    alert = await update_alert_acknowledgment(
        alert_id=alert_id,
        user_id=request.user_id,
        acknowledged_at=datetime.now(),
        notes=request.notes
    )
    
    if alert:
        # 推送更新给用户的所有设备
        await alert_ws_manager.push_alert_update(
            user_id=alert["user_id"],
            alert_id=alert_id,
            update_data={
                "is_acknowledged": True,
                "acknowledged_at": alert["acknowledged_at"],
                "acknowledged_by": request.user_id
            }
        )
    
    return {"code": 200, "message": "success", "data": alert}
```

---

## 七、测试建议

### 1. 单元测试

- 测试各种触发规则是否正确
- 测试预警生成逻辑
- 测试确认预警接口

### 2. 集成测试

- 测试WebSocket实时推送
- 测试前端与后端数据交互
- 测试并发场景

### 3. 模拟数据

```python
# 模拟预警数据生成脚本
def mock_alerts(user_id, count=10):
    alerts = []
    for i in range(count):
        alert = {
            "id": f"alert_{i:03d}",
            "user_id": user_id,
            "type": random.choice(["questionnaire", "emotion", "conversation"]),
            "level": random.choice(["info", "warning", "danger"]),
            "title": f"模拟预警标题 {i}",
            "message": f"模拟预警内容 {i}",
            "is_acknowledged": random.choice([True, False]),
            "created_at": (datetime.now() - timedelta(days=random.randint(0, 7))).isoformat()
        }
        alerts.append(alert)
    return alerts
```

---

**文档版本**: v1.0  
**创建日期**: 2026-03-30  
**更新日期**: 2026-03-30  
**作者**: 前端开发团队
