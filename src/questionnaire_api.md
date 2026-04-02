# 问卷自测系统 API 接口文档

## 概述

本文档描述了心理AI助手系统的问卷自测模块API接口，包括PHQ-9抑郁量表和GAD-7焦虑量表的获取、提交、跳过和历史记录查询等功能。

## 基础信息

- **基础URL**: `http://localhost:8000`
- **路由前缀**: `/api/questionnaires`
- **Content-Type**: `application/json`

## 数据表结构

### 1. questionnaire\_templates（问卷模板表）

存储问卷的基本信息和题目配置。

| 字段             | 类型           | 说明                               |
| -------------- | ------------ | -------------------------------- |
| id             | BIGINT       | 主键，自增                            |
| code           | VARCHAR(50)  | 问卷编码：PHQ9/GAD7/TCM\_CONSTITUTION |
| name           | VARCHAR(100) | 问卷名称                             |
| description    | TEXT         | 问卷说明                             |
| questions      | JSON         | 题目配置JSON                         |
| scoring\_rules | JSON         | 评分规则                             |
| version        | INT          | 版本号，默认1                          |
| is\_active     | BOOLEAN      | 是否启用，默认true                      |
| created\_at    | TIMESTAMP    | 创建时间                             |
| updated\_at    | TIMESTAMP    | 更新时间                             |

### 2. user\_questionnaire\_records（用户问卷记录表）

存储用户提交的问卷答案和结果。

| 字段               | 类型          | 说明                                       |
| ---------------- | ----------- | ---------------------------------------- |
| id               | BIGINT      | 主键，自增                                    |
| user\_id         | VARCHAR(50) | 用户ID                                     |
| template\_code   | VARCHAR(50) | 问卷类型编码                                   |
| answers          | JSON        | 答案详情 `[{question_id, option_id, score}]` |
| total\_score     | INT         | 总分                                       |
| result\_level    | VARCHAR(20) | 结果等级：none/mild/moderate/severe           |
| result\_analysis | JSON        | 结果分析                                     |
| created\_at      | TIMESTAMP   | 创建时间                                     |

### 3. user\_questionnaire\_schedule（问卷调度表）

控制用户的下次检测时间。

| 字段                  | 类型          | 说明          |
| ------------------- | ----------- | ----------- |
| id                  | BIGINT      | 主键，自增       |
| user\_id            | VARCHAR(50) | 用户ID        |
| template\_code      | VARCHAR(50) | 问卷类型编码      |
| first\_login\_at    | TIMESTAMP   | 首次登录时间      |
| last\_completed\_at | TIMESTAMP   | 上次完成时间      |
| next\_due\_at       | TIMESTAMP   | 下次应测时间      |
| skipped\_count      | INT         | 连续跳过次数，默认0  |
| is\_first\_time     | BOOLEAN     | 是否首次，默认true |
| created\_at         | TIMESTAMP   | 创建时间        |
| updated\_at         | TIMESTAMP   | 更新时间        |

### 4. questionnaire\_scoring\_rules（问卷评分规则表）

存储评分规则。

| 字段             | 类型          | 说明                                   |
| -------------- | ----------- | ------------------------------------ |
| id             | BIGINT      | 主键，自增                                |
| template\_code | VARCHAR(50) | 问卷编码                                 |
| rule\_type     | ENUM        | 规则类型：level/suggestion/interval/alert |
| rule\_config   | JSON        | 规则配置                                 |
| priority       | INT         | 优先级，默认0                              |
| is\_active     | BOOLEAN     | 是否启用，默认true                          |
| created\_at    | TIMESTAMP   | 创建时间                                 |

## API 接口列表

### 1. 获取待测问卷列表

获取当前用户需要填写的问卷列表。

**请求信息**

- **方法**: GET
- **路径**: `/api/questionnaires/next-due`
- **查询参数**:
  - `user_id` (string, 必需): 用户ID

**响应示例**

```json
{
  "code": 200,
  "data": [
    {
      "template_code": "GAD7",
      "template_name": "GAD-7 焦虑量表",
      "due_at": "2026-03-30T14:06:17",
      "days_overdue": 0
    },
    {
      "template_code": "PHQ9",
      "template_name": "PHQ-9 抑郁量表",
      "due_at": "2026-03-30T14:06:17",
      "days_overdue": 0
    }
  ]
}
```

**字段说明**

| 字段             | 类型       | 说明   |
| -------------- | -------- | ---- |
| template\_code | string   | 问卷编码 |
| template\_name | string   | 问卷名称 |
| due\_at        | datetime | 应测时间 |
| days\_overdue  | int      | 逾期天数 |

**业务逻辑**

1. 首次调用时会自动初始化用户的问卷调度记录
2. 查询 `user_questionnaire_schedule` 表中 `next_due_at <= now()` 的记录
3. 计算 `days_overdue = datediff(now(), next_due_at)`

***

### 2. 获取问卷模板

获取指定问卷的完整题目配置。

**请求信息**

- **方法**: GET
- **路径**: `/api/questionnaires/{code}/template`
- **路径参数**:
  - `code` (string, 必需): 问卷编码，如 PHQ9、GAD7

