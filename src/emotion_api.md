# 情绪记录功能后端接口文档

## 功能概述

情绪记录功能允许用户记录每日情绪状态，支持：
- 快速情绪记录（选择表情+签名）
- 情绪历史查看
- 日历视图展示
- 情绪趋势分析
- 情绪分布统计
- 智能提醒机制

---

## 数据库表设计

### 1. 情绪记录表 (emotion_records)

```sql
CREATE TABLE emotion_records (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NOT NULL COMMENT '用户ID',
    emotion_type VARCHAR(50) NOT NULL COMMENT '情绪类型：happy/excited/calm/tired/sad/anxious/angry/worried/grateful/confused/peaceful/lonely',
    emotion_icon VARCHAR(10) NOT NULL COMMENT '情绪图标emoji',
    emotion_name VARCHAR(20) NOT NULL COMMENT '情绪名称',
    emotion_color VARCHAR(20) NOT NULL COMMENT '情绪颜色代码',
    signature VARCHAR(200) COMMENT '用户签名/备注',
    record_date DATE NOT NULL COMMENT '记录日期',
    record_time TIME NOT NULL COMMENT '记录时间',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_user_date (user_id, record_date),
    INDEX idx_user_created (user_id, created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='情绪记录表';
```

### 2. 情绪提醒配置表 (emotion_remind_settings)

```sql
CREATE TABLE emotion_remind_settings (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NOT NULL UNIQUE COMMENT '用户ID',
    remind_enabled BOOLEAN DEFAULT TRUE COMMENT '是否启用提醒',
    remind_times INT DEFAULT 2 COMMENT '每日提醒次数',
    remind_interval INT DEFAULT 360 COMMENT '提醒间隔（分钟）',
    last_remind_at TIMESTAMP NULL COMMENT '上次提醒时间',
    next_remind_at TIMESTAMP NULL COMMENT '下次提醒时间',
    last_record_at TIMESTAMP NULL COMMENT '上次记录时间',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='情绪提醒配置表';
```

---

## API 接口列表

### 1. 记录情绪

**接口地址**: `POST /api/emotions/record`

**请求头**:
```
Authorization: Bearer {access_token}
Content-Type: application/json
```

**请求体**:
```json
{
  "emotion_type": "happy",
  "emotion_icon": "😊",
  "emotion_name": "开心",
  "emotion_color": "#FFD93D",
  "signature": "今天天气很好！",
  "record_date": "2026-03-31",
  "record_time": "14:30:25"
}
```

**字段说明**:
| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| emotion_type | string | 是 | 情绪类型标识 |
| emotion_icon | string | 是 | Emoji图标 |
| emotion_name | string | 是 | 情绪中文名称 |
| emotion_color | string | 是 | 颜色代码(HEX) |
| signature | string | 否 | 用户签名，最多200字符 |
| record_date | string | 是 | 记录日期，格式YYYY-MM-DD |
| record_time | string | 是 | 记录时间，格式HH:mm:ss |

**响应示例**:
```json
{
  "code": 200,
  "message": "记录成功",
  "data": {
    "id": 123,
    "emotion_type": "happy",
    "emotion_icon": "😊",
    "record_date": "2026-03-31",
    "created_at": "2026-03-31T14:30:25Z"
  }
}
```

---

### 2. 获取情绪历史记录

**接口地址**: `GET /api/emotions/history`

**请求头**:
```
Authorization: Bearer {access_token}
```

**查询参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| limit | int | 否 | 返回数量限制，默认50 |
| offset | int | 否 | 分页偏移量，默认0 |
| start_date | string | 否 | 开始日期，格式YYYY-MM-DD |
| end_date | string | 否 | 结束日期，格式YYYY-MM-DD |

**响应示例**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "total": 100,
    "records": [
      {
        "id": 123,
        "emotion_type": "happy",
        "emotion_icon": "😊",
        "emotion_name": "开心",
        "emotion_color": "#FFD93D",
        "signature": "今天天气很好！",
        "record_date": "2026-03-31",
        "record_time": "14:30:25",
        "created_at": "2026-03-31T14:30:25Z"
      }
    ]
  }
}
```

---

### 3. 获取日历数据

**接口地址**: `GET /api/emotions/calendar`

**请求头**:
```
Authorization: Bearer {access_token}
```

**查询参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| year | int | 是 | 年份，如2026 |
| month | int | 是 | 月份，1-12 |

**响应示例**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "year": 2026,
    "month": 3,
    "days": [
      {
        "date": "2026-03-31",
        "day": 31,
        "has_record": true,
        "record": {
          "id": 123,
          "emotion_type": "happy",
          "emotion_icon": "😊",
          "emotion_color": "#FFD93D"
        }
      },
      {
        "date": "2026-03-30",
        "day": 30,
        "has_record": false,
        "record": null
      }
    ]
  }
}
```