**响应示例**

```json
{
  "code": 200,
  "data": {
    "code": "PHQ9",
    "name": "PHQ-9 抑郁量表",
    "description": "用于筛查抑郁症状的严重程度",
    "questions": [
      {
        "id": "phq-1",
        "type": "phq9",
        "text": "对做事提不起劲或没有兴趣",
        "options": [
          {"id": "o0", "label": "完全没有", "desc": "0天", "score": 0},
          {"id": "o1", "label": "有几天", "desc": "1～4天", "score": 1},
          {"id": "o2", "label": "一半以上天数", "desc": "5～9天", "score": 2},
          {"id": "o3", "label": "几乎每天", "desc": "10～14天", "score": 3}
        ]
      }
    ]
  }
}
```

**题目字段说明**

| 字段      | 类型     | 说明     |
| ------- | ------ | ------ |
| id      | string | 题目唯一标识 |
| type    | string | 题目类型   |
| text    | string | 题目文本   |
| options | array  | 选项列表   |

**选项字段说明**

| 字段    | 类型     | 说明         |
| ----- | ------ | ---------- |
| id    | string | 选项唯一标识     |
| label | string | 选项标签（显示文字） |
| desc  | string | 选项描述       |
| score | int    | 选项分值       |

***

### 3. 提交问卷

提交用户的问卷答案并获取评分结果。

**请求信息**

- **方法**: POST
- **路径**: *`/api/questionnaires/submit`*
- **查询参数**:
  - `user_id` (string, 必需): 用户ID
- **请求体**:

```json
{
  "template_code": "PHQ9",
  "answers": [
    {"question_id": "phq-1", "option_id": "o1", "score": 1},
    {"question_id": "phq-2", "option_id": "o1", "score": 1},
    {"question_id": "phq-3", "option_id": "o2", "score": 2},
    {"question_id": "phq-4", "option_id": "o1", "score": 1},
    {"question_id": "phq-5", "option_id": "o0", "score": 0},
    {"question_id": "phq-6", "option_id": "o1", "score": 1},
    {"question_id": "phq-7", "option_id": "o1", "score": 1},
    {"question_id": "phq-8", "option_id": "o0", "score": 0},
    {"question_id": "phq-9", "option_id": "o0", "score": 0}
  ]
}
```

**请求体字段说明**

| 字段                      | 类型     | 说明   |
| ----------------------- | ------ | ---- |
| template\_code          | string | 问卷编码 |
| answers                 | array  | 答案列表 |
| answers\[].question\_id | string | 题目ID |
| answers\[].option\_id   | string | 选项ID |
| answers\[].score        | int    | 选项分值 |

**响应示例**

```json
{
  "code": 200,
  "data": {
    "record_id": "12345",
    "total_score": 7,
    "result_level": "mild",
    "result_level_text": "轻度抑郁",
    "result_analysis": {
      "summary": "根据您的回答，您目前处于轻度抑郁状态",
      "risk_level": "normal",
      "suggestions": [
        "建议保持规律作息",
        "适当进行运动锻炼",
        "如有需要可寻求专业帮助"
      ],
      "alert": null,
      "total_questions": 9,
      "answered_questions": 9
    },
    "next_due_at": "2026-04-02T14:30:00"
  }
}
```

**响应字段说明**

| 字段                           | 类型       | 说明               |
| ---------------------------- | -------- | ---------------- |
| record\_id                   | string   | 记录ID             |
| total\_score                 | int      | 总分               |
| result\_level                | string   | 结果等级编码           |
| result\_level\_text          | string   | 结果等级文本           |
| result\_analysis.summary     | string   | 结果总结             |
| result\_analysis.risk\_level | string   | 风险等级：normal/high |
| result\_analysis.suggestions | array    | 建议列表             |
| result\_analysis.alert       | object   | 高危预警信息（如有）       |
| next\_due\_at                | datetime | 下次应测时间           |

**业务逻辑**

1. 验证用户是否存在
2. 验证答案完整性（是否回答了所有题目）
3. 计算总分
4. 根据评分规则判断等级
5. 检查高危预警（PHQ-9第9题自杀倾向）
6. 保存记录到 `user_questionnaire_records`
7. 更新 `user_questionnaire_schedule` 的下次检测时间

**PHQ-9 评分标准**

| 总分    | 等级                 | 说明    |
| ----- | ------------------ | ----- |
| 0-4   | none               | 无抑郁   |
| 5-9   | mild               | 轻度抑郁  |
| 10-14 | moderate           | 中度抑郁  |
| 15-19 | moderately\_severe | 中重度抑郁 |
| 20-27 | severe             | 重度抑郁  |

**GAD-7 评分标准**

| 总分    | 等级       | 说明   |
| ----- | -------- | ---- |
| 0-4   | none     | 无焦虑  |
| 5-9   | mild     | 轻度焦虑 |
| 10-14 | moderate | 中度焦虑 |
| 15-21 | severe   | 重度焦虑 |

***

### 4. 跳过问卷