---

### 4. 获取情绪统计数据

**接口地址**: `GET /api/emotions/statistics`

**请求头**:
```
Authorization: Bearer {access_token}
```

**查询参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| days | int | 否 | 统计天数，默认30，可选7/30/90 |

**响应示例**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "period": {
      "days": 30,
      "start_date": "2026-03-01",
      "end_date": "2026-03-31"
    },
    "total_records": 25,
    "daily_average": 0.83,
    "distribution": [
      {
        "type": "happy",
        "name": "开心",
        "color": "#FFD93D",
        "count": 10,
        "percent": 40
      },
      {
        "type": "calm",
        "name": "平静",
        "color": "#6BCB77",
        "count": 8,
        "percent": 32
      }
    ],
    "trend": [
      {
        "date": "2026-03-31",
        "emotion_type": "happy",
        "emotion_score": 8,
        "has_record": true
      }
    ]
  }
}
```

**情绪分值映射**（用于趋势分析）:
| 情绪类型 | 分值 |
|---------|------|
| excited | 9 |
| happy, grateful | 8 |
| peaceful | 7 |
| calm | 6 |
| tired, confused | 4 |
| worried, lonely | 3 |
| sad, anxious | 2 |
| angry | 1 |

---

### 5. 检查下次提醒

**接口地址**: `GET /api/emotions/next-remind`

**请求头**:
```
Authorization: Bearer {access_token}
```

**响应示例**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "need_remind": true,
    "reason": "距离上次记录已超过6小时",
    "next_remind_at": "2026-03-31T20:00:00Z",
    "last_record": {
      "id": 123,
      "emotion_type": "happy",
      "emotion_icon": "😊",
      "record_date": "2026-03-31",
      "record_time": "14:30:25"
    }
  }
}
```

**提醒逻辑**:
- 每日最多提醒2次
- 默认间隔6小时（360分钟）
- 用户记录后重置计时
- 可配置是否启用提醒

---

### 6. 跳过本次提醒

**接口地址**: `POST /api/emotions/skip-remind`

**请求头**:
```
Authorization: Bearer {access_token}
```

**响应示例**:
```json
{
  "code": 200,
  "message": "已跳过本次提醒",
  "data": {
    "next_remind_at": "2026-03-31T20:00:00Z"
  }
}
```

---

### 7. 获取提醒设置

**接口地址**: `GET /api/emotions/remind-settings`

**请求头**:
```
Authorization: Bearer {access_token}
```

**响应示例**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "remind_enabled": true,
    "remind_times": 2,
    "remind_interval": 360,
    "last_remind_at": "2026-03-31T08:00:00Z",
    "next_remind_at": "2026-03-31T14:00:00Z"
  }
}
```

---

### 8. 更新提醒设置

**接口地址**: `PUT /api/emotions/remind-settings`

**请求头**:
```
Authorization: Bearer {access_token}
Content-Type: application/json
```

**请求体**:
```json
{
  "remind_enabled": true,
  "remind_times": 2,
  "remind_interval": 360
}
```

**字段说明**:
| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| remind_enabled | boolean | 是 | 是否启用提醒 |
| remind_times | int | 否 | 每日提醒次数，默认2 |
| remind_interval | int | 否 | 提醒间隔分钟数，默认360 |

**响应示例**:
```json
{
  "code": 200,
  "message": "设置已更新",
  "data": {
    "remind_enabled": true,
    "remind_times": 2,
    "remind_interval": 360
  }
}
```

---

## 前端组件说明

### 主要组件

1. **EmotionRecordPage.vue** - 情绪记录主页面
   - 快速记录区域
   - 日历视图
   - 情绪趋势图表
   - 情绪分布统计
   - 历史记录列表

2. **EmotionTrendChart.vue** - 情绪趋势图表组件
   - 自动调整大小
   - 支持7/30/90天视图切换
   - 使用ECharts绘制

3. **EmotionQuickModal.vue** - 快速记录弹窗
   - 12种情绪选择
   - 签名输入
   - 最近情绪快捷选择

4. **emotion.js (Pinia Store)** - 状态管理
   - 记录情绪
   - 获取历史
   - 日历数据
   - 统计分析
   - 提醒检查

---

## 情绪类型定义

```javascript
const emotionTags = [
  { type: 'happy',    icon: '😊', name: '开心',  color: '#FFD93D' },
  { type: 'excited',  icon: '🤩', name: '兴奋',  color: '#FF6B6B' },
  { type: 'calm',     icon: '😌', name: '平静',  color: '#6BCB77' },
  { type: 'tired',    icon: '😴', name: '疲惫',  color: '#95A5A6' },
  { type: 'sad',      icon: '😢', name: '难过',  color: '#74B9FF' },
  { type: 'anxious',  icon: '😰', name: '焦虑',  color: '#E17055' },
  { type: 'angry',    icon: '😠', name: '愤怒',  color: '#D63031' },
  { type: 'worried',  icon: '😟', name: '担忧',  color: '#FD79A8' },
  { type: 'grateful', icon: '🥰', name: '感恩',  color: '#FDCB6E' },
  { type: 'confused', icon: '😕', name: '困惑',  color: '#A29BFE' },
  { type: 'peaceful', icon: '🧘', name: '安宁',  color: '#00B894' },
  { type: 'lonely',   icon: '🥺', name: '孤独',  color: '#636E72' }
]
```

---

## 开发注意事项

1. **数据权限**: 所有接口必须验证用户身份，用户只能访问自己的数据
2. **日期处理**: 前端使用本地时间，后端存储为UTC时间
3. **重复记录**: 同一天允许多次记录，以最新记录为准
4. **提醒逻辑**: 需要后端定时任务检查并触发提醒
5. **性能优化**: 日历接口按月返回数据，避免一次性返回过多数据

---

## 需要后端配合的逻辑

### 1. 情绪记录接口 (POST /api/emotions/record)

**当前问题**: 后端可能返回 422 错误，提示缺少必填字段

**需要后端配合**:
- 确保接口接收所有必填字段: `emotion_type`, `emotion_icon`, `emotion_name`, `emotion_color`, `record_date`, `record_time`
- `signature` 字段为可选
- 返回格式需符合标准响应格式: `{ code: 200, message: "记录成功", data: {...} }`

**前端已发送的数据格式**:
```json
{
  "emotion_type": "happy",
  "emotion_icon": "😊",
  "emotion_name": "开心",
  "emotion_color": "#FFD93D",
  "signature": "",
  "record_date": "2026-03-31",
  "record_time": "14:30:25"
}
```

### 2. 日历数据接口 (GET /api/emotions/calendar)

**当前问题**: 前端目前使用本地计算，未调用此接口

**需要后端配合**:
- 确保接口返回格式与文档一致
- `days` 数组需包含完整的月份数据（包括前后补全的日期）
- 每个日期需包含: `date`, `day`, `has_record`, `record`

**前端期望的响应格式**:
```json
{
  "code": 200,
  "data": {
    "year": 2026,
    "month": 3,
    "days": [
      {
        "date": "2026-03-31",
        "day": 31,
        "has_record": true,
        "record": {
          "id": 123,
          "emotion_type": "happy",
          "emotion_icon": "😊",
          "emotion_color": "#FFD93D"
        }
      }
    ]
  }
}
```

### 3. 统计数据接口 (GET /api/emotions/statistics)

**当前问题**: 前端目前使用本地计算，未调用此接口

**需要后端配合**:
- 确保接口返回格式与文档一致
- `distribution` 需按 count 降序排列
- `trend` 需包含情绪分值映射（见文档情绪分值映射表）

**前端期望的响应格式**:
```json
{
  "code": 200,
  "data": {
    "period": { "days": 30, "start_date": "2026-03-01", "end_date": "2026-03-31" },
    "total_records": 25,
    "daily_average": 0.83,
    "distribution": [
      { "type": "happy", "name": "开心", "color": "#FFD93D", "count": 10, "percent": 40 }
    ],
    "trend": [
      { "date": "2026-03-31", "emotion_type": "happy", "emotion_score": 8, "has_record": true }
    ]
  }
}
```

### 4. 提醒设置接口

**当前状态**: 前端 store 中未实现这两个接口

**需要后端配合**:
- GET `/api/emotions/remind-settings` - 获取用户提醒配置
- PUT `/api/emotions/remind-settings` - 更新用户提醒配置

**前端将实现的调用**:
```javascript
// 获取提醒设置
const fetchRemindSettings = async () => {
  const data = await request('/api/emotions/remind-settings')
  return data
}

// 更新提醒设置
const updateRemindSettings = async (settings) => {
  const data = await request('/api/emotions/remind-settings', {
    method: 'PUT',
    body: JSON.stringify(settings)
  })
  return data
}
```

---

## 相关文件

- `src/components/emotion/EmotionRecordPage.vue` - 主页面
- `src/components/emotion/EmotionTrendChart.vue` - 趋势图表组件
- `src/components/emotion/EmotionQuickModal.vue` - 快速记录弹窗
- `src/stores/emotion.js` - Pinia状态管理