跳过当前问卷，推迟到下次检测。

**请求信息**

- **方法**: POST
- **路径**: `/api/questionnaires/skip`
- **查询参数**:
  - `user_id` (string, 必需): 用户ID
- **请求体**:

```json
{
  "template_code": "GAD7"
}
```

**响应示例**

```json
{
  "code": 200,
  "data": {
    "next_remind_at": "2026-03-31T14:07:31"
  }
}
```

**业务逻辑**

1. 更新 `user_questionnaire_schedule` 表
2. `skipped_count` 加1
3. `next_due_at` 设置为明天同一时间
4. 如果必填问卷跳过次数超过3次，可触发强制提醒（WebSocket）

***

### 5. 获取历史记录

获取用户的历史问卷记录和趋势数据。

**请求信息**

- **方法**: GET
- **路径**: `/api/questionnaires/history`
- **查询参数**:
  - `user_id` (string, 必需): 用户ID
  - `template_code` (string, 可选): 问卷编码，默认PHQ9
  - `limit` (int, 可选): 返回记录数量，默认5

**响应示例**

```json
{
  "code": 200,
  "data": {
    "template_code": "PHQ9",
    "template_name": "PHQ-9 抑郁量表",
    "records": [
      {
        "id": 1,
        "total_score": 7,
        "result_level": "mild",
        "result_level_text": "轻度抑郁",
        "created_at": "2026-03-30T14:30:00"
      }
    ],
    "trend_data": [
      {
        "date": "2026-03-30",
        "score": 7
      }
    ]
  }
}
```

**响应字段说明**

| 字段                             | 类型       | 说明     |
| ------------------------------ | -------- | ------ |
| template\_code                 | string   | 问卷编码   |
| template\_name                 | string   | 问卷名称   |
| records                        | array    | 历史记录列表 |
| records\[].id                  | int      | 记录ID   |
| records\[].total\_score        | int      | 总分     |
| records\[].result\_level       | string   | 结果等级   |
| records\[].result\_level\_text | string   | 结果等级文本 |
| records\[].created\_at         | datetime | 创建时间   |
| trend\_data                    | array    | 趋势数据   |
| trend\_data\[].date            | string   | 日期     |
| trend\_data\[].score           | int      | 当日分数   |

***

## 问卷内容详情

### PHQ-9 抑郁量表（9道题）

| 题号 | 题目内容                     |
| -- | ------------------------ |
| 1  | 对做事提不起劲或没有兴趣             |
| 2  | 感到心情低落、沮丧或绝望             |
| 3  | 入睡困难、睡不安稳或睡眠过多           |
| 4  | 感觉疲倦或没有活力                |
| 5  | 食欲不振或吃太多                 |
| 6  | 觉得自己很糟，或觉得自己很失败，让自己或家人失望 |
| 7  | 对事物专注有困难（例如阅读、看手机、看电视）   |
| 8  | 动作或说话速度特别缓慢，或相反：烦躁、坐立不安  |
| 9  | 有不如死掉或用某种方式伤害自己的念头 ⚠️    |

**⚠️ 高危预警**：第9题（自杀倾向）如果得分≥1分，系统会触发高危预警。

### GAD-7 焦虑量表（7道题）

| 题号 | 题目内容              |
| -- | ----------------- |
| 1  | 感觉紧张、焦虑或烦躁        |
| 2  | 不能停止或控制担忧         |
| 3  | 对各种事情过分担忧         |
| 4  | 很难放松下来            |
| 5  | 由于不安而无法静坐         |
| 6  | 容易生气或发怒           |
| 7  | 感到害怕，似乎有可怕的事情即将发生 |

### 评分选项（每道题）

| 选项     | 分值 | 说明     |
| ------ | -- | ------ |
| 完全没有   | 0  | 0天     |
| 有几天    | 1  | 1～4天   |
| 一半以上天数 | 2  | 5～9天   |
| 几乎每天   | 3  | 10～14天 |

***

## 测试账号

- **用户名**: pym
- **密码**: pym123456

## 错误码说明

| HTTP状态码 | 说明                    |
| ------- | --------------------- |
| 200     | 请求成功                  |
| 400     | 请求参数错误（如答案不完整）        |
| 404     | 资源不存在（如用户不存在、问卷模板不存在） |
| 422     | 请求体格式错误               |
| 500     | 服务器内部错误               |

***

## 前端集成建议

1. **首次登录时**：调用 `/next-due` 获取待测问卷列表
2. **展示问卷**：调用 `/{code}/template` 获取题目，渲染表单
3. **提交答案**：调用 `/submit` 提交，展示结果和建议
4. **跳过问卷**：调用 `/skip` 推迟到下次
5. **历史记录**：调用 `/history` 展示趋势图表

***

## 相关文件

- **路由实现**: `backend/api/v1/questionnaire_new_endpoints.py`
- **数据模型**: `backend/core/database.py`
- **Pydantic模型**: `backend/core/data_models.py`
- **初始化脚本**: `init_questionnaires.py`
- **测试脚本**: `test_with_user_account.py`

***

*文档生成时间: 2026-03-30*
